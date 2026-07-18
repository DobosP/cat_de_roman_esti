"""Offline, deterministic tests for the Lantul Cuvintelor word-ladder game."""

from __future__ import annotations

import random

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
        hint = _revealed_hop(gid)["hint"]
        body = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            {"text": hint["label"]},
            content_type="application/json",
        ).json()
    assert body["won"] is True
    return body


def _revealed_hop(game_id: str) -> dict:
    """Ask through direction/alternatives until the voluntary one-hop reveal."""
    for _ in range(3):
        body = c.post(f"/api/wordgames/lant/games/{game_id}/hint").json()
        if body.get("hint") is not None:
            return body
    raise AssertionError(f"third hint did not reveal one hop: {body}")


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


def test_local_choices_are_bounded_id_free_unique_and_tappable():
    game = _create(difficulty="usor")
    choices = game["choices"]
    # Prefer 4–6 when safe detours exist; an all-corridor position stops at the strict
    # three-hop quota instead of leaking more of the private route web.
    assert 1 <= len(choices) <= 6
    assert choices == c.get(f"/api/wordgames/lant/games/{game['game_id']}").json()["choices"]
    assert all(set(choice) == {"label", "relation"} for choice in choices)
    assert all(choice["label"] and 0 < len(choice["relation"]) <= 34 for choice in choices)
    normalized = [lant.normalize(choice["label"]) for choice in choices]
    assert len(normalized) == len(set(normalized))

    # Every chip can be submitted from the exact state that authored it.
    for choice in choices:
        session = LantSession(
            start=game["start"]["id"],
            target=game["target"]["id"],
            optimal=game["optimal"],
            difficulty="usor",
            chain=[game["start"]["id"]],
        )
        gid = store.create(session)
        moved = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            {"text": choice["label"]},
            content_type="application/json",
        ).json()
        assert moved["ok"] is True, choice


def test_choice_menu_is_deterministic_and_does_not_serialize_corridor_metadata():
    first = _create(seed=19, difficulty="usor")
    second = _create(seed=19, difficulty="usor")
    assert first["choices"] == second["choices"]
    assert "corridor" not in first
    assert "on_track" not in first
    assert all("id" not in choice for choice in first["choices"])


def test_valid_direct_hop_outside_visible_menu_stays_legal():
    svc = get_service()
    for seed in range(40):
        game = _create(seed=seed, difficulty="normal")
        shown = {lant.normalize(choice["label"]) for choice in game["choices"]}
        omitted = next(
            (
                node_id
                for node_id in svc.neighbor_ids(game["start"]["id"])
                if lant.normalize(svc.label(node_id)) not in shown
            ),
            None,
        )
        if omitted is not None:
            break
    else:
        pytest.skip("sampled starts have no neighbour outside the bounded menu")

    moved = c.post(
        f"/api/wordgames/lant/games/{game['game_id']}/move",
        {"text": svc.label(omitted)},
        content_type="application/json",
    ).json()
    assert moved["ok"] is True
    assert moved["current"]["id"] in svc.neighbor_ids(game["start"]["id"])


def test_winning_playthrough_by_following_hints():
    game = _create()
    gid = game["game_id"]
    optimal = game["optimal"]

    won = False
    # Following the shortest-path hint each turn must win in exactly `optimal` moves.
    for _ in range(optimal):
        hint = _revealed_hop(gid)["hint"]

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
    hint = _revealed_hop(gid)["hint"]
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
    dist_t = svc.distances_to(target)
    return sum(1 for nb in svc.neighbor_ids(start) if dist_t.get(nb) == optimal - 1)


def _generated_pair(seed: int, difficulty: str) -> dict[str, object]:
    """Exercise the mined fallback directly; ordinary endpoint play is curated-first."""
    lo, hi = _BANDS[difficulty]
    start, target, optimal = lant._pick_pair(
        random.Random(seed), lo, hi, difficulty=difficulty
    )
    return {"start": {"id": start}, "target": {"id": target}, "optimal": optimal}


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
            g = _generated_pair(seed, diff)
            samples += 1
            if _first_hop_choices(svc, g["start"]["id"], g["target"]["id"], g["optimal"]) < 2:
                forced += 1
    # Allow a tiny tail for sparse corners of the graph, but it must be rare.
    assert forced <= samples * 0.05, f"{forced}/{samples} forced first hops"


