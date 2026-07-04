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

from .service import SessionStore, daily_seed, get_service

router = APIRouter(prefix="/api/wordgames/contexto", tags=["contexto"])

GAME_KEY = "contexto"
_DIFFICULTIES = ("usor", "normal", "greu")
_DEFAULT_DIFFICULTY = "normal"

# A target needs a large reachable set so almost every guess gets a meaningful distance.
MIN_REACHABLE = 120

# In practice almost every node reaches the whole graph (~200 nodes), so MIN_REACHABLE
# alone never rejects a poor target. The signal that actually makes a game feel good is
# the "responsive zone": how many concepts sit at a graph distance the player can FEEL
# (1..5 hops -> Fierbinte..Rece). A target whose responsive zone is tiny pushes almost
# every guess into "Inghetat", which gives flat, unsatisfying feedback. We therefore
# require a minimum responsive-zone size so a guess is likely to land somewhere with a
# real temperature gradient. (Playtested: this floor removes the degenerate long-thin-tail
# targets — e.g. n_plumb / n_emil_racovita — while keeping wide variety per difficulty.)
RESPONSIVE_MAX_HOPS = 5
MIN_RESPONSIVE = 40

# A clue should help a stuck player without making the opening trivial. It reveals only
# the target's broad KG category, never the hidden id/label/description.
MIN_CLUE_ATTEMPTS = 3
CLUE_SCORE_PENALTY = 120

CATEGORY_LABELS = {
    "arta_cultura": "Arta & Cultura",
    "geografie": "Geografie",
    "istorie": "Istorie",
    "limba": "Limba",
    "literatura": "Literatura",
    "personalitati": "Personalitati",
    "societate": "Societate",
    "stiinta": "Stiinta",
}


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
    # guess ids in the chronological order they were first played (for the share trail)
    order: list[str] = field(default_factory=list)
    attempts: int = 0
    won: bool = False
    gave_up: bool = False
    clue_revealed: bool = False
    clues_used: int = 0
    difficulty: str = _DEFAULT_DIFFICULTY
    daily: str | None = None

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
    raw = round(100 * farther / (total - 1))
    # Only the target itself (distance 0, handled above) earns 100. A near miss can
    # otherwise saturate to 100 when nothing else is closer, which is ambiguous with a
    # win and reads as "you got it" when you didn't. Cap non-wins at 99.
    return max(1, min(99, raw))


# --------------------------------------------------------------------------- selection
# Hot/cold emoji trail for the shareable line: coldest -> hottest, plus a bullseye.
_TRAIL_FOUND = "🎯"
_TRAIL_HOT = "🟩"
_TRAIL_WARM = "🟨"
_TRAIL_COOL = "🟧"
_TRAIL_COLD = "🟥"


def score_for(attempts: int, clues_used: int = 0) -> int:
    """Reward few attempts: optimal (1 attempt) -> 1000, never below 50."""
    attempts = max(attempts, 1)
    return max(50, 1000 - 60 * (attempts - 1) - CLUE_SCORE_PENALTY * clues_used)


def _trail_emoji(record: GuessRecord) -> str:
    """One hot/cold square per guess, based on its closeness to the secret."""
    if record.distance == 0:
        return _TRAIL_FOUND
    c = record.closeness
    if c >= 75:
        return _TRAIL_HOT
    if c >= 50:
        return _TRAIL_WARM
    if c >= 25:
        return _TRAIL_COOL
    return _TRAIL_COLD


def share_line(session: ContextoSession) -> str:
    """Wordle-style shareable line with a hot/cold emoji trail of the guesses."""
    trail = "".join(_trail_emoji(session.guesses[gid]) for gid in session.order)
    lines = [
        "cat_de_roman_esti · Cald sau Rece",
        trail,
        f"{session.attempts} incercari",
    ]
    if session.clues_used:
        lines.append(f"indiciu x{session.clues_used}")
    if session.daily is not None:
        lines.append(session.daily)
    return "\n".join(lines)


