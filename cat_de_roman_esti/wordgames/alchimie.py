"""Alchimie — a bounded, target-oriented crafting game over the Romanian KG.

The shared graph is discovery input, not the live recipe book.  At game creation the
server deterministically projects one to four short target-useful routes.  That sparse
projection is stored in the session; a submitted pair normally
produces one clear result (never more than two), instead of every shared graph neighbour.
The goal is to craft a hidden TARGET concept into the inventory.

Server-authoritative: the whole game (seeds, target, inventory) lives here. The target
id is never echoed back until it has actually been discovered (``won``). Each instance is
*built to be solvable*: the target is drawn from the combine-CLOSURE of the seed
inventory (a fixpoint over ``common_neighbors``), at a depth of at least two generations
so it takes several combines rather than a single obvious pairing.  Recipe routes and
the target id remain server-side.
"""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import combinations

from django.urls import path
from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.response import Response

from ..web.http import (
    ContractAPIView,
    OptionalSessionAuth,
    http_error,
    parse_body,
    query_int,
    query_str,
)
from ._progress import excluded_pack_ids, record_finished
from .categories import category_label, is_known, known_keys
from .packs import (
    ALCHIMIE_MAX_ACTIONS,
    ALCHIMIE_MAX_SEARCH_STATES,
    get_pack,
)
from .service import SessionStore, WordGameService, daily_seed, get_service

GAME_KEY = "alchimie"

# A combine-closure must produce a target at least this many generations deep so the
# puzzle takes a few crafts (generation 1 == a direct common neighbour of two seeds).
MIN_TARGET_GENERATION = 2
# How many random seed sets to try before giving up on building a deep instance.
MAX_BUILD_ATTEMPTS = 400
# Seed inventory size range (recognizable, higher-salience nodes).
SEED_MIN, SEED_MAX = 5, 7
# Only consider reasonably salient (recognizable) nodes as seeds.
SEED_SALIENCE_FLOOR = 0.4
# Seeds must be recognizable AND have a couple of real edges so they are combinable.
SEED_MIN_DEGREE = 2
# A "good" mined instance offers several openings: at least this many seed-inventory
# pairs must yield a fresh result in that target's private recipe projection. Counting
# the broader graph here would promise choices that runtime intentionally hides.
MIN_OPENING_PAIRS = 2
# Targets should themselves be recognizable, not obscure intermediates.
TARGET_SALIENCE_FLOOR = 0.4
# Greu targets can otherwise sprawl very deep (gen 7+); cap so a game stays finishable.
GREU_MAX_GENERATION = 5
# How many consecutive fruitless combines before a gentle nudge becomes available.
NUDGE_AFTER_FRUITLESS = 3
# Sparse projection bounds.  Four routes keep replay varied without reopening the whole
# category closure; two extra actions let a board expose alternate near-optimal routes.
MAX_TARGET_ROUTES = 4
ROUTE_DETOUR_ACTIONS = 2
MAX_ROUTE_CANDIDATES = 128
MAX_RECIPE_PAIRS = 24
MAX_RESULTS_PER_RECIPE = 2
MAX_PROJECTED_CONCEPTS = 32
RECENT_INVENTORY_LIMIT = 8
PREFERRED_RECIPE_STRENGTH = 0.55

# Difficulty -> (target generation policy, seed-count range).
#   usor : shallow target (generation 2) but a wide 6-7 seed inventory (more options).
#   normal: target at generation 2-3 with the default 5-7 seeds.
#   greu : deepest available target (3..GREU_MAX) with a lean 5-seed inventory.
DIFFICULTIES = {"usor", "normal", "greu"}
DEFAULT_DIFFICULTY = "normal"

RecipePair = tuple[str, str]
RecipeStep = tuple[RecipePair, tuple[str, ...]]
RecipeRoute = tuple[RecipeStep, ...]


@dataclass(frozen=True, eq=False, slots=True)
class _ProjectionServiceRef:
    """Hashable identity key that also pins the service used by one cached build."""

    service: WordGameService


_projection_cache_service_ref: _ProjectionServiceRef | None = None
_projection_cache_service_lock = threading.Lock()


def _pair_key(a: str, b: str) -> RecipePair:
    return (a, b) if a < b else (b, a)


@dataclass(frozen=True)
class RecipeProjection:
    """A private, deterministic recipe book for one target."""

    recipes: dict[RecipePair, tuple[str, ...]]
    routes: tuple[RecipeRoute, ...]
    par: int
    # Private audit metadata: quality of bounded routes discovered before selection.
    candidate_quality: tuple[tuple[int, float, float], ...]