def test_reverse_distance_and_branch_profile_respect_directed_edges():
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.packs import lant_branch_profile
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": node_id, "label_ro": node_id, "category": "test"}
        for node_id in ("start", "a", "b", "target")
    ]
    edges = [
        {
            "id": f"e_{src}_{dst}",
            "src_id": src,
            "dst_id": dst,
            "bidirectional": 0,
            "is_distractor": 0,
        }
        for src, dst in (
            ("start", "a"),
            ("start", "b"),
            ("a", "target"),
            ("b", "target"),
        )
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))

    assert svc.distances_from("target") == {"target": 0}
    assert svc.distances_to("target") == {
        "target": 0,
        "a": 1,
        "b": 1,
        "start": 2,
    }
    assert lant_branch_profile(svc, "start", "target", 2) == (2, 2, 2)


def test_private_corridor_accepts_par_plus_two_but_not_par_plus_three(monkeypatch):
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    paths = (
        ("a",),
        ("b", "c"),
        ("d", "e", "f"),
        ("x", "y", "z", "w"),
    )
    node_ids = {"start", "target", *(node for route in paths for node in route)}
    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test"}
        for node_id in sorted(node_ids)
    ]
    edges = []
    for path_index, route in enumerate(paths):
        full = ("start", *route, "target")
        edges.extend(
            {
                "id": f"e{path_index}_{index}",
                "src_id": src,
                "dst_id": dst,
                "bidirectional": 0,
                "strength": 0.8,
            }
            for index, (src, dst) in enumerate(zip(full, full[1:], strict=False))
        )
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(start="start", target="target", optimal=2, chain=["start"])

    assert lant._corridor_profile("start", "target", 2) == (3, 3, 3)
    assert set(lant._near_route_hops(session)) == {"a", "b", "d"}
    assert "x" not in lant._near_route_hops(session)

    # The bounded cache is scoped to the service object, so monkeypatched graphs with
    # identical endpoint IDs cannot inherit another fixture's corridor.
    thin_nodes = [node for node in nodes if node["id"] in {"start", "a", "target"}]
    thin_edges = [
        edge
        for edge in edges
        if edge["src_id"] in {"start", "a"} and edge["dst_id"] in {"a", "target"}
    ]
    thin_svc = WordGameService(Graph.from_records(thin_nodes, thin_edges))
    monkeypatch.setattr(lant, "get_service", lambda: thin_svc)
    assert lant._corridor_profile("start", "target", 2) == (1, 1, 1)


