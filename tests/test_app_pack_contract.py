from __future__ import annotations

import json
from pathlib import Path

from cat_de_roman_esti.data import (
    APP_PACK_APP,
    APP_PACK_MANIFEST_VERSION,
    APP_PACK_SCHEMA_VERSION,
    content_hash,
    fixture_manifest,
    load_app_pack_fixture,
    load_from_client,
    mobile_app_pack_content_hash,
    mobile_app_pack_snapshot,
    records_from_app_packs,
)

from .conftest import FakeRoeduClient

FIXTURE = Path(__file__).parent / "fixtures" / "kg_app_pack_sample.json"
KG_SAMPLE = Path(__file__).parent / "fixtures" / "kg_sample.json"
MOBILE_CONTRACT_FIXTURE = (
    Path(__file__).parent / "fixtures" / "cat_mobile_app_pack_contract.json"
)


def test_app_pack_fixture_preserves_tags_facets_for_selection():
    bundle = load_app_pack_fixture(FIXTURE)

    assert len(bundle.graph.nodes) == 2
    assert len(bundle.graph.edges) == 1
    assert len(bundle.puzzles) == 1

    node = bundle.graph.node("n_dacia_pack")
    assert node is not None
    assert "topic:istorie" in node.tags
    assert node.facets["topic"] == "daci"
    assert node.facets["category"] == "istorie"
    assert node.facets["difficulty"] == "easy"
    assert node.source == "synthetic-contract-fixture"
    assert node.redistributable is True

    edge = bundle.graph.edge_between("n_dacia_pack", "n_traian_pack")
    assert edge is not None
    assert "source:synthetic" in edge.tags
    assert edge.facets["topic"] == "daci"
    assert edge.redistributable is True

    puzzle = bundle.puzzles[0]
    assert puzzle.tags == (
        "topic:istorie",
        "category:istorie",
        "difficulty:easy",
        "source:synthetic",
    )
    assert puzzle.facets["topic"] == "daci"
    assert puzzle.redistributable is True


def test_app_pack_contract_accepts_only_expected_kg_pack_ids():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    records = records_from_app_packs(raw)
    assert {rec["id"] for rec in records["kg_nodes"]} == {
        "n_dacia_pack",
        "n_traian_pack",
    }
    assert {rec["id"] for rec in records["kg_edges"]} == {"e_dacia_traian_pack"}
    assert {rec["id"] for rec in records["kg_puzzles"]} == {"pz_dacia_traian_pack"}

    raw["packs"][0]["pack_id"] = "roedu:cat_de_roman_esti:other:v1"
    assert records_from_app_packs(raw)["kg_nodes"] == []


def test_app_pack_contract_withholds_kind_mismatched_to_pack():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    edge_pack = next(pack for pack in raw["packs"] if pack["pack_id"].endswith(":kg_edges:v1"))
    node_item = next(pack for pack in raw["packs"] if pack["pack_id"].endswith(":kg_nodes:v1"))[
        "items"
    ][0]
    edge_pack["items"].append(dict(node_item, id="n_wrong_pack"))

    records = records_from_app_packs(raw)

    assert "n_wrong_pack" not in {rec["id"] for rec in records["kg_nodes"]}
    assert {rec["id"] for rec in records["kg_edges"]} == {"e_dacia_traian_pack"}


def test_app_pack_public_filter_fails_closed_and_strips_unsafe_provenance():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pack = raw["packs"][0]
    pack["items"].append(
        {
            "id": "n_unknown_legal",
            "kind": "kg_node",
            "label_ro": "Unknown Legal",
            "category": "istorie",
            "tags": [],
            "facets": {},
            "source": "synthetic-contract-fixture",
            "provenance": {"source_url": "internal://redacted", "sha256": "redacted"},
            "license": "unknown",
            "access_type": "",
            "legal_basis": "",
            "gdpr_relevant": False,
            "redistributable": True,
        }
    )
    pack["items"][0]["provenance"] = {
        "source_url": "internal://redacted",
        "sha256": "redacted",
        "proc_key": "fixture",
    }

    records = records_from_app_packs(raw)

    node_ids = {rec["id"] for rec in records["kg_nodes"]}
    assert "n_dacia_pack" in node_ids
    assert "n_unknown_legal" not in node_ids
    kept = next(rec for rec in records["kg_nodes"] if rec["id"] == "n_dacia_pack")
    assert kept["provenance"] == {"proc_key": "fixture"}


def test_internal_and_non_redistributable_packs_are_withheld():
    raw = {
        "packs": [
            {
                "pack_id": "roedu:cat_de_roman_esti:kg_nodes:internal:v1",
                "app": "cat_de_roman_esti",
                "layer": "internal",
                "schema_version": 1,
                "items": [
                    {
                        "id": "n_internal",
                        "kind": "kg_node",
                        "label_ro": "Internal",
                        "category": "istorie",
                        "access_type": "tdm_exception",
                        "legal_basis": "operator only",
                        "gdpr_relevant": False,
                        "redistributable": False,
                    }
                ],
                "pagination": {"next_cursor": None},
                "withheld": 0,
                "errors": [],
            }
        ]
    }

    assert records_from_app_packs(raw) == {"kg_nodes": [], "kg_edges": [], "kg_puzzles": []}