def _difficulty_params(difficulty: str) -> tuple[int, int | None, int, int]:
    """Return (min_gen, max_gen_or_None, seed_min, seed_max) for a difficulty."""
    if difficulty == "usor":
        return (2, 2, 6, 7)
    if difficulty == "greu":
        return (3, GREU_MAX_GENERATION, 5, 5)
    return (2, 3, SEED_MIN, SEED_MAX)


@dataclass
class AlchimieSession:
    """One in-progress Alchimie game (server-side secret state)."""

    seeds: list[str]
    target: str
    # Stable API name; value is the exact minimum number of sequential combines (par).
    target_depth: int = MIN_TARGET_GENERATION
    difficulty: str = DEFAULT_DIFFICULTY
    daily: str | None = None
    # owned id -> (parent_a, parent_b) or None for the original seeds.
    owned: dict[str, tuple[str, str] | None] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    moves: int = 0
    # Consecutive combines that discovered nothing — drives the nudge offer.
    fruitless_streak: int = 0
    # Number of hints (nudges) the player has revealed; each costs a little score.
    hints_used: int = 0
    # Player- or server-selected board theme + curated-pack provenance (None for mined games).
    category: str | None = None
    pack_id: str | None = None
    # Private sparse recipe projection.  It is deliberately never serialized.
    recipes: dict[RecipePair, tuple[str, ...]] = field(default_factory=dict)
    routes: tuple[RecipeRoute, ...] = ()

    @property
    def won(self) -> bool:
        return self.target in self.owned

    @property
    def score(self) -> int:
        """Reward few combines. Perfect (==target depth) gives 1000; floor of 100.

        Each combine beyond the optimal depth costs 120 pts; each revealed hint costs
        150 pts. Score never drops below the 100 floor for a finished game.
        """
        extra = max(0, self.moves - self.target_depth)
        return max(100, 1000 - 120 * extra - 150 * self.hints_used)

    def add(self, node_id: str, parents: tuple[str, str] | None) -> None:
        if node_id not in self.owned:
            self.owned[node_id] = parents
            self.order.append(node_id)


store: SessionStore[AlchimieSession] = SessionStore()


# --------------------------------------------------------------------- instance builder
# A themed Alchimie game needs a category with enough combinable nodes to reach a target
# a few generations deep. Every known category (~80-100 nodes) clears this comfortably.
_SCOPE_MIN_NODES = SEED_MAX + 4


def _pick_scope_category(rng: random.Random, svc) -> str | None:
    """Deterministically pick a themed category for a mined (un-requested) game."""
    usable = sorted(c for c in known_keys() if len(svc.by_category(c)) >= _SCOPE_MIN_NODES)
    return rng.choice(usable) if usable else None


def _closure_with_generations(
    seeds: list[str], category: str | None = None
) -> dict[str, int]:
    """Combine-closure of ``seeds`` mapping every reachable id -> its generation.

    Generation 0 are the seeds; generation 1 are direct common neighbours of two seeds;
    generation N nodes first appear when combining items available after generation N-1.
    Fixpoint loop: keep combining all owned pairs until nothing new appears.

    ``category`` scopes projection-candidate expansion to that category's subgraph
    (ADR-0044): the dense graph closure stays bounded and themed instead of reopening the
    whole graph (where everything becomes craftable in roughly two generations).
    """
    svc = get_service()
    gen: dict[str, int] = {s: 0 for s in seeds}
    owned = set(seeds)
    g = 0
    changed = True
    while changed:
        changed = False
        g += 1
        fresh: set[str] = set()
        for a, b in combinations(sorted(owned), 2):
            for c in svc.common_neighbors(a, b, category=category):
                if c not in owned and c not in fresh:
                    fresh.add(c)
                    gen.setdefault(c, g)
        if fresh:
            owned |= fresh
            changed = True
    return gen


def _prune_route(
    raw_steps: list[tuple[RecipePair, frozenset[str]]],
    seeds: frozenset[str],
    target: str,
) -> RecipeRoute | None:
    """Keep only outputs that a graph route actually needs later.

    Full-graph actions may yield many shared neighbours at once.  Walking the route
    backwards identifies the one or two outputs that feed a later pair (or the target)
    and discards unrelated discoveries.  A step needing more than two outputs is not a
    suitable beginner recipe route.
    """
    required = {target}
    selected: list[RecipeStep] = []
    for pair, fresh in reversed(raw_steps):
        outputs = tuple(sorted(required & fresh))
        if not outputs or len(outputs) > MAX_RESULTS_PER_RECIPE:
            return None
        selected.append((pair, outputs))
        required.difference_update(outputs)
        required.update(node_id for node_id in pair if node_id not in seeds)
    if required:
        return None
    selected.reverse()
    return tuple(selected)


