from __future__ import annotations

import json
from pathlib import Path

from cat_de_roman_esti.data import load_app_pack_fixture, load_from_client, records_from_app_packs

from .conftest import FakeRoeduClient

FIXTURE = Path(__file__).parent / "fixtures" / "kg_app_pack_sample.json"


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
