"""Lantul Cuvintelor — a Wiki-game / word-ladder over the offline KG.

The player is shown a START and a TARGET concept. Each turn they TYPE a concept that
is directly LINKED (a real, non-distractor KG edge) to the CURRENT concept, hopping
along the chain. The goal is to reach the target in as few moves as possible.

Server-authoritative: the chain, the optimal distance and all validation live here.
The target id is public (it must be shown) but is only meaningful with the hidden
graph; the frontend sees a bounded local menu, never the route corridor or full path.
"""

from __future__ import annotations

import random
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps

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
from .categories import category_label, is_known
from .packs import (
    CURATED_DAILY_MIN_POOL,
    LANT_MIN_FIRST_HOP_CHOICES,
    LANT_MIN_LAYER_WIDTH,
    CuratedItem,
    GamesPack,
    get_pack,
)
from .service import (
    SessionCapacityError,
    SessionStore,
    WordGameService,
    daily_seed,
    get_service,
    normalize,
)

GAME_KEY = "lant"

# Difficulty -> the (min, max) start/target distance band.
_DIFFICULTY_BANDS: dict[str, tuple[int, int]] = {
    "usor": (2, 3),
    "normal": (3, 4),
    "greu": (4, 6),
}
_DEFAULT_DIFFICULTY = "normal"

# How many candidate STARTS we sample before settling for the best pair found so far.
_MAX_STARTS = 140
# How many reachable targets we evaluate per start (a slice of the shuffled reachables).
_TARGETS_PER_START = 24
# Minimum endpoint degree: avoid leaf (degree-1) starts/targets — a leaf endpoint forces
# the first/last hop and makes the ladder feel like a single rail.
_MIN_ENDPOINT_DEGREE = 2
# A puzzle is "satisfying" only if the player has a real branch at the first hop AND no
# intermediate shortest-path layer collapses to a single forced node.
_MIN_FIRST_HOP_CHOICES = LANT_MIN_FIRST_HOP_CHOICES
_MIN_LAYER_WIDTH = LANT_MIN_LAYER_WIDTH
# Once we have found enough genuinely-good candidates we stop early (keeps latency low).
_ENOUGH_GOOD = 6

# A concept is in a board's private route corridor when a route through it is at most
# par + 2. The server never serializes membership or a full corridor.
_CORRIDOR_SLACK = 2
_BEGINNER_MIN_FIRST_HOPS = 3
_BEGINNER_MIN_LAYER_WIDTH = 3
_BEGINNER_PREFERRED_POOL = 3

# Small local menus scan well on phones. Detour-thin corners may expose only the three
# corridor slots; unreachable or extra corridor nodes never pad the visual count.
_MAX_VISIBLE_CHOICES = 6
_CORRIDOR_CHOICE_QUOTA = 3

# Broad generic nodes remain legal but lose guidance rank above the fixture's approximate
# 95th-percentile live degree.
_HUB_SOFT_DEGREE = 20

_PROGRESS_MESSAGES = {
    "closer": "Mai aproape de țintă.",
    "lateral": "Tot cam la aceeași distanță.",
    "farther": "Te-ai îndepărtat puțin.",
    "dead_end": "Fundătură — folosește Înapoi.",
    "won": "Ai ajuns la țintă!",
}

_ROUTE_PROFILE_CACHE_MAX = 512
_RouteProfiles = tuple[tuple[int, int, int], tuple[int, int, int]]
_route_profile_cache: OrderedDict[
    tuple[int, str, str, int, int], tuple[WordGameService, _RouteProfiles]
] = OrderedDict()
_route_profile_cache_lock = threading.Lock()


def _score_for(moves: int, optimal: int) -> int:
    """Par-relative score: playing at optimal -> 1000, never below 100."""
    moves = max(moves, 1)
    return max(100, round(1000 * optimal / max(moves, optimal)))


def _share_line(moves: int, optimal: int, daily: str | None, category: str | None = None) -> str:
    header = "cat_de_roman_esti · Lantul Cuvintelor"
    if category:
        header += f" · {category_label(category)}"
    return f"{header}\n🔗 {moves}/{optimal} mutari\n{daily or ''}"