def _route_quality(route: RecipeRoute) -> tuple[float, float, int]:
    """Return minimum strength, mean strength, and broadest output degree.

    A recipe result is a common neighbour, so both parent→output edges exist.  Stronger
    weakest/average links read more naturally; lower-degree outputs avoid generic hubs.
    """
    svc = get_service()
    strengths: list[float] = []
    degrees: list[int] = []
    for pair, outputs in route:
        for output in outputs:
            degrees.append(svc.degree(output))
            for parent in pair:
                edge = svc.link(parent, output)
                strengths.append(edge.strength if edge is not None else 0.0)
    if not strengths:
        return (0.0, 0.0, 0)
    return (
        min(strengths),
        sum(strengths) / len(strengths),
        max(degrees, default=0),
    )


def _route_sort_key(route: RecipeRoute) -> tuple[object, ...]:
    minimum, average, broadest_degree = _route_quality(route)
    return (len(route), -minimum, -average, broadest_degree, route)


def _minimum_projected_plan(
    owned_ids: set[str],
    target: str,
    recipes: dict[RecipePair, tuple[str, ...]],
    *,
    max_actions: int = ALCHIMIE_MAX_ACTIONS,
) -> list[RecipePair] | None:
    """Return one exact deterministic plan through a sparse recipe projection."""
    start = frozenset(owned_ids)
    if target in start:
        return []
    frontier: dict[frozenset[str], list[RecipePair]] = {start: []}
    seen = {start}
    for _action in range(1, max_actions + 1):
        next_layer: dict[frozenset[str], list[RecipePair]] = {}
        for owned, plan in sorted(
            frontier.items(), key=lambda item: tuple(sorted(item[0]))
        ):
            for pair in sorted(recipes):
                if pair[0] not in owned or pair[1] not in owned:
                    continue
                fresh = frozenset(node for node in recipes[pair] if node not in owned)
                if not fresh:
                    continue
                next_plan = [*plan, pair]
                if target in fresh:
                    return next_plan
                state = owned | fresh
                if state not in seen and state not in next_layer:
                    next_layer[state] = next_plan
        if not next_layer:
            return None
        frontier = next_layer
        seen.update(frontier)
    return None


def _build_recipe_projection(
    seeds: list[str],
    target: str,
    category: str | None,
) -> RecipeProjection | None:
    svc = get_service()
    service_ref = _projection_service_cache_ref(svc)
    return _build_recipe_projection_cached(tuple(seeds), target, category, service_ref)


def _projection_service_cache_ref(svc: WordGameService) -> _ProjectionServiceRef:
    """Return the current cache key, clearing stale-service entries on a swap.

    The lock protects only the identity check and invalidation.  Projection construction
    remains outside it, so simultaneous cold builds are not serialized.  The service
    reference is also part of each LRU key, preventing an in-flight old-service build from
    becoming a cache hit after another thread has switched services and cleared the cache.
    """

    global _projection_cache_service_ref
    current = _projection_cache_service_ref
    if current is not None and current.service is svc:
        return current
    with _projection_cache_service_lock:
        current = _projection_cache_service_ref
        if current is None or current.service is not svc:
            _build_recipe_projection_cached.cache_clear()
            current = _ProjectionServiceRef(svc)
            _projection_cache_service_ref = current
        return current


