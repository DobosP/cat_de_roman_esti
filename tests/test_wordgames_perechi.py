"""Bounded, server-authoritative contracts for V38 Perechi."""

from __future__ import annotations

import itertools
import json
import threading
from collections.abc import Iterator
from dataclasses import replace
from urllib.parse import urlencode

import pytest

pytest.importorskip("django")

from django.test import Client
from drf_spectacular.generators import SchemaGenerator

from cat_de_roman_esti.wordgames import perechi as P
from cat_de_roman_esti.wordgames.derived_catalog import DerivedCatalog, get_derived_catalog
from cat_de_roman_esti.wordgames.service import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
    SessionStore,
)

BASE = "/api/wordgames/perechi"
PRIVATE_KEYS = {
    "source_id",
    "catalog_id",
    "source_ring",
    "romanian_familiarity",
    "play_quality",
    "standard_score",
    "starter_score",
    "starter_eligible",
    "standard_rank",
    "starter_rank",
}


@pytest.fixture(autouse=True)
def _fresh_store(monkeypatch: pytest.MonkeyPatch) -> Iterator[SessionStore]:
    game_store: SessionStore[P.PerechiSession] = SessionStore()
    monkeypatch.setattr(P, "store", game_store)
    yield game_store


def _post_json(client: Client, url: str, payload: dict):
    return client.post(url, payload, content_type="application/json")


def _create(client: Client, **query) -> dict:
    suffix = f"?{urlencode(query)}" if query else ""
    response = client.post(f"{BASE}/games{suffix}")
    assert response.status_code == 200, response.content.decode()
    return response.json()


def _session(game_id: str) -> P.PerechiSession:
    session = P.store.get(game_id)
    assert session is not None
    return session


def _true_pairs(session: P.PerechiSession) -> list[list[str]]:
    return [list(pair.members) for pair in session.pairs]


def _wrong_pairs(session: P.PerechiSession) -> list[list[str]]:
    true = {frozenset(pair.members) for pair in session.pairs}
    return [
        list(pair)
        for pair in itertools.combinations(session.order, 2)
        if frozenset(pair) not in true
    ]


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(map(str, value))
        for nested in value.values():
            keys |= _all_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            keys |= _all_keys(nested)
    return keys


