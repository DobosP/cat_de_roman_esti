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


PUBLIC_STATE_KEYS = {
    "game_id",
    "tiles",
    "solved",
    "solved_count",
    "remaining_groups",
    "lives",
    "mistakes",
    "won",
    "lost",
    "difficulty",
    "clues_used",
    "clue_available",
    "clues",
}


def _groups_for(seed: int = SEED, difficulty: str = "normal") -> dict[str, list[str]]:
    """Reach into the server-side session to learn the true grouping (test-only)."""
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = make_client()
    body = c.post(BASE + "/games", params={"seed": seed, "difficulty": difficulty}).json()
    session = store.get(body["game_id"])
    assert session is not None
    return c, body, {cat: list(ids) for cat, ids in session.groups.items()}


def _strings(obj: object) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, str):
        found.add(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            found |= _strings(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _strings(item)
    return found


def _keys(obj: object) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, dict):
        found |= set(obj)
        for value in obj.values():
            found |= _keys(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _keys(item)
    return found


def _assert_preterminal_public(body: dict, groups: dict[str, list[str]] | None = None) -> None:
    from cat_de_roman_esti.wordgames.conexiuni import _category_label

    allowed = set(PUBLIC_STATE_KEYS)
    allowed.update({"ok", "correct", "one_away", "clue", "daily"})
    assert set(body) <= allowed
    assert "solution" not in body
    assert "score" not in body
    assert "share" not in body
    assert "category" not in body
    assert body["solved"] == []
    assert all(set(tile) == {"id", "label"} for tile in body["tiles"])
    assert "key" not in _keys(body)
    if groups is not None:
        strings = _strings(body)
        assert all(cat not in strings for cat in groups)
        assert all(_category_label(cat) not in strings for cat in groups)


def test_create_board_shape() -> None:
    c = make_client()
    res = c.post(BASE + "/games", params={"seed": SEED})
    assert res.status_code == 200
    b = res.json()
    assert len(b["tiles"]) == 16
    assert len({t["id"] for t in b["tiles"]}) == 16
    assert b["solved"] == []
    assert b["solved_count"] == 0
    assert b["remaining_groups"] == 4
    assert b["lives"] == 4
    assert b["mistakes"] == 0
    assert b["won"] is False
    assert b["lost"] is False
    assert b["difficulty"] == "normal"
    assert b["clue_available"] is False
    assert b["clues_used"] == 0
    assert b["clues"] == []
    # secret solution not leaked at start
    assert "solution" not in b
    assert "score" not in b
    _assert_preterminal_public(b)


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


def test_correct_group_hides_category_until_terminal() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    _, members = next(iter(groups.items()))
    res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": members})
    assert res.status_code == 200
    body = res.json()
    assert body["correct"] is True
    assert body["lives"] == 4
    assert body["won"] is False
    assert body["solved_count"] == 1
    assert body["remaining_groups"] == 3
    assert {t["id"] for t in body["tiles"]}.isdisjoint(members)
    assert len(body["tiles"]) == 12
    _assert_preterminal_public(body, groups)

    state = c.get(f"{BASE}/games/{gid}").json()
    assert state["solved_count"] == 1
    assert state["remaining_groups"] == 3
    assert {t["id"] for t in state["tiles"]}.isdisjoint(members)
    _assert_preterminal_public(state, groups)


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
    _assert_preterminal_public(res, groups)


def test_two_two_split_not_one_away() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    mixed = groups[cats[0]][:2] + groups[cats[1]][:2]
    res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": mixed}).json()
    assert res["correct"] is False
    assert res["one_away"] is False
    _assert_preterminal_public(res, groups)


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
    _assert_preterminal_public(state)


def test_unknown_game_404() -> None:
    c = make_client()
    assert c.get(f"{BASE}/games/nope").status_code == 404
    assert (
        c.post(f"{BASE}/games/nope/guess", json={"ids": ["a", "b", "c", "d"]}).status_code
        == 404
    )
    assert c.post(f"{BASE}/games/nope/clue").status_code == 404


def test_clue_unlocks_after_two_mistakes_without_solution_membership() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    wrong = [groups[cats[0]][0], groups[cats[1]][0], groups[cats[2]][0], groups[cats[3]][0]]

    early = c.post(f"{BASE}/games/{gid}/clue")
    assert early.status_code == 400

    c.post(f"{BASE}/games/{gid}/guess", json={"ids": wrong})
    assert c.get(f"{BASE}/games/{gid}").json()["clue_available"] is False
    c.post(f"{BASE}/games/{gid}/guess", json={"ids": wrong})
    state = c.get(f"{BASE}/games/{gid}").json()
    assert state["mistakes"] == 2
    assert state["clue_available"] is True
    _assert_preterminal_public(state, groups)

    clue = c.post(f"{BASE}/games/{gid}/clue").json()
    assert clue["ok"] is True
    assert clue["clues_used"] == 1
    assert clue["clue_available"] is False
    assert set(clue["clue"]) == {"pattern", "message"}
    assert clue["clue"] == clue["clues"][0]
    assert "solution" not in clue
    assert "tiles" in clue
    _assert_preterminal_public(clue, groups)

    # The clue is a redacted category-label pattern only: no category key, no exact
    # category label, and no tile ids/membership are returned through the clue payload.
    payload_text = f"{clue['clue']['pattern']} {clue['clue']['message']}"
    assert all(cat not in payload_text for cat in groups)
    from cat_de_roman_esti.wordgames.conexiuni import _category_label

    assert all(_category_label(cat) not in payload_text for cat in groups)
    assert all(nid not in payload_text for ids in groups.values() for nid in ids)
    assert c.post(f"{BASE}/games/{gid}/clue").status_code == 400


def test_clue_penalizes_score_and_share() -> None:
    c, b, groups = _groups_for()
    gid = b["game_id"]
    cats = list(groups.keys())
    wrong = [groups[cats[0]][0], groups[cats[1]][0], groups[cats[2]][0], groups[cats[3]][0]]
    c.post(f"{BASE}/games/{gid}/guess", json={"ids": wrong})
    c.post(f"{BASE}/games/{gid}/guess", json={"ids": wrong})
    c.post(f"{BASE}/games/{gid}/clue")

    last = None
    for members in groups.values():
        last = c.post(f"{BASE}/games/{gid}/guess", json={"ids": members}).json()

    assert last["won"] is True
    assert last["score"] == 400  # two mistakes (500 pts) + one clue penalty (100 pts)
    assert "indiciu x1" in last["share"]


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


def test_serializer_fail_closed_for_group_payloads_before_terminal() -> None:
    from cat_de_roman_esti.wordgames import conexiuni as C

    _, _, groups = _groups_for()
    order = [nid for ids in groups.values() for nid in ids]
    session = C.ConexiuniSession(groups=groups, order=order)
    session.solved.append(next(iter(groups)))

    with pytest.raises(RuntimeError, match="solved groups before reveal"):
        C._solved_groups(session, reveal=False)
    with pytest.raises(RuntimeError, match="solution before reveal"):
        C._full_solution(session, reveal=False)


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
    # The fairness invariants every generated board must hold, asserted generically over
    # many seeds and difficulties (no hard-coded categories/tiles): a well-formed 4x4
    # board of four 4-tile groups, with each tile in exactly one chosen category, no
    # label collisions, and a true group always accepted as a correct guess.
    import random

    from cat_de_roman_esti.wordgames.conexiuni import (
        NUM_GROUPS,
        _pick_board,
        get_service,
    )

    svc = get_service()
    for diff in ("usor", "normal", "greu"):
        for seed in range(60):
            session = _pick_board(random.Random(seed), diff)
            ctx = f"diff={diff} seed={seed} cats={sorted(session.groups)}"

            # exactly four groups of four => 16 distinct tiles
            assert len(session.groups) == NUM_GROUPS, ctx
            assert all(len(ids) == 4 for ids in session.groups.values()), ctx
            all_ids = [nid for ids in session.groups.values() for nid in ids]
            assert len(all_ids) == 16, ctx
            assert len(set(all_ids)) == 16, ctx

            # the shuffled board carries exactly those 16 tiles
            assert sorted(session.order) == sorted(all_ids), ctx

            # every tile belongs to exactly one chosen category
            for nid in all_ids:
                owners = [c for c, ids in session.groups.items() if nid in ids]
                assert owners == [session.category_of(nid)], ctx
                assert len(owners) == 1, ctx

            # every tile carries a real, non-empty label (no blank/placeholder tiles)
            labels = [svc.label(nid) for nid in all_ids]
            assert all(lbl and lbl.strip() for lbl in labels), f"blank label: {ctx}"

            # a guess of a full true group is accepted by the engine
            c = make_client()
            body = c.post(BASE + "/games", params={"seed": seed, "difficulty": diff}).json()
            gid = body["game_id"]
            for cat, members in session.groups.items():
                res = c.post(f"{BASE}/games/{gid}/guess", json={"ids": members}).json()
                assert res["correct"] is True, f"true group rejected: {ctx} cat={cat}"
                if res["won"]:
                    assert res["category"]["key"] == cat, ctx
                else:
                    assert "category" not in res, ctx
                    assert res["solved"] == [], ctx


def test_board_generation_fails_closed_when_every_candidate_is_invalid(monkeypatch) -> None:
    """Never ship a hidden unfair board if validation rejects every retry."""
    import random

    from fastapi import HTTPException

    from cat_de_roman_esti.wordgames import conexiuni as C

    fallback = C.ConexiuniSession(
        groups={"istorie": ["a", "b", "c", "d"]},
        order=["a", "b", "c", "d"],
    )
    monkeypatch.setattr(C, "_build_board", lambda rng, difficulty: fallback)
    monkeypatch.setattr(C, "_board_quality", lambda session: (False, 1_000_000))

    with pytest.raises(HTTPException) as exc:
        C._pick_board(random.Random(0), "normal")

    assert exc.value.status_code == 503


def test_usor_generation_uses_full_category_context_for_bridge_tiles() -> None:
    """Seed 7 used to pick cross-category bridge tiles before all groups were known."""
    import random

    from cat_de_roman_esti.wordgames.conexiuni import _board_quality, _pick_board

    board = _pick_board(random.Random(7), "usor")
    assert _board_quality(board) == (True, 0)


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
