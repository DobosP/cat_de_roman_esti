"""Conexiuni — NYT Connections over the Romanian KG.

The board is 4x4: four distinct KG categories, four concepts each, shuffled into 16
tiles. The player selects exactly 4 tiles and submits; the server says whether all four
share a single (still-unsolved) category, surfacing an ``one_away`` flag when exactly 3
of the 4 belong to one category. Four mistakes are allowed; the game is won when all 4
groups are found and lost at 0 lives (then the full solution is revealed).

Server-authoritative: the per-category membership and the shuffled order live here, and
the solution is only echoed back once the game is won or lost. Sessions are in-memory.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .service import SessionStore, daily_seed, get_service

router = APIRouter(prefix="/api/wordgames/conexiuni", tags=["conexiuni"])

GAME_KEY = "conexiuni"

# The 8 known KG categories. We derive which are usable (>=4 nodes) at pick time so the
# game keeps working even if the fixture changes.
KNOWN_CATEGORIES = (
    "arta_cultura",
    "geografie",
    "istorie",
    "limba",
    "literatura",
    "personalitati",
    "societate",
    "stiinta",
)

GROUP_SIZE = 4
NUM_GROUPS = 4
MAX_LIVES = 4

DIFFICULTIES = ("usor", "normal", "greu")

# A handful of stable emoji to colour the share grid (one per solved/true group slot).
_GROUP_EMOJI = ("🟩", "🟦", "🟪", "🟧")


@dataclass
class ConexiuniSession:
    # category key -> the 4 node ids that make up that group
    groups: dict[str, list[str]]
    # the shuffled 16 ids on the board
    order: list[str]
    # categories solved so far, in the order they were found
    solved: list[str] = field(default_factory=list)
    lives: int = MAX_LIVES
    mistakes: int = 0
    won: bool = False
    lost: bool = False
    difficulty: str = "normal"
    daily: str | None = None
    # history of guesses (each a list of 4 ids) for the share grid
    history: list[list[str]] = field(default_factory=list)

    def category_of(self, node_id: str) -> str | None:
        for cat, ids in self.groups.items():
            if node_id in ids:
                return cat
        return None


store: SessionStore[ConexiuniSession] = SessionStore()


# --------------------------------------------------------------------- request bodies
class GuessBody(BaseModel):
    ids: list[str]


# --------------------------------------------------------------------- selection
def _usable_categories() -> list[str]:
    svc = get_service()
    return [c for c in KNOWN_CATEGORIES if len(svc.by_category(c)) >= GROUP_SIZE]


def _pick_board(rng: random.Random, difficulty: str) -> ConexiuniSession:
    """Pick 4 categories + 4 concepts each, deterministically from ``rng``.

    Difficulty shapes both which categories and which concepts are chosen:
      - usor:   the 4 highest-salience-average categories (most distinct themes) and the
                highest-salience (most familiar) concepts within each.
      - normal: random categories, random concepts.
      - greu:   subtler (lower-salience-average) categories and lower-salience concepts.
    """
    svc = get_service()
    usable = _usable_categories()
    if len(usable) < NUM_GROUPS:
        raise HTTPException(
            status_code=503,
            detail="Nu exista suficiente categorii pentru un joc.",
        )

    def avg_salience(cat: str) -> float:
        ids = svc.by_category(cat)
        if not ids:
            return 0.0
        return sum((svc.node(i).salience if svc.node(i) else 0.0) for i in ids) / len(ids)

    if difficulty == "usor":
        ranked = sorted(usable, key=lambda c: (-avg_salience(c), c))
        chosen_cats = ranked[:NUM_GROUPS]
    elif difficulty == "greu":
        ranked = sorted(usable, key=lambda c: (avg_salience(c), c))
        chosen_cats = ranked[:NUM_GROUPS]
    else:  # normal
        pool = list(usable)
        rng.shuffle(pool)
        chosen_cats = pool[:NUM_GROUPS]

    # Deterministic order of the four chosen categories.
    chosen_cats = sorted(chosen_cats)

    groups: dict[str, list[str]] = {}
    for cat in chosen_cats:
        ids = svc.by_category(cat)  # already sorted by id
        if difficulty == "usor":
            # most salient (most familiar) tiles first
            ids = sorted(ids, key=lambda i: (-(svc.node(i).salience if svc.node(i) else 0.0), i))
            picked = ids[:GROUP_SIZE]
        elif difficulty == "greu":
            # least salient (subtler) tiles first
            ids = sorted(ids, key=lambda i: ((svc.node(i).salience if svc.node(i) else 0.0), i))
            picked = ids[:GROUP_SIZE]
        else:  # normal — random four
            pool = list(ids)
            rng.shuffle(pool)
            picked = sorted(pool[:GROUP_SIZE])
        groups[cat] = picked

    order = [nid for ids in groups.values() for nid in ids]
    rng.shuffle(order)

    return ConexiuniSession(groups=groups, order=order, difficulty=difficulty)


# --------------------------------------------------------------------- serializers
def _tiles(session: ConexiuniSession) -> list[dict[str, str]]:
    svc = get_service()
    return [{"id": nid, "label": svc.label(nid)} for nid in session.order]


def _solved_groups(session: ConexiuniSession) -> list[dict]:
    svc = get_service()
    out: list[dict] = []
    for cat in session.solved:
        out.append(
            {
                "key": cat,
                "label": _category_label(cat),
                "tiles": [
                    {"id": nid, "label": svc.label(nid)} for nid in session.groups[cat]
                ],
            }
        )
    return out


def _category_label(cat: str) -> str:
    # Romanian-friendly display names mirroring the frontend theme tokens.
    labels = {
        "arta_cultura": "Arta & Cultura",
        "geografie": "Geografie",
        "istorie": "Istorie",
        "limba": "Limba",
        "literatura": "Literatura",
        "personalitati": "Personalitati",
        "societate": "Societate",
        "stiinta": "Stiinta",
    }
    return labels.get(cat, cat)


def _full_solution(session: ConexiuniSession) -> list[dict]:
    svc = get_service()
    out: list[dict] = []
    # stable order: solved first (in found order), then the rest alphabetically
    rest = [c for c in sorted(session.groups) if c not in session.solved]
    for cat in [*session.solved, *rest]:
        out.append(
            {
                "key": cat,
                "label": _category_label(cat),
                "tiles": [
                    {"id": nid, "label": svc.label(nid)} for nid in session.groups[cat]
                ],
            }
        )
    return out


def _score(session: ConexiuniSession) -> int:
    return max(0, 1000 - 250 * session.mistakes)


def _share(session: ConexiuniSession) -> str:
    """A Connections-style emoji grid of the guess history, one row per guess."""
    # Assign a stable emoji per category by alphabetical group index.
    cat_index = {cat: i for i, cat in enumerate(sorted(session.groups))}
    lines: list[str] = []
    for guess in session.history:
        row = ""
        for nid in guess:
            cat = session.category_of(nid)
            idx = cat_index.get(cat, 0) if cat is not None else 0
            row += _GROUP_EMOJI[idx % len(_GROUP_EMOJI)]
        lines.append(row)
    header = "cat_de_roman_esti · Conexiuni · "
    header += f"{session.mistakes} greseli"
    if session.daily:
        header += f" · {session.daily}"
    body = "\n".join(lines) if lines else "—"
    return f"{header}\n{body}"


def _state(game_id: str, session: ConexiuniSession) -> dict:
    body: dict = {
        "game_id": game_id,
        "tiles": _tiles(session),
        "solved": _solved_groups(session),
        "lives": session.lives,
        "mistakes": session.mistakes,
        "won": session.won,
        "lost": session.lost,
        "difficulty": session.difficulty,
    }
    if session.daily:
        body["daily"] = session.daily
    if session.won or session.lost:
        body["score"] = _score(session)
        body["share"] = _share(session)
        body["solution"] = _full_solution(session)
    return body


# --------------------------------------------------------------------- endpoints
@router.post("/games")
def create_game(
    seed: int | None = None,
    difficulty: str = "normal",
    daily: str | None = None,
) -> dict:
    if difficulty not in DIFFICULTIES:
        difficulty = "normal"
    if daily:
        rng = random.Random(daily_seed(daily, GAME_KEY))
    else:
        rng = random.Random(seed)
    session = _pick_board(rng, difficulty)
    session.daily = daily
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
    if session.won or session.lost:
        raise HTTPException(status_code=400, detail="Jocul s-a terminat")

    ids = body.ids or []
    # must be exactly 4 distinct ids
    if len(ids) != GROUP_SIZE or len(set(ids)) != GROUP_SIZE:
        raise HTTPException(status_code=400, detail="Alege exact 4 concepte distincte")

    solved_ids = {nid for cat in session.solved for nid in session.groups[cat]}
    board_ids = set(session.order)
    for nid in ids:
        if nid not in board_ids:
            raise HTTPException(status_code=400, detail="Concept care nu e pe tabla")
        if nid in solved_ids:
            raise HTTPException(status_code=400, detail="Concept deja rezolvat")

    session.history.append(list(ids))

    # which (unsolved) category do all four share, if any?
    cats = [session.category_of(nid) for nid in ids]
    shared = cats[0] if cats and all(c == cats[0] for c in cats) else None

    if shared is not None and shared not in session.solved:
        session.solved.append(shared)
        svc = get_service()
        session.won = len(session.solved) == NUM_GROUPS
        return {
            "ok": True,
            "correct": True,
            "category": {"key": shared, "label": _category_label(shared)},
            "tiles": [{"id": nid, "label": svc.label(nid)} for nid in session.groups[shared]],
            "solved": _solved_groups(session),
            "lives": session.lives,
            "won": session.won,
            **({"score": _score(session), "share": _share(session)} if session.won else {}),
            **({"solution": _full_solution(session)} if session.won else {}),
        }

    # wrong guess
    session.mistakes += 1
    session.lives -= 1
    # one_away: some category has exactly 3 of the 4 selected
    counts: dict[str, int] = {}
    for c in cats:
        if c is not None:
            counts[c] = counts.get(c, 0) + 1
    one_away = any(v == GROUP_SIZE - 1 for v in counts.values())
    session.lost = session.lives <= 0

    result: dict = {
        "ok": True,
        "correct": False,
        "one_away": one_away,
        "lives": session.lives,
        "mistakes": session.mistakes,
        "lost": session.lost,
    }
    if session.lost:
        result["solution"] = _full_solution(session)
        result["score"] = _score(session)
        result["share"] = _share(session)
    return result
