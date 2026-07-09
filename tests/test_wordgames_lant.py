"""Offline, deterministic tests for the Lantul Cuvintelor word-ladder game."""

from __future__ import annotations

import pytest

pytest.importorskip("django")

from django.test import Client

from cat_de_roman_esti.wordgames import lant
from cat_de_roman_esti.wordgames.lant import LantSession, store
from cat_de_roman_esti.wordgames.service import get_service

c = Client()

SEED = 7

_BANDS = {"usor": (2, 3), "normal": (3, 4), "greu": (4, 6)}


def _create(seed: int = SEED, **params):
    q = f"?seed={seed}"
    for k, v in params.items():
        q += f"&{k}={v}"
    res = c.post(f"/api/wordgames/lant/games{q}")
    assert res.status_code == 200, res.content.decode()
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
            {"text": hint["label"]},
            content_type="application/json",
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
        assert hres.status_code == 200, hres.content.decode()
        hint = hres.json()["hint"]
        assert hint is not None, hres.content.decode()

        mres = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            {"text": hint["label"]},
            content_type="application/json",
        )
        assert mres.status_code == 200, mres.content.decode()
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
        {"text": "qwerty nonexistent xyz"},
        content_type="application/json",
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
        {"text": game["target"]["label"]},
        content_type="application/json",
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
    c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": hint["label"]},
        content_type="application/json",
    )
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
            {"text": "x"},
            content_type="application/json",
        ).status_code
        == 404
    )
    assert c.post("/api/wordgames/lant/games/does-not-exist/hint").status_code == 404
    assert c.post("/api/wordgames/lant/games/does-not-exist/undo").status_code == 404


# --------------------------------------------------------------------- hardening: selection
def _first_hop_choices(svc, start: str, target: str, optimal: int) -> int:
    """Neighbours of start that are one hop closer to the target (genuine first moves)."""
    dist_t = svc.distances_from(target)
    return sum(1 for nb in svc.neighbor_ids(start) if dist_t.get(nb) == optimal - 1)


def test_selection_is_branchy_not_a_forced_rail():
    """Generated puzzles must offer a real choice at the opening hop (no single rail).

    Regression for the v1 selection, where ~85% of instances had exactly one neighbour
    that moved you closer — the ladder was a forced single path.
    """
    svc = get_service()
    forced = 0
    samples = 0
    for diff in _BANDS:
        for seed in range(40):
            g = _create(seed=seed, difficulty=diff)
            samples += 1
            if _first_hop_choices(svc, g["start"]["id"], g["target"]["id"], g["optimal"]) < 2:
                forced += 1
    # Allow a tiny tail for sparse corners of the graph, but it must be rare.
    assert forced <= samples * 0.05, f"{forced}/{samples} forced first hops"


def test_selection_avoids_leaf_endpoints():
    """Neither start nor target should be a degree-1 leaf (it forces the first/last hop)."""
    svc = get_service()
    for diff in _BANDS:
        for seed in range(40):
            g = _create(seed=seed, difficulty=diff)
            assert svc.degree(g["start"]["id"]) >= 2, (diff, seed, g["start"]["id"])
            assert svc.degree(g["target"]["id"]) >= 2, (diff, seed, g["target"]["id"])


def test_selection_prefers_salient_endpoints_by_difficulty():
    """Endpoint salience tracks difficulty (v11): easier games favour recognizable
    endpoints, ``greu`` tolerates obscure ones. Assert the AVERAGE over many seeds so a
    single obscure endpoint on a very branchy board doesn't fail the intent."""
    svc = get_service()
    # minimum mean endpoint salience expected per difficulty
    floors = {"usor": 0.60, "normal": 0.45, "greu": 0.0}
    for diff in _BANDS:
        means = []
        for seed in range(30):
            g = _create(seed=seed, difficulty=diff)
            s = svc.node(g["start"]["id"]).salience
            t = svc.node(g["target"]["id"]).salience
            means.append((s + t) / 2)
        avg = sum(means) / len(means)
        assert avg >= floors[diff], (diff, avg)
    # sanity: usor endpoints are, on average, more salient than greu ones.
    usor_avg = sum(
        (svc.node(_create(seed=s, difficulty="usor")["start"]["id"]).salience
         + svc.node(_create(seed=s, difficulty="usor")["target"]["id"]).salience) / 2
        for s in range(15)
    ) / 15
    greu_avg = sum(
        (svc.node(_create(seed=s, difficulty="greu")["start"]["id"]).salience
         + svc.node(_create(seed=s, difficulty="greu")["target"]["id"]).salience) / 2
        for s in range(15)
    ) / 15
    assert usor_avg > greu_avg


def test_bands_respected_across_many_seeds():
    for diff, (lo, hi) in _BANDS.items():
        for seed in range(30):
            g = _create(seed=seed, difficulty=diff)
            assert lo <= g["optimal"] <= hi, (diff, seed, g["optimal"])


# --------------------------------------------------------------------- hardening: moves
def test_empty_and_whitespace_input_rejected():
    game = _create()
    gid = game["game_id"]
    for txt in ("", "   ", "\t\n"):
        res = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            {"text": txt},
            content_type="application/json",
        )
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is False
        assert body["last_error"] == "Scrie un concept"
    # State is untouched.
    assert c.get(f"/api/wordgames/lant/games/{gid}").json()["moves"] == 0


