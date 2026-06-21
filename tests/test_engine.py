from __future__ import annotations

import pytest

from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.engine import HopGame, Mode, Puzzle
from cat_de_roman_esti.graph import Graph

from .conftest import FIXTURE


def _bundle():
    return load_fixture(FIXTURE)


def _puzzle(bundle, pid):
    return next(p for p in bundle.puzzles if p.id == pid)


# ---------------------------------------------------------------- loading


def test_load_rejects_missing_start_or_target():
    b = _bundle()
    bad = _puzzle(b, "pz_easy_lit")
    object.__setattr__(bad, "start_id", "n_does_not_exist")
    with pytest.raises(ValueError, match="start node"):
        HopGame.load(b.graph, bad, "easy")


def test_mode_parsing():
    assert Mode.parse("EASY") is Mode.EASY
    assert Mode.parse(Mode.HARD) is Mode.HARD
    with pytest.raises(ValueError):
        Mode.parse("nightmare")


# ---------------------------------------------------------------- views


def test_easy_mode_hides_distractors_and_shows_labels():
    # pz_hard_soc_1: start n_consiliul_local has a NON-solution distractor edge to
    # n_nato (hard-mode decoy) and a labelled solution edge to n_primar.
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_hard_soc_1"), "easy")
    assert game.include_distractors is False
    assert game.show_labels is True
    opts = {nb.node.id for nb in game.options()}
    assert "n_nato" not in opts  # distractor edge filtered
    assert game.edge_label("n_primar") != ""  # easy mode reveals edge labels


def test_hard_mode_keeps_distractors_and_hides_labels_and_hints():
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_hard_soc_1"), "hard")
    assert game.include_distractors is True
    assert game.show_labels is False
    opts = {nb.node.id for nb in game.options()}
    assert "n_nato" in opts  # distractor edge kept as a decoy
    assert game.edge_label("n_primar") == ""
    assert game.hint_neighbors() == []


def test_easy_hint_only_lists_reachable_solution_neighbors():
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_easy_lit"), "easy")
    assert game.hint_neighbors() == ["n_luceafarul"]


def test_hint_is_immediate_next_solution_node_only():
    """FIX B: on the solution path the hint is solution_path[i+1] and nothing else."""
    b = _bundle()
    # mica_unire_1859 -> moldova -> unirea_1600 -> transilvania -> decebal
    pz = _puzzle(b, "pz_hard_ist")
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hint_neighbors() == ["n_moldova"]  # index 0 -> next is moldova
    assert game.hop("n_moldova").ok
    assert game.hint_neighbors() == ["n_unirea_1600"]  # index 1 -> next is unirea
    assert game.hop("n_unirea_1600").ok
    assert game.hint_neighbors() == ["n_transilvania"]  # index 2 -> next is transilvania


def test_hint_does_not_leak_downstream_solution_neighbor():
    """FIX B: a later solution node that is merely a side-neighbour is NOT hinted.

    Synthetic graph: solution s -> a -> b -> t, but s also has a direct side edge to b
    (a downstream solution node). The old behaviour surfaced b as a hint at s (b is in
    hint_neighbors AND a reachable neighbour), misleading the player into skipping a.
    The gated hint must offer only the immediate next node, a.
    """
    g = Graph.from_records(
        node_records=[{"id": x, "label_ro": x, "category": "c"} for x in ("s", "a", "b", "t")],
        edge_records=[
            {"id": "e_sa", "src_id": "s", "dst_id": "a", "relation": "r", "strength": 0.9},
            {"id": "e_ab", "src_id": "a", "dst_id": "b", "relation": "r", "strength": 0.9},
            {"id": "e_bt", "src_id": "b", "dst_id": "t", "relation": "r", "strength": 0.9},
            {"id": "e_sb", "src_id": "s", "dst_id": "b", "relation": "r", "strength": 0.5},
        ],
    )
    pz = Puzzle.from_record(
        {
            "id": "synthetic",
            "start_id": "s",
            "target_id": "t",
            "category": "c",
            "difficulty": "easy",
            "optimal_hops": 3,
            "par": 3,
            "solution_path": ["s", "a", "b", "t"],
            "hint_neighbors": ["a", "b", "t"],
        }
    )
    game = HopGame.load(g, pz, "easy")
    # b is a real, reachable neighbour of s AND in hint_neighbors, but it is NOT the
    # immediate next step (a is) -> it must not be hinted.
    reachable = {nb.node.id for nb in game.options()}
    assert "b" in reachable  # the misleading side edge exists
    assert game.hint_neighbors() == ["a"]


def test_hint_falls_back_to_reachable_when_off_solution():
    """FIX B: off the solution path, fall back to any reachable hint node.

    Synthetic graph: solution s -> a -> b -> t, plus an off-solution detour node d that
    is reachable from s and itself reaches the solution node a. After hopping onto the
    detour d (NOT on the solution path), the gated hint falls back to the reachable
    solution node a, guiding the player back onto the path.
    """
    g = Graph.from_records(
        node_records=[
            {"id": x, "label_ro": x, "category": "c"} for x in ("s", "a", "b", "t", "d")
        ],
        edge_records=[
            {"id": "e_sa", "src_id": "s", "dst_id": "a", "relation": "r", "strength": 0.9},
            {"id": "e_ab", "src_id": "a", "dst_id": "b", "relation": "r", "strength": 0.9},
            {"id": "e_bt", "src_id": "b", "dst_id": "t", "relation": "r", "strength": 0.9},
            {"id": "e_sd", "src_id": "s", "dst_id": "d", "relation": "r", "strength": 0.8},
            {"id": "e_da", "src_id": "d", "dst_id": "a", "relation": "r", "strength": 0.8},
        ],
    )
    pz = Puzzle.from_record(
        {
            "id": "synthetic-fallback",
            "start_id": "s",
            "target_id": "t",
            "category": "c",
            "difficulty": "easy",
            "optimal_hops": 3,
            "par": 3,
            "solution_path": ["s", "a", "b", "t"],
            "hint_neighbors": ["a", "b", "t"],
        }
    )
    game = HopGame.load(g, pz, "easy")
    assert game.hop("d").ok  # detour OFF the solution path
    assert game.current_id == "d"
    assert "d" not in pz.solution_path
    # d can reach a (a hint node), guiding the player back onto the solution.
    assert game.hint_neighbors() == ["a"]