@dataclass
class LantSession:
    start: str
    target: str
    optimal: int
    difficulty: str = _DEFAULT_DIFFICULTY
    daily: str | None = None
    # The chain of node ids walked so far; chain[0] is always the start.
    chain: list[str] = field(default_factory=list)
    won: bool = False
    # Player-picked board theme + curated-pack provenance (None for mined games).
    category: str | None = None
    pack_id: str | None = None
    # Voluntary help escalates only while the position stays unchanged.  Moves and undo
    # reset this capped counter, so exploratory/revisited chains cannot retain O(n²)
    # tuple keys in the session.
    hint_requests: int = 0
    # Easy-mode direction feedback remembers only whether the last two real hops failed
    # to improve directed distance. The capped scalar cannot retain route history.
    non_improving_moves: int = 0

    @property
    def current(self) -> str:
        return self.chain[-1]

    @property
    def moves(self) -> int:
        return len(self.chain) - 1


store: SessionStore[LantSession] = SessionStore()


def _atomic_session(method):
    """Run one request against a pinned, exclusively locked game session."""

    @wraps(method)
    def wrapped(self, request, game_id: str):
        with store.transaction(game_id) as session:
            if session is None:
                raise http_error(404, "Joc inexistent")
            return method(self, request, game_id, session)

    return wrapped


# --------------------------------------------------------------------- request bodies
class MoveBody(BaseModel):
    text: str


# --------------------------------------------------------------------- serializers
def _resolve_neighbor(text: str, current: str, target: str) -> str | None:
    """Resolve player text to a node, disambiguating by what is linked to ``current``.

    The shared index maps a normalized label to a *single* node id, so when two concepts
    share a label (e.g. two "Moldova" nodes) a literal resolve can pick the one that is
    NOT linked to the current node and a perfectly valid guess gets wrongly rejected.
    Here we look at every node carrying the typed label and keep the ones that are an
    actual neighbour of ``current`` (excluding ``current`` itself). When SEVERAL
    same-label nodes are legal hops (the dense graph has genuine homonyms), the typed
    text is truly ambiguous — disambiguation favours the player: hop to the candidate
    closest to the target, deterministically.
    """
    svc = get_service()
    primary = svc.resolve(text)
    key = normalize(text)
    if not key:
        return primary
    legal = [
        nid
        for nid in svc.all_ids()
        if nid != current
        and normalize(svc.label(nid)) == key
        and svc.link(current, nid) is not None
    ]
    if not legal:
        return primary
    if len(legal) == 1:
        return legal[0]

    dist_to_target = svc.distances_to(target)

    def _closeness(nid: str) -> tuple[int, float, str, str]:
        d = dist_to_target.get(nid)
        return (
            d if d is not None else 1_000_000,
            *_hop_quality(current, nid),
        )

    return min(legal, key=_closeness)


def _concept(node_id: str) -> dict[str, str]:
    svc = get_service()
    return {"id": node_id, "label": svc.label(node_id)}


def _short_relation(a: str, b: str) -> str:
    """Return a concise local-choice label without changing edge semantics."""
    label = " ".join(get_service().link_label(a, b).split()) or "legătură directă"
    if len(label) <= 34:
        return label
    head = label[:33].rsplit(" ", 1)[0]
    return f"{head or label[:33]}…"


def _hub_penalty(node_id: str) -> float:
    """Softly demote generic high-degree concepts; never make a legal hop illegal."""
    excess_degree = max(0, get_service().degree(node_id) - _HUB_SOFT_DEGREE)
    return min(1.25, excess_degree * 0.08)


def _hop_quality(current: str, node_id: str) -> tuple[float, str, str]:
    svc = get_service()
    edge = svc.link(current, node_id)
    strength = edge.strength if edge is not None else 0.0
    quality = strength * 4 + _salience(node_id) * 1.5 - _hub_penalty(node_id)
    return (-quality, normalize(svc.label(node_id)), node_id)


def _route_profiles(
    start: str, target: str, optimal: int, *, slack: int = _CORRIDOR_SLACK
) -> _RouteProfiles:
    """Compute strict-shortest and near-shortest width profiles with one BFS pair."""
    svc = get_service()
    key = (id(svc), start, target, optimal, slack)
    with _route_profile_cache_lock:
        cached = _route_profile_cache.get(key)
        if cached is not None and cached[0] is svc:
            _route_profile_cache.move_to_end(key)
            return cached[1]

    result = _compute_route_profiles(svc, start, target, optimal, slack=slack)
    with _route_profile_cache_lock:
        _route_profile_cache[key] = (svc, result)
        _route_profile_cache.move_to_end(key)
        while len(_route_profile_cache) > _ROUTE_PROFILE_CACHE_MAX:
            _route_profile_cache.popitem(last=False)
    return result


