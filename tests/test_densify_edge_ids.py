"""Generated dense-edge IDs must not reuse retired historical IDs."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.densify_content as densify_content


def test_run_allocates_after_present_ids_and_is_repeatable(tmp_path: Path, monkeypatch) -> None:
    """The merge path preserves an ID gap even when rebuild is replaced."""
    base = {
        "kg_nodes": [
            {"id": node_id, "label_ro": node_id, "category": "geografie", "salience": 0.5}
            for node_id in ("n1", "n2", "n3")
        ],
        "kg_edges": [
            {"id": edge_id, "src_id": "n1", "dst_id": "n2", "relation": relation}
            for edge_id, relation in (
                ("de1", "existing-1"),
                ("de7494", "existing-7494"),
                ("de7496", "existing-7496"),  # de7495 is retired.
                ("dd8123", "existing-distractor"),
                ("manual-edge", "manual"),
                ("de-not-a-number", "non-numeric"),
            )
        ],
    }
    fixture = tmp_path / "kg_sample.json"
    fixture.write_text(json.dumps(base), encoding="utf-8")
    monkeypatch.setattr(densify_content, "PACKAGE_FIXTURE", fixture)
    monkeypatch.setattr(densify_content, "TESTS_FIXTURE", fixture)

    captured: list[list[dict]] = []

    def capture_rebuild(data, nodes, edges, *args):
        captured.append(edges)
        return 0

    monkeypatch.setattr(densify_content, "rebuild", capture_rebuild)
    dense = {
        "edges": [
            {"src": "n1", "dst": "n3", "relation": "play", "is_distractor": 0},
            {"src": "n2", "dst": "n3", "relation": "distractor", "is_distractor": 1},
        ]
    }

    assert densify_content.run(dense, "test", "test") == 0
    assert densify_content.run(dense, "test", "test") == 0

    added_id_sets = [
        [edge["id"] for edge in edges if edge["relation"] in {"play", "distractor"}]
        for edges in captured
    ]
    assert added_id_sets == [["de8124", "dd8125"], ["de8124", "dd8125"]]
