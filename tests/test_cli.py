from __future__ import annotations

import io

from cat_de_roman_esti import cli
from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.engine import HopGame

from .conftest import FIXTURE


def _capture():
    lines: list[str] = []
    return lines, lambda *a, **k: lines.append(" ".join(str(x) for x in a))


def test_full_offline_playthrough_wins_via_cli():
    """Drive the interactive loop with scripted stdin to a perfect win."""
    bundle = load_fixture(FIXTURE)
    pz = next(p for p in bundle.puzzles if p.id == "pz_easy_lit")
    game = HopGame.load(bundle.graph, pz, "easy")

    # At start, options of eminescu (easy, no distractors), strength-sorted:
    # luceafarul (0.95), junimea (0.7), [creanga via contemporary 0.7]...
    # pick luceafarul, then romantism. We resolve numbers dynamically.
    def pick(node_id: str) -> str:
        opts = game.options()
        for i, nb in enumerate(opts, 1):
            if nb.node.id == node_id:
                return str(i)
        raise AssertionError(f"{node_id} not among options")

    n1 = pick("n_luceafarul")
    game2 = HopGame.load(bundle.graph, pz, "easy")  # fresh game for the real run

    # rebuild script using the fresh game's option ordering
    def pick2(g, node_id):
        for i, nb in enumerate(g.options(), 1):
            if nb.node.id == node_id:
                return str(i)
        raise AssertionError(node_id)

    script = pick2(game2, "n_luceafarul") + "\n"
    g_after = HopGame.load(bundle.graph, pz, "easy")
    g_after.hop("n_luceafarul")
    script += pick2(g_after, "n_romantism") + "\n"

    lines, out = _capture()
    summary = cli.play(game2, stream=io.StringIO(script), out=out)

    assert summary["won"] is True
    assert summary["score"] == 1000
    assert any("WIN!" in line for line in lines)
    assert n1  # sanity


def test_quit_is_clean():
    bundle = load_fixture(FIXTURE)
    pz = next(p for p in bundle.puzzles if p.id == "pz_easy_lit")
    game = HopGame.load(bundle.graph, pz, "easy")
    lines, out = _capture()
    summary = cli.play(game, stream=io.StringIO("q\n"), out=out)
    assert summary["won"] is False
    assert any("Bye." in line for line in lines)


def test_main_list_offline():
    import json

    from .conftest import FIXTURE

    n_puzzles = len(json.loads(FIXTURE.read_text(encoding="utf-8"))["kg_puzzles"])
    lines, out = _capture()
    rc = cli.main(["--offline", "--list"], out=out)
    assert rc == 0
    assert any(f"Puzzles available: {n_puzzles}" in line for line in lines)


def _hop_index_for(game: HopGame, node_id: str) -> str:
    return next(
        str(i) for i, nb in enumerate(game.options(), 1) if nb.node.id == node_id
    )


def test_main_offline_noninteractive_win():
    """--offline with category+difficulty supplied; stdin only feeds hops.

    pz_easy_ist is a 2-hop puzzle (stefan -> moldova -> unirea_1600), so we feed both
    hops. Option indices are resolved against a mirror game advanced in lockstep.
    """
    bundle = load_fixture(FIXTURE)
    pz = next(p for p in bundle.puzzles if p.id == "pz_easy_ist")
    mirror = HopGame.load(bundle.graph, pz, "easy")
    script = ""
    for nid in pz.solution_path[1:]:
        script += _hop_index_for(mirror, nid) + "\n"
        assert mirror.hop(nid).ok
    lines, out = _capture()
    rc = cli.main(
        ["--offline", "--category", "istorie", "--difficulty", "easy"],
        stream=io.StringIO(script),
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
    pz = next(p for p in bundle.puzzles if p.id == "pz_easy_ist")
    game = HopGame.load(bundle.graph, pz, "easy")
    n_opts = len(game.options())
    bad = str(n_opts + 5)  # out of range
    # After the rejected input the game state is unchanged, so resolve+feed the full
    # 2-hop solution (stefan -> moldova -> unirea_1600) against a lockstep mirror.
    mirror = HopGame.load(bundle.graph, pz, "easy")
    script = bad + "\n"
    for nid in pz.solution_path[1:]:
        script += next(
            str(i) for i, nb in enumerate(mirror.options(), 1) if nb.node.id == nid
        ) + "\n"
        assert mirror.hop(nid).ok
    lines, out = _capture()
    summary = cli.play(game, stream=io.StringIO(script), out=out)
    assert summary["won"] is True
    assert any("enter 1-" in line for line in lines)