def _compute_route_profiles(
    svc: WordGameService,
    start: str,
    target: str,
    optimal: int,
    *,
    slack: int,
) -> _RouteProfiles:
    dist_from_start = svc.distances_from(start)
    dist_to_target = svc.distances_to(target)
    budget = optimal + max(0, slack)
    shortest_layers: dict[int, int] = {}
    corridor_layers: dict[int, int] = {}
    for node_id, from_start in dist_from_start.items():
        to_target = dist_to_target.get(node_id)
        if to_target is None:
            continue
        route_length = from_start + to_target
        if route_length == optimal:
            shortest_layers[from_start] = shortest_layers.get(from_start, 0) + 1
        if route_length <= budget:
            corridor_layers[from_start] = corridor_layers.get(from_start, 0) + 1

    def profile(layers: dict[int, int], *, near: bool) -> tuple[int, int, int]:
        intermediate = [layers.get(layer, 0) for layer in range(1, optimal)]
        first_hops = sum(
            1
            for neighbor in svc.neighbor_ids(start)
            if (
                dist_to_target.get(neighbor, budget + 1) + 1 <= budget
                if near
                else dist_to_target.get(neighbor) == optimal - 1
            )
        )
        return (
            first_hops,
            min(intermediate) if intermediate else 1,
            sum(intermediate),
        )

    return profile(shortest_layers, near=False), profile(corridor_layers, near=True)


def _corridor_profile(
    start: str, target: str, optimal: int, *, slack: int = _CORRIDOR_SLACK
) -> tuple[int, int, int]:
    """Return first-hop, narrow-layer and total width for routes within par + slack."""
    return _route_profiles(start, target, optimal, slack=slack)[1]


def _near_route_hops(
    session: LantSession, dist_to_target: dict[str, int] | None = None
) -> list[str]:
    """Legal next hops that still permit an actual play of at most par + 2 moves."""
    svc = get_service()
    remaining_budget = session.optimal + _CORRIDOR_SLACK - session.moves
    if dist_to_target is None:
        dist_to_target = svc.distances_to(session.target)
    return [
        node_id
        for node_id in svc.neighbor_ids(session.current)
        if node_id not in session.chain
        and dist_to_target.get(node_id, remaining_budget + 1) + 1 <= remaining_budget
    ]


def _distinct_hops(
    current: str,
    target: str,
    node_ids: list[str],
    dist_to_target: dict[str, int] | None = None,
) -> list[str]:
    """Dedupe an ID-private candidate set by the public normalized label."""
    svc = get_service()
    if dist_to_target is None:
        dist_to_target = svc.distances_to(target)
    ranked = sorted(
        set(node_ids),
        key=lambda node_id: (
            dist_to_target.get(node_id, 1_000_000),
            *_hop_quality(current, node_id),
        ),
    )
    seen: set[str] = set()
    distinct: list[str] = []
    for node_id in ranked:
        key = normalize(svc.label(node_id))
        if not key or key in seen:
            continue
        seen.add(key)
        distinct.append(node_id)
    return distinct


def _shortest_hops(
    session: LantSession, dist_to_target: dict[str, int] | None = None
) -> list[str]:
    """Unvisited legal hops one step closer to the target, deterministically ranked."""
    svc = get_service()
    if dist_to_target is None:
        dist_to_target = svc.distances_to(session.target)
    remaining = dist_to_target.get(session.current)
    if remaining is None:
        return []
    hops = [
        node_id
        for node_id in svc.neighbor_ids(session.current)
        if node_id not in session.chain and dist_to_target.get(node_id) == remaining - 1
    ]
    return _distinct_hops(
        session.current, session.target, hops, dist_to_target
    )


def _choice_payload(current: str, node_id: str) -> dict[str, str]:
    """ID-free public choice: enough to understand and submit one local hop."""
    return {
        "label": get_service().label(node_id),
        "relation": _short_relation(current, node_id),
    }


