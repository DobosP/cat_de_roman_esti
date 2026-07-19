"""Intrusul — a bounded 3+1 game over the private V38 derived catalog.

Four familiar concepts are visible.  Three belong to one reviewed Conexiuni group;
the player taps the intruder.  The answer, trio membership, source provenance, and all
ranking inputs remain server-side until the game ends.  A wrong tap is useful evidence,
not a trap: it stays free on repeat, and one short authored-group hint unlocks after the
first mistake.
"""

from __future__ import annotations

import random
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
from .derived_catalog import DerivedBoard, DerivedCatalog, get_derived_catalog
from .service import (
    SessionCapacityError,
    SessionStore,
    daily_seed,
    get_service,
)

GAME_KEY = "intrusul"
MAX_MISTAKES = 3
SOURCE_RING_LIMIT = 4


class GuessBody(BaseModel):
    id: str


@dataclass
class IntrusulSession:
    members: tuple[str, str, str] = field(repr=False)
    intruder: str = field(repr=False)
    group_label: str = field(repr=False)
    order: list[str] = field(repr=False)
    difficulty: str
    source_id: str = field(repr=False)
    catalog_id: str = field(repr=False)
    source_ring: tuple[str, ...] = field(repr=False)
    daily: str | None = None
    # Echo only a player-requested category; a global/daily board keeps provenance private.
    category: str | None = None
    wrong_ids: list[str] = field(default_factory=list)
    attempts: int = 0
    hint_used: bool = False
    won: bool = False
    lost: bool = False

    @property
    def finished(self) -> bool:
        return self.won or self.lost

    @property
    def score(self) -> int:
        if not self.won:
            return 0
        return max(
            100,
            1_000 - 200 * len(self.wrong_ids) - 150 * int(self.hint_used),
        )


store: SessionStore[IntrusulSession] = SessionStore()


def _atomic_session(method):
    """Pin one session and serialize every compound read/mutation against it."""

    @wraps(method)
    def wrapped(self, request, game_id: str):
        with store.transaction(game_id) as session:
            if session is None:
                raise http_error(404, "Joc inexistent")
            return method(self, request, game_id, session)

    return wrapped


def _concept(node_id: str) -> dict[str, str]:
    return {"id": node_id, "label": get_service().label(node_id)}


def _clue(session: IntrusulSession) -> dict[str, str]:
    return {
        "label": session.group_label,
        "message": f"Trei cuvinte țin de: {session.group_label}.",
    }


def _share(session: IntrusulSession) -> str:
    header = "cat_de_roman_esti · Intrusul"
    if session.category:
        header += f" · {category_label(session.category)}"
    result = "🟩" if session.won else "🟥"
    detail = f"{session.attempts} încercări"
    if session.hint_used:
        detail += " · indiciu"
    lines = [header, f"{result} {detail}"]
    if session.daily:
        lines.append(session.daily)
    return "\n".join(lines)


def _state(game_id: str, session: IntrusulSession) -> dict[str, object]:
    body: dict[str, object] = {
        "game_id": game_id,
        "tiles": [_concept(node_id) for node_id in session.order],
        # These are only the player's own earned wrong taps, never the complete trio.
        "wrong_ids": list(session.wrong_ids),
        "attempts": session.attempts,
        "mistakes": len(session.wrong_ids),
        "remaining_mistakes": max(0, MAX_MISTAKES - len(session.wrong_ids)),
        "won": session.won,
        "lost": session.lost,
        "difficulty": session.difficulty,
        "hints_used": int(session.hint_used),
        "hint_available": (
            not session.finished and bool(session.wrong_ids) and not session.hint_used
        ),
    }
    if session.daily:
        body["daily"] = session.daily
    if session.category:
        body["board_category"] = session.category
    if session.hint_used:
        body["clue"] = _clue(session)
    if session.finished:
        body["score"] = session.score
        body["share"] = _share(session)
        body["solution"] = {
            "intruder": _concept(session.intruder),
            "group": {
                "label": session.group_label,
                "tiles": [_concept(node_id) for node_id in session.members],
            },
        }
    return body


def _previous_ring(previous_game_id: str | None) -> tuple[str, ...]:
    if not previous_game_id:
        return ()
    with store.transaction(previous_game_id) as previous:
        if previous is None:
            return ()
        return tuple(previous.source_ring[-SOURCE_RING_LIMIT:])


def _pick_non_daily(
    catalog: DerivedCatalog,
    rng: random.Random,
    *,
    category: str | None,
    starter: bool,
    excluded_sources: set[str],
) -> DerivedBoard | None:
    """Prefer starter-safe/new sources, then widen only inside the strict catalog."""

    exclusion_passes = (excluded_sources, set()) if excluded_sources else (set(),)
    for exclusions in exclusion_passes:
        if starter:
            selected = catalog.pick_seeded(
                GAME_KEY,
                rng,
                category=category,
                exclude_source_ids=exclusions,
                starter=True,
            )
            if selected is not None:
                return selected
        selected = catalog.pick_seeded(
            GAME_KEY,
            rng,
            category=category,
            exclude_source_ids=exclusions,
        )
        if selected is not None:
            return selected
    return None


