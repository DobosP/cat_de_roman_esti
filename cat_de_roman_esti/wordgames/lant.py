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

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .service import SessionStore, daily_seed, get_service, normalize

router = APIRouter(prefix="/api/wordgames/lant", tags=["lant"])

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
_MIN_FIRST_HOP_CHOICES = 2
_MIN_LAYER_WIDTH = 2
# Once we have found enough genuinely-good candidates we stop early (keeps latency low).
_ENOUGH_GOOD = 6


def _score_for(moves: int, optimal: int) -> int:
    """Par-relative score: playing at optimal -> 1000, never below 100."""
    moves = max(moves, 1)
    return max(100, round(1000 * optimal / max(moves, optimal)))


def _share_line(moves: int, optimal: int, daily: str | None) -> str:
    return (
        "cat_de_roman_esti · Lantul Cuvintelor\n"
        f"🔗 {moves}/{optimal} mutari\n"
        f"{daily or ''}"
    )


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
def _resolve_neighbor(text: str, current: str) -> str | None:
    """Resolve player text to a node, disambiguating by what is linked to ``current``.

    The shared index maps a normalized label to a *single* node id, so when two concepts
    share a label (e.g. two "Moldova" nodes) a literal resolve can pick the one that is
    NOT linked to the current node and a perfectly valid guess gets wrongly rejected.
    Here we look at every node carrying the typed label and prefer one that is an actual
    neighbour of ``current`` (excluding ``current`` itself), so disambiguation favours a
    legal hop.
    """
    svc = get_service()
    primary = svc.resolve(text)
    if primary is not None and primary != current and svc.link(current, primary) is not None:
        return primary
    key = normalize(text)
    if not key:
        return primary
    # Scan for same-label siblings that ARE a legal hop from here.
    for nid in svc.all_ids():
        if nid == current:
            continue
        if normalize(svc.label(nid)) == key and svc.link(current, nid) is not None:
            return nid
    return primary


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
    if session.won:
        state["score"] = _score_for(session.moves, session.optimal)
        state["share"] = _share_line(session.moves, session.optimal, session.daily)
    return state


# --------------------------------------------------------------------- puzzle picking
def _salience(node_id: str) -> float:
    node = get_service().node(node_id)
    return node.salience if node else 0.0


def _branch_profile(
    start: str, target: str, optimal: int, dist_from_target: dict[str, int]
) -> tuple[int, int, int]:
    """Measure how branchy the shortest-path "diamond" between start and target is.

    Returns ``(first_hop_choices, min_layer_width, total_on_path)`` where:

    * ``first_hop_choices`` — neighbours of START that are one hop closer to the target
      (i.e. genuine, correct first moves). >1 means the opening is not a forced rail.
    * ``min_layer_width`` — the narrowest shortest-path layer between the endpoints. A
      width of 1 anywhere means every solver is funnelled through that single node.
    * ``total_on_path`` — count of intermediate nodes lying on *some* shortest path; a
      bigger web means more legitimate routes and a more satisfying solve.
    """
    svc = get_service()
    dist_from_start = svc.distances_from(start)
    layers: dict[int, int] = {}
    for nid, ds in dist_from_start.items():
        dt = dist_from_target.get(nid)
        if dt is not None and ds + dt == optimal:
            layers[ds] = layers.get(ds, 0) + 1
    intermediate = [layers.get(k, 0) for k in range(1, optimal)]
    min_width = min(intermediate) if intermediate else 1
    total_on_path = sum(intermediate)
    first_hop = sum(
        1
        for nb in svc.neighbor_ids(start)
        if dist_from_target.get(nb) == optimal - 1
    )
    return first_hop, min_width, total_on_path


def _pair_score(start: str, target: str, first_hop: int, min_width: int, total: int) -> float:
    """Rank candidate pairs: reward branchiness, salient endpoints and richer webs."""
    salience = (_salience(start) + _salience(target)) / 2
    return min_width * 10 + first_hop * 3 + total + salience * 4


