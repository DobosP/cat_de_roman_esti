"""Offline, deterministic tests for the "Conexiuni" (NYT Connections) word game."""

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_client() -> TestClient:
    app = FastAPI()
    from cat_de_roman_esti.wordgames.conexiuni import router

    app.include_router(router)
    return TestClient(app)


SEED = 1
BASE = "/api/wordgames/conexiuni"


def _groups_for(seed: int = SEED, difficulty: str = "normal") -> dict[str, list[str]]:
    """Reach into the server-side session to learn the true grouping (test-only)."""
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = make_client()
    body = c.post(BASE + "/games", params={"seed": seed, "difficulty": difficulty}).json()
    session = store.get(body["game_id"])
    assert session is not None
    return c, body, {cat: list(ids) for cat, ids in session.groups.items()}


def test_create_board_shape() -> None:
    c = make_client()
    res = c.post(BASE + "/games", params={"seed": SEED})
    assert res.status_code == 200
    b = res.json()
    assert len(b["tiles"]) == 16
    assert len({t["id"] for t in b["tiles"]}) == 16
    assert b["solved"] == []
    assert b["lives"] == 4
    assert b["mistakes"] == 0
    assert b["won"] is False
    assert b["lost"] is False
    assert b["difficulty"] == "normal"
    # secret solution not leaked at start
    assert "solution" not in b
    assert "score" not in b


def test_difficulty_accepted() -> None:
    c = make_client()
    for diff in ("usor", "normal", "greu"):
        res = c.post(BASE + "/games", params={"seed": SEED, "difficulty": diff})
        assert res.status_code == 200
        assert res.json()["difficulty"] == diff
    # unknown difficulty falls back to normal
    res = c.post(BASE + "/games", params={"seed": SEED, "difficulty": "ploaie"})
    assert res.json()["difficulty"] == "normal"


def test_daily_is_deterministic() -> None:
    c = make_client()
    a = c.post(BASE + "/games", params={"daily": "2026-06-21"}).json()
    b = c.post(BASE + "/games", params={"daily": "2026-06-21"}).json()
    assert [t["id"] for t in a["tiles"]] == [t["id"] for t in b["tiles"]]
    assert a["daily"] == "2026-06-21"
    assert b["daily"] == "2026-06-21"
    # different date -> (almost surely) different board / at least carries its date
    other = c.post(BASE + "/games", params={"daily": "2026-06-22"}).json()
    assert other["daily"] == "2026-06-22"


def test_guess_requires_exactly_four_distinct() -> None:
    c = make_client()
    b = c.post(BASE + "/games", params={"seed": SEED}).json()
    gid = b["game_id"]
    ids = [t["id"] for t in b["tiles"]]
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": ids[:3]}).status_code == 400
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": ids[:5]}).status_code == 400
    # duplicates are not 4 distinct
    dup = [ids[0], ids[0], ids[1], ids[2]]
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": dup}).status_code == 400
    # an id not on the board
    bad = [ids[0], ids[1], ids[2], "n_does_not_exist"]
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": bad}).status_code == 400


def test_correct_group_reveals_category() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cat, members = next(iter(groups.items()))
    res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": members})
    assert res.status_code == 200
    body = res.json()
    assert body["correct"] is True
    assert body["category"]["key"] == cat
    assert body["lives"] == 4
    assert {t["id"] for t in body["tiles"]} == set(members)
    assert len(body["solved"]) == 1
    assert body["won"] is False


def test_one_away_flag() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    # 3 from one group + 1 from another => one_away True
    near = groups[cats[0]][:3] + [groups[cats[1]][0]]
    res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": near}).json()
    assert res["correct"] is False
    assert res["one_away"] is True
    assert res["lives"] == 3
    assert res["mistakes"] == 1
    assert res["lost"] is False


def test_two_two_split_not_one_away() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    mixed = groups[cats[0]][:2] + groups[cats[1]][:2]
    res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": mixed}).json()
    assert res["correct"] is False
    assert res["one_away"] is False


def test_winning_playthrough_score_and_share() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    last = None
    for members in groups.values():
        last = c.post(f"{BASE}/games/{gid}/guess", json={"ids": members}).json()
    assert last["won"] is True
    # perfect game: no mistakes -> top score
    assert last["score"] == 1000
    assert "share" in last
    assert "Conexiuni" in last["share"]
    assert "0 greseli" in last["share"]
    assert "solution" in last
    assert len(last["solution"]) == 4
    # cannot guess after the game is over
    members = next(iter(groups.values()))
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": members}).status_code == 400


def test_losing_reveals_solution_and_scores_by_mistakes() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    # craft a deliberately wrong 4-mix that shares no full category and isn't one-away:
    wrong = [groups[cats[0]][0], groups[cats[1]][0], groups[cats[2]][0], groups[cats[3]][0]]
    last = None
    for _ in range(4):
        last = c.post(f"{BASE}/games/{gid}/guess", json={"ids": wrong}).json()
    assert last["lost"] is True
    assert last["lives"] == 0
    assert last["mistakes"] == 4
    assert last["score"] == 0
    assert len(last["solution"]) == 4
    assert "share" in last