def test_hint_empty_at_target_node():
    """FIX B: once on the final solution node there is no next step to hint."""
    b = _bundle()
    pz = _puzzle(b, "pz_easy_lit")  # eminescu -> luceafarul -> romantism
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hop("n_luceafarul").ok
    assert game.hop("n_romantism").ok  # at target == last solution node
    assert game.hint_neighbors() == []


# ---------------------------------------------------------------- hops


def test_invalid_hop_no_edge():
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_easy_lit"), "easy")
    res = game.hop("n_alba_iulia")  # no edge eminescu -> alba iulia
    assert res.ok is False
    assert "no edge" in res.reason
    assert game.hops == 0  # path unchanged


def test_distractor_hop_invalid_in_easy_mode():
    # pz_easy_ist starts at n_stefan_cel_mare, whose edge to n_transilvania (hd1) is a
    # distractor -> filtered out of the easy-mode view, so the hop is illegal.
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_easy_ist"), "easy")
    res = game.hop("n_transilvania")  # only reachable via a distractor edge
    assert res.ok is False


def test_hop_to_self_rejected():
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_easy_lit"), "easy")
    res = game.hop(game.current_id)
    assert res.ok is False
    assert "already at" in res.reason


# ---------------------------------------------------------------- win + score


def test_optimal_playthrough_scores_perfect():
    b = _bundle()
    pz = _puzzle(b, "pz_easy_lit")
    game = HopGame.load(b.graph, pz, "easy")
    for nid in pz.solution_path[1:]:
        res = game.hop(nid)
        assert res.ok
    assert game.won is True
    assert game.hops == pz.par == 2
    assert game.score() == 1000
    assert game.summary()["path"] == pz.solution_path


def test_hard_playthrough_full_solution():
    b = _bundle()
    pz = _puzzle(b, "pz_hard_ist")
    game = HopGame.load(b.graph, pz, "hard")
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok
    assert game.won
    assert game.hops == 4
    assert game.score() == 1000


def test_over_par_deducts_score():
    b = _bundle()
    pz = _puzzle(b, "pz_easy_ist")  # par 2: stefan -> moldova -> unirea_1600
    assert pz.par == 2
    game = HopGame.load(b.graph, pz, "easy")
    # deliberate extra hop: stefan -> putna -> moldova -> unirea_1600 (3 hops, par 2)
    assert game.hop("n_putna").ok
    assert game.hop("n_moldova").ok
    assert game.hop("n_unirea_1600").ok
    assert game.won
    assert game.hops == 3
    assert game.score() == 900  # 1000 - 100*(3-2)


def test_hop_after_win_is_noop():
    b = _bundle()
    pz = _puzzle(b, "pz_easy_ist")  # stefan -> moldova -> unirea_1600
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hop("n_moldova").ok
    assert game.hop("n_unirea_1600").ok  # win reached
    assert game.won
    res = game.hop("n_mihai_viteazul")  # any further hop is a no-op
    assert res.ok is False
    assert res.won is True


def test_unwon_game_scores_zero():
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_hard_ist"), "hard")
    assert game.score() == 0


# ---------------------------------------------------------------- undo


def test_undo_steps_back_one_hop():
    b = _bundle()
    pz = _puzzle(b, "pz_easy_ist")  # stefan -> moldova -> unirea_1600
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hop("n_moldova").ok
    assert game.hop("n_unirea_1600").ok
    assert game.won and game.hops == 2
    # undo the winning hop: back on n_moldova, no longer won, move count drops.
    res = game.undo()
    assert res.ok and res.won is False
    assert game.current_id == "n_moldova"
    assert game.hops == 1
    assert game.won is False
    # undo again: back at the start.
    assert game.undo().ok
    assert game.current_id == "n_stefan_cel_mare"
    assert game.hops == 0


def test_undo_at_start_is_rejected():
    b = _bundle()
    game = HopGame.load(b.graph, _puzzle(b, "pz_easy_ist"), "easy")
    res = game.undo()
    assert res.ok is False
    assert "nothing to undo" in res.reason
    assert game.hops == 0
    assert game.path == ["n_stefan_cel_mare"]


def test_undo_then_replay_to_win():
    # Undo is the inverse of hop: after undoing, the player can re-hop and still win.
    b = _bundle()
    pz = _puzzle(b, "pz_easy_ist")
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hop("n_putna").ok  # a detour off the optimal path
    assert game.undo().ok  # take it back
    assert game.current_id == "n_stefan_cel_mare"
    # now play the optimal solution
    assert game.hop("n_moldova").ok
    assert game.hop("n_unirea_1600").ok
    assert game.won and game.hops == 2 and game.score() == 1000