def _serialized_strings(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_private_preterminal(body: dict, session: P.PerechiSession) -> None:
    assert PRIVATE_KEYS.isdisjoint(_all_keys(body))
    assert "solution" not in body and "score" not in body and "share" not in body
    serialized = _serialized_strings(body)
    assert session.source_id not in serialized
    assert session.catalog_id not in serialized
    revealed = {pair["label"] for pair in body["solved_pairs"]}
    if body.get("hint"):
        revealed.add(body["hint"]["label"])
    for pair in session.pairs:
        if pair.label not in revealed:
            assert pair.label not in serialized


def test_create_shape_privacy_and_default_store_bounds() -> None:
    body = _create(Client(), seed=38)
    session = _session(body["game_id"])
    assert len(body["tiles"]) == 8
    assert len({tile["id"] for tile in body["tiles"]}) == 8
    assert all(set(tile) == {"id", "label", "solved"} for tile in body["tiles"])
    assert not any(tile["solved"] for tile in body["tiles"])
    assert body["solved_pairs"] == []
    assert body["solved_count"] == 0 and body["remaining_pairs"] == 4
    assert body["mistakes"] == 0 and body["remaining_mistakes"] == 6
    assert body["actions"] == 0 and body["hint_available"] is False
    assert body["hints_used"] == 0 and body["won"] is body["lost"] is False
    assert len(session.pairs) == 4
    assert len({frozenset(pair.members) for pair in session.pairs}) == 4
    assert P.store._ttl == DEFAULT_SESSION_TTL_SECONDS == 7_200
    assert P.store._max == DEFAULT_MAX_SESSIONS == 1_000
    _assert_private_preterminal(body, session)


def test_dataclass_reprs_hide_answers_tile_order_and_provenance() -> None:
    client = Client()
    body = _create(client, seed=38)
    session = _session(body["game_id"])

    for wrong in _wrong_pairs(session)[:2]:
        response = _post_json(
            client,
            f"{BASE}/games/{body['game_id']}/match",
            {"ids": wrong},
        )
        assert response.status_code == 200
    assert client.post(f"{BASE}/games/{body['game_id']}/hint").status_code == 200
    matched = _post_json(
        client,
        f"{BASE}/games/{body['game_id']}/match",
        {"ids": list(session.pairs[0].members)},
    )
    assert matched.status_code == 200

    session_repr = repr(session)

    private_values = {
        *session.order,
        *(pair.label for pair in session.pairs),
        session.source_id,
        session.catalog_id,
        *session.source_ring,
    }
    assert private_values
    assert all(value not in session_repr for value in private_values)
    assert "mistakes=2" in session_repr
    assert "hints_used=1" in session_repr
    assert "won=False" in session_repr

    for pair in session.pairs:
        pair_repr = repr(pair)
        assert pair.label not in pair_repr
        assert all(member not in pair_repr for member in pair.members)


def test_seed_category_and_starter_selection_are_deterministic() -> None:
    client = Client()
    first = _create(client, seed=731, starter=1)
    second = _create(client, seed=731, starter=1)
    first_session = _session(first["game_id"])
    second_session = _session(second["game_id"])
    assert first["tiles"] == second["tiles"]
    assert first_session.catalog_id == second_session.catalog_id
    selected = next(
        board
        for board in get_derived_catalog().pool("perechi")
        if board._catalog_id == first_session.catalog_id
    )
    assert selected._starter_eligible is True

    category = get_derived_catalog().pool("perechi")[0].category
    themed = _create(client, seed=19, category=category)
    themed_session = _session(themed["game_id"])
    assert themed["board_category"] == category
    assert next(
        board.category
        for board in get_derived_catalog().pool("perechi")
        if board._catalog_id == themed_session.catalog_id
    ) == category
    assert "board_category" not in first


def test_starter_uses_safe_standard_fallback_only_when_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = get_derived_catalog().pool("perechi")[0]
    reserve = replace(real, _starter_eligible=False, _starter_rank=None)
    catalog = DerivedCatalog([reserve])
    monkeypatch.setattr(P, "get_derived_catalog", lambda: catalog)
    body = _create(Client(), seed=1, starter=1)
    assert _session(body["game_id"]).catalog_id == reserve._catalog_id


def test_query_validation_and_empty_finite_shelf_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    assert client.post(f"{BASE}/games?category=nu_exista").status_code == 400
    assert client.post(f"{BASE}/games?starter=2").status_code == 400
    assert client.post(f"{BASE}/games?starter=da").status_code == 422
    monkeypatch.setattr(P, "get_derived_catalog", lambda: DerivedCatalog([]))
    assert client.post(f"{BASE}/games?seed=1").status_code == 503


def test_daily_ignores_starter_previous_and_account_exclusions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    previous = _create(client, seed=4)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("daily must not consult account exclusions")

    monkeypatch.setattr(P, "excluded_pack_ids", forbidden)
    plain = _create(client, daily="2026-07-19", starter=0)
    personalized = _create(
        client,
        daily="2026-07-19",
        starter=1,
        previous_game_id=previous["game_id"],
    )
    assert plain["tiles"] == personalized["tiles"]
    assert _session(plain["game_id"]).source_id == _session(
        personalized["game_id"]
    ).source_id
    assert _session(personalized["game_id"]).source_ring == (
        _session(personalized["game_id"]).source_id,
    )


def test_previous_source_ring_and_account_exclusions_are_combined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    previous = _create(client, seed=11)
    previous_source = _session(previous["game_id"]).source_id
    other_source = next(
        board._source_id
        for board in get_derived_catalog().pool("perechi")
        if board._source_id != previous_source
    )

    class SpyCatalog:
        def __init__(self, wrapped):
            self.wrapped = wrapped
            self.exclusions: list[set[str]] = []

        def pick_seeded(self, *args, **kwargs):
            self.exclusions.append(set(kwargs.get("exclude_source_ids") or set()))
            return self.wrapped.pick_seeded(*args, **kwargs)

    spy = SpyCatalog(get_derived_catalog())
    monkeypatch.setattr(P, "get_derived_catalog", lambda: spy)
    monkeypatch.setattr(P, "excluded_pack_ids", lambda request, game: {other_source})
    current = _create(client, seed=12, previous_game_id=previous["game_id"])
    current_session = _session(current["game_id"])
    assert spy.exclusions[0] == {previous_source, other_source}
    assert current_session.source_id not in {previous_source, other_source}
    assert current_session.source_ring[-2:] == (
        previous_source,
        current_session.source_id,
    )


def test_source_ring_is_bounded_to_four_live_predecessors() -> None:
    client = Client()
    previous_id = None
    last = None
    for seed in range(6):
        query = {"seed": seed}
        if previous_id is not None:
            query["previous_game_id"] = previous_id
        last = _create(client, **query)
        previous_id = last["game_id"]
    assert last is not None
    session = _session(last["game_id"])
    assert 1 <= len(session.source_ring) <= P.SOURCE_RING_CAP == 4
    assert session.source_ring[-1] == session.source_id
    assert len(set(session.source_ring)) == len(session.source_ring)


def test_exhausted_source_exclusions_retry_the_same_strict_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    only_board = get_derived_catalog().pool("perechi")[0]
    monkeypatch.setattr(P, "get_derived_catalog", lambda: DerivedCatalog([only_board]))
    client = Client()
    first = _create(client, seed=1)
    second = _create(client, seed=2, previous_game_id=first["game_id"])
    assert _session(first["game_id"]).source_id == _session(second["game_id"]).source_id
    assert _session(second["game_id"]).source_ring == (only_board._source_id,)


def test_correct_match_reveals_only_earned_label_and_solved_tiles_are_locked() -> None:
    client = Client()
    body = _create(client, seed=7)
    session = _session(body["game_id"])
    first_pair = list(session.pairs[0].members)
    matched = _post_json(client, f"{BASE}/games/{body['game_id']}/match", {"ids": first_pair})
    assert matched.status_code == 200
    result = matched.json()
    assert result["correct"] is True and result["solved_count"] == 1
    assert result["pair"]["label"] == session.pairs[0].label
    assert [pair["label"] for pair in result["solved_pairs"]] == [session.pairs[0].label]
    assert sum(tile["solved"] for tile in result["tiles"]) == 2
    _assert_private_preterminal(result, session)
    reused = _post_json(
        client,
        f"{BASE}/games/{body['game_id']}/match",
        {"ids": [first_pair[0], session.pairs[1].members[0]]},
    )
    assert reused.status_code == 400


@pytest.mark.parametrize("ids", [[], ["one"], ["same", "same"], ["a", "b", "c"]])
def test_match_requires_exactly_two_distinct_board_tiles(ids: list[str]) -> None:
    client = Client()
    body = _create(client, seed=9)
    response = _post_json(client, f"{BASE}/games/{body['game_id']}/match", {"ids": ids})
    assert response.status_code == 400


def test_unordered_repeated_wrong_pair_is_200_and_free() -> None:
    client = Client()
    body = _create(client, seed=10)
    session = _session(body["game_id"])
    wrong = _wrong_pairs(session)[0]
    first = _post_json(client, f"{BASE}/games/{body['game_id']}/match", {"ids": wrong})
    repeated = _post_json(
        client,
        f"{BASE}/games/{body['game_id']}/match",
        {"ids": list(reversed(wrong))},
    )
    assert first.status_code == repeated.status_code == 200
    assert first.json()["repeated"] is False
    assert repeated.json()["repeated"] is True
    assert repeated.json()["mistakes"] == 1 and repeated.json()["actions"] == 1
    assert session.mistakes == len(session.wrong_history) == 1


def test_hint_unlocks_after_two_mistakes_reveals_without_solving_and_is_single_use() -> None:
    client = Client()
    body = _create(client, seed=12)
    gid = body["game_id"]
    session = _session(gid)
    assert client.post(f"{BASE}/games/{gid}/hint").status_code == 400
    for wrong in _wrong_pairs(session)[:2]:
        assert _post_json(client, f"{BASE}/games/{gid}/match", {"ids": wrong}).status_code == 200
    hinted = client.post(f"{BASE}/games/{gid}/hint")
    assert hinted.status_code == 200
    result = hinted.json()
    assert result["hints_used"] == 1 and result["solved_count"] == 0
    assert result["actions"] == 2 and result["hint_available"] is False
    assert {tile["id"] for tile in result["hint"]["tiles"]} == set(
        session.pairs[session.hinted_pair].members
    )
    assert client.post(f"{BASE}/games/{gid}/hint").status_code == 400
    _assert_private_preterminal(result, session)


def test_perfect_win_score_terminal_solution_answer_free_share_and_progress_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[str, str]] = []
    monkeypatch.setattr(
        P,
        "record_finished",
        lambda request, game, source: recorded.append((game, source)),
    )
    client = Client()
    body = _create(client, seed=14)
    gid = body["game_id"]
    session = _session(gid)
    result = None
    for pair in _true_pairs(session):
        result = _post_json(client, f"{BASE}/games/{gid}/match", {"ids": pair}).json()
    assert result is not None
    assert result["won"] is True and result["lost"] is False
    assert result["score"] == 1000 and result["actions"] == 4
    assert len(result["solution"]) == 4
    assert recorded == [("perechi", session.source_id)]
    assert session.source_id not in _serialized_strings(result)
    assert session.catalog_id not in _serialized_strings(result)
    assert all(pair.label not in result["share"] for pair in session.pairs)
    assert all(tile["label"] not in result["share"] for tile in result["tiles"])
    assert "Perechi" in result["share"]
    after_terminal = _post_json(
        client,
        f"{BASE}/games/{gid}/match",
        {"ids": _true_pairs(session)[0]},
    )
    assert after_terminal.status_code == 400


