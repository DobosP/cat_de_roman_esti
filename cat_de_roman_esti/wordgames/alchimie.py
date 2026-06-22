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

from .service import SessionStore, daily_seed, get_service

router = APIRouter(prefix="/api/wordgames/alchimie", tags=["alchimie"])

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

# Difficulty -> (target generation policy, seed-count range).
#   usor : shallow target (generation 2) but a wide 6-7 seed inventory (more options).
#   normal: target at generation 2-3 with the default 5-7 seeds.
#   greu : deepest available target (>=3) with a lean 5-seed inventory.
DIFFICULTIES = {"usor", "normal", "greu"}
DEFAULT_DIFFICULTY = "normal"


def _difficulty_params(difficulty: str) -> tuple[int, int | None, int, int]:
    """Return (min_gen, max_gen_or_None, seed_min, seed_max) for a difficulty."""
    if difficulty == "usor":
        return (2, 2, 6, 7)
    if difficulty == "greu":
        return (3, None, 5, 5)
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

    @property
    def won(self) -> bool:
        return self.target in self.owned

    @property
    def score(self) -> int:
        """Reward few combines. Perfect (==target depth) gives 1000; floor of 100."""
        extra = max(0, self.moves - self.target_depth)
        return max(100, 1000 - 120 * extra)

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


def _build_session(
    rng: random.Random, difficulty: str = DEFAULT_DIFFICULTY, daily: str | None = None
) -> AlchimieSession:
    """Sample a solvable instance: a recognizable seed set + a target at a difficulty-

    tuned depth in the seed combine-closure.
    """
    svc = get_service()
    min_gen, max_gen, seed_min, seed_max = _difficulty_params(difficulty)
    pool = [nid for nid in svc.by_salience(minimum=SEED_SALIENCE_FLOOR)]
    if len(pool) < seed_max:
        pool = svc.all_ids()

    def _finish(seeds: list[str], target: str, depth: int) -> AlchimieSession:
        session = AlchimieSession(
            seeds=list(seeds),
            target=target,
            target_depth=depth,
            difficulty=difficulty,
            daily=daily,
        )
        for s in seeds:
            session.add(s, None)
        return session

    for _ in range(MAX_BUILD_ATTEMPTS):
        k = rng.randint(seed_min, min(seed_max, len(pool)))
        seeds = rng.sample(pool, k)
        gen = _closure_with_generations(seeds)
        # Candidates satisfying this difficulty's generation window.
        cands = [
            nid
            for nid, depth in gen.items()
            if depth >= min_gen and (max_gen is None or depth <= max_gen)
        ]
        if not cands:
            continue
        if difficulty == "greu":
            # Deepest available target (>=3) for the most satisfying multi-combine puzzle.
            max_depth = max(gen[nid] for nid in cands)
            cands = [nid for nid in cands if gen[nid] == max_depth]
        target = rng.choice(cands)
        return _finish(seeds, target, gen[target])

    # Fallback: relax to the global MIN_TARGET_GENERATION over the full id pool.
    seeds = rng.sample(svc.all_ids(), min(seed_max, len(svc.all_ids())))
    gen = _closure_with_generations(seeds)
    deep = [nid for nid, depth in gen.items() if depth >= MIN_TARGET_GENERATION]
    if not deep:
        raise HTTPException(status_code=500, detail="Nu am putut genera un joc solvabil.")
    target = rng.choice(deep)
    return _finish(seeds, target, gen[target])


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
    perfect = session.moves <= session.target_depth
    medal = "✨" if perfect else "⚗️"
    lines = [
        "cat_de_roman_esti · Alchimie",
        f"⚗️ {session.moves} combinatii · {session.score} pct {medal}",
    ]
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
    }
    if session.daily:
        payload["daily"] = session.daily
    if session.won:
        payload["score"] = session.score
        payload["share"] = _share_line(session)
    return payload


def _require(game_id: str) -> AlchimieSession:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent.")
    return session


# --------------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(
    seed: int | None = None,
    difficulty: str = DEFAULT_DIFFICULTY,
    daily: str | None = None,
) -> dict[str, object]:
    """Start a new Alchimie game.

    ``?difficulty=`` in {usor,normal,greu} tunes the target depth + seed count.
    ``?daily=YYYY-MM-DD`` makes a shared, deterministic daily instance (ignores seed).
    Otherwise an optional ``?seed=`` makes the instance reproducible.
    """
    if difficulty not in DIFFICULTIES:
        difficulty = DEFAULT_DIFFICULTY
    if daily:
        rng = random.Random(daily_seed(daily, GAME_KEY))
    else:
        rng = random.Random(seed)
    session = _build_session(rng, difficulty=difficulty, daily=daily)
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
