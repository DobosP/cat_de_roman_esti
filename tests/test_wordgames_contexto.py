"""Offline, deterministic tests for the "Cald sau Rece" (contexto) word game."""

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_client() -> TestClient:
    app = FastAPI()
    from cat_de_roman_esti.wordgames.contexto import router

    app.include_router(router)
    return TestClient(app)


# With seed=1 the secret target is "Dunărea" (id n_dunarea); "Banat" is a distance-1
# neighbour. These are stable properties of the bundled offline KG.
SEED = 1


def test_create_game_hides_target() -> None:
    c = make_client()
    res = c.post("/api/wordgames/contexto/games", params={"seed": SEED})
    assert res.status_code == 200
    body = res.json()
    assert body["attempts"] == 0
    assert body["won"] is False
    assert body["guesses"] == []
    assert body["reachable_count"] >= 120
    assert "target" not in body  # secret never leaks before win/giveup


def test_unknown_concept_not_counted() -> None:
    c = make_client()
    gid = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()["game_id"]
    res = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        json={"text": "zzz nu exista zzz"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is False
    assert body["message"] == "Nu cunosc acest concept"
    assert body["attempts"] == 0


def test_guess_reports_temperature_and_closeness() -> None:
    c = make_client()
    gid = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()["game_id"]
    res = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        json={"text": "Banat"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    g = body["guess"]
    assert g["id"] == "n_banat"
    assert g["distance"] == 1
    assert g["temperature"] == "Fierbinte"
    assert 0 <= g["closeness"] <= 100
    assert body["attempts"] == 1
    assert body["won"] is False
    assert "target" not in body


def test_winning_playthrough_reveals_target() -> None:
    c = make_client()
    gid = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()["game_id"]
    # one cold-ish guess first, then the exact target (accent-insensitive)
    c.post(f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Banat"})
    res = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        json={"text": "Dunarea"},
    )
    body = res.json()
    assert body["ok"] is True
    assert body["won"] is True
    assert body["guess"]["distance"] == 0
    assert body["guess"]["temperature"] == "Gasit"
    assert body["guess"]["closeness"] == 100
    assert body["target"]["id"] == "n_dunarea"
    # guesses are sorted best-first: the winning guess leads.
    assert body["guesses"][0]["distance"] == 0


def test_duplicate_guess_not_double_counted() -> None:
    c = make_client()
    gid = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()["game_id"]
    c.post(f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Banat"})
    res = c.post(f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Banat"})
    assert res.json()["attempts"] == 1


def test_giveup_reveals_target() -> None:
    c = make_client()
    gid = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()["game_id"]
    res = c.post(f"/api/wordgames/contexto/games/{gid}/giveup")
    assert res.status_code == 200
    body = res.json()
    assert body["gave_up"] is True
    assert body["target"]["id"] == "n_dunarea"
    # cannot guess after giving up
    after = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Banat"}
    )
    assert after.status_code == 400


def test_get_state_keeps_target_hidden() -> None:
    c = make_client()
    gid = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()["game_id"]
    res = c.get(f"/api/wordgames/contexto/games/{gid}")
    assert res.status_code == 200
    assert "target" not in res.json()


def test_unknown_game_404() -> None:
    c = make_client()
    assert c.get("/api/wordgames/contexto/games/nope").status_code == 404
    assert (
        c.post(
            "/api/wordgames/contexto/games/nope/guess", json={"text": "Banat"}
        ).status_code
        == 404
    )
    assert c.post("/api/wordgames/contexto/games/nope/giveup").status_code == 404