def _visible_choice_nodes(session: LantSession) -> list[str]:
    """Return the private node ids backing the current ID-free choice menu."""
    if session.won:
        return []
    svc = get_service()
    cur = session.current
    dist_to_target = svc.distances_to(session.target)
    safe = _distinct_hops(
        cur,
        session.target,
        [
            node_id
            for node_id in svc.neighbor_ids(cur)
            if node_id not in session.chain and node_id in dist_to_target
        ],
        dist_to_target,
    )
    corridor = set(_near_route_hops(session, dist_to_target))
    on_route = sorted(
        (node_id for node_id in safe if node_id in corridor),
        key=lambda node_id: _hop_quality(cur, node_id),
    )
    detours = sorted(
        (node_id for node_id in safe if node_id not in corridor),
        key=lambda node_id: _hop_quality(cur, node_id),
    )

    chosen = on_route[:_CORRIDOR_CHOICE_QUOTA]
    chosen.extend(detours[: _MAX_VISIBLE_CHOICES - len(chosen)])

    # Alphabetical display order does not leak the private route/detour ranking.
    chosen.sort(key=lambda node_id: (normalize(svc.label(node_id)), node_id))
    return chosen


def _visible_choices(session: LantSession) -> list[dict[str, str]]:
    """Build a bounded, unmarked mix of corridor hops and safe local detours."""
    return [
        _choice_payload(session.current, node_id)
        for node_id in _visible_choice_nodes(session)
    ]


def _path(session: LantSession) -> list[dict[str, str]]:
    svc = get_service()
    out: list[dict[str, str]] = []
    for i, nid in enumerate(session.chain):
        step: dict[str, str] = {"id": nid, "label": svc.label(nid)}
        if i > 0:
            step["relation"] = svc.link_label(session.chain[i - 1], nid)
        out.append(step)
    return out


def _state(game_id: str, session: LantSession) -> dict:
    svc = get_service()
    state = {
        "game_id": game_id,
        "start": _concept(session.start),
        "target": {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
        },
        "current": _concept(session.current),
        "path": _path(session),
        "moves": session.moves,
        "optimal": session.optimal,
        "won": session.won,
        "difficulty": session.difficulty,
        "choices": _visible_choices(session),
        "backtrack_recommended": (
            session.difficulty == "usor" and session.non_improving_moves >= 2
        ),
    }
    if session.daily is not None:
        state["daily"] = session.daily
    if session.category:
        state["board_category"] = session.category
    if session.won:
        state["score"] = _score_for(session.moves, session.optimal)
        state["share"] = _share_line(
            session.moves, session.optimal, session.daily, session.category
        )
    return state


# --------------------------------------------------------------------- puzzle picking
def _salience(node_id: str) -> float:
    node = get_service().node(node_id)
    return node.salience if node else 0.0


# Per-difficulty weight on endpoint salience (v11): easier tiers strongly prefer
# recognizable endpoints; ``greu`` mostly ignores fame so it can pick obscure endpoints.
# Meaningful now that salience is recalibrated into balanced tiers (ADR-none; STATUS v11).
_SALIENCE_WEIGHT = {"usor": 16.0, "normal": 9.0, "greu": 2.0}

# Hard endpoint-salience floor per difficulty (mirrors Contexto's ``usor`` target pool).
# Score weighting alone kept famous endpoints dominant only while low-salience nodes were
# poorly connected; after the v16 enrichment those nodes are branchy enough to win on
# structure, so ``usor`` filters the candidate pool outright. Applied only when enough
# candidates survive, so thin category pools degrade gracefully instead of 503-ing.
_SALIENCE_FLOOR = {"usor": 0.6}
_MIN_SALIENT_POOL = 8


def _pair_score(
    start: str,
    target: str,
    first_hop: int,
    min_width: int,
    total: int,
    salience_weight: float = 4.0,
) -> float:
    """Rank candidate pairs: reward branchiness, salient endpoints and richer webs.

    ``salience_weight`` is set by difficulty so easier games favour famous endpoints.
    """
    salience = (_salience(start) + _salience(target)) / 2
    hub_cost = _hub_penalty(start) + _hub_penalty(target)
    return min_width * 10 + first_hop * 3 + total + salience * salience_weight - hub_cost