@lru_cache(maxsize=512)
def _build_recipe_projection_cached(
    seeds: tuple[str, ...],
    target: str,
    category: str | None,
    service_ref: _ProjectionServiceRef,
) -> RecipeProjection | None:
    """Project a small private recipe book from the shared semantic graph.

    Search mirrors the historical exact-action game so the established par stays valid.
    Terminal paths are then backward-pruned and combined only while the explicit recipe,
    result, and concept bounds remain satisfied.  Search and selection are sorted, hence
    identical seeds/target/category always produce byte-equivalent projections.
    """
    svc = service_ref.service
    start = frozenset(seeds)
    frontier: set[frozenset[str]] = {start}
    seen: set[frozenset[str]] = {start}
    parents: dict[
        frozenset[str], tuple[frozenset[str], RecipePair, frozenset[str]]
    ] = {}
    candidates: list[RecipeRoute] = []
    minimum_par: int | None = None
    state_count = 1
    exhausted = False

    def reconstruct(
        owned: frozenset[str], pair: RecipePair, fresh: frozenset[str]
    ) -> RecipeRoute | None:
        raw_steps = [(pair, fresh)]
        state = owned
        while state != start:
            previous, previous_pair, previous_fresh = parents[state]
            raw_steps.append((previous_pair, previous_fresh))
            state = previous
        raw_steps.reverse()
        return _prune_route(raw_steps, start, target)

    for actions in range(1, ALCHIMIE_MAX_ACTIONS + 1):
        if minimum_par is not None and actions > minimum_par + ROUTE_DETOUR_ACTIONS:
            break
        next_layer: set[frozenset[str]] = set()
        for owned in sorted(frontier, key=lambda state: tuple(sorted(state))):
            for pair in combinations(sorted(owned), 2):
                fresh = frozenset(
                    node_id
                    for node_id in svc.common_neighbors(
                        pair[0], pair[1], category=category
                    )
                    if node_id not in owned
                )
                if not fresh:
                    continue
                if target in fresh:
                    if minimum_par is None:
                        minimum_par = actions
                    route = reconstruct(owned, pair, fresh)
                    if route is not None and route not in candidates:
                        candidates.append(route)
                    if len(candidates) >= MAX_ROUTE_CANDIDATES:
                        exhausted = True
                        break
                    continue
                state = owned | fresh
                if state in seen or state in next_layer:
                    continue
                state_count += 1
                if state_count > ALCHIMIE_MAX_SEARCH_STATES:
                    exhausted = True
                    break
                parents[state] = (owned, pair, fresh)
                next_layer.add(state)
            if exhausted:
                break
        if exhausted or not next_layer:
            break
        frontier = next_layer
        seen.update(frontier)

    if minimum_par is None or not candidates:
        return None

    # Human-legibility wins between equally short routes found by the bounded search:
    # protect the weakest semantic link first, then average strength, then avoid generic
    # high-degree outputs. This does not claim to enumerate every possible graph route.
    candidates.sort(key=_route_sort_key)
    candidate_quality = tuple(
        (len(route), *_route_quality(route)[:2]) for route in candidates
    )

    recipes: dict[RecipePair, set[str]] = {}
    routes: list[RecipeRoute] = []
    for route in candidates:
        minimum_strength, _average, _degree = _route_quality(route)
        # The strongest discovered shortest route is the explicit solvability fallback.
        # Additional routes must clear a semantic-strength floor; weak technical detours
        # stay hidden.
        if routes and minimum_strength < PREFERRED_RECIPE_STRENGTH:
            continue
        merged = {pair: set(outputs) for pair, outputs in recipes.items()}
        compatible = True
        for pair, outputs in route:
            proposed = set(outputs)
            existing = merged.get(pair)
            # Never manufacture a two-result recipe merely by merging two alternative
            # singleton routes.  Two outputs are retained only when one route genuinely
            # needs both together for a later step.
            if (
                existing is not None
                and len(existing) == 1
                and len(proposed) == 1
                and existing != proposed
            ):
                compatible = False
                break
            merged.setdefault(pair, set()).update(proposed)
        if not compatible or any(
            len(outputs) > MAX_RESULTS_PER_RECIPE for outputs in merged.values()
        ):
            continue
        if routes and all(
            set(outputs) <= recipes.get(pair, set()) for pair, outputs in route
        ):
            continue
        projected = set(start)
        for pair, outputs in merged.items():
            projected.update(pair)
            projected.update(outputs)
        if len(merged) > MAX_RECIPE_PAIRS or len(projected) > MAX_PROJECTED_CONCEPTS:
            continue
        recipes = merged
        routes.append(route)
        if len(routes) >= MAX_TARGET_ROUTES:
            break

    if not routes:
        return None
    frozen_recipes = {
        pair: tuple(sorted(outputs)) for pair, outputs in sorted(recipes.items())
    }
    plan = _minimum_projected_plan(set(seeds), target, frozen_recipes)
    if plan is None or len(plan) != minimum_par:
        return None
    return RecipeProjection(
        recipes=frozen_recipes,
        routes=tuple(routes),
        par=minimum_par,
        candidate_quality=candidate_quality,
    )


def _projected_opening_pair_count(
    seeds: list[str], recipes: dict[RecipePair, tuple[str, ...]]
) -> int:
    """Count seed pairs that are productive in this target's live recipe projection."""
    owned = set(seeds)
    return sum(
        any(result not in owned for result in recipes.get(_pair_key(a, b), ()))
        for a, b in combinations(sorted(owned), 2)
    )