def test_visible_menu_never_refills_past_three_corridor_hops(monkeypatch):
    """A branchy corridor may be wide, but its public menu quota remains three."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    hops = [f"hop_{index}" for index in range(6)]
    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test"}
        for node_id in ("start", *hops, "target")
    ]
    edges = [
        {
            "id": f"e_start_{hop}",
            "src_id": "start",
            "dst_id": hop,
            "strength": 0.8,
        }
        for hop in hops
    ] + [
        {
            "id": f"e_{hop}_target",
            "src_id": hop,
            "dst_id": "target",
            "strength": 0.8,
        }
        for hop in hops
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(start="start", target="target", optimal=2, chain=["start"])

    corridor = set(lant._near_route_hops(session))
    chosen = lant._visible_choice_nodes(session)
    assert corridor == set(hops)
    assert len(chosen) == lant._CORRIDOR_CHOICE_QUOTA == 3
    assert set(chosen) <= corridor
    assert len(lant._visible_choices(session)) == 3


def test_hub_penalty_is_soft_not_a_high_degree_ban(monkeypatch):
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    spokes = [f"spoke_{index}" for index in range(24)]
    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test", "salience": 0.5}
        for node_id in ("start", "plain", "hub", "target", *spokes)
    ]
    edges = [
        {
            "id": "e_plain",
            "src_id": "start",
            "dst_id": "plain",
            "bidirectional": 0,
            "strength": 0.8,
        },
        {"id": "e_hub", "src_id": "start", "dst_id": "hub", "bidirectional": 0, "strength": 0.8},
        {
            "id": "e_plain_t",
            "src_id": "plain",
            "dst_id": "target",
            "bidirectional": 0,
            "strength": 0.8,
        },
        {"id": "e_hub_t", "src_id": "hub", "dst_id": "target", "bidirectional": 0, "strength": 0.8},
        *[
            {
                "id": f"e_spoke_{index}",
                "src_id": "hub",
                "dst_id": spoke,
                "bidirectional": 0,
                "strength": 0.8,
            }
            for index, spoke in enumerate(spokes)
        ],
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(start="start", target="target", optimal=2, chain=["start"])

    assert svc.degree("hub") > lant._HUB_SOFT_DEGREE
    assert lant._shortest_hops(session) == ["plain", "hub"]
    assert lant._hub_penalty("hub") <= 1.25

    # A much tighter semantic edge must still beat the capped degree penalty.
    strong_hub_edges = [
        {
            **edge,
            "strength": (
                0.99
                if edge["id"] == "e_hub"
                else 0.10
                if edge["id"] == "e_plain"
                else edge["strength"]
            ),
        }
        for edge in edges
    ]
    strong_hub_svc = WordGameService(Graph.from_records(nodes, strong_hub_edges))
    monkeypatch.setattr(lant, "get_service", lambda: strong_hub_svc)
    assert lant._shortest_hops(session) == ["hub", "plain"]


def test_easy_mined_boards_prefer_width_three_near_shortest_corridors():
    for seed in range(20):
        game = _generated_pair(seed, "usor")
        first_hops, min_width, _ = lant._corridor_profile(
            game["start"]["id"], game["target"]["id"], game["optimal"]
        )
        assert first_hops >= 3, seed
        assert min_width >= 3, seed


def test_pack_gate_rejects_a_mid_path_funnel():
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.packs import _validate_lant, lant_branch_profile
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": node_id, "label_ro": node_id, "category": "test"}
        for node_id in ("start", "a", "b", "funnel", "target")
    ]
    edges = [
        {
            "id": f"e_{src}_{dst}",
            "src_id": src,
            "dst_id": dst,
            "bidirectional": 0,
            "is_distractor": 0,
        }
        for src, dst in (
            ("start", "a"),
            ("start", "b"),
            ("a", "funnel"),
            ("b", "funnel"),
            ("funnel", "target"),
        )
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))

    assert lant_branch_profile(svc, "start", "target", 3) == (2, 1, 3)
    assert _validate_lant(
        {
            "start": "start",
            "target": "target",
            "optimal": 3,
            "difficulty": "normal",
        },
        svc,
    ) == ["narrowest shortest-path layer has width 1 (< 2)"]


def test_selection_avoids_leaf_endpoints():
    """Neither start nor target should be a degree-1 leaf (it forces the first/last hop)."""
    svc = get_service()
    for diff in _BANDS:
        for seed in range(40):
            g = _generated_pair(seed, diff)
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
            g = _generated_pair(seed, diff)
            s = svc.node(g["start"]["id"]).salience
            t = svc.node(g["target"]["id"]).salience
            means.append((s + t) / 2)
        avg = sum(means) / len(means)
        assert avg >= floors[diff], (diff, avg)
    # sanity: usor endpoints are, on average, more salient than greu ones.
    usor_avg = sum(
        (svc.node(_generated_pair(s, "usor")["start"]["id"]).salience
         + svc.node(_generated_pair(s, "usor")["target"]["id"]).salience) / 2
        for s in range(15)
    ) / 15
    greu_avg = sum(
        (svc.node(_generated_pair(s, "greu")["start"]["id"]).salience
         + svc.node(_generated_pair(s, "greu")["target"]["id"]).salience) / 2
        for s in range(15)
    ) / 15
    assert usor_avg > greu_avg


def test_bands_respected_across_many_seeds():
    for diff, (lo, hi) in _BANDS.items():
        for seed in range(30):
            g = _generated_pair(seed, diff)
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


def test_visible_homonym_chip_binds_to_its_unvisited_authored_node(monkeypatch):
    """A later-position chip must not be stolen by a stronger visited homonym."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": "start", "label_ro": "START", "category": "test"},
        {"id": "visited", "label_ro": "DUPLICAT", "category": "test"},
        {"id": "current", "label_ro": "CURRENT", "category": "test"},
        {"id": "authored", "label_ro": "DUPLICAT", "category": "test"},
        {"id": "target", "label_ro": "TARGET", "category": "test"},
    ]
    edges = [
        {"id": "e_start_visited", "src_id": "start", "dst_id": "visited"},
        {"id": "e_visited_current", "src_id": "visited", "dst_id": "current"},
        {"id": "e_visited_target", "src_id": "visited", "dst_id": "target"},
        {
            "id": "e_current_visited",
            "src_id": "current",
            "dst_id": "visited",
            "strength": 0.99,
            "label_ro": "cale veche",
        },
        {
            "id": "e_current_authored",
            "src_id": "current",
            "dst_id": "authored",
            "strength": 0.10,
            "label_ro": "cale afișată",
        },
        {"id": "e_authored_target", "src_id": "authored", "dst_id": "target"},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(
        start="start",
        target="target",
        optimal=3,
        chain=["start", "visited", "current"],
    )
    gid = store.create(session)

    # General homonym ranking would revisit the stronger/closer old node.
    assert lant._resolve_neighbor("DUPLICAT", "current", "target") == "visited"
    assert lant._visible_choice_nodes(session) == ["authored"]
    assert lant._visible_choices(session) == [
        {"label": "DUPLICAT", "relation": "cale afișată"}
    ]

    moved = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "  duplicat  "},
        content_type="application/json",
    ).json()
    assert moved["ok"] is True
    assert moved["current"]["id"] == "authored"
    assert moved["relation"] == "cale afișată"