def _prefer_wide_beginner_pool(
    items: list[CuratedItem], difficulty: str, *, minimum_pool: int
) -> list[CuratedItem]:
    """Prefer width-three easy boards, falling back when a filtered shelf is thin."""
    if difficulty != "usor" or not items:
        return items
    wide = []
    for item in items:
        first_hops, min_width, _ = _corridor_profile(
            str(item.payload["start"]),
            str(item.payload["target"]),
            int(item.payload["optimal"]),
        )
        if (
            first_hops >= _BEGINNER_MIN_FIRST_HOPS
            and min_width >= _BEGINNER_MIN_LAYER_WIDTH
        ):
            wide.append(item)
    return wide if len(wide) >= max(1, minimum_pool) else items


def _is_wide_beginner_item(item: CuratedItem) -> bool:
    first_hops, min_width, _ = _corridor_profile(
        str(item.payload["start"]),
        str(item.payload["target"]),
        int(item.payload["optimal"]),
    )
    return (
        first_hops >= _BEGINNER_MIN_FIRST_HOPS
        and min_width >= _BEGINNER_MIN_LAYER_WIDTH
    )


def _pick_curated(
    rng: random.Random,
    *,
    daily: str | None,
    category: str | None,
    difficulty: str,
    exclude_ids: set[str],
) -> CuratedItem | None:
    """Select curated content with an easy width-three preference and safe fallback."""
    pack = get_pack()
    if daily is not None:
        picked = pack.pick_daily(
            GAME_KEY,
            daily,
            category=category,
            difficulty=difficulty,
        )
    else:
        picked = pack.pick_seeded(
            GAME_KEY,
            rng,
            category=category,
            difficulty=difficulty,
            exclude_ids=exclude_ids,
        )
    if picked is None or difficulty != "usor" or _is_wide_beginner_item(picked):
        return picked

    pool = pack.pool(
        GAME_KEY,
        category=category,
        difficulty=difficulty,
        exclude_ids=None if daily is not None else exclude_ids,
    )
    if daily is not None and category is None:
        preference_floor = CURATED_DAILY_MIN_POOL
    else:
        preference_floor = min(_BEGINNER_PREFERRED_POOL, len(pool))
    selected_pool = _prefer_wide_beginner_pool(
        pool, difficulty, minimum_pool=preference_floor
    )
    narrowed = GamesPack(selected_pool)
    if daily is not None:
        return narrowed.pick_daily(
            GAME_KEY,
            daily,
            category=category,
            difficulty=difficulty,
        )
    return narrowed.pick_seeded(
        GAME_KEY,
        rng,
        category=category,
        difficulty=difficulty,
    )


def _pick_pair(
    rng: random.Random,
    lo: int,
    hi: int,
    category: str | None = None,
    difficulty: str = _DEFAULT_DIFFICULTY,
) -> tuple[str, str, int]:
    """Pick a (start, target) whose distance is in [lo, hi].

    We don't take the first reachable pair: we *playtest* candidates and keep the most
    satisfying one. A good ladder has REAL choices at the opening hop, never funnels
    every solver through a single forced node, prefers salient (recognisable) endpoints
    and avoids leaf (degree-1) endpoints. The search is bounded and deterministic in the
    seed, and degrades gracefully — if nothing clears the "genuinely good" bar we keep
    the best-scoring pair seen, and as a last resort accept any reachable pair.
    With a ``category``, both endpoints stay in that category (the walk may wander).
    """
    svc = get_service()
    pool = svc.by_category(category) if category is not None else svc.all_ids()
    candidates = [nid for nid in pool if svc.degree(nid) >= _MIN_ENDPOINT_DEGREE]
    if not candidates and category is None:
        candidates = [nid for nid in pool if svc.degree(nid) >= 1]
    if not candidates:
        if category is not None:
            raise http_error(503, "Nu exista inca jocuri pentru aceasta categorie.")
        raise http_error(503, "Graful nu are noduri jucabile.")
    sal_floor = _SALIENCE_FLOOR.get(difficulty, 0.0)
    if sal_floor:
        salient = [nid for nid in candidates if _salience(nid) >= sal_floor]
        if len(salient) >= _MIN_SALIENT_POOL:
            candidates = salient
    endpoint_ok = set(candidates)
    sal_weight = _SALIENCE_WEIGHT.get(difficulty, 4.0)

    best_good: tuple[float, str, str, int] | None = None
    good_count = 0
    # Fallback if no pair clears the satisfying bar: best-scoring, else any reachable.
    best_any: tuple[float, str, str, int] | None = None
    fallback: tuple[str, str, int] | None = None

    for _ in range(_MAX_STARTS):
        start = rng.choice(candidates)
        dist_map = svc.distances_from(start)
        reachable = [
            (nid, d)
            for nid, d in dist_map.items()
            if lo <= d <= hi
            and svc.degree(nid) >= _MIN_ENDPOINT_DEGREE
            and nid in endpoint_ok
        ]
        if not reachable:
            continue
        rng.shuffle(reachable)
        for target, optimal in reachable[:_TARGETS_PER_START]:
            if fallback is None:
                fallback = (start, target, optimal)
            strict_profile, near_profile = _route_profiles(start, target, optimal)
            first_hop, min_width, total = strict_profile
            score = _pair_score(start, target, first_hop, min_width, total, sal_weight)
            if best_any is None or score > best_any[0]:
                best_any = (score, start, target, optimal)
            near_first, near_width, _ = near_profile
            beginner_wide = difficulty != "usor" or (
                near_first >= _BEGINNER_MIN_FIRST_HOPS
                and near_width >= _BEGINNER_MIN_LAYER_WIDTH
            )
            if (
                first_hop >= _MIN_FIRST_HOP_CHOICES
                and min_width >= _MIN_LAYER_WIDTH
                and beginner_wide
            ):
                if best_good is None or score > best_good[0]:
                    best_good = (score, start, target, optimal)
                good_count += 1
        if good_count >= _ENOUGH_GOOD:
            break

    chosen = best_good or best_any
    if chosen is not None:
        _, start, target, optimal = chosen
        return start, target, optimal
    if fallback is not None:
        return fallback

    if category is not None:
        raise http_error(503, "Nu exista inca jocuri pentru aceasta categorie.")
    raise http_error(503, "Nu am putut genera un lant valid; reincearca.")


