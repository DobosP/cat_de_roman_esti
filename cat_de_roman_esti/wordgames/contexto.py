"""Contexto / Semantle-style word game: "Cald sau Rece".

There is a hidden SECRET target concept in the Romanian knowledge graph. The player
types concept guesses; each guess reports how CLOSE it is to the target, measured as the
BFS graph distance on the shared non-distractor subgraph (:mod:`.service`). Distance 0
means the guess IS the target — the player wins. Otherwise the game maps the distance to
a "temperature" tier (Fierbinte … Inghetat) and a 0..100 closeness score derived from how
the guess ranks within the precomputed distance distribution of all reachable concepts.

Server-authoritative: the target id is NEVER returned to the client until the game is won
or given up. Sessions live in-memory in a :class:`SessionStore`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .service import SessionStore, get_service

router = APIRouter(prefix="/api/wordgames/contexto", tags=["contexto"])

# A target needs a large reachable set so almost every guess gets a meaningful distance.
MIN_REACHABLE = 120


# --------------------------------------------------------------------------- session
@dataclass
class GuessRecord:
    id: str
    label: str
    distance: int
    temperature: str
    closeness: int


@dataclass
class ContextoSession:
    target: str
    # distance (from target) -> count of reachable nodes at that distance
    dist_hist: dict[int, int]
    reachable: int
    # how many reachable nodes are STRICTLY farther than distance d (for ranking)
    farther_than: dict[int, int] = field(default_factory=dict)
    guesses: dict[str, GuessRecord] = field(default_factory=dict)
    attempts: int = 0
    won: bool = False
    gave_up: bool = False

    def __post_init__(self) -> None:
        # Precompute, for each distance value, how many reachable nodes are farther.
        # closeness uses this so we don't recompute on every guess.
        total = self.reachable
        # sorted distances ascending
        cumulative = 0
        self.farther_than = {}
        for d in sorted(self.dist_hist):
            count_at = self.dist_hist[d]
            # nodes farther than d = total - (nodes at distance <= d)
            self.farther_than[d] = total - (cumulative + count_at)
            cumulative += count_at


store: SessionStore[ContextoSession] = SessionStore()


# --------------------------------------------------------------------------- scoring
def temperature_for(distance: int | None) -> str:
    """Map a BFS distance to a Romanian temperature tier."""
    if distance is None:
        return "Inghetat"
    if distance == 0:
        return "Gasit"
    if distance == 1:
        return "Fierbinte"
    if distance == 2:
        return "Cald"
    if distance == 3:
        return "Caldut"
    if distance in (4, 5):
        return "Rece"
    return "Inghetat"


def closeness_for(session: ContextoSession, distance: int | None) -> int:
    """0..100 closeness: the percentage of reachable concepts this guess beats.

    A guess at distance ``d`` is "closer than" every reachable node strictly farther
    than ``d``. We express that as a percentage of the reachable set, so the target
    itself (distance 0) is 100 and the most distant nodes approach 0.
    """
    if distance is None:
        return 0
    if distance == 0:
        return 100
    total = session.reachable
    if total <= 1:
        return 0
    farther = session.farther_than.get(distance)
    if farther is None:
        # Distance larger than any reachable bucket (shouldn't happen for reachable
        # guesses) -> treat as the coldest.
        farther = 0
    return max(0, min(100, round(100 * farther / (total - 1))))


# --------------------------------------------------------------------------- selection
def _pick_target(seed: int | None) -> ContextoSession:
    """Choose a solvable secret target with a sufficiently large reachable set."""
    svc = get_service()
    rng = random.Random(seed)
    candidates = [nid for nid in svc.all_ids()]
    rng.shuffle(candidates)
    for nid in candidates:
        dist = svc.distances_from(nid)
        if len(dist) >= MIN_REACHABLE:
            hist: dict[int, int] = {}
            for d in dist.values():
                hist[d] = hist.get(d, 0) + 1
            return ContextoSession(target=nid, dist_hist=hist, reachable=len(dist))
    # Fallback: no node met the threshold (impossible for the bundled KG) — take the
    # best available so we still return a solvable game.
    best = max(svc.all_ids(), key=lambda n: len(svc.distances_from(n)))
    dist = svc.distances_from(best)
    hist = {}
    for d in dist.values():
        hist[d] = hist.get(d, 0) + 1
    return ContextoSession(target=best, dist_hist=hist, reachable=len(dist))


# --------------------------------------------------------------------------- schemas
class GuessBody(BaseModel):
    text: str


def _sorted_guesses(session: ContextoSession) -> list[dict]:
    """Past guesses serialized best-first (smallest distance, then highest closeness)."""
    records = sorted(
        session.guesses.values(),
        key=lambda g: (g.distance, -g.closeness, g.label),
    )
    return [
        {
            "id": g.id,
            "label": g.label,
            "distance": g.distance,
            "temperature": g.temperature,
            "closeness": g.closeness,
        }
        for g in records
    ]


def _state(game_id: str, session: ContextoSession) -> dict:
    body: dict = {
        "game_id": game_id,
        "attempts": session.attempts,
        "won": session.won,
        "gave_up": session.gave_up,
        "reachable_count": session.reachable,
        "guesses": _sorted_guesses(session),
    }
    if session.won or session.gave_up:
        svc = get_service()
        body["target"] = {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
        }
    return body


# --------------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(seed: int | None = None) -> dict:
    session = _pick_target(seed)
    game_id = store.create(session)
    return _state(game_id, session)


@router.get("/games/{game_id}")
def get_game(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    return _state(game_id, session)


@router.post("/games/{game_id}/guess")
def guess(game_id: str, body: GuessBody) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    if session.won or session.gave_up:
        raise HTTPException(status_code=400, detail="Jocul s-a terminat")

    svc = get_service()
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Scrie un concept")

    node_id = svc.resolve(text)
    if node_id is None:
        # Unknown concept: do NOT count it as an attempt.
        return {
            "ok": False,
            "message": "Nu cunosc acest concept",
            "guesses": _sorted_guesses(session),
            "attempts": session.attempts,
            "won": session.won,
            "reachable_count": session.reachable,
        }

    distance = svc.distance(node_id, session.target)
    temperature = temperature_for(distance)
    closeness = closeness_for(session, distance)
    # distance is None when the guess is in a disconnected part of the graph — we still
    # store it (as the coldest possible) so a repeated guess shows the same verdict.
    stored_distance = distance if distance is not None else 999

    record = GuessRecord(
        id=node_id,
        label=svc.label(node_id),
        distance=stored_distance,
        temperature=temperature,
        closeness=closeness,
    )
    is_new = node_id not in session.guesses
    session.guesses[node_id] = record
    if is_new:
        session.attempts += 1

    if distance == 0:
        session.won = True

    result: dict = {
        "ok": True,
        "guess": {
            "id": record.id,
            "label": record.label,
            "distance": record.distance,
            "temperature": record.temperature,
            "closeness": record.closeness,
        },
        "guesses": _sorted_guesses(session),
        "attempts": session.attempts,
        "won": session.won,
        "reachable_count": session.reachable,
    }
    if session.won:
        result["target"] = {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
        }
    return result


@router.post("/games/{game_id}/giveup")
def give_up(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    session.gave_up = True
    return _state(game_id, session)