def test_hint_and_mistake_penalties_are_server_authored() -> None:
    client = Client()
    body = _create(client, seed=17)
    gid = body["game_id"]
    session = _session(gid)
    for wrong in _wrong_pairs(session)[:2]:
        _post_json(client, f"{BASE}/games/{gid}/match", {"ids": wrong})
    assert client.post(f"{BASE}/games/{gid}/hint").status_code == 200
    result = None
    for pair in _true_pairs(session):
        result = _post_json(client, f"{BASE}/games/{gid}/match", {"ids": pair}).json()
    assert result is not None and result["score"] == 650
    session.mistakes = 20
    assert P._score(session) == 100


def test_sixth_distinct_wrong_pair_loses_and_history_stays_bounded() -> None:
    client = Client()
    body = _create(client, seed=20)
    gid = body["game_id"]
    session = _session(gid)
    result = None
    for wrong in _wrong_pairs(session)[:6]:
        response = _post_json(client, f"{BASE}/games/{gid}/match", {"ids": wrong})
        assert response.status_code == 200
        result = response.json()
    assert result is not None
    assert result["lost"] is True and result["won"] is False
    assert result["score"] == 0 and result["actions"] == 6
    assert len(result["solution"]) == 4
    assert session.mistakes == len(session.wrong_history) == P.MAX_MISTAKES == 6
    assert client.post(f"{BASE}/games/{gid}/hint").status_code == 400


