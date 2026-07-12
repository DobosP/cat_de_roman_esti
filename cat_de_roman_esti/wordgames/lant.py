"""Lantul Cuvintelor — a Wiki-game / word-ladder over the offline KG.

The player is shown a START and a TARGET concept. Each turn they TYPE a concept that
is directly LINKED (a real, non-distractor KG edge) to the CURRENT concept, hopping
along the chain. The goal is to reach the target in as few moves as possible.

Server-authoritative: the chain, the optimal distance and all validation live here.
The target id is public (it must be shown) but is only meaningful with the hidden
graph; the frontend never sees the shortest path until it asks for a hint.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

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
    LANT_MIN_FIRST_HOP_CHOICES,
    LANT_MIN_LAYER_WIDTH,
    get_pack,
    lant_branch_profile,
)
from .service import SessionStore, daily_seed, get_service, normalize

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

    @property
    def current(self) -> str:
        return self.chain[-1]

    @property
    def moves(self) -> int:
        return len(self.chain) - 1


store: SessionStore[LantSession] = SessionStore()


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

    def _closeness(nid: str) -> tuple[int, str]:
        d = dist_to_target.get(nid)
        return (d if d is not None else 1_000_000, nid)

    return min(legal, key=_closeness)


def _concept(node_id: str) -> dict[str, str]:
    svc = get_service()
    return {"id": node_id, "label": svc.label(node_id)}


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
    return min_width * 10 + first_hop * 3 + total + salience * salience_weight


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
            first_hop, min_width, total = lant_branch_profile(
                svc, start, target, optimal
            )
            score = _pair_score(start, target, first_hop, min_width, total, sal_weight)
            if best_any is None or score > best_any[0]:
                best_any = (score, start, target, optimal)
            if first_hop >= _MIN_FIRST_HOP_CHOICES and min_width >= _MIN_LAYER_WIDTH:
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
            curated = get_pack().pick_daily(
                GAME_KEY, daily, category=category, difficulty=difficulty
            )
        else:
            curated = get_pack().pick_seeded(
                GAME_KEY,
                random.Random(seed),
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
            rng = random.Random(seed)
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
        game_id = store.create(session)
        return Response(_state(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="lant_get_game", tags=["lant"])
    def get(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        return Response(_state(game_id, session))


class MoveView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="lant_move", tags=["lant"])
    def post(self, request, game_id: str):
        body = parse_body(request, MoveBody)
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        if session.won:
            return Response({"ok": True, **_state(game_id, session)})

        svc = get_service()
        if not body.text or not body.text.strip():
            return Response({"ok": False, "last_error": "Scrie un concept"})

        prev = session.current
        guess = _resolve_neighbor(body.text, prev, session.target)
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

        if guess == prev:
            return Response({"ok": False, "last_error": "Esti deja aici"})
        if svc.link(prev, guess) is None:
            return Response({"ok": False, "last_error": "Nu exista o legatura directa"})

        session.chain.append(guess)
        session.won = guess == session.target
        if session.won:
            record_finished(request, GAME_KEY, session.pack_id)

        result = {
            "ok": True,
            "current": _concept(guess),
            "relation": svc.link_label(prev, guess),
            "path": _path(session),
            "moves": session.moves,
            "won": session.won,
        }
        if session.won:
            result["score"] = _score_for(session.moves, session.optimal)
            result["share"] = _share_line(
                session.moves, session.optimal, session.daily, session.category
            )
        return Response(result)


class UndoView(ContractAPIView):
    @extend_schema(operation_id="lant_undo", tags=["lant"])
    def post(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        # Never step below the start.
        if len(session.chain) > 1:
            session.chain.pop()
            session.won = session.current == session.target
        return Response(_state(game_id, session))


class HintView(ContractAPIView):
    @extend_schema(operation_id="lant_hint", tags=["lant"])
    def post(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        if session.won:
            return Response({"hint": None, "message": "Ai ajuns deja la tinta."})

        svc = get_service()
        cur = session.current
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
                            "message": f"Fundatura — intoarce-te la {svc.label(nid)}.",
                        }
                    )
            return Response(
                {"hint": None, "message": "Nicio scurtatura de aici — incearca sa revii."}
            )

        # All neighbours that lie on a shortest path (one hop closer to the target). When
        # several exist, suggest the most salient (most recognisable) one so the hint is
        # genuinely helpful rather than an obscure node the player has never heard of.
        on_path = [
            nb
            for nb in svc.neighbor_ids(cur)
            if dist_to_target.get(nb) == remaining - 1
        ]
        if on_path:
            on_path.sort(key=lambda nb: (_salience(nb), nb), reverse=True)
            best = on_path[0]
            return Response(
                {
                    "hint": _concept(best),
                    "relation": svc.link_label(cur, best),
                    "remaining": remaining,
                    # When >1 such neighbour exists, the player genuinely had a choice here.
                    "alternatives": len(on_path),
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