# --------------------------------------------------------------------- endpoints
class CreateGameView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="lant_create_game", tags=["lant"])
    def post(self, request):
        """Start a game. Optional ``?category=`` prefers a curated pair for that
        theme and otherwise mines with both endpoints inside the category; the
        daily prefers a curated pair whenever one is approved (ADR-0011)."""
        seed = query_int(request, "seed")
        difficulty = query_str(request, "difficulty", _DEFAULT_DIFFICULTY)
        daily = query_str(request, "daily")
        category = query_str(request, "category")
        if difficulty not in _DIFFICULTY_BANDS:
            difficulty = _DEFAULT_DIFFICULTY
        if category is not None and not is_known(category):
            raise http_error(400, "Categorie necunoscuta.")
        lo, hi = _DIFFICULTY_BANDS[difficulty]
        if daily is not None:
            seed = daily_seed(daily, GAME_KEY)
        rng = random.Random(seed)
        curated = _pick_curated(
            rng,
            daily=daily,
            category=category,
            difficulty=difficulty,
            exclude_ids=excluded_pack_ids(request, GAME_KEY),
        )
        if curated is not None:
            start = str(curated.payload["start"])
            target = str(curated.payload["target"])
            optimal = int(curated.payload["optimal"])
            pack_id: str | None = curated.id
        else:
            start, target, optimal = _pick_pair(rng, lo, hi, category, difficulty)
            pack_id = None
        session = LantSession(
            start=start,
            target=target,
            optimal=optimal,
            difficulty=difficulty,
            daily=daily,
            chain=[start],
            # Echo only a player-requested theme (curated dailies stay themeless).
            category=category,
            pack_id=pack_id,
        )
        try:
            game_id = store.create(session)
        except SessionCapacityError as exc:
            raise http_error(503, "Prea multe jocuri active. Încearcă din nou.") from exc
        return Response(_state(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="lant_get_game", tags=["lant"])
    @_atomic_session
    def get(self, request, game_id: str, session: LantSession):
        return Response(_state(game_id, session))


class MoveView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="lant_move", tags=["lant"])
    @_atomic_session
    def post(self, request, game_id: str, session: LantSession):
        body = parse_body(request, MoveBody)
        if session.won:
            return Response({"ok": True, **_state(game_id, session)})

        svc = get_service()
        if not body.text or not body.text.strip():
            return Response({"ok": False, "last_error": "Scrie un concept"})

        prev = session.current
        # An ID-free chip submits its public label. Recompute the authored menu at this
        # exact position and bind a unique label match before general homonym resolution;
        # otherwise a closer/stronger *visited* homonym could steal the visible action.
        submitted_key = normalize(body.text)
        visible_matches = [
            node_id
            for node_id in _visible_choice_nodes(session)
            if normalize(svc.label(node_id)) == submitted_key
        ]
        guess = (
            visible_matches[0]
            if len(visible_matches) == 1
            else _resolve_neighbor(body.text, prev, session.target)
        )
        corrected = False
        if guess is None:
            # Confident auto-accept (ADR-0022): a high-confidence, unambiguous near-miss
            # is played as the corrected concept and goes through the exact same
            # legality checks below (neighbour -> move, target -> win).
            guess = svc.resolve_fuzzy(body.text)
            corrected = guess is not None
        if guess is None:
            # Unknown concept: offer fuzzy "did you mean" hints. Lanț's target is public
            # (ADR-0021), so no suggestion needs to be withheld here.
            suggestions = svc.suggest(body.text)
            last_error = "Nu cunosc acest concept"
            if suggestions:
                last_error = f"Nu cunosc acest concept. Poate cautai: {suggestions[0]}?"
            return Response(
                {"ok": False, "last_error": last_error, "suggestions": suggestions}
            )

        # On a correction every verdict names what we understood, so a rejected move
        # blames the corrected concept and not the player's raw typo.
        understood = f"Am înțeles: {svc.label(guess)}. " if corrected else ""
        if guess == prev:
            return Response({"ok": False, "last_error": f"{understood}Esti deja aici"})
        if svc.link(prev, guess) is None:
            return Response(
                {"ok": False, "last_error": f"{understood}Nu exista o legatura directa"}
            )

        session.chain.append(guess)
        session.hint_requests = 0
        session.won = guess == session.target
        if session.won:
            record_finished(request, GAME_KEY, session.pack_id)

        notes: list[str] = []
        if corrected:
            notes.append(f"Am înțeles: {svc.label(guess)}.")
        # Early dead-end warning (ADR-0022): the move is legal, but from here the target
        # is unreachable on the directed graph — say so now instead of letting the
        # player discover it hints later (pairs with the hint's backtrack escape).
        dist_to_target = svc.distances_to(session.target)
        previous_remaining = dist_to_target.get(prev)
        next_remaining = dist_to_target.get(guess)
        dead_end = not session.won and next_remaining is None
        if dead_end and session.difficulty != "usor":
            notes.append("Atenție: fundătură — de aici ținta nu mai e accesibilă.")

        progress: dict[str, str] | None = None
        if session.difficulty == "usor":
            if session.won:
                progress_kind = "won"
            elif dead_end:
                progress_kind = "dead_end"
            elif previous_remaining is None or next_remaining < previous_remaining:
                progress_kind = "closer"
            elif next_remaining == previous_remaining:
                progress_kind = "lateral"
            else:
                progress_kind = "farther"

            if progress_kind in {"closer", "won"}:
                session.non_improving_moves = 0
            else:
                session.non_improving_moves = min(
                    2, session.non_improving_moves + 1
                )
            progress = {
                "kind": progress_kind,
                "message": _PROGRESS_MESSAGES[progress_kind],
            }
        else:
            # Automatic direction is an easy-mode aid only; other modes retain no
            # latent progress streak that could later surface unexpectedly.
            session.non_improving_moves = 0

        result = {
            "ok": True,
            "current": _concept(guess),
            "relation": svc.link_label(prev, guess),
            "path": _path(session),
            "moves": session.moves,
            "won": session.won,
            "choices": _visible_choices(session),
            "backtrack_recommended": (
                session.difficulty == "usor"
                and session.non_improving_moves >= 2
            ),
        }
        if progress is not None:
            result["progress"] = progress
        if dead_end:
            result["dead_end"] = True
        if notes:
            result["message"] = " ".join(notes)
        if session.won:
            result["score"] = _score_for(session.moves, session.optimal)
            result["share"] = _share_line(
                session.moves, session.optimal, session.daily, session.category
            )
        return Response(result)