def _build_session(
    board: DerivedBoard,
    rng: random.Random,
    *,
    daily: str | None,
    requested_category: str | None,
    previous_ring: tuple[str, ...],
) -> IntrusulSession:
    members = tuple(str(node_id) for node_id in board.payload["members"])
    if len(members) != 3:
        raise http_error(503, "Tabla aleasă nu mai este validă.")
    intruder = str(board.payload["intruder"])
    order = [*members, intruder]
    rng.shuffle(order)
    # Keep the last four DISTINCT sources.  A forced repeat moves that source to the
    # newest slot without shrinking the fatigue memory.
    earlier_sources = [source for source in previous_ring if source != board._source_id]
    source_ring = (*earlier_sources, board._source_id)[-SOURCE_RING_LIMIT:]
    return IntrusulSession(
        members=(members[0], members[1], members[2]),
        intruder=intruder,
        group_label=str(board.payload["group_label"]),
        order=order,
        difficulty=board.difficulty,
        source_id=board._source_id,
        catalog_id=board._catalog_id,
        source_ring=source_ring,
        daily=daily,
        category=requested_category,
    )


class CreateGameView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="intrusul_create_game", tags=["intrusul"])
    def post(self, request):
        seed = query_int(request, "seed")
        daily = query_str(request, "daily")
        category = query_str(request, "category")
        starter_value = query_int(request, "starter")
        previous_game_id = query_str(request, "previous_game_id")
        if category is not None and not is_known(category):
            raise http_error(400, "Categorie necunoscută.")
        if starter_value not in (None, 0, 1):
            raise http_error(400, "starter trebuie să fie 0 sau 1.")

        catalog = get_derived_catalog()
        if daily:
            # One shared daily: starter, previous sessions, and account history cannot
            # fork the result.  The daily seed controls only the stable tile shuffle.
            board = catalog.pick_daily(GAME_KEY, daily, category=category)
            rng = random.Random(daily_seed(daily, GAME_KEY))
            previous_ring: tuple[str, ...] = ()
        else:
            rng = random.Random(seed)
            previous_ring = _previous_ring(previous_game_id)
            excluded_sources = set(previous_ring)
            excluded_sources.update(excluded_pack_ids(request, GAME_KEY))
            board = _pick_non_daily(
                catalog,
                rng,
                category=category,
                starter=starter_value == 1,
                excluded_sources=excluded_sources,
            )
        if board is None:
            raise http_error(503, "Nu există încă jocuri sigure pentru această categorie.")

        session = _build_session(
            board,
            rng,
            daily=daily,
            requested_category=category,
            previous_ring=previous_ring,
        )
        try:
            game_id = store.create(session)
        except SessionCapacityError as exc:
            raise http_error(503, "Prea multe jocuri active. Încearcă din nou.") from exc
        return Response(_state(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="intrusul_get_game", tags=["intrusul"])
    @_atomic_session
    def get(self, request, game_id: str, session: IntrusulSession):
        return Response(_state(game_id, session))


class GuessView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="intrusul_guess", tags=["intrusul"])
    @_atomic_session
    def post(self, request, game_id: str, session: IntrusulSession):
        body = parse_body(request, GuessBody)
        if session.finished:
            raise http_error(400, "Jocul s-a terminat")
        selected = body.id.strip()
        if selected not in session.order:
            raise http_error(400, "Concept care nu este pe tablă")
        if selected in session.wrong_ids:
            return Response(
                {
                    "ok": True,
                    "correct": False,
                    "already_tried": True,
                    "message": "Deja încercat · fără cost.",
                    **_state(game_id, session),
                }
            )

        session.attempts += 1
        correct = selected == session.intruder
        if correct:
            session.won = True
            message = "Exact — acesta este intrusul!"
        else:
            session.wrong_ids.append(selected)
            session.lost = len(session.wrong_ids) >= MAX_MISTAKES
            message = (
                "Gata — îți arăt intrusul și legătura dintre celelalte trei."
                if session.lost
                else "Face parte din grup. Mai încearcă."
            )
        if session.finished:
            record_finished(request, GAME_KEY, session.source_id)
        return Response(
            {
                "ok": True,
                "correct": correct,
                "already_tried": False,
                "message": message,
                **_state(game_id, session),
            }
        )


class HintView(ContractAPIView):
    @extend_schema(operation_id="intrusul_hint", tags=["intrusul"])
    @_atomic_session
    def post(self, request, game_id: str, session: IntrusulSession):
        if session.finished:
            raise http_error(400, "Jocul s-a terminat")
        if session.hint_used:
            raise http_error(400, "Indiciul a fost deja folosit")
        if not session.wrong_ids:
            raise http_error(400, "Indiciul apare după prima încercare.")
        session.hint_used = True
        return Response({"ok": True, **_state(game_id, session)})


_BASE = "api/wordgames/intrusul"
urlpatterns = [
    path(f"{_BASE}/games", CreateGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>", GetGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/guess", GuessView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/hint", HintView.as_view()),
]