def _pick_pair(rng: random.Random, lo: int, hi: int) -> tuple[str, str, int]:
    """Pick a (start, target) whose distance is in [lo, hi].

    We don't take the first reachable pair: we *playtest* candidates and keep the most
    satisfying one. A good ladder has REAL choices at the opening hop, never funnels
    every solver through a single forced node, prefers salient (recognisable) endpoints
    and avoids leaf (degree-1) endpoints. The search is bounded and deterministic in the
    seed, and degrades gracefully — if nothing clears the "genuinely good" bar we keep
    the best-scoring pair seen, and as a last resort accept any reachable pair.
    """
    svc = get_service()
    candidates = [nid for nid in svc.all_ids() if svc.degree(nid) >= _MIN_ENDPOINT_DEGREE]
    if not candidates:
        candidates = [nid for nid in svc.all_ids() if svc.degree(nid) >= 1]
    if not candidates:
        raise HTTPException(status_code=503, detail="Graful nu are noduri jucabile.")

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
            if lo <= d <= hi and svc.degree(nid) >= _MIN_ENDPOINT_DEGREE
        ]
        if not reachable:
            continue
        rng.shuffle(reachable)
        for target, optimal in reachable[:_TARGETS_PER_START]:
            if fallback is None:
                fallback = (start, target, optimal)
            dist_from_target = svc.distances_from(target)
            first_hop, min_width, total = _branch_profile(
                start, target, optimal, dist_from_target
            )
            score = _pair_score(start, target, first_hop, min_width, total)
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

    raise HTTPException(
        status_code=503,
        detail="Nu am putut genera un lant valid; reincearca.",
    )


# --------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(
    seed: int | None = None,
    difficulty: str = _DEFAULT_DIFFICULTY,
    daily: str | None = None,
) -> dict:
    if difficulty not in _DIFFICULTY_BANDS:
        difficulty = _DEFAULT_DIFFICULTY
    lo, hi = _DIFFICULTY_BANDS[difficulty]
    if daily is not None:
        seed = daily_seed(daily, GAME_KEY)
    rng = random.Random(seed)
    start, target, optimal = _pick_pair(rng, lo, hi)
    session = LantSession(
        start=start,
        target=target,
        optimal=optimal,
        difficulty=difficulty,
        daily=daily,
        chain=[start],
    )
    game_id = store.create(session)
    return _state(game_id, session)


@router.get("/games/{game_id}")
def get_game(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    return _state(game_id, session)


@router.post("/games/{game_id}/move")
def move(game_id: str, body: MoveBody) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    if session.won:
        return {"ok": True, **_state(game_id, session)}

    svc = get_service()
    if not body.text or not body.text.strip():
        return {"ok": False, "last_error": "Scrie un concept"}

    prev = session.current
    guess = _resolve_neighbor(body.text, prev)
    if guess is None:
        return {"ok": False, "last_error": "Nu cunosc acest concept"}

    if guess == prev:
        return {"ok": False, "last_error": "Esti deja aici"}
    if svc.link(prev, guess) is None:
        return {"ok": False, "last_error": "Nu exista o legatura directa"}

    session.chain.append(guess)
    session.won = guess == session.target

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
        result["share"] = _share_line(session.moves, session.optimal, session.daily)
    return result


@router.post("/games/{game_id}/undo")
def undo(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    # Never step below the start.
    if len(session.chain) > 1:
        session.chain.pop()
        session.won = session.current == session.target
    return _state(game_id, session)


@router.post("/games/{game_id}/hint")
def hint(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    if session.won:
        return {"hint": None, "message": "Ai ajuns deja la tinta."}

    svc = get_service()
    cur = session.current
    remaining = svc.distance(cur, session.target)
    if remaining is None:
        # Player wandered into a dead end (shouldn't happen on the connected subgraph,
        # but be defensive): suggest stepping back.
        return {"hint": None, "message": "Nicio scurtatura de aici — incearca sa revii."}

    # All neighbours that lie on a shortest path (one hop closer to the target). When
    # several exist, suggest the most salient (most recognisable) one so the hint is
    # genuinely helpful rather than an obscure node the player has never heard of.
    on_path = [
        nb
        for nb in svc.neighbor_ids(cur)
        if svc.distance(nb, session.target) == remaining - 1
    ]
    if on_path:
        on_path.sort(key=lambda nb: (_salience(nb), nb), reverse=True)
        best = on_path[0]
        return {
            "hint": _concept(best),
            "relation": svc.link_label(cur, best),
            "remaining": remaining,
            # When >1 such neighbour exists, the player genuinely had a choice here.
            "alternatives": len(on_path),
        }

    return {"hint": None, "message": "Niciun indiciu disponibil."}
