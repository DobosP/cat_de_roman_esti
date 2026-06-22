from __future__ import annotations

import pytest

from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.engine import HopGame, Mode, Puzzle
from cat_de_roman_esti.graph import Graph

from .conftest import FIXTURE


def _bundle():
    return load_fixture(FIXTURE)


# ----------------------------------------------------------- fixture selectors
#
# The bundled KG fixture is regenerated periodically (node/edge ids are stable, but
# puzzle ids, graph distances and reachability are not). These helpers SELECT a
# puzzle by its structure rather than by a hard-coded id, so the engine-invariant
# tests below stay valid across fixture regenerations.


def _first_puzzle(bundle, *, difficulty, category=None):
    """First puzzle of a given difficulty (and optionally category)."""
    matches = bundle.puzzles_for(category=category, difficulty=difficulty)
    if not matches:
        pytest.skip(f"fixture has no {difficulty!r}/{category!r} puzzle")
    return matches[0]


def _puzzle_with_start_distractor(bundle, *, reachable_in_easy):
    """An easy puzzle whose START has a non-solution distractor neighbour.

    ``reachable_in_easy`` selects whether the distractor's destination is ALSO
    reachable from the start via some non-distractor edge:

      * False — the destination is reachable ONLY through the distractor edge, so it
        vanishes from the easy-mode view entirely (used to assert easy mode hides the
        decoy and that hopping onto it is illegal).
      * True  — the destination still appears in the easy view via another edge (not
        needed today, kept for symmetry).

    Returns ``(puzzle, distractor_dst_id)``.
    """
    g = bundle.graph
    for pz in bundle.puzzles_for(difficulty="easy"):
        sol = set(pz.solution_path)
        easy_nb = {nb.node.id for nb in g.neighbors(pz.start_id, include_distractors=False)}
        for dst_id, edge in g._adj.get(pz.start_id, ()):
            if not edge.is_distractor or g.node(dst_id) is None or dst_id in sol:
                continue
            if (dst_id in easy_nb) == reachable_in_easy:
                return pz, dst_id
    pytest.skip("fixture has no easy puzzle with a usable start distractor edge")


def _easy_puzzle_with_start_detour(bundle):
    """An easy puzzle with a non-solution detour neighbour off ``solution_path[0]``.

    The detour node X is reachable from the start via a non-distractor edge, is NOT on
    the solution path, and itself connects (non-distractor) to ``solution_path[1]`` — so
    the player can take ``start -> X -> solution_path[1] -> ... -> target`` to finish one
    hop over par. Returns ``(puzzle, detour_id)``.
    """
    g = bundle.graph
    for pz in bundle.puzzles_for(difficulty="easy"):
        sol = pz.solution_path
        if len(sol) < 2:
            continue
        start_nb = {nb.node.id for nb in g.neighbors(sol[0], include_distractors=False)}
        for x in start_nb:
            if x in sol:
                continue
            x_nb = {nb.node.id for nb in g.neighbors(x, include_distractors=False)}
            if sol[1] in x_nb:
                return pz, x
    pytest.skip("fixture has no easy puzzle with a start detour reaching solution_path[1]")


def _node_not_adjacent(bundle, node_id):
    """Some node id with NO edge (any mode) from ``node_id`` — for invalid-hop tests."""
    g = bundle.graph
    adjacent = {dst for dst, _ in g._adj.get(node_id, ())}
    adjacent.add(node_id)
    for nid in g.nodes:
        if nid not in adjacent:
            return nid
    pytest.skip("graph node is adjacent to everything")


# ---------------------------------------------------------------- loading


def test_load_rejects_missing_start_or_target():
    b = _bundle()
    bad = _first_puzzle(b, difficulty="easy")
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
    # Pick (content-agnostically) an easy puzzle whose START has a distractor edge to a
    # non-solution node that is reachable ONLY via that distractor edge: easy mode must
    # drop it from the options, while still revealing the label on the real solution edge.
    b = _bundle()
    pz, decoy = _puzzle_with_start_distractor(b, reachable_in_easy=False)
    game = HopGame.load(b.graph, pz, "easy")
    assert game.include_distractors is False
    assert game.show_labels is True
    opts = {nb.node.id for nb in game.options()}
    assert decoy not in opts  # distractor edge filtered
    next_sol = pz.solution_path[1]
    assert game.edge_label(next_sol) != ""  # easy mode reveals edge labels


def test_hard_mode_keeps_distractors_and_hides_labels_and_hints():
    b = _bundle()
    pz, decoy = _puzzle_with_start_distractor(b, reachable_in_easy=False)
    game = HopGame.load(b.graph, pz, "hard")
    assert game.include_distractors is True
    assert game.show_labels is False
    opts = {nb.node.id for nb in game.options()}
    assert decoy in opts  # distractor edge kept as a decoy
    assert game.edge_label(pz.solution_path[1]) == ""
    assert game.hint_neighbors() == []


def test_easy_hint_only_lists_reachable_solution_neighbors():
    # At the start the only hint is the immediate next solution node, nothing else.
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hint_neighbors() == [pz.solution_path[1]]


