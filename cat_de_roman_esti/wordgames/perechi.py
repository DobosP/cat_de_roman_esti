"""Perechi — match four hidden pairs derived from reviewed Conexiuni boards.

The server owns the four-pair mapping, source provenance, ranking, and recent-source
ring.  Public state exposes eight shuffled tiles and only labels for pairs the player
has solved (plus the one explicitly requested hint).  There is no mined fallback.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
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
from .categories import is_known
from .derived_catalog import DerivedBoard, get_derived_catalog
from .service import SessionCapacityError, SessionStore, daily_seed, get_service

GAME_KEY = "perechi"
PAIR_COUNT = 4
BOARD_SIZE = 8
MAX_MISTAKES = 6
MIN_HINT_MISTAKES = 2
MAX_HINTS = 1
SOURCE_RING_CAP = 4


@dataclass(frozen=True)
class Pair:
    members: tuple[str, str] = field(repr=False)
    label: str = field(repr=False)


@dataclass
class PerechiSession:
    pairs: tuple[Pair, Pair, Pair, Pair] = field(repr=False)
    order: list[str] = field(repr=False)
    solved: list[int] = field(default_factory=list, repr=False)
    wrong_history: list[tuple[str, str]] = field(default_factory=list, repr=False)
    mistakes: int = 0
    hinted_pair: int | None = field(default=None, repr=False)
    hints_used: int = 0
    won: bool = False
    lost: bool = False
    daily: str | None = None
    category: str | None = None
    # Every field below stays inside the server session.
    source_id: str = field(default="", repr=False)
    catalog_id: str = field(default="", repr=False)
    source_ring: tuple[str, ...] = field(default=(), repr=False)

    def pair_index(self, selected: frozenset[str]) -> int | None:
        for index, pair in enumerate(self.pairs):
            if frozenset(pair.members) == selected:
                return index
        return None


store: SessionStore[PerechiSession] = SessionStore()


def _atomic_session(method):
    @wraps(method)
    def wrapped(self, request, game_id: str):
        with store.transaction(game_id) as session:
            if session is None:
                raise http_error(404, "Joc inexistent")
            return method(self, request, game_id, session)

    return wrapped


class MatchBody(BaseModel):
    ids: list[str]


def _pair_payload(pair: Pair) -> dict:
    svc = get_service()
    return {
        "tiles": [
            {"id": node_id, "label": svc.label(node_id)} for node_id in pair.members
        ],
        "label": pair.label,
    }


def _score(session: PerechiSession) -> int:
    if session.lost:
        return 0
    return max(100, 1000 - 100 * session.mistakes - 150 * session.hints_used)


def _share(session: PerechiSession) -> str:
    header = f"cat_de_roman_esti · Perechi · {session.mistakes} greseli"
    if session.hints_used:
        header += " · indiciu"
    if session.daily:
        header += f" · {session.daily}"
    progress = "🟩" * len(session.solved) + "⬜" * (PAIR_COUNT - len(session.solved))
    return f"{header}\n{progress}"


def _hint_available(session: PerechiSession) -> bool:
    return (
        not session.won
        and not session.lost
        and session.hints_used < MAX_HINTS
        and session.mistakes >= MIN_HINT_MISTAKES
        and len(session.solved) < PAIR_COUNT
    )


def _state(game_id: str, session: PerechiSession) -> dict:
    svc = get_service()
    solved = set(session.solved)
    terminal = session.won or session.lost
    body: dict = {
        "game_id": game_id,
        "tiles": [
            {
                "id": node_id,
                "label": svc.label(node_id),
                "solved": any(
                    index in solved and node_id in pair.members
                    for index, pair in enumerate(session.pairs)
                ),
            }
            for node_id in session.order
        ],
        "solved_pairs": [_pair_payload(session.pairs[index]) for index in session.solved],
        "solved_count": len(session.solved),
        "remaining_pairs": PAIR_COUNT - len(session.solved),
        "mistakes": session.mistakes,
        "remaining_mistakes": MAX_MISTAKES - session.mistakes,
        "actions": len(session.solved) + len(session.wrong_history),
        "hint_available": _hint_available(session),
        "hints_used": session.hints_used,
        "won": session.won,
        "lost": session.lost,
    }
    if session.hinted_pair is not None:
        body["hint"] = _pair_payload(session.pairs[session.hinted_pair])
    if session.daily is not None:
        body["daily"] = session.daily
    if session.category is not None:
        body["board_category"] = session.category
    if terminal:
        body["score"] = _score(session)
        body["share"] = _share(session)
        body["solution"] = [_pair_payload(pair) for pair in session.pairs]
    return body


def _previous_source_ring(previous_game_id: str | None) -> tuple[str, ...]:
    if not previous_game_id:
        return ()
    with store.transaction(previous_game_id) as previous:
        if previous is None:
            return ()
        return tuple(previous.source_ring[-SOURCE_RING_CAP:])


def _append_source(ring: tuple[str, ...], source_id: str) -> tuple[str, ...]:
    # Keep the most recent occurrence only, so a forced repeat does not waste ring space.
    recent = [item for item in ring if item != source_id]
    return tuple([*recent, source_id][-SOURCE_RING_CAP:])


def _pick_non_daily(
    request,
    rng: random.Random,
    *,
    category: str | None,
    starter: bool,
    previous_game_id: str | None,
) -> tuple[DerivedBoard | None, tuple[str, ...]]:
    catalog = get_derived_catalog()
    previous_ring = _previous_source_ring(previous_game_id)
    exclusions = set(previous_ring) | excluded_pack_ids(request, GAME_KEY)
    profiles = (True, False) if starter else (False,)

    for starter_profile in profiles:
        board = catalog.pick_seeded(
            GAME_KEY,
            rng,
            category=category,
            exclude_source_ids=exclusions,
            starter=starter_profile,
        )
        if board is not None:
            return board, previous_ring

    # A finite shelf must remain playable after a player exhausts its source IDs. Retry
    # the same strict catalog without exclusions, retaining category and profile order.
    if exclusions:
        for starter_profile in profiles:
            board = catalog.pick_seeded(
                GAME_KEY,
                rng,
                category=category,
                starter=starter_profile,
            )
            if board is not None:
                return board, previous_ring
    return None, previous_ring


def _session_from_board(
    board: DerivedBoard,
    rng: random.Random,
    *,
    daily: str | None,
    requested_category: str | None,
    previous_ring: tuple[str, ...],
) -> PerechiSession:
    raw_pairs = board.payload.get("pairs")
    if not isinstance(raw_pairs, list | tuple) or len(raw_pairs) != PAIR_COUNT:
        raise http_error(503, "Catalogul Perechi este invalid.")
    parsed_pairs: list[Pair] = []
    for raw in raw_pairs:
        if not isinstance(raw, Mapping) or set(raw) != {"members", "group_label"}:
            raise http_error(503, "Catalogul Perechi este invalid.")
        members = raw["members"]
        if not isinstance(members, list | tuple) or len(members) != 2:
            raise http_error(503, "Catalogul Perechi este invalid.")
        parsed_pairs.append(
            Pair(
                members=(str(members[0]), str(members[1])),
                label=str(raw["group_label"]),
            )
        )
    pairs = tuple(parsed_pairs)
    visible = [node_id for pair in pairs for node_id in pair.members]
    if len(visible) != BOARD_SIZE or len(set(visible)) != BOARD_SIZE:
        raise http_error(503, "Catalogul Perechi este invalid.")
    order = list(visible)
    rng.shuffle(order)
    return PerechiSession(
        pairs=pairs,  # type: ignore[arg-type] - exact length is enforced above
        order=order,
        daily=daily,
        category=requested_category,
        source_id=board._source_id,
        catalog_id=board._catalog_id,
        source_ring=_append_source(previous_ring, board._source_id),
    )


class CreateGameView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="perechi_create_game", tags=["perechi"])
    def post(self, request):
        seed = query_int(request, "seed")
        daily = query_str(request, "daily")
        category = query_str(request, "category")
        starter_value = query_int(request, "starter")
        previous_game_id = query_str(request, "previous_game_id")
        if category is not None and not is_known(category):
            raise http_error(400, "Categorie necunoscuta.")
        if starter_value not in (None, 0, 1):
            raise http_error(400, "starter trebuie sa fie 0 sau 1.")
        starter = starter_value == 1

        if daily:
            # A shared daily ignores personal history, starter hints, and account state.
            rng = random.Random(daily_seed(daily, GAME_KEY))
            board = get_derived_catalog().pick_daily(GAME_KEY, daily, category=category)
            previous_ring: tuple[str, ...] = ()
        else:
            rng = random.Random(seed)
            board, previous_ring = _pick_non_daily(
                request,
                rng,
                category=category,
                starter=starter,
                previous_game_id=previous_game_id,
            )
        if board is None:
            raise http_error(503, "Nu exista jocuri Perechi pentru filtrul ales.")
        session = _session_from_board(
            board,
            rng,
            daily=daily if daily else None,
            requested_category=category,
            previous_ring=previous_ring,
        )
        try:
            game_id = store.create(session)
        except SessionCapacityError as exc:
            raise http_error(503, "Prea multe jocuri active. Încearcă din nou.") from exc
        return Response(_state(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="perechi_get_game", tags=["perechi"])
    @_atomic_session
    def get(self, request, game_id: str, session: PerechiSession):
        return Response(_state(game_id, session))


class MatchView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="perechi_match", tags=["perechi"])
    @_atomic_session
    def post(self, request, game_id: str, session: PerechiSession):
        if session.won or session.lost:
            raise http_error(400, "Jocul s-a terminat")
        body = parse_body(request, MatchBody)
        ids = body.ids or []
        if len(ids) != 2 or len(set(ids)) != 2:
            raise http_error(400, "Alege exact doua concepte distincte")
        board_ids = set(session.order)
        if any(node_id not in board_ids for node_id in ids):
            raise http_error(400, "Concept care nu e pe tabla")
        solved_ids = {
            node_id for index in session.solved for node_id in session.pairs[index].members
        }
        if any(node_id in solved_ids for node_id in ids):
            raise http_error(400, "Concept deja rezolvat")

        selected = frozenset(ids)
        pair_index = session.pair_index(selected)
        if pair_index is not None:
            session.solved.append(pair_index)
            session.won = len(session.solved) == PAIR_COUNT
            if session.won:
                record_finished(request, GAME_KEY, session.source_id)
            return Response(
                {
                    "ok": True,
                    "correct": True,
                    "pair": _pair_payload(session.pairs[pair_index]),
                    **_state(game_id, session),
                }
            )

        if any(frozenset(previous) == selected for previous in session.wrong_history):
            return Response(
                {
                    "ok": True,
                    "correct": False,
                    "repeated": True,
                    **_state(game_id, session),
                }
            )

        session.wrong_history.append(tuple(sorted(ids)))
        session.mistakes += 1
        session.lost = session.mistakes >= MAX_MISTAKES
        if session.lost:
            record_finished(request, GAME_KEY, session.source_id)
        return Response(
            {
                "ok": True,
                "correct": False,
                "repeated": False,
                **_state(game_id, session),
            }
        )


class HintView(ContractAPIView):
    @extend_schema(operation_id="perechi_hint", tags=["perechi"])
    @_atomic_session
    def post(self, request, game_id: str, session: PerechiSession):
        if session.won or session.lost:
            raise http_error(400, "Jocul s-a terminat")
        if session.hints_used >= MAX_HINTS:
            raise http_error(400, "Indiciul a fost deja folosit")
        if session.mistakes < MIN_HINT_MISTAKES:
            raise http_error(400, "Indiciul se deschide dupa doua greseli.")
        unresolved = [index for index in range(PAIR_COUNT) if index not in session.solved]
        session.hinted_pair = unresolved[0]
        session.hints_used += 1
        hint = _pair_payload(session.pairs[session.hinted_pair])
        return Response({"ok": True, "hint": hint, **_state(game_id, session)})


_BASE = "api/wordgames/perechi"
urlpatterns = [
    path(f"{_BASE}/games", CreateGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>", GetGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/match", MatchView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/hint", HintView.as_view()),
]
