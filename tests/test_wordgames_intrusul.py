"""Deterministic, bounded API contracts for the V38 Intrusul game."""

from __future__ import annotations

import itertools
import random
import threading

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import intrusul  # noqa: E402
from cat_de_roman_esti.wordgames.categories import known_keys  # noqa: E402
from cat_de_roman_esti.wordgames.derived_catalog import (  # noqa: E402
    DerivedCatalog,
    get_derived_catalog,
)
from cat_de_roman_esti.wordgames.service import (  # noqa: E402
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
    SessionStore,
    get_service,
)

BASE = "/api/wordgames/intrusul"


def _create(client: Client, query: str = "seed=17") -> dict:
    response = client.post(f"{BASE}/games?{query}" if query else f"{BASE}/games")
    assert response.status_code == 200, response.content
    return response.json()


def _post(client: Client, path: str, payload: dict | None = None):
    if payload is None:
        return client.post(path)
    return client.post(path, payload, content_type="application/json")


def _session(body: dict) -> intrusul.IntrusulSession:
    session = intrusul.store.get(body["game_id"])
    assert session is not None
    return session


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _all_strings(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(_all_strings(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_strings(item) for item in value), set())
    return set()


def _strength(left: str, right: str) -> float:
    svc = get_service()
    edges = (svc.link(left, right), svc.link(right, left))
    return max((edge.strength for edge in edges if edge is not None), default=0.0)


def test_create_uses_one_strict_private_catalog_board() -> None:
    body = _create(Client())
    session = _session(body)
    visible = [tile["id"] for tile in body["tiles"]]

    assert len(visible) == len(set(visible)) == 4
    assert set(visible) == {*session.members, session.intruder}
    assert len({get_service().node(node_id).node_type for node_id in visible}) == 1
    assert sum(
        _strength(left, right) >= 0.6
        for left, right in itertools.combinations(session.members, 2)
    ) >= 2
    assert all(_strength(member, session.intruder) == 0 for member in session.members)
    assert body["attempts"] == body["mistakes"] == 0
    assert body["remaining_mistakes"] == intrusul.MAX_MISTAKES
    assert body["wrong_ids"] == []
    assert body["hints_used"] == 0 and body["hint_available"] is False
    assert body["won"] is False and body["lost"] is False
    assert "board_category" not in body


def test_seed_and_daily_are_stable_and_daily_ignores_optional_rotation_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    seeded_a = _create(client, "seed=91")
    seeded_b = _create(client, "seed=91")
    assert seeded_a["tiles"] == seeded_b["tiles"]
    assert _session(seeded_a).catalog_id == _session(seeded_b).catalog_id

    daily_a = _create(client, "daily=2026-07-19")
    monkeypatch.setattr(
        intrusul,
        "excluded_pack_ids",
        lambda *_args: (_ for _ in ()).throw(AssertionError("daily queried account history")),
    )
    daily_b = _create(
        client,
        f"daily=2026-07-19&seed=999&starter=1&previous_game_id={seeded_a['game_id']}",
    )
    assert daily_a["tiles"] == daily_b["tiles"]
    assert daily_b["daily"] == "2026-07-19"
    assert _session(daily_a).catalog_id == _session(daily_b).catalog_id
    assert _session(daily_b).source_ring == (_session(daily_b).source_id,)


def test_starter_gate_category_contract_and_safe_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = get_derived_catalog()
    client = Client()
    starter = _create(client, "seed=7&starter=1")
    starter_ids = {
        board._catalog_id for board in catalog.pool(intrusul.GAME_KEY, starter=True)
    }
    assert _session(starter).catalog_id in starter_ids

    category = catalog.pool(intrusul.GAME_KEY)[0].category
    themed = _create(client, f"seed=7&category={category}")
    assert themed["board_category"] == category
    assert _session(themed).category == category

    assert client.post(f"{BASE}/games?category=nu_exista").status_code == 400
    assert client.post(f"{BASE}/games?starter=2").status_code == 400
    assert client.post(f"{BASE}/games?starter=da").status_code == 422

    starter_sources = {
        board._source_id for board in catalog.pool(intrusul.GAME_KEY, starter=True)
    }
    monkeypatch.setattr(intrusul, "excluded_pack_ids", lambda *_args: starter_sources)
    fallback = _create(client, "seed=7&starter=1")
    assert _session(fallback).source_id not in starter_sources

    all_sources = {
        board._source_id for board in catalog.pool(intrusul.GAME_KEY)
    }
    monkeypatch.setattr(intrusul, "excluded_pack_ids", lambda *_args: all_sources)
    exhausted = _create(client, "seed=7")
    assert _session(exhausted).source_id in all_sources

    monkeypatch.setattr(intrusul, "get_derived_catalog", lambda: DerivedCatalog([]))
    assert client.post(f"{BASE}/games?category={known_keys()[0]}").status_code == 503


def test_previous_game_carries_a_bounded_distinct_source_ring() -> None:
    client = Client()
    previous_id: str | None = None
    seen: list[str] = []
    for _ in range(7):
        query = "seed=31"
        if previous_id:
            query += f"&previous_game_id={previous_id}"
        body = _create(client, query)
        session = _session(body)
        seen = [source for source in seen if source != session.source_id]
        seen.append(session.source_id)
        seen = seen[-intrusul.SOURCE_RING_LIMIT :]
        assert list(session.source_ring) == seen
        assert len(session.source_ring) <= intrusul.SOURCE_RING_LIMIT
        assert len(session.source_ring) == len(set(session.source_ring))
        previous_id = body["game_id"]

    assert _create(client, "seed=31&previous_game_id=expired-id")["game_id"]


def test_forced_source_repeat_moves_to_tail_without_shrinking_ring() -> None:
    board = get_derived_catalog().pool(intrusul.GAME_KEY)[0]
    previous = ("source-a", board._source_id, "source-c", "source-d")
    session = intrusul._build_session(
        board,
        random.Random(1),
        daily=None,
        requested_category=None,
        previous_ring=previous,
    )
    assert session.source_ring == (
        "source-a",
        "source-c",
        "source-d",
        board._source_id,
    )
    assert len(session.source_ring) == intrusul.SOURCE_RING_LIMIT


def test_account_sources_combine_with_previous_ring(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Client()
    first = _create(client, "seed=44")
    first_session = _session(first)
    monkeypatch.setattr(
        intrusul,
        "excluded_pack_ids",
        lambda *_args: {first_session.source_id},
    )
    second = _create(client, f"seed=44&previous_game_id={first['game_id']}")
    assert _session(second).source_id != first_session.source_id


def test_preterminal_state_hides_solution_provenance_and_rankings() -> None:
    client = Client()
    body = _create(client)
    session = _session(body)
    forbidden = {
        "solution",
        "intruder",
        "members",
        "group",
        "group_label",
        "source_id",
        "source_ring",
        "catalog_id",
        "rank",
        "standard_rank",
        "starter_rank",
        "standard_score",
        "starter_score",
        "selection_weight",
    }
    assert forbidden.isdisjoint(_all_keys(body))
    assert session.group_label not in _all_strings(body)
    assert session.source_id not in repr(session)
    assert session.catalog_id not in repr(session)

    fetched = client.get(f"{BASE}/games/{body['game_id']}").json()
    assert forbidden.isdisjoint(_all_keys(fetched))
    assert session.group_label not in _all_strings(fetched)


def test_wrong_repeat_hint_and_scored_win_are_bounded() -> None:
    client = Client()
    body = _create(client)
    session = _session(body)
    wrong = session.members[0]
    guess_url = f"{BASE}/games/{body['game_id']}/guess"
    hint_url = f"{BASE}/games/{body['game_id']}/hint"

    assert _post(client, hint_url).status_code == 400
    first = _post(client, guess_url, {"id": wrong}).json()
    assert first["correct"] is False and first["already_tried"] is False
    assert first["attempts"] == first["mistakes"] == 1
    assert first["wrong_ids"] == [wrong]
    assert first["hint_available"] is True
    assert "solution" not in first and "clue" not in first

    repeated = _post(client, guess_url, {"id": wrong}).json()
    assert repeated["already_tried"] is True
    assert repeated["attempts"] == repeated["mistakes"] == 1

    hinted = _post(client, hint_url).json()
    assert hinted["hints_used"] == 1 and hinted["hint_available"] is False
    assert hinted["clue"] == intrusul._clue(session)
    assert set(hinted["clue"]) == {"label", "message"}
    assert _post(client, hint_url).status_code == 400

    won = _post(client, guess_url, {"id": session.intruder}).json()
    assert won["correct"] is True and won["won"] is True and won["lost"] is False
    assert won["attempts"] == 2 and won["score"] == 650
    assert won["solution"]["intruder"]["id"] == session.intruder
    assert {tile["id"] for tile in won["solution"]["group"]["tiles"]} == set(
        session.members
    )
    assert won["solution"]["group"]["label"] == session.group_label


def test_first_try_score_third_wrong_loss_and_terminal_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[str, str]] = []
    monkeypatch.setattr(
        intrusul,
        "record_finished",
        lambda _request, game, source: recorded.append((game, source)),
    )
    client = Client()
    first = _create(client, "seed=51")
    first_session = _session(first)
    first_url = f"{BASE}/games/{first['game_id']}"
    won = _post(client, f"{first_url}/guess", {"id": first_session.intruder}).json()
    assert won["score"] == 1_000
    assert recorded[-1] == (intrusul.GAME_KEY, first_session.source_id)
    assert _post(client, f"{first_url}/guess", {"id": first_session.intruder}).status_code == 400
    assert _post(client, f"{first_url}/hint").status_code == 400

    lost_game = _create(client, "seed=52")
    lost_session = _session(lost_game)
    lost_url = f"{BASE}/games/{lost_game['game_id']}/guess"
    responses = [
        _post(client, lost_url, {"id": node_id}).json()
        for node_id in lost_session.members
    ]
    assert [response["lost"] for response in responses] == [False, False, True]
    lost = responses[-1]
    assert lost["attempts"] == lost["mistakes"] == 3
    assert lost["remaining_mistakes"] == 0 and lost["score"] == 0
    assert lost["solution"]["intruder"]["id"] == lost_session.intruder
    assert "îți arăt intrusul" in lost["message"]
    assert recorded[-1] == (intrusul.GAME_KEY, lost_session.source_id)


def test_invalid_actions_and_missing_session_use_contract_errors() -> None:
    client = Client()
    body = _create(client)
    url = f"{BASE}/games/{body['game_id']}/guess"
    assert _post(client, url, {"id": "nu-este-pe-tabla"}).status_code == 400
    assert _post(client, url, {}).status_code == 422
    assert client.get(f"{BASE}/games/lipsa").status_code == 404
    assert _post(client, f"{BASE}/games/lipsa/hint").status_code == 404


def test_concurrent_duplicate_wrong_tap_costs_once() -> None:
    body = _create(Client(), "seed=61")
    session = _session(body)
    wrong = session.members[0]
    url = f"{BASE}/games/{body['game_id']}/guess"
    barrier = threading.Barrier(3)
    results: list[dict] = []

    def worker() -> None:
        client = Client()
        barrier.wait()
        response = _post(client, url, {"id": wrong})
        assert response.status_code == 200
        results.append(response.json())

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive()

    assert sorted(result["already_tried"] for result in results) == [False, True]
    assert session.attempts == 1 and session.wrong_ids == [wrong]


def test_store_defaults_and_all_borrowed_capacity_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert intrusul.store._ttl == DEFAULT_SESSION_TTL_SECONDS == 7_200
    assert intrusul.store._max == DEFAULT_MAX_SESSIONS == 1_000

    tiny: SessionStore[intrusul.IntrusulSession] = SessionStore(
        ttl_seconds=None,
        max_sessions=1,
    )
    monkeypatch.setattr(intrusul, "store", tiny)
    client = Client()
    first = _create(client, "seed=71")
    with tiny.transaction(first["game_id"]) as borrowed:
        assert borrowed is not None
        response = client.post(f"{BASE}/games?seed=72")
    assert response.status_code == 503
    assert response.json() == {"detail": "Prea multe jocuri active. Încearcă din nou."}


def test_openapi_operation_ids_are_stable() -> None:
    schema = Client().get("/openapi.json").json()
    expected = {
        f"{BASE}/games": ("post", "intrusul_create_game"),
        f"{BASE}/games/{{game_id}}": ("get", "intrusul_get_game"),
        f"{BASE}/games/{{game_id}}/guess": ("post", "intrusul_guess"),
        f"{BASE}/games/{{game_id}}/hint": ("post", "intrusul_hint"),
    }
    for path, (method, operation_id) in expected.items():
        assert schema["paths"][path][method]["operationId"] == operation_id