def _difficulty_pool(svc, difficulty: str) -> list[str]:
    """Candidate target ids for a difficulty tier (before the reachability filter).

    usor  -> high-salience, well-known targets (salience >= 0.6).
    greu  -> low-salience / obscure targets (the bottom of the salience order).
    normal-> the full pool (the historical default; any reachable concept).

    ``normal`` keeps the original ``all_ids`` candidate set so the long-standing
    seeded instances stay stable; only ``usor``/``greu`` bias the selection.
    """
    if difficulty == "usor":
        high = svc.by_salience(minimum=0.6)
        return high or svc.all_ids()
    if difficulty == "greu":
        # obscure: lowest salience first, restricted to the less-prominent half so a
        # "greu" target is genuinely off the beaten path.
        by_sal = svc.by_salience(descending=True)  # high -> low
        obscure = list(reversed(by_sal))
        return obscure[: max(1, len(obscure) // 2)] or obscure
    # normal: the historical default candidate set.
    return svc.all_ids()


def _responsive_count(dist: dict[str, int]) -> int:
    """How many reachable concepts sit in the player-perceptible temperature band.

    These are the concepts at 1..RESPONSIVE_MAX_HOPS hops — i.e. everything that comes
    back warmer than "Inghetat". A larger band means guesses spread across more tiers and
    the game feels responsive instead of flatly frozen.
    """
    return sum(1 for d in dist.values() if 1 <= d <= RESPONSIVE_MAX_HOPS)


def _is_good_target(dist: dict[str, int]) -> bool:
    """A target is good if it is both broadly reachable and has a real warm band."""
    return len(dist) >= MIN_REACHABLE and _responsive_count(dist) >= MIN_RESPONSIVE


def _build_session(target: str, difficulty: str, daily: str | None) -> ContextoSession:
    svc = get_service()
    dist = svc.distances_from(target)
    hist: dict[int, int] = {}
    for d in dist.values():
        hist[d] = hist.get(d, 0) + 1
    return ContextoSession(
        target=target,
        dist_hist=hist,
        reachable=len(dist),
        difficulty=difficulty,
        daily=daily,
    )


def _pick_target(
    seed: int | None,
    difficulty: str = _DEFAULT_DIFFICULTY,
    daily: str | None = None,
) -> ContextoSession:
    """Choose a solvable, *satisfying* secret target of the requested difficulty.

    Selection is deterministic for a given seed (so the daily challenge is stable) and
    enforces two quality floors so no degenerate instance ships:

    * reachability (``MIN_REACHABLE``) — almost every guess gets a real distance; and
    * a responsive warm band (``MIN_RESPONSIVE``) — enough concepts land at 1..5 hops
      that guesses spread across temperatures instead of all reading "Inghetat".

    We walk the seeded-shuffled candidate pool and take the FIRST target that clears both
    floors. Taking the first (rather than the best) keeps the per-seed variety wide while
    still guaranteeing quality. Fallbacks degrade gracefully: relax to reachability-only,
    then to the single most-reachable node, so a game is always returned.
    """
    svc = get_service()
    rng = random.Random(seed)
    candidates = _difficulty_pool(svc, difficulty)
    # Deterministic ordering: for daily/seeded runs the pool order is fixed, then a
    # seeded shuffle picks within it -> same date+difficulty => same target.
    candidates = list(candidates)
    rng.shuffle(candidates)

    fallback: str | None = None  # first node clearing reachability but not the warm band
    for nid in candidates:
        dist = svc.distances_from(nid)
        if not _is_good_target(dist):
            if fallback is None and len(dist) >= MIN_REACHABLE:
                fallback = nid
            continue
        return _build_session(nid, difficulty, daily)

    if fallback is not None:
        return _build_session(fallback, difficulty, daily)
    # Last resort: nothing in this tier met even the reachability floor — take the
    # most-reachable node so we still return a solvable game.
    best = max(svc.all_ids(), key=lambda n: len(svc.distances_from(n)))
    return _build_session(best, difficulty, daily)


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


def _clue_payload(session: ContextoSession) -> dict:
    svc = get_service()
    node = svc.node(session.target)
    category = node.category if node is not None else ""
    label = CATEGORY_LABELS.get(category, category)
    return {
        "category": {"key": category, "label": label},
        "message": f"Categoria secretului: {label}.",
    }


def _state(game_id: str, session: ContextoSession) -> dict:
    body: dict = {
        "game_id": game_id,
        "attempts": session.attempts,
        "won": session.won,
        "gave_up": session.gave_up,
        "reachable_count": session.reachable,
        "difficulty": session.difficulty,
        "clues_used": session.clues_used,
        "clue_available": (
            not session.won
            and not session.gave_up
            and not session.clue_revealed
            and session.attempts >= MIN_CLUE_ATTEMPTS
        ),
        "guesses": _sorted_guesses(session),
    }
    if session.daily is not None:
        body["daily"] = session.daily
    if session.clue_revealed:
        body["clue"] = _clue_payload(session)
    if session.won or session.gave_up:
        svc = get_service()
        body["target"] = {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
        }
    if session.won:
        body["score"] = score_for(session.attempts, session.clues_used)
        body["share"] = share_line(session)
    return body


# --------------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(
    seed: int | None = None,
    difficulty: str = _DEFAULT_DIFFICULTY,
    daily: str | None = None,
) -> dict:
    if difficulty not in _DIFFICULTIES:
        difficulty = _DEFAULT_DIFFICULTY
    if daily is not None:
        seed = daily_seed(daily, GAME_KEY)
    session = _pick_target(seed, difficulty, daily)
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
            "clues_used": session.clues_used,
            "clue_available": (
                not session.clue_revealed
                and session.attempts >= MIN_CLUE_ATTEMPTS
            ),
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
        session.order.append(node_id)

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
        "clues_used": session.clues_used,
        "clue_available": (
            not session.won
            and not session.clue_revealed
            and session.attempts >= MIN_CLUE_ATTEMPTS
        ),
    }
    if session.clue_revealed:
        result["clue"] = _clue_payload(session)
    if session.won:
        result["target"] = {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
        }
        result["score"] = score_for(session.attempts, session.clues_used)
        result["share"] = share_line(session)
    return result


@router.post("/games/{game_id}/clue")
def clue(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    if session.won or session.gave_up:
        raise HTTPException(status_code=400, detail="Jocul s-a terminat")
    if session.attempts < MIN_CLUE_ATTEMPTS and not session.clue_revealed:
        need = MIN_CLUE_ATTEMPTS - session.attempts
        raise HTTPException(
            status_code=400,
            detail=f"Mai incearca {need} concepte inainte de indiciu.",
        )
    if not session.clue_revealed:
        session.clue_revealed = True
        session.clues_used += 1
    return {"ok": True, **_clue_payload(session), **_state(game_id, session)}


@router.post("/games/{game_id}/giveup")
def give_up(game_id: str) -> dict:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Joc inexistent")
    session.gave_up = True
    return _state(game_id, session)