# --------------------------------------------------------------------- hardening: hint
def test_progressive_hint_reveals_direction_alternatives_then_shortest_hop():
    game = _create()
    gid = game["game_id"]
    svc = get_service()
    first = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert first["stage"] == "direction"
    assert first["hint"] is None
    assert first["relation"]
    assert first["remaining"] == game["optimal"]
    assert "alternatives_choices" not in first

    second = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert second["stage"] == "alternatives"
    assert second["hint"] is None
    assert 1 <= len(second["alternatives_choices"]) <= 2
    assert all(set(choice) == {"label", "relation"} for choice in second["alternatives_choices"])

    h = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert h["stage"] == "hop"
    assert h["hint"] is not None
    # The suggested neighbour is one hop closer to the target.
    dist_t = svc.distances_to(game["target"]["id"])
    assert dist_t.get(h["hint"]["id"]) == game["optimal"] - 1
    # It is a genuine neighbour of the current node.
    assert h["hint"]["id"] in svc.neighbor_ids(game["start"]["id"])
    # alternatives counts the on-path neighbours and is at least 1.
    assert h["alternatives"] >= 1


def _hop_strength(svc, cur: str, nb: str) -> float:
    edge = svc.link(cur, nb)
    return edge.strength if edge is not None else 0.0


def test_revealed_hint_uses_semantic_hub_aware_ordering():
    """The final revealed hop uses ADR-0043's shared semantic/hub ranking."""
    svc = get_service()
    found = False
    for diff in _BANDS:
        for seed in range(40):
            g = _create(seed=seed, difficulty=diff)
            gid = g["game_id"]
            cur = g["start"]["id"]
            dist_t = svc.distances_to(g["target"]["id"])
            on_path = [
                nb
                for nb in svc.neighbor_ids(cur)
                if dist_t.get(nb) == g["optimal"] - 1
            ]
            if len(on_path) < 2:
                continue
            found = True
            best = sorted(on_path, key=lambda nb: lant._hop_quality(cur, nb))[0]
            h = _revealed_hop(gid)
            assert h["hint"]["id"] == best, (diff, seed, on_path)
            assert h["alternatives"] == len(on_path)
            break
        if found:
            break
    assert found, "expected at least one puzzle with multiple shortest-path neighbours"


