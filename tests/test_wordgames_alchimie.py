"""Offline, deterministic tests for the Alchimie word game router."""

from __future__ import annotations

from itertools import combinations

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from cat_de_roman_esti.wordgames.alchimie import router  # noqa: E402

BASE = "/api/wordgames/alchimie"


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _create(client: TestClient, seed: int = 7) -> dict:
    res = client.post(f"{BASE}/games?seed={seed}")
    assert res.status_code == 200, res.text
    return res.json()


def test_create_returns_hidden_target_and_seed_inventory(client: TestClient) -> None:
    state = _create(client)
    assert state["game_id"]
    assert state["won"] is False
    assert state["moves"] == 0
    # A recognizable seed inventory of 5-7 concepts.
    assert 5 <= state["seed_count"] <= 7
    assert len(state["inventory"]) == state["seed_count"]
    # Target label is shown, but the secret id stays hidden until won.
    assert state["target"]["label"]
    assert state["target"]["revealed"] is False
    assert state["target"]["id"] is None
    # Seeds have no parents.
    for item in state["inventory"]:
        assert item["parents"] is None


def test_deterministic_for_same_seed(client: TestClient) -> None:
    a = _create(client, seed=42)
    b = _create(client, seed=42)
    assert a["target"]["label"] == b["target"]["label"]
    assert [i["id"] for i in a["inventory"]] == [i["id"] for i in b["inventory"]]


def test_winning_play_through(client: TestClient) -> None:
    """Greedily combine every owned pair until the target is crafted."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    tried: set[tuple[str, str]] = set()

    while not state["won"]:
        ids = [item["id"] for item in state["inventory"]]
        progressed = False
        for a, b in combinations(ids, 2):
            if (a, b) in tried:
                continue
            tried.add((a, b))
            res = client.post(f"{BASE}/games/{gid}/combine", json={"a": a, "b": b})
            assert res.status_code == 200, res.text
            state = res.json()
            if state["discovered"] or state["won"]:
                progressed = True
                break
        assert progressed, "ran out of combinations without winning"

    assert state["won"] is True
    # On win the target id + description are revealed.
    assert state["target"]["revealed"] is True
    assert state["target"]["id"] is not None
    assert "tinta" in state["message"].lower()
    # Discovered concepts carry their two parents (the WHY).
    crafted = [i for i in state["inventory"] if i["parents"] is not None]
    assert crafted
    for item in crafted:
        assert len(item["parents"]) == 2


def test_combine_with_no_discovery_counts_move(client: TestClient) -> None:
    """A combine with no shared neighbour still counts as a move with a clear message."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    ids = [item["id"] for item in state["inventory"]]

    # Find a barren pair (no common neighbours) among the seeds.
    barren: tuple[str, str] | None = None
    for a, b in combinations(ids, 2):
        res = client.post(f"{BASE}/games/{gid}/combine", json={"a": a, "b": b})
        body = res.json()
        if not body["discovered"]:
            barren = (a, b)
            assert body["message"] == "Nicio combinatie noua."
            assert body["moves"] >= 1
            break
        # Re-create to keep a clean inventory for the next probe.
        state = _create(client, seed=7)
        gid = state["game_id"]
    assert barren is not None


def test_combine_unowned_is_400(client: TestClient) -> None:
    state = _create(client)
    gid = state["game_id"]
    a = state["inventory"][0]["id"]
    res = client.post(
        f"{BASE}/games/{gid}/combine", json={"a": a, "b": "n_nonexistent_node"}
    )
    assert res.status_code == 400


def test_combine_same_concept_is_400(client: TestClient) -> None:
    state = _create(client)
    gid = state["game_id"]
    a = state["inventory"][0]["id"]
    res = client.post(f"{BASE}/games/{gid}/combine", json={"a": a, "b": a})
    assert res.status_code == 400


def test_reset_restores_seed_inventory(client: TestClient) -> None:
    state = _create(client, seed=7)
    gid = state["game_id"]
    ids = [item["id"] for item in state["inventory"]]
    # Make some progress.
    client.post(f"{BASE}/games/{gid}/combine", json={"a": ids[0], "b": ids[1]})

    res = client.post(f"{BASE}/games/{gid}/reset")
    assert res.status_code == 200
    reset = res.json()
    assert reset["moves"] == 0
    assert reset["won"] is False
    assert [i["id"] for i in reset["inventory"]] == ids


def test_unknown_game_is_404(client: TestClient) -> None:
    assert client.get(f"{BASE}/games/does-not-exist").status_code == 404
    res = client.post(
        f"{BASE}/games/does-not-exist/combine", json={"a": "x", "b": "y"}
    )
    assert res.status_code == 404


# --------------------------------------------------------------- difficulty + daily + score


def _play_to_win(client: TestClient, state: dict) -> dict:
    """Greedily combine pairs until the target is crafted; return the won state."""
    gid = state["game_id"]
    tried: set[tuple[str, str]] = set()
    while not state["won"]:
        ids = [item["id"] for item in state["inventory"]]
        progressed = False
        for a, b in combinations(ids, 2):
            if (a, b) in tried:
                continue
            tried.add((a, b))
            res = client.post(f"{BASE}/games/{gid}/combine", json={"a": a, "b": b})
            assert res.status_code == 200, res.text
            state = res.json()
            if state["discovered"] or state["won"]:
                progressed = True
                break
        assert progressed, "ran out of combinations without winning"
    return state


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_difficulty_is_accepted(client: TestClient, difficulty: str) -> None:
    res = client.post(f"{BASE}/games?seed=7&difficulty={difficulty}")
    assert res.status_code == 200, res.text
    state = res.json()
    assert state["difficulty"] == difficulty
    assert state["target_depth"] >= 2
    # usor offers a wide inventory; greu is lean.
    if difficulty == "usor":
        assert 6 <= state["seed_count"] <= 7
    if difficulty == "greu":
        assert state["seed_count"] == 5
        assert state["target_depth"] >= 3


def test_unknown_difficulty_falls_back_to_normal(client: TestClient) -> None:
    res = client.post(f"{BASE}/games?seed=7&difficulty=imposibil")
    assert res.status_code == 200
    assert res.json()["difficulty"] == "normal"


def test_daily_is_deterministic_and_echoed(client: TestClient) -> None:
    date = "2026-06-21"
    a = client.post(f"{BASE}/games?daily={date}").json()
    b = client.post(f"{BASE}/games?daily={date}").json()
    assert a["daily"] == date
    assert a["target"]["label"] == b["target"]["label"]
    assert [i["id"] for i in a["inventory"]] == [i["id"] for i in b["inventory"]]
    # A different date yields a (very likely) different instance and is echoed.
    other = client.post(f"{BASE}/games?daily=2026-01-01").json()
    assert other["daily"] == "2026-01-01"


def test_in_progress_state_has_no_score_or_share(client: TestClient) -> None:
    state = _create(client, seed=7)
    assert "score" not in state
    assert "share" not in state


def test_win_includes_score_and_share(client: TestClient) -> None:
    state = _play_to_win(client, _create(client, seed=7))
    assert state["won"] is True
    assert isinstance(state["score"], int)
    assert 100 <= state["score"] <= 1000
    share = state["share"]
    assert "Alchimie" in share
    assert "combinatii" in share
    assert "⚗️" in share


def test_daily_win_share_includes_date(client: TestClient) -> None:
    date = "2026-06-21"
    state = _play_to_win(client, client.post(f"{BASE}/games?daily={date}").json())
    assert date in state["share"]
    assert isinstance(state["score"], int)