def _grow_seed_set(
    rng: random.Random, k: int, pool: list[str], category: str | None = None
) -> list[str] | None:
    """Grow a *connected, combinable* seed set of size ``k``.

    Start from a salient, well-connected node, then keep adding nodes that introduce a
    NEW productive pair with something already owned. This avoids the old failure mode
    where seeds were sampled independently and most shared nothing (dead weight), leaving
    only a single productive pairing in the whole inventory. Combines are category-scoped
    (ADR-0044) so seeds are wired to each other *within the theme*.
    """
    svc = get_service()
    starts = [n for n in pool if svc.degree(n) >= 3]
    if not starts or len(pool) < k:
        return None
    owned = [rng.choice(starts)]
    attempts = 0
    # Shuffle a working list so additions are deterministic per rng but varied.
    while len(owned) < k and attempts < 4000:
        attempts += 1
        cand = rng.choice(pool)
        if cand in owned:
            continue
        # Seed the first companion freely; afterwards require it to wire into the set.
        creates_link = len(owned) < 2 or any(
            c not in owned and c != cand
            for o in owned
            for c in svc.common_neighbors(cand, o, category=category)
        )
        if creates_link:
            owned.append(cand)
    return owned if len(owned) == k else None


def _build_session(
    rng: random.Random,
    difficulty: str = DEFAULT_DIFFICULTY,
    daily: str | None = None,
    category: str | None = None,
) -> AlchimieSession:
    """Sample a *satisfying*, solvable instance.

    Guarantees:
      * seeds are recognizable (salience floor) and combinable (min degree);
      * prefer an inventory with several currently productive projected openings
        (``>= MIN_OPENING_PAIRS``), with a solvable thin fallback for sparse themes;
      * the target is reachable through the combine-closure at the difficulty's depth
        window and is itself recognizable (``TARGET_SALIENCE_FLOOR``).
    """
    svc = get_service()
    min_gen, max_gen, seed_min, seed_max = _difficulty_params(difficulty)
    # Alchimie stays themed (ADR-0044): if no category was requested, pick one so private
    # projection construction stays bounded instead of reopening the whole dense graph.
    if category is None:
        category = _pick_scope_category(rng, svc)
    members = set(svc.by_category(category)) if category is not None else None

    def _in_scope(nid: str) -> bool:
        return members is None or nid in members

    pool = [
        nid
        for nid in svc.by_salience(minimum=SEED_SALIENCE_FLOOR)
        if svc.degree(nid) >= SEED_MIN_DEGREE and _in_scope(nid)
    ]
    if len(pool) < seed_max:
        pool = [
            nid
            for nid in svc.all_ids()
            if svc.degree(nid) >= SEED_MIN_DEGREE and _in_scope(nid)
        ]
    if category is not None and len(pool) < seed_min:
        raise http_error(503, "Nu exista inca jocuri pentru aceasta categorie.")

    def _finish(seeds: list[str], target: str) -> AlchimieSession | None:
        projection = _build_recipe_projection(seeds, target, category)
        if projection is None:
            return None
        session = AlchimieSession(
            seeds=list(seeds),
            target=target,
            target_depth=projection.par,
            difficulty=difficulty,
            daily=daily,
            category=category,
            recipes=projection.recipes,
            routes=projection.routes,
        )
        for s in seeds:
            session.add(s, None)
        return session

    best_relaxed: AlchimieSession | None = None
    for _ in range(MAX_BUILD_ATTEMPTS):
        k = rng.randint(seed_min, min(seed_max, len(pool)))
        seeds = _grow_seed_set(rng, k, pool, category)
        if seeds is None:
            continue
        gen = _closure_with_generations(seeds, category)
        # Candidates satisfying this difficulty's depth window AND recognizable.
        cands = [
            nid
            for nid, depth in gen.items()
            if depth >= min_gen
            and (max_gen is None or depth <= max_gen)
            and nid not in seeds
            and svc.node(nid) is not None
            and svc.node(nid).salience >= TARGET_SALIENCE_FLOOR
        ]
        if not cands:
            continue
        if difficulty == "greu":
            # Pick the deepest *recognizable* target for a meatier multi-combine puzzle.
            max_depth = max(gen[nid] for nid in cands)
            cands = [nid for nid in cands if gen[nid] == max_depth]
        target = rng.choice(cands)
        session = _finish(seeds, target)
        if session is None:
            continue
        openings = _projected_opening_pair_count(session.seeds, session.recipes)
        if openings >= MIN_OPENING_PAIRS:
            return session
        # Keep the first viable-but-thin instance as a fallback if nothing better lands.
        if best_relaxed is None:
            best_relaxed = session

    if best_relaxed is not None:
        return best_relaxed

    # Last-resort fallback: relax everything over the full in-scope pool so we never 500.
    fallback_pool = [
        nid
        for nid in svc.all_ids()
        if svc.degree(nid) >= SEED_MIN_DEGREE and _in_scope(nid)
    ]
    seeds = rng.sample(fallback_pool, min(seed_max, len(fallback_pool)))
    gen = _closure_with_generations(seeds, category)
    deep = [
        nid
        for nid, depth in gen.items()
        if depth >= MIN_TARGET_GENERATION and nid not in seeds
    ]
    if not deep:
        if category is not None:
            raise http_error(503, "Nu exista inca jocuri pentru aceasta categorie.")
        raise http_error(500, "Nu am putut genera un joc solvabil.")
    rng.shuffle(deep)
    for target in deep:
        session = _finish(seeds, target)
        if session is not None:
            return session
    raise http_error(
        503,
        f"Nu exista inca o tinta rezolvabila in cel mult {ALCHIMIE_MAX_ACTIONS} mutari.",
    )


