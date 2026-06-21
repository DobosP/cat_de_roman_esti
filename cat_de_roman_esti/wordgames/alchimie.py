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

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .service import SessionStore, get_service

router = APIRouter(prefix="/api/wordgames/alchimie", tags=["alchimie"])

# A combine-closure must produce a target at least this many generations deep so the
# puzzle takes a few crafts (generation 1 == a direct common neighbour of two seeds).
MIN_TARGET_GENERATION = 2
# How many random seed sets to try before giving up on building a deep instance.
MAX_BUILD_ATTEMPTS = 400
# Seed inventory size range (recognizable, higher-salience nodes).
SEED_MIN, SEED_MAX = 5, 7
# Only consider reasonably salient (recognizable) nodes as seeds.
SEED_SALIENCE_FLOOR = 0.4


@dataclass
class AlchimieSession:
    """One in-progress Alchimie game (server-side secret state)."""

    seeds: list[str]
    target: str
    # owned id -> (parent_a, parent_b) or None for the original seeds.
    owned: dict[str, tuple[str, str] | None] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    moves: int = 0

    @property
    def won(self) -> bool:
        return self.target in self.owned

    def add(self, node_id: str, parents: tuple[str, str] | None) -> None:
        if node_id not in self.owned:
            self.owned[node_id] = parents
            self.order.append(node_id)


store: SessionStore[AlchimieSession] = SessionStore()


# --------------------------------------------------------------------- instance builder
def _closure_with_generations(seeds: list[str]) -> dict[str, int]:
    """Combine-closure of ``seeds`` mapping every reachable id -> its generation.

    Generation 0 are the seeds; generation 1 are direct common neighbours of two seeds;
    generation N nodes first appear when combining items available after generation N-1.
    Fixpoint loop: keep combining all owned pairs until nothing new appears.
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
            for c in svc.common_neighbors(a, b):
                if c not in owned and c not in fresh:
                    fresh.add(c)
                    gen.setdefault(c, g)
        if fresh:
            owned |= fresh
            changed = True
    return gen


def _build_session(rng: random.Random) -> AlchimieSession:
    """Sample a solvable instance: a recognizable seed set + a deep target."""
    svc = get_service()
    pool = [nid for nid in svc.by_salience(minimum=SEED_SALIENCE_FLOOR)]
    if len(pool) < SEED_MAX:
        pool = svc.all_ids()

    for _ in range(MAX_BUILD_ATTEMPTS):
        k = rng.randint(SEED_MIN, min(SEED_MAX, len(pool)))
        seeds = rng.sample(pool, k)
        gen = _closure_with_generations(seeds)
        deep = [nid for nid, depth in gen.items() if depth >= MIN_TARGET_GENERATION]
        if not deep:
            continue
        # Prefer the deepest available targets (more satisfying multi-combine puzzles).
        max_depth = max(gen[nid] for nid in deep)
        deepest = [nid for nid in deep if gen[nid] == max_depth]
        target = rng.choice(deepest)
        session = AlchimieSession(seeds=list(seeds), target=target)
        for s in seeds:
            session.add(s, None)
        return session

    # Extremely unlikely fallback: widen the pool to everything and retry once more.
    seeds = rng.sample(svc.all_ids(), SEED_MAX)
    gen = _closure_with_generations(seeds)
    deep = [nid for nid, depth in gen.items() if depth >= MIN_TARGET_GENERATION]
    if not deep:
        raise HTTPException(status_code=500, detail="Nu am putut genera un joc solvabil.")
    session = AlchimieSession(seeds=list(seeds), target=rng.choice(deep))
    for s in seeds:
        session.add(s, None)
    return session


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


def _state_payload(game_id: str, session: AlchimieSession) -> dict[str, object]:
    return {
        "game_id": game_id,
        "target": _target_payload(session),
        "inventory": _inventory_payload(session),
        "discovered_count": max(0, len(session.order) - len(session.seeds)),
        "seed_count": len(session.seeds),
        "moves": session.moves,
        "won": session.won,
    }


def _require(game_id: str) -> AlchimieSession:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent.")
    return session


# --------------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(seed: int | None = None) -> dict[str, object]:
    """Start a new Alchimie game. Optional ``?seed=`` makes the instance deterministic."""
    rng = random.Random(seed)
    session = _build_session(rng)
    game_id = store.create(session)
    return _state_payload(game_id, session)


@router.get("/games/{game_id}")
def get_game(game_id: str) -> dict[str, object]:
    """Full current state of an existing game."""
    return _state_payload(game_id, _require(game_id))


@router.post("/games/{game_id}/combine")
def combine(game_id: str, body: CombineBody) -> dict[str, object]:
    """Combine two owned concepts; append any newly-discovered shared neighbours."""
    svc = get_service()
    session = _require(game_id)

    a, b = body.a, body.b
    if a not in session.owned or b not in session.owned:
        raise HTTPException(
            status_code=400, detail="Ambele concepte trebuie sa fie in inventar."
        )
    if a == b:
        raise HTTPException(
            status_code=400, detail="Alege doua concepte diferite."
        )

    session.moves += 1
    discovered = [c for c in svc.common_neighbors(a, b) if c not in session.owned]
    for c in discovered:
        session.add(c, (a, b))

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
    return payload


@router.post("/games/{game_id}/reset")
def reset_game(game_id: str) -> dict[str, object]:
    """Reset the SAME instance back to its original seed inventory (target unchanged)."""
    session = _require(game_id)
    session.owned.clear()
    session.order.clear()
    session.moves = 0
    for s in session.seeds:
        session.add(s, None)
    return _state_payload(game_id, session)
