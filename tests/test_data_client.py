from __future__ import annotations

from cat_de_roman_esti.data import load_from_client
from cat_de_roman_esti.engine import HopGame

from .conftest import FakeRoeduClient


def test_load_from_fake_client_builds_full_bundle(fake_client, kg_raw):
    bundle = load_from_client(fake_client)
    # The full (no-filter) load pulls every node + every puzzle from the served products.
    # Counts are derived from the bundled fixture so the invariant tracks the assembled
    # fixture rather than a hard-coded snapshot.
    assert len(bundle.graph) == len(kg_raw["kg_nodes"])
    assert len(bundle.puzzles) == len(kg_raw["kg_puzzles"])
    # cursor pagination actually happened (page_size 2 over many nodes -> many pages)
    node_pages = [c for c in fake_client.calls if c[0] == "kg_nodes"]
    assert len(node_pages) > 1


def test_load_from_client_category_filter_pure_in_category(fake_client):
    """A category with no cross-category puzzle stays scoped to that category."""
    bundle = load_from_client(fake_client, category="literatura")
    # literatura's only out-of-category puzzle is pz_mixed_lit_ist, whose solution
    # bridges into istorie (n_moldova, n_putna) -> the loader widens to the union so
    # those solution nodes are present. Every loaded puzzle is therefore winnable.
    assert all(p.category in ("literatura", "mixed") for p in bundle.puzzles)
    for p in bundle.puzzles:
        for nid in p.solution_path:
            assert bundle.graph.has_node(nid), f"missing solution node {nid} for {p.id}"


def test_load_from_client_mixed_widens_to_union(fake_client):
    """FIX A: a mixed puzzle pulls in cross-category solution nodes (union load)."""
    bundle = load_from_client(fake_client, category="istorie")
    # The mixed puzzle is surfaced alongside the istorie puzzles...
    cats = {p.category for p in bundle.puzzles}
    assert "mixed" in cats
    assert all(p.category in ("istorie", "mixed") for p in bundle.puzzles)
    # ...and because its solution_path strays into literatura, the loader widened the
    # node fetch to the union: literatura solution nodes are present in the graph.
    assert bundle.graph.has_node("n_luceafarul")  # literatura, on the mixed solution
    assert bundle.graph.has_node("n_mihai_eminescu")  # literatura bridge node
    # Post-condition: no solution_path node id is ever missing from the loaded graph.
    for p in bundle.puzzles:
        for nid in p.solution_path:
            assert bundle.graph.has_node(nid), f"missing solution node {nid} for {p.id}"


def test_load_from_client_pure_category_not_widened(kg_raw):
    """A category whose puzzles all stay in-category does NOT over-fetch other cats.

    The widening branch only triggers when a surfaced puzzle (e.g. a cross-category
    'mixed' one) references a node outside the requested category. To assert the
    no-widening path deterministically we serve a fixture SLICE that keeps the istorie
    nodes/edges but only the in-category istorie puzzles (no 'mixed' bucket): the load
    must then stay scoped to istorie-only nodes.
    """
    sliced = {
        "kg_nodes": [n for n in kg_raw["kg_nodes"] if n["category"] == "istorie"],
        "kg_edges": list(kg_raw["kg_edges"]),
        "kg_puzzles": [p for p in kg_raw["kg_puzzles"] if p["category"] == "istorie"],
    }
    assert sliced["kg_puzzles"], "fixture should have at least one istorie puzzle"
    client = FakeRoeduClient(sliced)
    bundle = load_from_client(client, category="istorie")
    assert all(p.category == "istorie" for p in bundle.puzzles)
    # No mixed/cross-category puzzle referenced an out-of-scope node -> no union widening.
    assert all(n.category == "istorie" for n in bundle.graph.nodes.values())
    # Every loaded puzzle is still winnable (solution nodes all present).
    for p in bundle.puzzles:
        for nid in p.solution_path:
            assert bundle.graph.has_node(nid), f"missing solution node {nid} for {p.id}"


def test_fail_closed_blocked_product_yields_no_records(kg_raw):
    client = FakeRoeduClient(kg_raw, blocked={"kg_puzzles"})
    bundle = load_from_client(client)
    # nodes/edges still present, but the blocked product produced zero records
    assert len(bundle.graph) == len(kg_raw["kg_nodes"])
    assert bundle.puzzles == []


def test_fail_closed_blocked_nodes_means_unplayable(kg_raw):
    client = FakeRoeduClient(kg_raw, blocked={"kg_nodes"})
    bundle = load_from_client(client)
    assert len(bundle.graph) == 0
    # puzzles exist but cannot be loaded onto an empty graph -> fail closed
    import pytest

    with pytest.raises(ValueError):
        HopGame.load(bundle.graph, bundle.puzzles[0], "easy")


def test_end_to_end_via_fake_client(fake_client):
    """Full game playthrough sourced from the fake server, not the fixture loader.

    Selects a puzzle dynamically rather than hard-coding an id: the bundled KG fixture's
    puzzle ids are regenerated (``pz_<category>_<difficulty>_<n>``), so the test pins
    behaviour, not naming. We pick any hard-mode puzzle that is fully playable on the
    loaded graph (start, target, and every solution-path edge present in the hard view),
    walk its canonical solution, and assert the loader -> fake-client round-trip yields a
    winnable game that scores a perfect 1000 (solution length == par for these puzzles).
    """
    bundle = load_from_client(fake_client)
    assert bundle.puzzles, "fake client should serve at least one puzzle"

    def playable(pz) -> bool:
        if not (bundle.graph.has_node(pz.start_id) and bundle.graph.has_node(pz.target_id)):
            return False
        # Every consecutive hop along the solution must be a real edge in the hard view.
        path = pz.solution_path
        for a, b in zip(path, path[1:], strict=False):
            if bundle.graph.edge_between(a, b, include_distractors=True) is None:
                return False
        return len(path) >= 2

    pz = next(
        (p for p in bundle.puzzles if p.difficulty == "hard" and playable(p)),
        None,
    )
    assert pz is not None, "expected at least one playable hard puzzle from the bundle"

    game = HopGame.load(bundle.graph, pz, "hard")
    for nid in pz.solution_path[1:]:
        assert game.hop(nid).ok, f"hop to {nid} should be valid for {pz.id}"
    assert game.won
    # Walking the canonical solution reaches the target at par -> a perfect score.
    assert game.score() == 1000