class UndoView(ContractAPIView):
    @extend_schema(operation_id="lant_undo", tags=["lant"])
    @_atomic_session
    def post(self, request, game_id: str, session: LantSession):
        # Never step below the start.
        if len(session.chain) > 1:
            session.chain.pop()
            session.hint_requests = 0
            session.won = session.current == session.target
        session.non_improving_moves = 0
        return Response(_state(game_id, session))


class HintView(ContractAPIView):
    @extend_schema(operation_id="lant_hint", tags=["lant"])
    @_atomic_session
    def post(self, request, game_id: str, session: LantSession):
        if session.won:
            return Response({"hint": None, "message": "Ai ajuns deja la tinta."})

        svc = get_service()
        cur = session.current
        # Help escalates only while no move/undo occurs.  Three is the terminal reveal,
        # so capping here bounds even an abusive stream of repeated hint requests.
        session.hint_requests = min(3, session.hint_requests + 1)
        asks_here = session.hint_requests
        dist_to_target = svc.distances_to(session.target)
        remaining = dist_to_target.get(cur)
        if remaining is None:
            # Player wandered into a dead end: the target is unreachable from here. Point
            # them back to the nearest node ON THEIR OWN CHAIN that can still reach the
            # target — naming only a node they have already visited (never a hidden one).
            for nid in reversed(session.chain):
                if nid != cur and dist_to_target.get(nid) is not None:
                    return Response(
                        {
                            "hint": None,
                            "stage": "backtrack",
                            "message": (
                                "Fundătură — folosește Înapoi până la "
                                f"{svc.label(nid)}."
                            ),
                        }
                    )
            return Response(
                {"hint": None, "message": "Nicio scurtatura de aici — incearca sa revii."}
            )

        shortest = _shortest_hops(session, dist_to_target)
        forward = shortest or _distinct_hops(
            cur,
            session.target,
            [
                node_id
                for node_id in svc.neighbor_ids(cur)
                if node_id not in session.chain and node_id in dist_to_target
            ],
            dist_to_target,
        )
        if not forward:
            # A legal revisit may leave the only shortest continuation on the already
            # walked chain.  Suggestions intentionally suppress revisits, so point to the
            # free undo control instead of returning an empty/misleading hint.
            prior_shortest = {
                node_id
                for node_id in svc.neighbor_ids(cur)
                if node_id in session.chain[:-1]
                and dist_to_target.get(node_id) == remaining - 1
            }
            if prior_shortest:
                recovery = next(
                    node_id
                    for node_id in reversed(session.chain[:-1])
                    if node_id in prior_shortest
                )
                return Response(
                    {
                        "hint": None,
                        "stage": "backtrack",
                        "remaining": remaining,
                        "message": (
                            "Drumul continuă printr-un pas deja vizitat. Folosește "
                            f"Înapoi până la {svc.label(recovery)}."
                        ),
                    }
                )
        if forward:
            best = forward[0]
            guided_remaining = 1 + dist_to_target[best]
            common = {
                "hint": None,
                "remaining": guided_remaining,
                "alternatives": len(forward),
            }
            if asks_here == 1:
                relation = _short_relation(cur, best)
                return Response(
                    {
                        **common,
                        "stage": "direction",
                        "relation": relation,
                        "message": f"Direcție: caută o legătură „{relation}”.",
                    }
                )
            if asks_here == 2:
                near = (
                    _distinct_hops(
                        cur,
                        session.target,
                        [*shortest, *_near_route_hops(session, dist_to_target)],
                        dist_to_target,
                    )
                    if shortest
                    else forward
                )
                alternatives = [_choice_payload(cur, node_id) for node_id in near[:2]]
                lead = (
                    "O variantă utilă: "
                    if len(alternatives) == 1
                    else "Variante utile: "
                )
                return Response(
                    {
                        **common,
                        "stage": "alternatives",
                        "alternatives_choices": alternatives,
                        "alternatives_labels": [choice["label"] for choice in alternatives],
                        "message": lead
                        + ", ".join(choice["label"] for choice in alternatives)
                        + ".",
                    }
                )
            return Response(
                {
                    **common,
                    "stage": "hop",
                    "hint": _concept(best),
                    "relation": _short_relation(cur, best),
                    "message": f"Un salt bun: {svc.label(best)}.",
                }
            )

        return Response({"hint": None, "message": "Niciun indiciu disponibil."})


_BASE = "api/wordgames/lant"
urlpatterns = [
    path(f"{_BASE}/games", CreateGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>", GetGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/move", MoveView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/undo", UndoView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/hint", HintView.as_view()),
]
