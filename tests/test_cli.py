from __future__ import annotations

import io

from cat_de_roman_esti import cli
from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.engine import HopGame

from .conftest import FIXTURE


def _capture():
    lines: list[str] = []
    return lines, lambda *a, **k: lines.append(" ".join(str(x) for x in a))


def _easy(bundle, category=None):
    """First easy puzzle (optionally in a category) — matches the CLI's deterministic pick."""
    pool = bundle.puzzles_for(category=category, difficulty="easy")
    assert pool, f"fixture has no easy puzzle{f' for {category}' if category else ''}"
    return pool[0]


def _hop_index_for(game: HopGame, node_id: str) -> str:
    return next(
        str(i) for i, nb in enumerate(game.options(), 1) if nb.node.id == node_id
    )


def _script_for(bundle, pz) -> str:
    """The CLI option-index keystrokes that walk a puzzle's solution_path to a win."""
    mirror = HopGame.load(bundle.graph, pz, "easy")
    script = ""
    for nid in pz.solution_path[1:]:
        script += _hop_index_for(mirror, nid) + "\n"
        assert mirror.hop(nid).ok
    return script


def test_full_offline_playthrough_wins_via_cli():
    """Drive the interactive loop with scripted stdin to a perfect win (any easy puzzle)."""
    bundle = load_fixture(FIXTURE)
    pz = _easy(bundle)
    game = HopGame.load(bundle.graph, pz, "easy")
    lines, out = _capture()
    summary = cli.play(game, stream=io.StringIO(_script_for(bundle, pz)), out=out)
    assert summary["won"] is True
    assert summary["score"] == 1000
    assert any("WIN!" in line for line in lines)


def test_quit_is_clean():
    bundle = load_fixture(FIXTURE)
    game = HopGame.load(bundle.graph, _easy(bundle), "easy")
    lines, out = _capture()
    summary = cli.play(game, stream=io.StringIO("q\n"), out=out)
    assert summary["won"] is False
    assert any("Bye." in line for line in lines)


def test_main_list_offline():
    import json

    n_puzzles = len(json.loads(FIXTURE.read_text(encoding="utf-8"))["kg_puzzles"])
    lines, out = _capture()
    rc = cli.main(["--offline", "--list"], out=out)
    assert rc == 0
    assert any(f"Puzzles available: {n_puzzles}" in line for line in lines)


def test_main_offline_noninteractive_win():
    """--offline with category+difficulty supplied; stdin only feeds hops.

    The CLI picks the first easy istorie puzzle; we feed its solution_path hops, resolving
    option indices against a mirror game advanced in lockstep.
    """
    bundle = load_fixture(FIXTURE)
    pz = _easy(bundle, "istorie")
    lines, out = _capture()
    rc = cli.main(
        ["--offline", "--category", "istorie", "--difficulty", "easy"],
        stream=io.StringIO(_script_for(bundle, pz)),
        out=out,
    )
    assert rc == 0
    assert any("WIN!" in line for line in lines)


def test_main_no_puzzles_returns_error(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text('{"kg_nodes": [], "kg_edges": [], "kg_puzzles": []}', encoding="utf-8")
    lines, out = _capture()
    rc = cli.main(["--offline", "--fixture", str(empty)], out=out)
    assert rc == 1


def test_invalid_hop_then_recover():
    bundle = load_fixture(FIXTURE)
    pz = _easy(bundle)
    game = HopGame.load(bundle.graph, pz, "easy")
    n_opts = len(game.options())
    bad = str(n_opts + 5)  # out of range
    # After the rejected input the game state is unchanged, so feed the full solution.
    script = bad + "\n" + _script_for(bundle, pz)
    lines, out = _capture()
    summary = cli.play(game, stream=io.StringIO(script), out=out)
    assert summary["won"] is True
    assert any("enter 1-" in line for line in lines)