def _useful_pair(session: AlchimieSession) -> tuple[str, str] | None:
    """The first action in an exact remaining plan through the private projection."""
    if session.won:
        return None
    plan = _minimum_projected_plan(
        set(session.owned), session.target, session.recipes
    )
    return plan[0] if plan else None


# ----------------------------------------------------------------------------- schemas
class CombineBody(BaseModel):
    a: str
    b: str


def _concept(node_id: str) -> dict[str, str]:
    svc = get_service()
    return {"id": node_id, "label": svc.label(node_id)}


def _inventory_flags(
    session: AlchimieSession,
) -> dict[str, tuple[bool, bool, bool, bool]]:
    """Return ``recent, useful, ready, depleted`` for every owned concept.

    ``useful`` means the concept still participates in a private recipe with an unseen
    output. ``ready`` narrows that to a recipe whose other ingredient is already owned.
    Depleted ingredients remain in the full encyclopedia/lineage but leave the active
    beginner workspace automatically.
    """
    owned = set(session.owned)
    useful: set[str] = set()
    ready: set[str] = set()
    for pair, outputs in session.recipes.items():
        if not any(output not in owned for output in outputs):
            continue
        useful.update(node_id for node_id in pair if node_id in owned)
        if pair[0] in owned and pair[1] in owned:
            ready.update(pair)
    recent = set(session.order[-RECENT_INVENTORY_LIMIT:])
    return {
        node_id: (
            node_id in recent,
            node_id in useful,
            node_id in ready,
            node_id not in useful,
        )
        for node_id in session.order
    }


def _inventory_payload(session: AlchimieSession) -> list[dict[str, object]]:
    """Inventory in discovery order, each item carrying its parent concepts (the WHY)."""
    svc = get_service()
    flags = _inventory_flags(session)
    out: list[dict[str, object]] = []
    for nid in session.order:
        parents = session.owned[nid]
        recent, useful, ready, depleted = flags[nid]
        out.append(
            {
                "id": nid,
                "label": svc.label(nid),
                "parents": (
                    [_concept(parents[0]), _concept(parents[1])] if parents else None
                ),
                "recent": recent,
                "useful": useful,
                "ready": ready,
                "depleted": depleted,
            }
        )
    return out


def _target_payload(session: AlchimieSession) -> dict[str, object]:
    """Public target view. The id/description are only revealed once it's been crafted."""
    svc = get_service()
    if session.won:
        return {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
            "revealed": True,
        }
    # Hide the secret id but show the label + description so the player has a goal.
    return {
        "id": None,
        "label": svc.label(session.target),
        "description": svc.description(session.target),
        "revealed": False,
    }


def _share_line(session: AlchimieSession) -> str:
    """A short Wordle-style shareable result line for a won game."""
    # "Perfect" == solved in the optimal number of combines with no hints.
    perfect = session.moves <= session.target_depth and session.hints_used == 0
    medal = "✨" if perfect else "⚗️"
    header = "cat_de_roman_esti · Alchimie"
    if session.category:
        header += f" · {category_label(session.category)}"
    lines = [
        header,
        f"⚗️ {session.moves} combinatii · {session.score} pct {medal}",
    ]
    if session.hints_used:
        lines.append(f"💡 x{session.hints_used}")
    if session.daily:
        lines.append(session.daily)
    return "\n".join(lines)


