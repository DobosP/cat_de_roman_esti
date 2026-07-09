"""Alchimie — an Infinite-Craft-style word game over the Romanian KG.

The player holds an INVENTORY of concepts and COMBINES two of them to discover new
ones. A combine of ``a`` + ``b`` yields :meth:`WordGameService.common_neighbors` — the
KG nodes adjacent to BOTH parents — minus whatever is already owned. The goal is to
craft a hidden TARGET concept into the inventory.

Server-authoritative: the whole game (seeds, target, inventory) lives here. The target
id is never echoed back until it has actually been discovered (``won``). Each instance is
*built to be solvable*: the target is drawn from the combine-CLOSURE of the seed
inventory (a fixpoint over ``common_neighbors``), at a depth of at least two generations
so it takes several combines rather than a single obvious pairing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
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
from .packs import get_pack
from .service import SessionStore, daily_seed, get_service

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
# A "good" instance offers several openings: at least this many of the seed-inventory
# pairs must already yield a fresh discovery, so a player never has to brute-force all
# pairs to find their first move.
MIN_OPENING_PAIRS = 2
# Targets should themselves be recognizable, not obscure intermediates.
TARGET_SALIENCE_FLOOR = 0.4
# Greu targets can otherwise sprawl very deep (gen 7+); cap so a game stays finishable.
GREU_MAX_GENERATION = 5
# How many consecutive fruitless combines before a gentle nudge becomes available.
NUDGE_AFTER_FRUITLESS = 3

# Difficulty -> (target generation policy, seed-count range).
#   usor : shallow target (generation 2) but a wide 6-7 seed inventory (more options).
#   normal: target at generation 2-3 with the default 5-7 seeds.
#   greu : deepest available target (3..GREU_MAX) with a lean 5-seed inventory.
DIFFICULTIES = {"usor", "normal", "greu"}
DEFAULT_DIFFICULTY = "normal"


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
    # The generation depth of the target in the seed closure == minimum combines to win.
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
    # Player-picked board theme + curated-pack provenance (None for mined games).
    category: str | None = None
    pack_id: str | None = None

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

    ``category`` scopes every combine to that category's subgraph (ADR-0013): the game is
    always themed, so on the dense graph the closure stays ~a category (bounded, with real
    depth) instead of exploding to the whole graph (everything craftable in ~2 gens).
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


def _opening_pair_count(seeds: list[str], category: str | None = None) -> int:
    """How many of the seed-inventory pairs already yield a *fresh* common neighbour.

    A high count means the player has several visible openings and never has to
    brute-force every pair to find a first productive move.
    """
    svc = get_service()
    owned = set(seeds)
    count = 0
    for a, b in combinations(sorted(owned), 2):
        if any(c not in owned for c in svc.common_neighbors(a, b, category=category)):
            count += 1
    return count


def _grow_seed_set(
    rng: random.Random, k: int, pool: list[str], category: str | None = None
) -> list[str] | None:
    """Grow a *connected, combinable* seed set of size ``k``.

    Start from a salient, well-connected node, then keep adding nodes that introduce a
    NEW productive pair with something already owned. This avoids the old failure mode
    where seeds were sampled independently and most shared nothing (dead weight), leaving
    only a single productive pairing in the whole inventory. Combines are category-scoped
    (ADR-0013) so seeds are wired to each other *within the theme*.
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
      * the inventory forms a connected web with several opening moves
        (``>= MIN_OPENING_PAIRS`` fresh pairs) so progress never needs brute force;
      * the target is reachable through the combine-closure at the difficulty's depth
        window and is itself recognizable (``TARGET_SALIENCE_FLOOR``).
    """
    svc = get_service()
    min_gen, max_gen, seed_min, seed_max = _difficulty_params(difficulty)
    # Alchimie is ALWAYS themed (ADR-0013): if no category was requested, pick one so the
    # combine-closure stays bounded to a category subgraph instead of the whole dense graph.
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

    def _finish(seeds: list[str], target: str, depth: int) -> AlchimieSession:
        session = AlchimieSession(
            seeds=list(seeds),
            target=target,
            target_depth=depth,
            difficulty=difficulty,
            daily=daily,
            category=category,
        )
        for s in seeds:
            session.add(s, None)
        return session

    best_relaxed: tuple[list[str], str, int] | None = None
    for _ in range(MAX_BUILD_ATTEMPTS):
        k = rng.randint(seed_min, min(seed_max, len(pool)))
        seeds = _grow_seed_set(rng, k, pool, category)
        if seeds is None:
            continue
        openings = _opening_pair_count(seeds, category)
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
        if openings >= MIN_OPENING_PAIRS:
            return _finish(seeds, target, gen[target])
        # Keep the first viable-but-thin instance as a fallback if nothing better lands.
        if best_relaxed is None:
            best_relaxed = (seeds, target, gen[target])

    if best_relaxed is not None:
        return _finish(*best_relaxed)

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
    target = rng.choice(deep)
    return _finish(seeds, target, gen[target])


def _useful_pair(session: AlchimieSession) -> tuple[str, str] | None:
    """A currently-owned pair that makes *forward progress* toward the target.

    Returns the lexicographically-first owned pair whose fresh discovery strictly lowers
    the number of remaining combine-generations to the target. ``None`` if the target is
    already owned or somehow unreachable from the current inventory (shouldn't happen for
    built instances). Used to power the gentle nudge after fruitless combines.
    """
    if session.won:
        return None
    svc = get_service()
    cat = session.category
    owned = set(session.owned)
    base_gen = _closure_with_generations(list(owned), cat).get(session.target)
    if base_gen is None or base_gen == 0:
        return None
    for a, b in combinations(sorted(owned), 2):
        fresh = [c for c in svc.common_neighbors(a, b, category=cat) if c not in owned]
        if not fresh:
            continue
        new_gen = _closure_with_generations(list(owned | set(fresh)), cat).get(session.target)
        if new_gen is not None and new_gen < base_gen:
            return (a, b)
    return None


# ----------------------------------------------------------------------------- schemas
class CombineBody(BaseModel):
    a: str
    b: str


def _concept(node_id: str) -> dict[str, str]:
    svc = get_service()
    return {"id": node_id, "label": svc.label(node_id)}


def _inventory_payload(session: AlchimieSession) -> list[dict[str, object]]:
    """Inventory in discovery order, each item carrying its parent concepts (the WHY)."""
    svc = get_service()
    out: list[dict[str, object]] = []
    for nid in session.order:
        parents = session.owned[nid]
        out.append(
            {
                "id": nid,
                "label": svc.label(nid),
                "parents": (
                    [_concept(parents[0]), _concept(parents[1])] if parents else None
                ),
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
    payload: dict[str, object] = {
        "game_id": game_id,
        "target": _target_payload(session),
        "inventory": _inventory_payload(session),
        "discovered_count": max(0, len(session.order) - len(session.seeds)),
        "seed_count": len(session.seeds),
        "moves": session.moves,
        "difficulty": session.difficulty,
        "target_depth": session.target_depth,
        "won": session.won,
        "hints_used": session.hints_used,
        # A gentle nudge unlocks only after several fruitless combines in a row.
        "hint_available": (
            not session.won and session.fruitless_streak >= NUDGE_AFTER_FRUITLESS
        ),
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
        Otherwise an optional ``?seed=`` makes the instance reproducible.
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
            curated = (
                get_pack().pick_seeded(
                    GAME_KEY,
                    rng,
                    category=category,
                    difficulty=difficulty,
                    exclude_ids=excluded_pack_ids(request, GAME_KEY),
                )
                if category is not None
                else None
            )
        if curated is not None:
            session = AlchimieSession(
                seeds=[str(s) for s in curated.payload["seeds"]],
                target=str(curated.payload["target"]),
                target_depth=int(curated.payload["target_depth"]),
                difficulty=difficulty,
                daily=daily,
                # The item's OWN category scopes combines (ADR-0013); Alchimie shows the
                # target label so the theme is not a hidden secret — always set + echoed.
                category=curated.category,
                pack_id=curated.id,
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
        """Combine two owned concepts; append any newly-discovered shared neighbours."""
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
        # Combines are scoped to the game's category (ADR-0013) so the reachable set
        # matches the closure the target_depth/score were computed against.
        discovered = [
            c
            for c in svc.common_neighbors(a, b, category=session.category)
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
        else:
            names = ", ".join(svc.label(c) for c in discovered)
            message = f"Ai descoperit {len(discovered)} concepte: {names}."

        payload = _state_payload(game_id, session)
        payload["discovered"] = [_concept(c) for c in discovered]
        payload["message"] = message
        return Response(payload)


class HintGameView(ContractAPIView):
    @extend_schema(operation_id="alchimie_hint_game", tags=["alchimie"])
    def post(self, request, game_id: str):
        """Reveal a gentle nudge: a pair of owned concepts that makes forward progress.

        Only allowed once the player has been genuinely stuck (``NUDGE_AFTER_FRUITLESS``
        fruitless combines in a row). Each hint costs score and resets the dry-spell counter
        so it can't be spammed. Makes the "discovered nothing" path feel fair without handing
        over the answer — it points at a useful *pair*, never the target itself.
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
            payload["message"] = "Niciun indiciu disponibil acum."
            return Response(payload)
        session.hints_used += 1
        a, b = pair
        payload = _state_payload(game_id, session)
        payload["hint"] = [_concept(a), _concept(b)]
        payload["message"] = (
            f"Indiciu: incearca sa combini {get_service().label(a)} + "
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
