"""A graph correction must bind exact old evidence and remain one transaction."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import apply_common_words_v24 as applier  # noqa: E402
import densify_content as builder  # noqa: E402


def _edge() -> dict:
    return {
        "id": "de99999", "src_id": "a", "dst_id": "b", "relation": "same_category",
        "label_ro": "a false category", "strength": 0.9, "bidirectional": 1,
        "is_distractor": 0,
    }


def _fixture() -> dict:
    return {
        "kg_nodes": [
            {"id": name, "label_ro": name, "category": "gastronomie", "degree": 1}
            for name in ("a", "b")
        ],
        "kg_edges": [_edge()], "kg_puzzles": [], "meta": {},
    }


def _batch() -> applier.Batch:
    return applier.Batch(
        nodes=(), edges=(), aliases={}, game_items=None, expected_game_item_ids=(),
        expected_node_ids=(), beginner_benchmark=("a",), deferred_terms=(),
        intuitive_pairs=(), build_version="removal-test", note="remove reviewed false link",
        remove_edges=(_edge(),),
    )


@pytest.mark.parametrize("change", ["partial", "stale_label", "missing", "duplicate", "bool"])
def test_removal_rejects_incomplete_stale_missing_duplicate_or_retyped_evidence(change):
    prior = _edge()
    if change == "partial":
        del prior["strength"]
    elif change == "stale_label":
        prior["label_ro"] = "unreviewed new category"
    elif change == "missing":
        prior["id"] = "unknown"
    elif change == "bool":
        prior["bidirectional"] = True
    removals = [prior, prior] if change == "duplicate" else [prior]
    fixture = _fixture()
    baseline = deepcopy(fixture)
    with pytest.raises(ValueError):
        builder.remove_reviewed_edges(fixture["kg_edges"], removals)
    assert fixture == baseline


def test_removal_preflight_keeps_source_unchanged_and_checks_corrected_degrees():
    fixture = _fixture()
    baseline = deepcopy(fixture)
    plan = applier._preflight(_batch(), fixture)
    assert fixture == baseline
    assert plan.baseline_edge_count == 0
    assert plan.expected_degrees == {"a": 0, "b": 0}


def test_same_id_cannot_remove_an_unreviewed_duplicate_record():
    reviewed = _edge()
    unreviewed = reviewed | {"dst_id": "c", "label_ro": "different unreviewed claim"}
    edges = [unreviewed, reviewed]
    with pytest.raises(ValueError, match="duplicate edge IDs"):
        builder.remove_reviewed_edges(edges, [reviewed])
    assert edges == [unreviewed, reviewed]


def test_builder_does_not_recycle_the_removed_highest_edge_id(tmp_path, monkeypatch):
    paths = (tmp_path / "package.json", tmp_path / "tests.json")
    for path in paths:
        path.write_text(json.dumps(_fixture()))
    monkeypatch.setattr(builder, "PACKAGE_FIXTURE", paths[0])
    monkeypatch.setattr(builder, "TESTS_FIXTURE", paths[1])
    captured = []
    monkeypatch.setattr(
        builder, "rebuild", lambda _data, _nodes, edges, *_: captured.extend(edges) or 0
    )
    assert builder.run({
        "remove_edges": [_edge()],
        "edges": [{
            "src": "a", "dst": "b", "relation": "related_to",
            "label_ro": "a separately reviewed relation", "strength": 0.8,
        }],
    }, "test", "reviewed correction") == 0
    assert len(captured) == 1
    assert captured[0]["id"] == "de100000"
    assert captured[0]["relation"] == "related_to"


def test_failed_rebuild_rolls_back_both_fixtures_pack_and_mobile(tmp_path, monkeypatch):
    paths = tuple(tmp_path / f"artifact-{i}.json" for i in range(5))
    for path in paths[:2]:
        path.write_text(json.dumps(_fixture()))
    for path in paths[2:]:
        path.write_text('{"meta": {}}\n')
    originals = {path: path.read_bytes() for path in paths}
    monkeypatch.setattr(applier, "TRANSACTION_FILES", paths)
    monkeypatch.setattr(applier, "FIXTURE_COPIES", paths[:2])
    monkeypatch.setattr(applier, "PACK_COPIES", paths[2:4])
    monkeypatch.setattr(applier, "MOBILE_CONTRACT", paths[4])
    monkeypatch.setattr(builder, "PACKAGE_FIXTURE", paths[0])
    monkeypatch.setattr(builder, "TESTS_FIXTURE", paths[1])
    monkeypatch.setattr(applier, "_load_batch", lambda _: _batch())

    def interrupted_rebuild(*_):
        for path in paths:
            path.write_bytes(b"partial rebuild")
        raise RuntimeError("interrupted after edge removal")

    monkeypatch.setattr(builder, "rebuild", interrupted_rebuild)
    with pytest.raises(RuntimeError, match="interrupted after edge removal"):
        applier.apply(module_name="reviewed-test")
    assert {path: path.read_bytes() for path in paths} == originals


def test_dry_run_of_removal_never_invokes_writer(tmp_path, monkeypatch):
    paths = tuple(tmp_path / f"artifact-{i}.json" for i in range(5))
    for path in paths[:2]:
        path.write_text(json.dumps(_fixture()))
    for path in paths[2:]:
        path.write_text('{"meta": {}}\n')
    originals = {path: path.read_bytes() for path in paths}
    monkeypatch.setattr(applier, "TRANSACTION_FILES", paths)
    monkeypatch.setattr(applier, "FIXTURE_COPIES", paths[:2])
    monkeypatch.setattr(applier, "PACK_COPIES", paths[2:4])
    monkeypatch.setattr(applier, "_load_batch", lambda _: _batch())

    def unexpected_write(*_):
        pytest.fail("dry run invoked fixture writer")

    monkeypatch.setattr(builder, "run", unexpected_write)
    applier.apply(dry_run=True, module_name="reviewed-test")
    assert {path: path.read_bytes() for path in paths} == originals