def _state_payload(game_id: str, session: AlchimieSession) -> dict[str, object]:
    inventory = _inventory_payload(session)
    active_count = sum(not bool(item["depleted"]) for item in inventory)
    payload: dict[str, object] = {
        "game_id": game_id,
        "target": _target_payload(session),
        "inventory": inventory,
        "inventory_summary": {
            "active": active_count,
            "depleted": len(inventory) - active_count,
            "total": len(inventory),
        },
        "discovered_count": max(0, len(session.order) - len(session.seeds)),
        "seed_count": len(session.seeds),
        "moves": session.moves,
        "difficulty": session.difficulty,
        "target_depth": session.target_depth,
        "won": session.won,
        "hints_used": session.hints_used,
        "hint_stage": "output" if session.hints_used == 0 else "pair",
        # A gentle nudge unlocks only after several fruitless combines in a row.
        "hint_available": (
            not session.won and session.fruitless_streak >= NUDGE_AFTER_FRUITLESS
        ),
        # Counts describe the bounded shape, never the private recipe ids/routes.
        "recipe_summary": {
            "pairs": len(session.recipes),
            "routes": len(session.routes),
            "max_results": max(
                (len(outputs) for outputs in session.recipes.values()), default=0
            ),
        },
    }
    if session.daily:
        payload["daily"] = session.daily
    if session.category:
        payload["board_category"] = session.category
    if session.won:
        payload["score"] = session.score
        payload["share"] = _share_line(session)
    return payload


def _require(game_id: str) -> AlchimieSession:
    session = store.get(game_id)
    if session is None:
        raise http_error(404, "Joc inexistent.")
    return session


# --------------------------------------------------------------------------- endpoints
class CreateGameView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="alchimie_create_game", tags=["alchimie"])
    def post(self, request):
        """Start a new Alchimie game.

        ``?difficulty=`` in {usor,normal,greu} tunes the target depth + seed count.
        ``?daily=YYYY-MM-DD`` makes a shared, deterministic daily instance (ignores seed).
        Otherwise an optional ``?seed=`` makes the instance reproducible. Every board is
        themed; without ``?category=`` the server deterministically selects a usable theme.
        """
        seed = query_int(request, "seed")
        difficulty = query_str(request, "difficulty", DEFAULT_DIFFICULTY)
        daily = query_str(request, "daily")
        category = query_str(request, "category")
        if difficulty not in DIFFICULTIES:
            difficulty = DEFAULT_DIFFICULTY
        if category is not None and not is_known(category):
            raise http_error(400, "Categorie necunoscuta.")
        if daily:
            rng = random.Random(daily_seed(daily, GAME_KEY))
            curated = get_pack().pick_daily(
                GAME_KEY, daily, category=category, difficulty=difficulty
            )
        else:
            rng = random.Random(seed)
            curated = get_pack().pick_seeded(
                GAME_KEY,
                rng,
                category=category,
                difficulty=difficulty,
                exclude_ids=excluded_pack_ids(request, GAME_KEY),
            )
        if curated is not None:
            curated_seeds = [str(s) for s in curated.payload["seeds"]]
            curated_target = str(curated.payload["target"])
            projection = _build_recipe_projection(
                curated_seeds, curated_target, curated.category
            )
            if (
                projection is None
                or projection.par != int(curated.payload["target_depth"])
            ):
                raise http_error(503, "Jocul ales nu are o proiecție de rețete validă.")
            session = AlchimieSession(
                seeds=curated_seeds,
                target=curated_target,
                target_depth=projection.par,
                difficulty=difficulty,
                daily=daily,
                # The item's own category scopes private projection construction
                # (ADR-0044); runtime never queries the broad common-neighbour set.
                # The target label already makes the theme public, so always echo it.
                category=curated.category,
                pack_id=curated.id,
                recipes=projection.recipes,
                routes=projection.routes,
            )
            for s in session.seeds:
                session.add(s, None)
        else:
            # _build_session always resolves a scope category (picks one if none requested).
            session = _build_session(rng, difficulty=difficulty, daily=daily, category=category)
        game_id = store.create(session)
        return Response(_state_payload(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="alchimie_get_game", tags=["alchimie"])
    def get(self, request, game_id: str):
        """Full current state of an existing game."""
        return Response(_state_payload(game_id, _require(game_id)))


class CombineView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="alchimie_combine", tags=["alchimie"])
    def post(self, request, game_id: str):
        """Combine two owned concepts through the session's sparse recipe projection."""
        body = parse_body(request, CombineBody)
        svc = get_service()
        session = _require(game_id)

        # A finished game is read-only: never count extra moves or mutate a won score.
        if session.won:
            payload = _state_payload(game_id, session)
            payload["discovered"] = []
            payload["message"] = "Jocul s-a terminat — ai craftat deja tinta."
            return Response(payload)

        a, b = (body.a or "").strip(), (body.b or "").strip()
        if a not in session.owned or b not in session.owned:
            raise http_error(400, "Ambele concepte trebuie sa fie in inventar.")
        if a == b:
            raise http_error(400, "Alege doua concepte diferite.")

        session.moves += 1
        # The category graph was used only to build this private, target-useful recipe
        # book. Runtime never reopens the broad common-neighbour space.
        discovered = [
            c
            for c in session.recipes.get(_pair_key(a, b), ())
            if c not in session.owned
        ]
        for c in discovered:
            session.add(c, (a, b))
        if session.won:
            record_finished(request, GAME_KEY, session.pack_id)

        # Track dry spells so the nudge can surface only when the player is genuinely stuck.
        if discovered:
            session.fruitless_streak = 0
        else:
            session.fruitless_streak += 1

        if not discovered:
            message = "Nicio combinatie noua."
        elif session.target in discovered:
            message = f"Ai descoperit tinta: {svc.label(session.target)}!"
        elif len(discovered) == 1:
            message = f"Ai descoperit: {svc.label(discovered[0])}."
        else:  # The explicit projection permits at most two tied/paired results.
            names = ", ".join(svc.label(c) for c in discovered)
            message = f"Ai descoperit {len(discovered)} concepte: {names}."

        payload = _state_payload(game_id, session)
        payload["discovered"] = [_concept(c) for c in discovered]
        payload["message"] = message
        return Response(payload)