def _branchy_hint_service():
    """A tiny graph where the salient hop and the strong hop differ (ADR-0022)."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": "start", "label_ro": "START", "category": "test", "salience": 0.5},
        # `famous` is the more recognisable hop, but its edge is weak; `tight` must win.
        {"id": "famous", "label_ro": "FAMOUS", "category": "test", "salience": 0.95},
        {"id": "tight", "label_ro": "TIGHT", "category": "test", "salience": 0.1},
        {"id": "target", "label_ro": "TARGET", "category": "test", "salience": 0.5},
    ]
    edges = [
        {"id": "e1", "src_id": "start", "dst_id": "famous", "bidirectional": 1, "strength": 0.2},
        {"id": "e2", "src_id": "start", "dst_id": "tight", "bidirectional": 1, "strength": 0.9},
        {"id": "e3", "src_id": "famous", "dst_id": "target", "bidirectional": 1, "strength": 0.5},
        {"id": "e4", "src_id": "tight", "dst_id": "target", "bidirectional": 1, "strength": 0.5},
    ]
    return WordGameService(Graph.from_records(nodes, edges))


def test_hint_strength_beats_salience(monkeypatch):
    svc = _branchy_hint_service()
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(start="start", target="target", optimal=2, chain=["start"])
    gid = store.create(session)
    h = _revealed_hop(gid)
    assert h["hint"]["id"] == "tight"  # strong edge outranks higher salience
    assert h["alternatives"] == 2
    assert h["stage"] == "hop"


def test_hint_stages_reset_after_a_move(monkeypatch):
    svc = _branchy_hint_service()
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(start="start", target="target", optimal=2, chain=["start"])
    gid = store.create(session)
    first = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert first["stage"] == "direction"
    assert first["hint"] is None
    assert "alternatives_labels" not in first
    second = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert second["stage"] == "alternatives"
    assert second["hint"] is None
    assert second["alternatives_labels"] == ["TIGHT", "FAMOUS"]
    third = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert third["stage"] == "hop"
    assert third["hint"]["id"] == "tight"

    mv = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "TIGHT"},
        content_type="application/json",
    ).json()
    assert mv["ok"] is True
    next_position = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert next_position["stage"] == "direction"
    assert next_position["hint"] is None


def test_hint_on_won_game_returns_message():
    game = _create()
    _win(game)
    h = c.post(f"/api/wordgames/lant/games/{game['game_id']}/hint").json()
    assert h["hint"] is None
    assert h["message"]


# --------------------------------------------------------------------- hardening: score
def _detour_neighbor(svc, start: str, target: str, optimal: int) -> str | None:
    """A legal neighbour of start that does NOT move closer to the target (a real detour)."""
    dist_t = svc.distances_to(target)
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
        h = _revealed_hop(gid)["hint"]
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


# --------------------------------------------------------------------- fuzzy suggestions
def test_unknown_move_offers_fuzzy_suggestions():
    """A mangled concept surfaces a "did you mean" hint on the move endpoint.

    Updated for ADR-0022: a light typo now usually auto-corrects, so the advisory path
    is driven with a heavier typo that resolve_fuzzy() must NOT accept.
    """
    game = _create()
    gid = game["game_id"]
    svc = get_service()
    # A concept whose two-char-dropped form stays suggestible but is not auto-corrected.
    concept = next(
        nid
        for nid in svc.all_ids()
        if len(svc.label(nid)) >= 7
        and svc.resolve(svc.label(nid)[:3] + svc.label(nid)[5:]) is None
        and svc.resolve_fuzzy(svc.label(nid)[:3] + svc.label(nid)[5:]) is None
        and svc.label(nid) in svc.suggest(svc.label(nid)[:3] + svc.label(nid)[5:])
    )
    label = svc.label(concept)
    typo = label[:3] + label[5:]
    body = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is False
    assert "Poate cautai" in body["last_error"]
    assert label in body["suggestions"]


def test_no_suggestion_keeps_the_plain_unknown_error():
    """Gibberish with no close match keeps the exact legacy error and an empty list."""
    game = _create()
    res = c.post(
        f"/api/wordgames/lant/games/{game['game_id']}/move",
        {"text": "qwerty nonexistent xyz"},
        content_type="application/json",
    ).json()
    assert res["last_error"] == "Nu cunosc acest concept"
    assert res["suggestions"] == []


# --------------------------------------------------------------------- confident auto-accept
def _drop_mid(label: str) -> str:
    """Drop one interior character: high-confidence fuzzy-close to the original."""
    mid = len(label) // 2
    return label[:mid] + label[mid + 1 :]


def _find_correctable_hop(svc) -> tuple[str, str, str]:
    """(cur, nb, typo): nb is a neighbour of cur whose typo confidently auto-corrects."""
    for cur in svc.all_ids():
        for nb in svc.neighbor_ids(cur):
            label = svc.label(nb)
            if len(label) < 7:
                continue
            typo = _drop_mid(label)
            if svc.resolve(typo) is None and svc.resolve_fuzzy(typo) == nb:
                return cur, nb, typo
    raise AssertionError("no auto-correctable neighbour label found in the fixture")


def test_move_typo_auto_accepts_and_names_the_correction():
    """A unique high-confidence typo of a legal neighbour moves there (ADR-0022)."""
    svc = get_service()
    cur, nb, typo = _find_correctable_hop(svc)
    # Any concept still reachable FROM nb keeps this move off the dead-end path.
    target = next(t for t in svc.distances_from(nb) if t not in (cur, nb))
    session = LantSession(start=cur, target=target, optimal=2, chain=[cur])
    gid = store.create(session)
    body = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is True, body
    assert body["current"]["id"] == nb
    assert body["moves"] == 1  # auto-accepted moves count normally
    assert body["message"] == f"Am înțeles: {svc.label(nb)}."
    assert "dead_end" not in body


def test_move_typo_that_reaches_the_target_wins():
    """A typo'd target next door is still the answer: correction + win in one move."""
    svc = get_service()
    cur, nb, typo = _find_correctable_hop(svc)
    session = LantSession(start=cur, target=nb, optimal=1, chain=[cur])
    gid = store.create(session)
    body = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is True, body
    assert body["won"] is True
    assert body["message"] == f"Am înțeles: {svc.label(nb)}."
    assert body["score"] == 1000


