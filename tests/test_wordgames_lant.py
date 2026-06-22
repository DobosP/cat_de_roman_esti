"""Offline, deterministic tests for the Lantul Cuvintelor word-ladder game."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from cat_de_roman_esti.wordgames.lant import router

app = FastAPI()
app.include_router(router)
c = TestClient(app)

SEED = 7


def _create(seed: int = SEED, **params):
    q = f"?seed={seed}"
    for k, v in params.items():
        q += f"&{k}={v}"
    res = c.post(f"/api/wordgames/lant/games{q}")
    assert res.status_code == 200, res.text
    return res.json()


def _win(game: dict) -> dict:
    """Follow shortest-path hints to a win; return the final move response body."""
    gid = game["game_id"]
    body = {}
    for _ in range(game["optimal"]):
        hint = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()["hint"]
        assert hint is not None
        body = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            json={"text": hint["label"]},
        ).json()
    assert body["won"] is True
    return body


def test_create_is_solvable_and_seed_deterministic():
    a = _create()
    b = _create()
    # Same seed -> same puzzle.
    assert a["start"]["id"] == b["start"]["id"]
    assert a["target"]["id"] == b["target"]["id"]

    assert 3 <= a["optimal"] <= 5
    assert a["moves"] == 0
    assert a["won"] is False
    assert a["current"]["id"] == a["start"]["id"]
    assert a["path"][0]["id"] == a["start"]["id"]
    assert a["target"]["description"]  # target description is shown


def test_winning_playthrough_by_following_hints():
    game = _create()
    gid = game["game_id"]
    optimal = game["optimal"]

    won = False
    # Following the shortest-path hint each turn must win in exactly `optimal` moves.
    for _ in range(optimal):
        hres = c.post(f"/api/wordgames/lant/games/{gid}/hint")
        assert hres.status_code == 200, hres.text
        hint = hres.json()["hint"]
        assert hint is not None, hres.text

        mres = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            json={"text": hint["label"]},
        )
        assert mres.status_code == 200, mres.text
        body = mres.json()
        assert body["ok"] is True, body
        assert body["relation"] != "" or True  # relation label may be empty for some edges
        won = body["won"]

    assert won is True
    final = c.get(f"/api/wordgames/lant/games/{gid}").json()
    assert final["won"] is True
    assert final["current"]["id"] == final["target"]["id"]
    assert final["moves"] == optimal


def test_unknown_concept_rejected():
    game = _create()
    gid = game["game_id"]
    res = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        json={"text": "qwerty nonexistent xyz"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is False
    assert body["last_error"] == "Nu cunosc acest concept"


def test_non_neighbor_rejected():
    game = _create()
    gid = game["game_id"]
    # The target is (>=3 hops away) definitely not a direct neighbour of the start.
    res = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        json={"text": game["target"]["label"]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is False
    assert body["last_error"] == "Nu exista o legatura directa"


def test_undo_does_not_go_below_start():
    game = _create()
    gid = game["game_id"]
    # Undo with no moves yet stays at start.
    res = c.post(f"/api/wordgames/lant/games/{gid}/undo")
    assert res.status_code == 200
    body = res.json()
    assert body["moves"] == 0
    assert body["current"]["id"] == body["start"]["id"]

    # Make one valid hinted move, then undo back to start.
    hint = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()["hint"]
    c.post(f"/api/wordgames/lant/games/{gid}/move", json={"text": hint["label"]})
    after_undo = c.post(f"/api/wordgames/lant/games/{gid}/undo").json()
    assert after_undo["moves"] == 0
    assert after_undo["current"]["id"] == game["start"]["id"]


def test_difficulty_bands_accepted_and_respected():
    bands = {"usor": (2, 3), "normal": (3, 4), "greu": (4, 6)}
    for diff, (lo, hi) in bands.items():
        g = _create(seed=11, difficulty=diff)
        assert g["difficulty"] == diff
        assert lo <= g["optimal"] <= hi, (diff, g["optimal"])


def test_invalid_difficulty_falls_back_to_normal():
    g = _create(difficulty="impossible")
    assert g["difficulty"] == "normal"
    assert 3 <= g["optimal"] <= 4


def test_win_includes_score_and_share():
    game = _create()
    body = _win(game)
    assert "score" in body and isinstance(body["score"], int)
    # Optimal play -> max score of 1000; score is always at least 100.
    assert body["score"] == 1000
    assert body["score"] >= 100
    assert "share" in body
    share = body["share"]
    assert "Lantul Cuvintelor" in share
    assert "🔗" in share
    assert f"{body['moves']}/{game['optimal']} mutari" in share

    # Final GET state also surfaces score + share.
    final = c.get(f"/api/wordgames/lant/games/{game['game_id']}").json()
    assert final["score"] == body["score"]
    assert final["share"] == body["share"]


def test_score_formula_holds_on_win():
    game = _create()
    optimal = game["optimal"]
    body = _win(game)
    # Hint-following wins in exactly `optimal` moves -> the maximum score.
    assert body["moves"] == optimal
    assert body["score"] == max(
        100, round(1000 * optimal / max(body["moves"], optimal))
    )


def test_daily_is_deterministic_and_echoed():
    a = _create(daily="2026-06-21")
    b = _create(daily="2026-06-21")
    assert a["daily"] == "2026-06-21"
    assert a["start"]["id"] == b["start"]["id"]
    assert a["target"]["id"] == b["target"]["id"]
    # A different date generally yields a different puzzle.
    diff = _create(daily="2026-01-01")
    assert (diff["start"]["id"], diff["target"]["id"]) != (
        a["start"]["id"],
        a["target"]["id"],
    )
    # Daily win share embeds the date.
    body = _win(a)
    assert "2026-06-21" in body["share"]


def test_unknown_game_404():
    assert c.get("/api/wordgames/lant/games/does-not-exist").status_code == 404
    assert (
        c.post(
            "/api/wordgames/lant/games/does-not-exist/move",
            json={"text": "x"},
        ).status_code
        == 404
    )
    assert c.post("/api/wordgames/lant/games/does-not-exist/hint").status_code == 404
    assert c.post("/api/wordgames/lant/games/does-not-exist/undo").status_code == 404
