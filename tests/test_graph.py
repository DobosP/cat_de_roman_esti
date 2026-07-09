from __future__ import annotations

from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.graph import Graph

from .conftest import FIXTURE


def _bundle():
    return load_fixture(FIXTURE)


def test_graph_builds_nodes_and_edges():
    import json

    g = _bundle().graph
    assert g.has_node("n_stefan_cel_mare")
    assert g.node("n_stefan_cel_mare").label_ro == "Ștefan cel Mare"
    assert g.node("nonexistent") is None
    # The graph loads every fixture node (count derived from the bundled fixture so this
    # invariant tracks the assembled fixture rather than a hard-coded snapshot).
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(g) == len(raw["kg_nodes"])


def test_bidirectional_edges_traversable_both_ways():
    g = _bundle().graph
    fwd = {nb.node.id for nb in g.neighbors("n_stefan_cel_mare")}
    assert "n_moldova" in fwd
    # reverse direction works because edges are bidirectional
    back = {nb.node.id for nb in g.neighbors("n_moldova")}
    assert "n_stefan_cel_mare" in back


def test_neighbors_filter_distractors():
    g = _bundle().graph
    with_d = {nb.node.id for nb in g.neighbors("n_stefan_cel_mare", include_distractors=True)}
    without_d = {nb.node.id for nb in g.neighbors("n_stefan_cel_mare", include_distractors=False)}
    # hd1 is a distractor edge stefan -> transilvania
    assert "n_transilvania" in with_d
    assert "n_transilvania" not in without_d
    assert without_d <= with_d


def test_neighbors_sorted_by_strength_desc():
    g = _bundle().graph
    nbs = g.neighbors("n_stefan_cel_mare", include_distractors=False)
    strengths = [nb.edge.strength for nb in nbs]
    assert strengths == sorted(strengths, reverse=True)


def test_neighbors_skip_out_of_scope_nodes():
    g = Graph.from_records(
        node_records=[{"id": "a", "label_ro": "A", "category": "x"}],
        edge_records=[{"id": "e", "src_id": "a", "dst_id": "ghost", "relation": "related_to"}],
    )
    # "ghost" is not loaded as a node, so it is not offered as a neighbour
    assert g.neighbors("a") == []


def test_edge_between_respects_mode():
    g = _bundle().graph
    assert g.edge_between("n_stefan_cel_mare", "n_moldova") is not None
    # distractor edge hidden in easy view
    assert g.edge_between("n_stefan_cel_mare", "n_transilvania", include_distractors=False) is None
    via = g.edge_between("n_stefan_cel_mare", "n_transilvania", include_distractors=True)
    assert via is not None