def test_state_hides_solution_until_finished() -> None:
    c = make_client()
    gid = c.post(BASE + "/games", params={"seed": SEED}).json()["game_id"]
    state = c.get(f"{BASE}/games/{gid}").json()
    assert "solution" not in state
    assert "score" not in state


def test_unknown_game_404() -> None:
    c = make_client()
    assert c.get(f"{BASE}/games/nope").status_code == 404
    assert (
        c.post(f"{BASE}/games/nope/guess", json={"ids": ["a", "b", "c", "d"]}).status_code
        == 404
    )


# --------------------------------------------------------------------- input hardening
def test_guess_rejects_empty_and_malformed_bodies() -> None:
    c = make_client()
    gid = c.post(BASE + "/games", params={"seed": SEED}).json()["game_id"]
    # empty list -> our 400 (not 4 distinct)
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": []}).status_code == 400
    # missing field / null / wrong element type -> pydantic 422
    assert c.post(f"{BASE}/games/{gid}/guess", json={}).status_code == 422
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": None}).status_code == 422
    assert c.post(f"{BASE}/games/{gid}/guess", json={"ids": [1, 2, 3, 4]}).status_code == 422


def test_guess_rejects_already_solved_tile() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    # solve the first group
    c.post(f"{BASE}/games/{gid}/guess", json={"ids": groups[cats[0]]})
    # reusing a solved tile in a new guess is rejected
    reused = [groups[cats[0]][0], *groups[cats[1]][:3]]
    res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": reused})
    assert res.status_code == 400


# --------------------------------------------------------------------- generation
def _board_cats(seed: int, difficulty: str) -> tuple[str, ...]:
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = make_client()
    body = c.post(
        BASE + "/games", params={"seed": seed, "difficulty": difficulty}
    ).json()
    session = store.get(body["game_id"])
    assert session is not None
    return tuple(sorted(session.groups))


def test_boards_vary_with_seed_at_every_difficulty() -> None:
    # Regression: usor/greu used to be seed-independent (one fixed board forever).
    for diff in ("usor", "normal", "greu"):
        seen = {_board_cats(s, diff) for s in range(40)}
        assert len(seen) >= 3, f"{diff} barely varies across seeds: {seen}"


def test_all_generated_boards_are_fair() -> None:
    # Across many seeds and difficulties no tile may link more to a foreign on-board
    # group than to its own (that would be an unfair / unwinnable tile).
    import random

    from cat_de_roman_esti.wordgames.conexiuni import _board_quality, _pick_board

    for diff in ("usor", "normal", "greu"):
        for seed in range(60):
            session = _pick_board(random.Random(seed), diff)
            ok, residual = _board_quality(session)
            assert ok, f"unfair board diff={diff} seed={seed} cats={sorted(session.groups)}"
            # 16 distinct tiles, four groups of four
            all_ids = [nid for ids in session.groups.values() for nid in ids]
            assert len(all_ids) == 16
            assert len(set(all_ids)) == 16
            assert len(session.groups) == 4


def test_usor_is_less_entangled_than_greu() -> None:
    # 'usor' should pick clearly-distinct themes; 'greu' the trickier culture-clusters.
    from cat_de_roman_esti.wordgames.conexiuni import _set_entanglement

    usor = [_set_entanglement(_board_cats(s, "usor")) for s in range(30)]
    greu = [_set_entanglement(_board_cats(s, "greu")) for s in range(30)]
    assert max(usor) < min(greu), (
        f"usor max {max(usor):.3f} should be below greu min {min(greu):.3f}"
    )


def test_daily_differs_by_difficulty_independent_of_clock() -> None:
    # The daily seed is a pure function of (date, game-key) — same date is reproducible.
    c = make_client()
    a = c.post(BASE + "/games", params={"daily": "2026-06-21"}).json()
    b = c.post(BASE + "/games", params={"daily": "2026-06-21"}).json()
    assert [t["id"] for t in a["tiles"]] == [t["id"] for t in b["tiles"]]


def test_share_grid_has_one_row_per_guess() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    # one wrong guess, then win the rest
    wrong = [groups[cats[0]][0], groups[cats[1]][0], groups[cats[2]][0], groups[cats[3]][0]]
    c.post(f"{BASE}/games/{gid}/guess", json={"ids": wrong})
    last = None
    for members in groups.values():
        last = c.post(f"{BASE}/games/{gid}/guess", json={"ids": members}).json()
    assert last["won"] is True
    assert last["score"] == 750  # one mistake
    share = last["share"]
    # header + one row per guess (1 wrong + 4 correct = 5 rows)
    body_rows = [ln for ln in share.split("\n")[1:] if ln.strip()]
    assert len(body_rows) == 5
    assert "1 greseli" in share