class HintGameView(ContractAPIView):
    @extend_schema(operation_id="alchimie_hint_game", tags=["alchimie"])
    def post(self, request, game_id: str):
        """Reveal a progressive nudge without serializing the private recipe route.

        Only allowed once the player has been genuinely stuck (``NUDGE_AFTER_FRUITLESS``
        fruitless combines in a row). Each hint costs score and resets the dry-spell counter
        so it can't be spammed. The first hint names a reachable non-target output (or just
        re-orients to the already-public theme when the target is one action away). A later
        hint may reveal one useful owned pair. Neither response exposes the target id or the
        hidden full route.
        """
        session = _require(game_id)
        if session.won:
            raise http_error(400, "Jocul s-a terminat deja.")
        if session.fruitless_streak < NUDGE_AFTER_FRUITLESS:
            need = NUDGE_AFTER_FRUITLESS - session.fruitless_streak
            raise http_error(400, f"Mai incearca {need} combinatii inainte de un indiciu.")
        pair = _useful_pair(session)
        session.fruitless_streak = 0
        if pair is None:
            # Defensive: no forward pair (shouldn't happen for built instances).
            payload = _state_payload(game_id, session)
            payload["hint"] = None
            payload["hint_kind"] = "none"
            payload["hint_output"] = None
            payload["message"] = "Niciun indiciu disponibil acum."
            return Response(payload)
        session.hints_used += 1
        a, b = pair
        payload = _state_payload(game_id, session)
        if session.hints_used == 1:
            outputs = [
                output
                for output in session.recipes.get(pair, ())
                if output not in session.owned and output != session.target
            ]
            payload["hint"] = None
            if outputs:
                output = outputs[0]
                payload["hint_kind"] = "output"
                # Label only: output ids and every route stay private until discovered.
                payload["hint_output"] = {"label": get_service().label(output)}
                payload["message"] = (
                    f"Indiciu: caută mai întâi «{get_service().label(output)}»."
                )
            else:
                payload["hint_kind"] = "category"
                payload["hint_output"] = None
                if session.category:
                    payload["message"] = (
                        "Indiciu: ținta e aproape. Rămâi în tema "
                        f"{category_label(session.category)}."
                    )
                else:
                    payload["message"] = (
                        "Indiciu: ținta e la un pas; caută o pereche utilă."
                    )
        else:
            payload["hint"] = [_concept(a), _concept(b)]
            payload["hint_kind"] = "pair"
            payload["hint_output"] = None
            payload["message"] = (
                f"Indiciu: combină {get_service().label(a)} + "
                f"{get_service().label(b)}."
            )
        return Response(payload)


class ResetGameView(ContractAPIView):
    @extend_schema(operation_id="alchimie_reset_game", tags=["alchimie"])
    def post(self, request, game_id: str):
        """Reset the SAME instance back to its original seed inventory (target unchanged)."""
        session = _require(game_id)
        session.owned.clear()
        session.order.clear()
        session.moves = 0
        session.fruitless_streak = 0
        session.hints_used = 0
        for s in session.seeds:
            session.add(s, None)
        return Response(_state_payload(game_id, session))


_BASE = "api/wordgames/alchimie"
urlpatterns = [
    path(f"{_BASE}/games", CreateGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>", GetGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/combine", CombineView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/hint", HintGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/reset", ResetGameView.as_view()),
]