def test_winning_action_history_is_bounded_at_nine() -> None:
    client = Client()
    body = _create(client, seed=23)
    gid = body["game_id"]
    session = _session(gid)
    for wrong in _wrong_pairs(session)[:5]:
        _post_json(client, f"{BASE}/games/{gid}/match", {"ids": wrong})
    result = None
    for pair in _true_pairs(session):
        result = _post_json(client, f"{BASE}/games/{gid}/match", {"ids": pair}).json()
    assert result is not None and result["won"] is True
    assert result["actions"] == 9
    assert len(session.wrong_history) == 5 and len(session.solved) == 4


def test_get_missing_and_operation_ids() -> None:
    client = Client()
    created = _create(client, seed=25)
    assert client.get(f"{BASE}/games/{created['game_id']}").status_code == 200
    assert client.get(f"{BASE}/games/missing").status_code == 404
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operations = {
        operation["operationId"]
        for path, methods in schema["paths"].items()
        if path.startswith(f"/{BASE.lstrip('/')}")
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    assert operations == {
        "perechi_create_game",
        "perechi_get_game",
        "perechi_match",
        "perechi_hint",
    }


def test_concurrent_duplicate_wrong_pair_is_charged_once() -> None:
    client = Client()
    body = _create(client, seed=27)
    gid = body["game_id"]
    session = _session(gid)
    wrong = _wrong_pairs(session)[0]
    rendezvous = threading.Barrier(2)

    class RendezvousHistory(list):
        def __iter__(self):
            snapshot = tuple(super().__iter__())
            try:
                rendezvous.wait(timeout=0.15)
            except threading.BrokenBarrierError:
                pass
            return iter(snapshot)

    session.wrong_history = RendezvousHistory()
    start = threading.Barrier(3)
    responses: list[dict] = []

    def submit(ids: list[str]) -> None:
        request_client = Client()
        start.wait()
        response = _post_json(
            request_client,
            f"{BASE}/games/{gid}/match",
            {"ids": ids},
        )
        assert response.status_code == 200
        responses.append(response.json())

    threads = [
        threading.Thread(target=submit, args=(wrong,)),
        threading.Thread(target=submit, args=(list(reversed(wrong)),)),
    ]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert sorted(response["repeated"] for response in responses) == [False, True]
    assert session.mistakes == len(session.wrong_history) == 1


def test_all_borrowed_capacity_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    limited: SessionStore[P.PerechiSession] = SessionStore(
        ttl_seconds=None, max_sessions=1
    )
    monkeypatch.setattr(P, "store", limited)
    client = Client()
    first = _create(client, seed=30)
    with limited.transaction(first["game_id"]) as session:
        assert session is not None
        blocked = client.post(f"{BASE}/games?seed=31")
        assert blocked.status_code == 503
        assert len(limited) == 1