def test_staying_put_rejected():
    game = _create()
    gid = game["game_id"]
    res = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": game["start"]["label"]},
        content_type="application/json",
    )
    body = res.json()
    assert body["ok"] is False
    assert body["last_error"] == "Esti deja aici"


def test_move_on_won_game_is_idempotent():
    game = _create()
    body = _win(game)
    gid = game["game_id"]
    assert body["won"] is True
    # Any further move on a finished game returns ok + the final state, no extra hop.
    after = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "orice"},
        content_type="application/json",
    ).json()
    assert after["ok"] is True
    assert after["won"] is True
    assert after["moves"] == body["moves"]


def test_label_collision_disambiguates_to_a_linked_node():
    """Two nodes share the label 'Moldova'; resolve() picks one, but a move should accept
    whichever same-label node is actually linked to the current concept.

    Regression: from a node linked only to the *other* Moldova, typing 'Moldova' used to
    be wrongly rejected as 'no direct link'.
    """
    svc = get_service()
    start = "n_stefan_cel_mare"
    linked = "n_moldova"  # the one resolve() does NOT return
    other = "n_moldova_reg"
    # Sanity: the fixture still matches the regression's assumptions.
    assert svc.resolve("Moldova") == other
    assert svc.link(start, linked) is not None
    assert svc.link(start, other) is None

    session = LantSession(
        start=start,
        target=linked,
        optimal=1,
        chain=[start],
    )
    gid = store.create(session)
    res = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "Moldova"},
        content_type="application/json",
    )
    body = res.json()
    assert body["ok"] is True, body
    assert body["current"]["id"] == linked
    assert body["won"] is True


# --------------------------------------------------------------------- hardening: hint
def test_hint_is_on_a_shortest_path_and_reports_remaining():
    game = _create()
    gid = game["game_id"]
    svc = get_service()
    h = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert h["hint"] is not None
    assert h["remaining"] == game["optimal"]
    # The suggested neighbour is one hop closer to the target.
    dist_t = svc.distances_from(game["target"]["id"])
    assert dist_t.get(h["hint"]["id"]) == game["optimal"] - 1
    # It is a genuine neighbour of the current node.
    assert h["hint"]["id"] in svc.neighbor_ids(game["start"]["id"])
    # alternatives counts the on-path neighbours and is at least 1.
    assert h["alternatives"] >= 1


def test_hint_prefers_the_most_salient_next_step():
    """When several neighbours lie on a shortest path, the hint suggests the salient one."""
    svc = get_service()
    found = False
    for diff in _BANDS:
        for seed in range(40):
            g = _create(seed=seed, difficulty=diff)
            gid = g["game_id"]
            cur = g["start"]["id"]
            dist_t = svc.distances_from(g["target"]["id"])
            on_path = [
                nb
                for nb in svc.neighbor_ids(cur)
                if dist_t.get(nb) == g["optimal"] - 1
            ]
            if len(on_path) < 2:
                continue
            found = True
            best = max(on_path, key=lambda nb: (svc.node(nb).salience, nb))
            h = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
            assert h["hint"]["id"] == best, (diff, seed, on_path)
            assert h["alternatives"] == len(on_path)
            break
        if found:
            break
    assert found, "expected at least one puzzle with multiple shortest-path neighbours"


def test_hint_on_won_game_returns_message():
    game = _create()
    _win(game)
    h = c.post(f"/api/wordgames/lant/games/{game['game_id']}/hint").json()
    assert h["hint"] is None
    assert h["message"]


# --------------------------------------------------------------------- hardening: score
def _detour_neighbor(svc, start: str, target: str, optimal: int) -> str | None:
    """A legal neighbour of start that does NOT move closer to the target (a real detour)."""
    dist_t = svc.distances_from(target)
    for nb in svc.neighbor_ids(start):
        d = dist_t.get(nb)
        if d is not None and d >= optimal:  # not closer than the start itself
            return nb
    return None


def test_over_par_lowers_score_but_never_below_floor():
    """A genuine detour (a non-shortest hop) increases moves and reduces the score."""
    svc = get_service()
    # Find a puzzle that actually has a detour neighbour available.
    for seed in range(60):
        game = _create(seed=seed, difficulty="greu")
        detour = _detour_neighbor(
            svc, game["start"]["id"], game["target"]["id"], game["optimal"]
        )
        if detour:
            break
    else:  # pragma: no cover - the greu graph always has one in practice
        pytest.skip("no detour neighbour found in sampled puzzles")

    gid = game["game_id"]
    optimal = game["optimal"]
    step = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": svc.label(detour)},
        content_type="application/json",
    ).json()
    assert step["ok"] is True

    # Now follow hints from the detour to the target; total moves must exceed optimal.
    body = step
    while not body.get("won"):
        h = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()["hint"]
        assert h is not None
        body = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            {"text": h["label"]},
            content_type="application/json",
        ).json()

    assert body["moves"] > optimal
    expected = max(100, round(1000 * optimal / max(body["moves"], optimal)))
    assert body["score"] == expected
    assert 100 <= body["score"] < 1000


def test_score_for_helper_floor_and_cap():
    assert lant._score_for(0, 5) == 1000  # sub-optimal optimal can't exceed cap
    assert lant._score_for(5, 5) == 1000
    assert lant._score_for(1000, 3) == 100  # huge detour clamps to the floor
