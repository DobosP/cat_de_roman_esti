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


# --------------------------------------------------------------------- new: difficulty


def test_create_defaults_to_normal_and_exposes_difficulty() -> None:
    c = make_client()
    body = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()
    assert body["difficulty"] == "normal"
    assert "daily" not in body  # only present for daily challenges


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_difficulty_accepted_and_reachable(difficulty: str) -> None:
    c = make_client()
    body = c.post(
        "/api/wordgames/contexto/games",
        params={"seed": SEED, "difficulty": difficulty},
    ).json()
    assert body["difficulty"] == difficulty
    # every tier (incl. obscure "greu") still yields a richly reachable target
    assert body["reachable_count"] >= 120


def test_unknown_difficulty_falls_back_to_normal() -> None:
    c = make_client()
    body = c.post(
        "/api/wordgames/contexto/games",
        params={"seed": SEED, "difficulty": "imposibil"},
    ).json()
    assert body["difficulty"] == "normal"


# ------------------------------------------------------------------------- new: daily


def test_daily_is_deterministic_and_echoed() -> None:
    c = make_client()
    date = "2026-06-21"
    a = c.post("/api/wordgames/contexto/games", params={"daily": date})
    b = c.post("/api/wordgames/contexto/games", params={"daily": date})
    assert a.status_code == 200 and b.status_code == 200
    abody, bbody = a.json(), b.json()
    # same date -> same instance: reveal the secret via giveup and compare.
    ta = c.post(f"/api/wordgames/contexto/games/{abody['game_id']}/giveup").json()
    tb = c.post(f"/api/wordgames/contexto/games/{bbody['game_id']}/giveup").json()
    assert ta["target"]["id"] == tb["target"]["id"]
    assert abody["daily"] == date
    assert ta["daily"] == date


def test_daily_differs_by_date() -> None:
    c = make_client()
    g1 = c.post("/api/wordgames/contexto/games", params={"daily": "2026-06-21"}).json()
    g2 = c.post("/api/wordgames/contexto/games", params={"daily": "2026-09-09"}).json()
    t1 = c.post(f"/api/wordgames/contexto/games/{g1['game_id']}/giveup").json()
    t2 = c.post(f"/api/wordgames/contexto/games/{g2['game_id']}/giveup").json()
    # Overwhelmingly likely to differ across these two unrelated dates.
    assert t1["target"]["id"] != t2["target"]["id"]


# --------------------------------------------------------------- new: score and share


def test_win_includes_score_and_share() -> None:
    c = make_client()
    gid = c.post(
        "/api/wordgames/contexto/games", params={"seed": SEED}
    ).json()["game_id"]
    c.post(f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Banat"})
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Dunarea"}
    ).json()
    assert body["won"] is True
    # 2 attempts -> 1000 - 60 = 940
    assert body["score"] == 940
    share = body["share"]
    assert "Cald sau Rece" in share
    assert "2 incercari" in share
    # one emoji square per guess + the bullseye for the win
    assert "🎯" in share
    lines = share.splitlines()
    assert lines[0] == "cat_de_roman_esti · Cald sau Rece"


def test_score_rewards_fewer_attempts() -> None:
    c = make_client()
    gid = c.post(
        "/api/wordgames/contexto/games", params={"seed": SEED}
    ).json()["game_id"]
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess", json={"text": "Dunarea"}
    ).json()
    assert body["won"] is True
    assert body["score"] == 1000  # solved on the first attempt


def test_daily_win_share_includes_date() -> None:
    c = make_client()
    date = "2026-06-21"
    gid = c.post(
        "/api/wordgames/contexto/games", params={"daily": date}
    ).json()["game_id"]
    # reveal the secret, then guess it to win cleanly
    target = c.post(f"/api/wordgames/contexto/games/{gid}/giveup")
    # giveup ends the game; start a fresh daily and win it via the revealed label.
    label = target.json()["target"]["label"]
    gid2 = c.post(
        "/api/wordgames/contexto/games", params={"daily": date}
    ).json()["game_id"]
    body = c.post(
        f"/api/wordgames/contexto/games/{gid2}/guess", json={"text": label}
    ).json()
    assert body["won"] is True
    assert date in body["share"]


def test_no_score_or_share_before_win() -> None:
    c = make_client()
    body = c.post("/api/wordgames/contexto/games", params={"seed": SEED}).json()
    assert "score" not in body
    assert "share" not in body
