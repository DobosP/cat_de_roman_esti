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

from .service import SessionStore, get_service

router = APIRouter(prefix="/api/wordgames/lant", tags=["lant"])

# A satisfying ladder: not trivial, not a marathon.
_MIN_DISTANCE = 3
_MAX_DISTANCE = 5
# How many random start/target draws we attempt before giving up (always succeeds in
# practice — the KG has thousands of pairs in range).
_MAX_DRAWS = 400


@dataclass
class LantSession:
    start: str
    target: str
    optimal: int
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
    return {
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
    }


# --------------------------------------------------------------------- puzzle picking
def _pick_pair(rng: random.Random) -> tuple[str, str, int]:
    """Pick a (start, target) whose distance is in [_MIN_DISTANCE, _MAX_DISTANCE].

    Prefer reasonably salient, well-connected concepts so the ladder is meaningful and
    the player has real choices at every hop. Guaranteed solvable by construction.
    """
    svc = get_service()
    # Candidate starts: decently connected nodes (degree >= 2) so a hop is always possible.
    candidates = [nid for nid in svc.all_ids() if svc.degree(nid) >= 2]
    if not candidates:
        candidates = svc.all_ids()

    for _ in range(_MAX_DRAWS):
        start = rng.choice(candidates)
        dist_map = svc.distances_from(start)
        reachable = [
            nid
            for nid, d in dist_map.items()
            if _MIN_DISTANCE <= d <= _MAX_DISTANCE and svc.degree(nid) >= 1
        ]
        if not reachable:
            continue
        target = rng.choice(reachable)
        return start, target, dist_map[target]

    raise HTTPException(
        status_code=503,
        detail="Nu am putut genera un lant valid; reincearca.",
    )


# --------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(seed: int | None = None) -> dict:
    rng = random.Random(seed)
    start, target, optimal = _pick_pair(rng)
    session = LantSession(start=start, target=target, optimal=optimal, chain=[start])
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
    guess = svc.resolve(body.text)
    if guess is None:
        return {"ok": False, "last_error": "Nu cunosc acest concept"}

    prev = session.current
    if guess == prev:
        return {"ok": False, "last_error": "Esti deja aici"}
    if svc.link(prev, guess) is None:
        return {"ok": False, "last_error": "Nu exista o legatura directa"}

    session.chain.append(guess)
    session.won = guess == session.target

    return {
        "ok": True,
        "current": _concept(guess),
        "relation": svc.link_label(prev, guess),
        "path": _path(session),
        "moves": session.moves,
        "won": session.won,
    }


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

    # A neighbour that lies on a shortest path: one hop closer to the target.
    for neighbor in svc.neighbor_ids(cur):
        nd = svc.distance(neighbor, session.target)
        if nd is not None and nd == remaining - 1:
            return {
                "hint": _concept(neighbor),
                "relation": svc.link_label(cur, neighbor),
                "remaining": remaining,
            }

    return {"hint": None, "message": "Niciun indiciu disponibil."}