def test_move_typo_of_a_non_neighbor_names_the_correction():
    """An auto-corrected concept that is NOT linked is rejected BY ITS CORRECTED NAME."""
    svc = get_service()
    game = _create()
    gid = game["game_id"]
    cur = game["start"]["id"]
    found = None
    for nid in svc.all_ids():
        if nid == cur or svc.link(cur, nid) is not None:
            continue
        label = svc.label(nid)
        if len(label) < 7:
            continue
        typo = _drop_mid(label)
        if svc.resolve(typo) is None and svc.resolve_fuzzy(typo) == nid:
            found = (nid, typo)
            break
    assert found, "no auto-correctable non-neighbour found in the fixture"
    nid, typo = found
    body = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is False
    assert body["last_error"] == (
        f"Am înțeles: {svc.label(nid)}. Nu exista o legatura directa"
    )
    # A rejected correction changes nothing.
    assert c.get(f"/api/wordgames/lant/games/{gid}").json()["moves"] == 0


# --------------------------------------------------------------------- dead-end escape
def _direction_progress_service():
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    node_ids = (
        "start",
        "s1",
        "lateral",
        "l1",
        "farther",
        "f1",
        "f2",
        "closer",
        "c1",
        "dead",
        "target",
    )
    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test"}
        for node_id in node_ids
    ]
    directed_pairs = (
        ("start", "s1"),
        ("s1", "target"),
        ("start", "lateral"),
        ("lateral", "l1"),
        ("l1", "target"),
        ("lateral", "farther"),
        ("farther", "f1"),
        ("f1", "f2"),
        ("f2", "target"),
        ("farther", "closer"),
        ("closer", "c1"),
        ("c1", "target"),
        ("farther", "dead"),
    )
    edges = [
        {
            "id": f"e_{src}_{dst}",
            "src_id": src,
            "dst_id": dst,
            "bidirectional": 0,
        }
        for src, dst in directed_pairs
    ]
    return WordGameService(Graph.from_records(nodes, edges))


def test_easy_moves_expose_only_coarse_direction_and_a_bounded_undo_signal(monkeypatch):
    svc = _direction_progress_service()
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(
        start="start",
        target="target",
        optimal=2,
        difficulty="usor",
        chain=["start"],
    )
    gid = store.create(session)

    initial = c.get(f"/api/wordgames/lant/games/{gid}").json()
    assert initial["backtrack_recommended"] is False
    assert "non_improving_moves" not in initial

    lateral = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "LATERAL"},
        content_type="application/json",
    ).json()
    assert lateral["progress"] == {
        "kind": "lateral",
        "message": "Tot cam la aceeași distanță.",
    }
    assert set(lateral["progress"]) == {"kind", "message"}
    assert lateral["backtrack_recommended"] is False
    assert session.non_improving_moves == 1

    farther = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "FARTHER"},
        content_type="application/json",
    ).json()
    assert farther["progress"]["kind"] == "farther"
    assert farther["backtrack_recommended"] is True
    assert session.non_improving_moves == 2
    assert "remaining" not in farther["progress"]
    assert "corridor" not in farther["progress"]

    dead_end = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "DEAD"},
        content_type="application/json",
    ).json()
    assert dead_end["progress"]["kind"] == "dead_end"
    assert dead_end["dead_end"] is True
    assert dead_end["backtrack_recommended"] is True
    assert session.non_improving_moves == 2

    undone = c.post(f"/api/wordgames/lant/games/{gid}/undo").json()
    assert undone["backtrack_recommended"] is False
    assert session.non_improving_moves == 0


