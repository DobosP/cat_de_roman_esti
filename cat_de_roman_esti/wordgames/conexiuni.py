"""Conexiuni — NYT Connections over the Romanian KG.

The board is 4x4: four distinct KG categories, four concepts each, shuffled into 16
tiles. The player selects exactly 4 tiles and submits; the server says whether all four
share a single (still-unsolved) category, surfacing an ``one_away`` flag when exactly 3
of the 4 belong to one category. Four mistakes are allowed; the game is won when all 4
groups are found and lost at 0 lives (then the full solution is revealed).

Server-authoritative: the per-category membership and the shuffled order live here. Public
responses are serialized through a terminal-state reveal gate so category keys, full labels,
and membership are only echoed back once the game is won or lost. Sessions are in-memory.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import combinations

from django.urls import path
from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.response import Response

from ..web.http import ContractAPIView, http_error, parse_body, query_int, query_str
from .service import SessionStore, WordGameService, daily_seed, get_service

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
BOARD_PICK_RETRIES = 16
MIN_CLUE_MISTAKES = 2
MAX_CLUES = 1
CLUE_SCORE_PENALTY = 100

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
    # Redacted label-pattern clues already revealed. They never include category keys,
    # exact labels, tile ids, or membership.
    clues: list[dict[str, str]] = field(default_factory=list)
    clues_used: int = 0
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


def _salience(svc: WordGameService, node_id: str) -> float:
    node = svc.node(node_id)
    return node.salience if node else 0.0


def _neighbors(svc: WordGameService, node_id: str) -> set[str]:
    """Non-distractor neighbour set via the public service API (no internals)."""
    return set(svc.neighbor_ids(node_id))


@lru_cache(maxsize=1)
def _category_entanglement() -> dict[tuple[str, str], float]:
    """Pairwise theme-overlap between whole categories on the non-distractor KG.

    For each pair we count cross-category edges and normalise by the geometric mean of
    the category sizes. High = the two categories are semantically entangled (their
    concepts plausibly belong together), so a board mixing them yields fun red-herrings;
    low = the two themes are clearly distinct (easy to tell apart). Computed once.
    """
    svc = get_service()
    usable = _usable_categories()
    members = {c: set(svc.by_category(c)) for c in usable}
    out: dict[tuple[str, str], float] = {}
    for a, b in combinations(usable, 2):
        cross = sum(len(_neighbors(svc, x) & members[b]) for x in members[a])
        norm = (len(members[a]) * len(members[b])) ** 0.5 or 1.0
        out[(a, b)] = cross / norm
    return out


def _set_entanglement(cats: tuple[str, ...]) -> float:
    """Total pairwise entanglement of a 4-category set (higher = trickier board)."""
    ent = _category_entanglement()
    return sum(ent.get(tuple(sorted((a, b))), 0.0) for a, b in combinations(cats, 2))


@lru_cache(maxsize=1)
def _ranked_category_sets() -> list[tuple[str, ...]]:
    """All usable 4-category combinations, ascending by entanglement (clean -> tricky)."""
    usable = _usable_categories()
    return sorted(
        (tuple(sorted(c)) for c in combinations(usable, NUM_GROUPS)),
        key=lambda s: (_set_entanglement(s), s),
    )


def _choose_categories(rng: random.Random, difficulty: str) -> tuple[str, ...]:
    """Pick a 4-category set sized to the difficulty, with seed-driven variety.

    'usor' samples from the cleanest (least entangled) third of all sets so the four
    themes are unmistakable; 'greu' samples from the most entangled third for plausible
    red-herrings; 'normal' samples uniformly. Sampling (not a fixed top-N) means the
    board actually varies with the seed at every difficulty.
    """
    ranked = _ranked_category_sets()
    n = len(ranked)
    if n == 0:
        raise http_error(
            503,
            "Nu exista suficiente categorii pentru un joc.",
        )
    third = max(1, n // 3)
    if difficulty == "usor":
        pool = ranked[:third]
    elif difficulty == "greu":
        pool = ranked[-third:]
    else:  # normal
        pool = ranked
    return rng.choice(pool)


def _tile_ambiguity(
    svc: WordGameService, node_id: str, own: set[str], foreign: set[str]
) -> int:
    """How much a tile pulls toward a *foreign* on-board group vs. its own.

    Returns the count of foreign-on-board neighbours minus own-on-board neighbours.
    A positive value means the tile links more strongly to another group than its own —
    a genuinely unfair tile that we avoid on every difficulty.
    """
    nbrs = _neighbors(svc, node_id)
    own_n = len(nbrs & (own - {node_id}))
    foreign_n = len(nbrs & foreign)
    return foreign_n - own_n


def _pick_tiles_for_category(
    svc: WordGameService,
    rng: random.Random,
    cat: str,
    foreign: set[str],
    difficulty: str,
) -> list[str]:
    """Pick GROUP_SIZE tiles for one category, biased by difficulty and de-confused.

    We never let a tile that links more to a *foreign* category than its own onto the
    board (that would be unfair). Among the fair candidates: 'usor' prefers the most
    salient/recognisable concepts, 'greu' the subtler ones, 'normal' samples randomly.
    Falls back to the full pool if too few fair tiles exist (keeps generation total).
    """
    ids = svc.by_category(cat)
    own = set(ids)
    fair = [i for i in ids if _tile_ambiguity(svc, i, own, foreign) <= 0]
    pool = fair if len(fair) >= GROUP_SIZE else list(ids)

    if difficulty == "usor":
        ordered = sorted(pool, key=lambda i: (-_salience(svc, i), i))
        return sorted(ordered[:GROUP_SIZE])
    if difficulty == "greu":
        ordered = sorted(pool, key=lambda i: (_salience(svc, i), i))
        return sorted(ordered[:GROUP_SIZE])
    shuffled = list(pool)
    rng.shuffle(shuffled)
    return sorted(shuffled[:GROUP_SIZE])


def _build_board(rng: random.Random, difficulty: str) -> ConexiuniSession:
    chosen_cats = sorted(_choose_categories(rng, difficulty))
    svc = get_service()

    groups: dict[str, list[str]] = {}
    category_members = {cat: set(svc.by_category(cat)) for cat in chosen_cats}
    all_chosen_members = set().union(*category_members.values())
    # Iterate in a difficulty-independent order. Each category sees the full member
    # pool for the other chosen categories, so early categories do not unknowingly pick
    # bridge tiles that validation will later reject once the whole board is assembled.
    for cat in chosen_cats:
        foreign = all_chosen_members - category_members[cat]
        picked = _pick_tiles_for_category(svc, rng, cat, foreign, difficulty)
        groups[cat] = picked

    order = [nid for ids in groups.values() for nid in ids]
    rng.shuffle(order)
    return ConexiuniSession(groups=groups, order=order, difficulty=difficulty)


def _board_quality(session: ConexiuniSession) -> tuple[bool, int]:
    """Validate a generated board. Returns (ok, residual_ambiguity).

    Rejects degenerate boards: wrong tile count, duplicate tiles, or any tile that —
    given the *actual* four groups on this board — links more to a foreign group than
    its own (an unwinnable/unfair tile). residual_ambiguity counts borderline (equal)
    tiles, used only to pick the least-confusing board among retries.
    """
    all_ids = [nid for ids in session.groups.values() for nid in ids]
    if len(all_ids) != GROUP_SIZE * NUM_GROUPS:
        return False, 1_000_000
    if len(set(all_ids)) != len(all_ids):
        return False, 1_000_000

    svc = get_service()
    member_cat = {nid: cat for cat, ids in session.groups.items() for nid in ids}
    residual = 0
    for nid, own_cat in member_cat.items():
        nbrs = _neighbors(svc, nid)
        own_n = sum(1 for x in nbrs if member_cat.get(x) == own_cat and x != nid)
        worst_foreign = 0
        for cat in session.groups:
            if cat == own_cat:
                continue
            fn = sum(1 for x in nbrs if member_cat.get(x) == cat)
            worst_foreign = max(worst_foreign, fn)
        if worst_foreign > own_n:
            return False, 1_000_000  # unfair tile -> reject outright
        if worst_foreign == own_n and own_n > 0:
            residual += 1
    return True, residual


def _pick_board(rng: random.Random, difficulty: str) -> ConexiuniSession:
    """Pick 4 categories + 4 concepts each, deterministically from ``rng``.

    Difficulty shapes the board:
      - usor:   the cleanest (least entangled) category sets + most recognisable tiles.
      - normal: any category set, random tiles.
      - greu:   the most entangled category sets + subtler tiles (plausible red-herrings)
                that are still individually reasoned-about (never strictly unfair).

    Generation is validated and retried: we draw several candidate boards from ``rng``
    and keep the first strictly-fair one (lowest residual ambiguity). If validation
    cannot produce a fair board, fail closed instead of returning a degenerate or
    unwinnable board. Deterministic for a fixed seed/difficulty.
    """
    best: ConexiuniSession | None = None
    best_residual = 1_000_000
    for _ in range(BOARD_PICK_RETRIES):
        candidate = _build_board(rng, difficulty)
        ok, residual = _board_quality(candidate)
        if ok and residual == 0:
            return candidate
        if ok and residual < best_residual:
            best, best_residual = candidate, residual
    if best is not None:
        return best
    raise http_error(
        503,
        "Nu am putut genera o tabla valida; reincearca.",
    )


# --------------------------------------------------------------------- serializers
def _tiles(session: ConexiuniSession, *, include_solved: bool = False) -> list[dict[str, str]]:
    svc = get_service()
    solved_ids = {
        nid
        for cat in session.solved
        for nid in session.groups[cat]
    }
    return [
        {"id": nid, "label": svc.label(nid)}
        for nid in session.order
        if include_solved or nid not in solved_ids
    ]


def _solved_groups(session: ConexiuniSession, *, reveal: bool) -> list[dict]:
    if not reveal:
        raise RuntimeError("refusing to serialize Conexiuni solved groups before reveal")
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


def _full_solution(session: ConexiuniSession, *, reveal: bool) -> list[dict]:
    if not reveal:
        raise RuntimeError("refusing to serialize Conexiuni solution before reveal")
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
    return max(0, 1000 - 250 * session.mistakes - CLUE_SCORE_PENALTY * session.clues_used)


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
    if session.clues_used:
        header += f" · indiciu x{session.clues_used}"
    if session.daily:
        header += f" · {session.daily}"
    body = "\n".join(lines) if lines else "—"
    return f"{header}\n{body}"


def _label_pattern(label: str) -> str:
    """Redact a category label to first letters + lengths, preserving separators."""
    out: list[str] = []
    at_word_start = True
    for ch in label:
        if ch.isalpha():
            if at_word_start:
                out.append(ch.upper())
                at_word_start = False
            else:
                out.append("_")
        else:
            out.append(ch)
            at_word_start = ch.isspace()
    return "".join(out)


def _clue_available(session: ConexiuniSession) -> bool:
    return (
        not session.won
        and not session.lost
        and session.clues_used < MAX_CLUES
        and session.mistakes >= MIN_CLUE_MISTAKES
        and len(session.solved) < len(session.groups)
    )


def _next_clue(session: ConexiuniSession) -> dict[str, str]:
    """Pick a deterministic redacted label-pattern clue for one unsolved group."""
    unsolved = [cat for cat in sorted(session.groups) if cat not in session.solved]
    cat = unsolved[0]
    pattern = _label_pattern(_category_label(cat))
    return {
        "pattern": pattern,
        "message": f"Un grup ramas are eticheta: {pattern}.",
    }


def _state(game_id: str, session: ConexiuniSession) -> dict:
    reveal = session.won or session.lost
    body: dict = {
        "game_id": game_id,
        "tiles": _tiles(session, include_solved=reveal),
        "solved": _solved_groups(session, reveal=True) if reveal else [],
        "solved_count": len(session.solved),
        "remaining_groups": len(session.groups) - len(session.solved),
        "lives": session.lives,
        "mistakes": session.mistakes,
        "won": session.won,
        "lost": session.lost,
        "difficulty": session.difficulty,
        "clues_used": session.clues_used,
        "clue_available": _clue_available(session),
        "clues": list(session.clues),
    }
    if session.daily:
        body["daily"] = session.daily
    if reveal:
        body["score"] = _score(session)
        body["share"] = _share(session)
        body["solution"] = _full_solution(session, reveal=True)
    return body


# --------------------------------------------------------------------- endpoints
class CreateGameView(ContractAPIView):
    @extend_schema(operation_id="conexiuni_create_game", tags=["conexiuni"])
    def post(self, request):
        seed = query_int(request, "seed")
        difficulty = query_str(request, "difficulty", "normal")
        daily = query_str(request, "daily")
        if difficulty not in DIFFICULTIES:
            difficulty = "normal"
        if daily:
            rng = random.Random(daily_seed(daily, GAME_KEY))
        else:
            rng = random.Random(seed)
        session = _pick_board(rng, difficulty)
        session.daily = daily
        game_id = store.create(session)
        return Response(_state(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="conexiuni_get_game", tags=["conexiuni"])
    def get(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        return Response(_state(game_id, session))


class GuessView(ContractAPIView):
    @extend_schema(operation_id="conexiuni_guess", tags=["conexiuni"])
    def post(self, request, game_id: str):
        body = parse_body(request, GuessBody)
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        if session.won or session.lost:
            raise http_error(400, "Jocul s-a terminat")

        ids = body.ids or []
        # must be exactly 4 distinct ids
        if len(ids) != GROUP_SIZE or len(set(ids)) != GROUP_SIZE:
            raise http_error(400, "Alege exact 4 concepte distincte")

        solved_ids = {nid for cat in session.solved for nid in session.groups[cat]}
        board_ids = set(session.order)
        for nid in ids:
            if nid not in board_ids:
                raise http_error(400, "Concept care nu e pe tabla")
            if nid in solved_ids:
                raise http_error(400, "Concept deja rezolvat")

        session.history.append(list(ids))

        # which (unsolved) category do all four share, if any?
        cats = [session.category_of(nid) for nid in ids]
        shared = cats[0] if cats and all(c == cats[0] for c in cats) else None

        if shared is not None and shared not in session.solved:
            session.solved.append(shared)
            session.won = len(session.solved) == NUM_GROUPS
            state = _state(game_id, session)
            result = {
                "ok": True,
                "correct": True,
                **state,
            }
            if session.won:
                result["category"] = {"key": shared, "label": _category_label(shared)}
            return Response(result)

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
            **_state(game_id, session),
        }
        return Response(result)


class ClueView(ContractAPIView):
    @extend_schema(operation_id="conexiuni_clue", tags=["conexiuni"])
    def post(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        if session.won or session.lost:
            raise http_error(400, "Jocul s-a terminat")
        if session.clues_used >= MAX_CLUES:
            raise http_error(400, "Indiciul a fost deja folosit")
        if session.mistakes < MIN_CLUE_MISTAKES:
            need = MIN_CLUE_MISTAKES - session.mistakes
            raise http_error(
                400,
                f"Mai greseste {need} incercari inainte de indiciu.",
            )

        clue_payload = _next_clue(session)
        session.clues.append(clue_payload)
        session.clues_used += 1
        return Response({"ok": True, "clue": clue_payload, **_state(game_id, session)})


_BASE = "api/wordgames/conexiuni"
urlpatterns = [
    path(f"{_BASE}/games", CreateGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>", GetGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/guess", GuessView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/clue", ClueView.as_view()),
]
