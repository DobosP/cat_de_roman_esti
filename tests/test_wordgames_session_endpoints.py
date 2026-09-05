"""Cross-game contracts for the shared session-endpoint transaction boundary."""

from __future__ import annotations

import threading
from types import ModuleType

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import (  # noqa: E402
    alchimie,
    conexiuni,
    contexto,
    intrusul,
    lant,
    perechi,
)
from cat_de_roman_esti.wordgames.service import (  # noqa: E402
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
    SessionStore,
)

GAME_ENDPOINTS = (
    (alchimie, "alchimie", "_state_payload", "Joc inexistent."),
    (conexiuni, "conexiuni", "_state", "Joc inexistent"),
    (contexto, "contexto", "_state", "Joc inexistent"),
    (intrusul, "intrusul", "_state", "Joc inexistent"),
    (lant, "lant", "_state", "Joc inexistent"),
    (perechi, "perechi", "_state", "Joc inexistent"),
)
MISSING_ACTIONS = (
    ("alchimie", "combine", {"a": "x", "b": "y"}, "Joc inexistent."),
    ("conexiuni", "guess", {"ids": ["a", "b", "c", "d"]}, "Joc inexistent"),
    ("contexto", "guess", {"text": "x"}, "Joc inexistent"),
    ("intrusul", "guess", {"id": "x"}, "Joc inexistent"),
    ("lant", "move", {"text": "x"}, "Joc inexistent"),
    ("perechi", "match", {"ids": ["a", "b"]}, "Joc inexistent"),
)


@pytest.mark.parametrize(
    ("module", "game", "_serializer", "detail"),
    GAME_ENDPOINTS,
    ids=[game for _module, game, _serializer, _detail in GAME_ENDPOINTS],
)
def test_missing_sessions_keep_each_games_public_error(
    module: ModuleType,
    game: str,
    _serializer: str,
    detail: str,
) -> None:
    response = Client().get(f"/api/wordgames/{game}/games/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    ("game", "action", "payload", "detail"),
    MISSING_ACTIONS,
    ids=[game for game, _action, _payload, _detail in MISSING_ACTIONS],
)
def test_missing_sessions_win_over_action_body_handling(
    game: str,
    action: str,
    payload: dict[str, object],
    detail: str,
) -> None:
    response = Client().post(
        f"/api/wordgames/{game}/games/does-not-exist/{action}",
        payload,
        content_type="application/json",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    ("module", "game", "serializer", "_detail"),
    GAME_ENDPOINTS,
    ids=[game for _module, game, _serializer, _detail in GAME_ENDPOINTS],
)
def test_same_session_endpoint_requests_are_serialized(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    game: str,
    serializer: str,
    _detail: str,
) -> None:
    """The real GET routes must run their full serializer under one entry lock."""
    replacement: SessionStore[dict[str, int]] = SessionStore()
    game_id = replacement.create({"calls": 0})
    monkeypatch.setattr(module, "store", replacement)

    start = threading.Barrier(3)
    overlap = threading.Barrier(2)
    guard = threading.Lock()
    active = 0
    max_active = 0

    def tracked_state(received_id: str, session: dict[str, int]) -> dict[str, object]:
        nonlocal active, max_active
        assert received_id == game_id
        with guard:
            active += 1
            max_active = max(max_active, active)
        try:
            # A missing endpoint transaction lets both serializers meet here. With the
            # per-entry lock, the first times out and the second enters only afterwards.
            overlap.wait(timeout=0.15)
        except threading.BrokenBarrierError:
            pass
        session["calls"] += 1
        result = {"game_id": received_id, "calls": session["calls"]}
        with guard:
            active -= 1
        return result

    monkeypatch.setattr(module, serializer, tracked_state)
    responses: list[dict[str, object]] = []

    def fetch() -> None:
        client = Client()
        start.wait()
        response = client.get(f"/api/wordgames/{game}/games/{game_id}")
        assert response.status_code == 200, response.content.decode()
        responses.append(response.json())

    threads = [threading.Thread(target=fetch) for _ in range(2)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert max_active == 1
    assert sorted(response["calls"] for response in responses) == [1, 2]
    assert replacement.get(game_id) == {"calls": 2}


@pytest.mark.parametrize(
    ("module", "_game", "_serializer", "_detail"),
    GAME_ENDPOINTS,
    ids=[game for _module, game, _serializer, _detail in GAME_ENDPOINTS],
)
def test_every_game_store_keeps_production_bounds(
    module: ModuleType,
    _game: str,
    _serializer: str,
    _detail: str,
) -> None:
    assert module.store._ttl == DEFAULT_SESSION_TTL_SECONDS == 7_200
    assert module.store._max == DEFAULT_MAX_SESSIONS == 1_000