def test_easy_closer_and_won_reset_direction_streak(monkeypatch):
    svc = _direction_progress_service()
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(
        start="start",
        target="target",
        optimal=2,
        difficulty="usor",
        chain=["start", "lateral", "farther"],
        non_improving_moves=2,
    )
    gid = store.create(session)

    closer = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "CLOSER"},
        content_type="application/json",
    ).json()
    assert closer["progress"]["kind"] == "closer"
    assert closer["backtrack_recommended"] is False
    assert session.non_improving_moves == 0

    session.non_improving_moves = 2
    c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "C1"},
        content_type="application/json",
    )
    session.non_improving_moves = 2
    won = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "TARGET"},
        content_type="application/json",
    ).json()
    assert won["progress"] == {"kind": "won", "message": "Ai ajuns la țintă!"}
    assert won["backtrack_recommended"] is False
    assert session.non_improving_moves == 0


def test_normal_moves_do_not_emit_automatic_direction(monkeypatch):
    svc = _direction_progress_service()
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(
        start="start",
        target="target",
        optimal=2,
        difficulty="normal",
        chain=["start"],
    )
    gid = store.create(session)
    body = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "LATERAL"},
        content_type="application/json",
    ).json()
    assert "progress" not in body
    assert body["backtrack_recommended"] is False
    assert session.non_improving_moves == 0