def test_hint_is_immediate_next_solution_node_only():
    """FIX B: on the solution path the hint is solution_path[i+1] and nothing else."""
    b = _bundle()
    # Use a multi-hop puzzle so we can step along the path and re-check the hint.
    pz = next(
        (p for p in b.puzzles_for(difficulty="easy") if len(p.solution_path) >= 4),
        None,
    )
    if pz is None:
        pytest.skip("fixture has no easy puzzle with >= 3 hops")
    game = HopGame.load(b.graph, pz, "easy")
    # At each on-solution position the hint is exactly the immediate next node.
    for i in range(len(pz.solution_path) - 2):
        assert game.hint_neighbors() == [pz.solution_path[i + 1]]
        assert game.hop(pz.solution_path[i + 1]).ok
    # Now standing on the second-to-last node: hint is the final node.
    assert game.hint_neighbors() == [pz.solution_path[-1]]


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
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok
    assert game.won  # at target == last solution node
    assert game.hint_neighbors() == []


# ---------------------------------------------------------------- hops


def test_invalid_hop_no_edge():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    target = _node_not_adjacent(b, pz.start_id)
    res = game.hop(target)  # no edge from start to this node
    assert res.ok is False
    assert "no edge" in res.reason
    assert game.hops == 0  # path unchanged


def test_distractor_hop_invalid_in_easy_mode():
    # An easy puzzle whose start reaches a node ONLY via a distractor edge: that node is
    # filtered out of the easy-mode view, so the hop onto it is illegal.
    b = _bundle()
    pz, decoy = _puzzle_with_start_distractor(b, reachable_in_easy=False)
    game = HopGame.load(b.graph, pz, "easy")
    res = game.hop(decoy)  # only reachable via a distractor edge
    assert res.ok is False


def test_hop_to_self_rejected():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    res = game.hop(game.current_id)
    assert res.ok is False
    assert "already at" in res.reason


# ---------------------------------------------------------------- win + score


def test_optimal_playthrough_scores_perfect():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    for nid in pz.solution_path[1:]:
        res = game.hop(nid)
        assert res.ok
    assert game.won is True
    assert game.hops == pz.par == len(pz.solution_path) - 1
    assert game.score() == 1000
    assert game.summary()["path"] == pz.solution_path


def test_hard_playthrough_full_solution():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="hard")
    game = HopGame.load(b.graph, pz, "hard")
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok
    assert game.won
    assert game.hops == len(pz.solution_path) - 1 == pz.par
    assert game.score() == 1000


def test_over_par_deducts_score():
    # Take a deliberate one-hop detour off the optimal path, then rejoin and finish:
    # hops == par + 1, so the score drops by exactly 100.
    b = _bundle()
    pz, detour = _easy_puzzle_with_start_detour(b)
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hop(detour).ok  # start -> detour (off the optimal path)
    for nid in pz.solution_path[1:]:  # detour -> solution_path[1] -> ... -> target
        assert game.hop(nid).ok
    assert game.won
    assert game.hops == pz.par + 1
    assert game.score() == 1000 - 100  # 1000 - 100*(hops-par), one over par


def test_hop_after_win_is_noop():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok  # reach the win
    assert game.won
    # Any further hop, even onto a real neighbour of the target, is a no-op.
    after = next(iter(game.options()), None)
    extra = after.node.id if after else "n_anything"
    res = game.hop(extra)
    assert res.ok is False
    assert res.won is True


def test_unwon_game_scores_zero():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="hard")
    game = HopGame.load(b.graph, pz, "hard")
    assert game.score() == 0


# ---------------------------------------------------------------- undo


def test_undo_steps_back_one_hop():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok
    par = pz.par
    assert game.won and game.hops == par
    # undo the winning hop: back on the second-to-last node, no longer won.
    res = game.undo()
    assert res.ok and res.won is False
    assert game.current_id == pz.solution_path[-2]
    assert game.hops == par - 1
    assert game.won is False
    # undo all the way back to the start.
    while game.hops > 0:
        assert game.undo().ok
    assert game.current_id == pz.start_id
    assert game.hops == 0


def test_undo_at_start_is_rejected():
    b = _bundle()
    pz = _first_puzzle(b, difficulty="easy")
    game = HopGame.load(b.graph, pz, "easy")
    res = game.undo()
    assert res.ok is False
    assert "nothing to undo" in res.reason
    assert game.hops == 0
    assert game.path == [pz.start_id]


def test_undo_then_replay_to_win():
    # Undo is the inverse of hop: after undoing a detour, the player can play the optimal
    # solution and still win with a perfect score.
    b = _bundle()
    pz, detour = _easy_puzzle_with_start_detour(b)
    game = HopGame.load(b.graph, pz, "easy")
    assert game.hop(detour).ok  # a detour off the optimal path
    assert game.undo().ok  # take it back
    assert game.current_id == pz.start_id
    # now play the optimal solution
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok
    assert game.won and game.hops == pz.par and game.score() == 1000