def test_missing_or_empty_app_packs_yield_empty_bundle(tmp_path):
    fixture = tmp_path / "empty_pack.json"
    fixture.write_text(
        json.dumps(
            {
                "pack_id": "roedu:cat_de_roman_esti:kg_nodes:v1",
                "app": "cat_de_roman_esti",
                "layer": "redistributable",
                "schema_version": 1,
                "items": [],
                "pagination": {"next_cursor": None},
                "withheld": 0,
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    bundle = load_app_pack_fixture(fixture)
    assert len(bundle.graph.nodes) == 0
    assert bundle.graph.edges == []
    assert bundle.puzzles == []


def test_scope_isolation_blocks_other_app_keys(kg_raw):
    allowed = load_from_client(FakeRoeduClient(kg_raw, api_key="cat-de-roman-dev"))
    assert allowed.graph.nodes
    assert allowed.puzzles

    for key in ("social-app-dev", "ro-teacher-dev"):
        denied = load_from_client(FakeRoeduClient(kg_raw, api_key=key))
        assert len(denied.graph.nodes) == 0
        assert denied.graph.edges == []
        assert denied.puzzles == []


def test_client_load_caps_all_product_reads(kg_raw):
    client = FakeRoeduClient(kg_raw, page_size=10)
    bundle = load_from_client(client, max_nodes=5, max_edges=7, max_puzzles=3)

    assert len(bundle.graph.nodes) <= 5
    assert len(bundle.graph.edges) <= 7
    assert len(bundle.puzzles) <= 3


# --------------------------------------------------------------------------- manifest
# A mobile client trusts the fixture manifest to detect a stale offline bundle and pick
# the right generated types; these pin the manifest's shape, determinism and hash rules.


def test_fixture_manifest_shape_and_counts(kg_raw):
    manifest = fixture_manifest(KG_SAMPLE)

    assert manifest["app"] == APP_PACK_APP
    assert manifest["schema_version"] == APP_PACK_SCHEMA_VERSION
    assert manifest["manifest_version"] == APP_PACK_MANIFEST_VERSION
    assert manifest["build_version"]  # non-empty human-facing label
    assert manifest["content_hash"].startswith("sha256:")
    assert len(manifest["content_hash"].split(":", 1)[1]) == 64  # full sha256 hex
    # counts mirror the actual fixture payload
    assert manifest["counts"] == {
        "nodes": len(kg_raw["kg_nodes"]),
        "edges": len(kg_raw["kg_edges"]),
        "puzzles": len(kg_raw["kg_puzzles"]),
    }


def test_fixture_manifest_is_deterministic():
    # Pure function of the content: same fixture -> byte-identical manifest every time.
    assert fixture_manifest(KG_SAMPLE) == fixture_manifest(KG_SAMPLE)


def test_content_hash_is_order_independent(kg_raw):
    nodes, edges, puzzles = kg_raw["kg_nodes"], kg_raw["kg_edges"], kg_raw["kg_puzzles"]
    base = content_hash(nodes, edges, puzzles)
    # Reversing record order must NOT change the hash (canonicalised by id + sorted keys).
    shuffled = content_hash(list(reversed(nodes)), list(reversed(edges)), list(reversed(puzzles)))
    assert base == shuffled


def test_content_hash_changes_when_content_changes(kg_raw):
    nodes, edges, puzzles = kg_raw["kg_nodes"], kg_raw["kg_edges"], kg_raw["kg_puzzles"]
    base = content_hash(nodes, edges, puzzles)
    mutated = [dict(nodes[0], label_ro=nodes[0]["label_ro"] + " (changed)"), *nodes[1:]]
    assert content_hash(mutated, edges, puzzles) != base


def test_fixture_manifest_matches_bundled_copies():
    # The two byte-identical fixture copies must yield the same trust manifest.
    repo_root = Path(__file__).resolve().parents[1]
    package_copy = repo_root / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
    assert fixture_manifest(KG_SAMPLE) == fixture_manifest(package_copy)


# ------------------------------------------------------------- mobile app-pack snapshot
# roedu-mobile consumes this checked-in fixture in its own Jest contract tests. These
# guards keep it generated from the cat fixture, public-only, and hash-compatible with
# the mobile verifier without importing mobile code or starting a server.


def test_mobile_app_pack_contract_snapshot_matches_generator():
    checked_in = json.loads(MOBILE_CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    assert checked_in == mobile_app_pack_snapshot(KG_SAMPLE)


def test_mobile_app_pack_contract_snapshot_is_public_only(kg_raw):
    snapshot = json.loads(MOBILE_CONTRACT_FIXTURE.read_text(encoding="utf-8"))

    assert snapshot["manifest"]["counts"] == {
        "nodes": len(kg_raw["kg_nodes"]),
        "edges": len(kg_raw["kg_edges"]),
        "puzzles": len(kg_raw["kg_puzzles"]),
    }
    assert all(set(node) == {"id", "label_ro"} for node in snapshot["kg_nodes"])
    assert all(set(edge) == {"id", "src_id", "dst_id"} for edge in snapshot["kg_edges"])
    assert all(
        set(puzzle) == {"id", "start_id", "target_id", "difficulty"}
        for puzzle in snapshot["kg_puzzles"]
    )
    serialized = json.dumps(snapshot, ensure_ascii=False)
    assert "solution_path" not in serialized
    assert "hint_neighbors" not in serialized


def test_mobile_app_pack_contract_hash_matches_public_projection():
    snapshot = json.loads(MOBILE_CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    assert snapshot["manifest"]["content_hash"] == mobile_app_pack_content_hash(
        snapshot["kg_nodes"],
        snapshot["kg_edges"],
        snapshot["kg_puzzles"],
    )