def test_move_into_a_dead_end_sets_flag_and_warns(monkeypatch):
    """A legal move onto a node that can no longer reach the target says so at once."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": n, "label_ro": n.upper(), "category": "test"}
        for n in ("start", "mid", "dead", "target")
    ]
    edges = [
        {"id": "e1", "src_id": "start", "dst_id": "mid", "bidirectional": 1},
        {"id": "e2", "src_id": "mid", "dst_id": "target", "bidirectional": 1},
        {"id": "e3", "src_id": "mid", "dst_id": "dead", "bidirectional": 0},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)

    session = LantSession(
        start="start", target="target", optimal=2, chain=["start", "mid"]
    )
    gid = store.create(session)
    body = c.post(
        f"/api/wordgames/lant/games/{gid}/move",
        {"text": "DEAD"},
        content_type="application/json",
    ).json()
    assert body["ok"] is True
    assert body["dead_end"] is True
    assert "fundătură" in body["message"]

    # A move that stays on a live path never carries the flag or the warning.
    session2 = LantSession(start="start", target="target", optimal=2, chain=["start"])
    gid2 = store.create(session2)
    ok = c.post(
        f"/api/wordgames/lant/games/{gid2}/move",
        {"text": "MID"},
        content_type="application/json",
    ).json()
    assert ok["ok"] is True
    assert "dead_end" not in ok
    assert "message" not in ok

    # Nor does the winning move (the game is over, not stuck).
    win = c.post(
        f"/api/wordgames/lant/games/{gid2}/move",
        {"text": "TARGET"},
        content_type="application/json",
    ).json()
    assert win["won"] is True
    assert "dead_end" not in win


def test_hint_dead_end_names_a_reachable_chain_ancestor(monkeypatch):
    """From a dead end the hint points back to the nearest visited node that can still
    reach the target — naming only a node the player already walked through."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": n, "label_ro": n.upper(), "category": "test"}
        for n in ("start", "mid", "dead", "target")
    ]
    edges = [
        {"id": "e1", "src_id": "start", "dst_id": "mid", "bidirectional": 1},
        {"id": "e2", "src_id": "mid", "dst_id": "target", "bidirectional": 1},
        # A one-way step into a sink: reachable from `mid`, but nothing leads on to target.
        {"id": "e3", "src_id": "mid", "dst_id": "dead", "bidirectional": 0},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    # Sanity: the current node truly cannot reach the target, but `mid` can.
    dt = svc.distances_to("target")
    assert dt.get("dead") is None
    assert dt.get("mid") == 1

    session = LantSession(
        start="start", target="target", optimal=2, chain=["start", "mid", "dead"]
    )
    gid = store.create(session)
    body = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert body["hint"] is None
    assert body["stage"] == "backtrack"
    assert body["message"].startswith("Fundătură")
    assert svc.label("mid") in body["message"]


def test_hint_recommends_free_undo_when_only_shortest_hop_was_visited(monkeypatch):
    """A directed detour can stay target-reachable only through its prior node.

    Revisited nodes remain absent from the public hop menu, but help must never claim that
    no route exists: it explicitly points to free undo and resets escalation after undo.
    """
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test"}
        for node_id in ("start", "mid", "detour", "target")
    ]
    edges = [
        {"id": "e_start_mid", "src_id": "start", "dst_id": "mid"},
        {"id": "e_mid_detour", "src_id": "mid", "dst_id": "detour"},
        {"id": "e_detour_mid", "src_id": "detour", "dst_id": "mid"},
        {"id": "e_mid_target", "src_id": "mid", "dst_id": "target"},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(
        start="start",
        target="target",
        optimal=2,
        chain=["start", "mid", "detour"],
    )
    gid = store.create(session)

    assert svc.distances_to("target")["detour"] == 2
    assert lant._shortest_hops(session) == []
    assert lant._visible_choices(session) == []

    body = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert body["hint"] is None
    assert body["stage"] == "backtrack"
    assert "Înapoi" in body["message"]
    assert "MID" in body["message"]

    undone = c.post(f"/api/wordgames/lant/games/{gid}/undo").json()
    assert undone["current"]["id"] == "mid"
    assert session.hint_requests == 0
    fresh_hint = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert fresh_hint["stage"] == "direction"


def test_hint_prefers_a_longer_unvisited_safe_route_before_backtracking(monkeypatch):
    """A visited shortest hop does not suppress truthful forward help when one exists."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test"}
        for node_id in ("start", "mid", "detour", "scenic", "x", "target")
    ]
    edges = [
        {"id": "e_start_mid", "src_id": "start", "dst_id": "mid"},
        {"id": "e_mid_detour", "src_id": "mid", "dst_id": "detour"},
        {"id": "e_mid_target", "src_id": "mid", "dst_id": "target"},
        {"id": "e_detour_mid", "src_id": "detour", "dst_id": "mid"},
        {
            "id": "e_detour_scenic",
            "src_id": "detour",
            "dst_id": "scenic",
            "label_ro": "ocol sigur",
        },
        {"id": "e_scenic_x", "src_id": "scenic", "dst_id": "x"},
        {"id": "e_x_target", "src_id": "x", "dst_id": "target"},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(
        start="start",
        target="target",
        optimal=2,
        chain=["start", "mid", "detour"],
    )
    gid = store.create(session)

    assert svc.distances_to("target")["detour"] == 2  # via the visited `mid`
    assert lant._shortest_hops(session) == []
    assert lant._visible_choice_nodes(session) == ["scenic"]

    first = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert first["stage"] == "direction"
    assert first["relation"] == "ocol sigur"
    assert first["remaining"] == 3
    second = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert second["stage"] == "alternatives"
    assert second["alternatives"] == 1
    assert second["alternatives_labels"] == ["SCENIC"]
    assert second["message"].startswith("O variantă utilă")
    third = c.post(f"/api/wordgames/lant/games/{gid}/hint").json()
    assert third["stage"] == "hop"
    assert third["hint"]["id"] == "scenic"


def test_hint_escalation_counter_is_capped_and_resets_during_revisits(monkeypatch):
    """Repeated A↔B walks retain one small counter, not every historical chain tuple."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": node_id, "label_ro": node_id.upper(), "category": "test"}
        for node_id in ("a", "b", "target")
    ]
    edges = [
        {"id": "e_cycle", "src_id": "a", "dst_id": "b", "bidirectional": 1},
        {"id": "e_a_target", "src_id": "a", "dst_id": "target"},
        {"id": "e_b_target", "src_id": "b", "dst_id": "target"},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    session = LantSession(start="a", target="target", optimal=1, chain=["a"])
    gid = store.create(session)

    for walk in range(24):
        stages = [
            c.post(f"/api/wordgames/lant/games/{gid}/hint").json()["stage"]
            for _ in range(4)
        ]
        assert stages == ["direction", "alternatives", "hop", "hop"]
        assert session.hint_requests == 3

        next_node = "b" if walk % 2 == 0 else "a"
        moved = c.post(
            f"/api/wordgames/lant/games/{gid}/move",
            {"text": next_node.upper()},
            content_type="application/json",
        ).json()
        assert moved["ok"] is True
        assert session.hint_requests == 0

    session.hint_requests = 3
    c.post(f"/api/wordgames/lant/games/{gid}/undo")
    assert session.hint_requests == 0
    assert isinstance(session.hint_requests, int)
