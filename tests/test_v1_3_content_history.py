"""Strict V1.3 history preserves new-current checks and every earlier wave pin."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history as history

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "kg_sample.json": "c9f23c4a9dab1281ad91baaf0e2c836a5b7ab9a6d5f2776799908d76e10f4b85",
    "board_rankings_v37.json": "96409c88927a60e9d6d379237af88a57aef6b40279520bf54f64214017b45806",
    "derived_catalog_v38.json": "1340147300b3d9d174e09d899ac8eaf91756ca0470d0550121af66751ea92d71",
    "cat_mobile_app_pack_contract.json": (
        "8735d304a7d9734a53c03307c034093c910c1a931e73c40df346ed25700f1438"
    ),
}
AFTER = {
    "kg_sample.json": "d035f616b4aef5077d77d9cbbdefbd74c1ce2b360a1874a0533a0bd43bb04f63",
    "board_rankings_v37.json": "e24954508573a06c885be3163b3e25c011a14809a7b358cb0aad004dad9a8f2b",
    "derived_catalog_v38.json": "b4ae19266627b738ebe29928acc5952da9be98415fb8632870243e8634a32ad9",
    "cat_mobile_app_pack_contract.json": (
        "f5ebc91f3cefb2fdc9755ea015d1eae9e58a2edf722621f273e73ef937d82e94"
    ),
}


def current(filename: str) -> dict:
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    return json.loads((ROOT / directory / filename).read_bytes())


def digest(value: dict, filename: str) -> str:
    blob = (json.dumps(value, ensure_ascii=False,
                       indent=2 if filename == "kg_sample.json" or filename in CATALOG_BEFORE
                       else 1) + "\n").encode()
    return hashlib.sha256(blob).hexdigest()


@pytest.mark.parametrize("filename", BASELINE)
def test_v1_3_inverse_preserves_current_checks_and_restores_exact_18832_bytes(filename):
    latest = current(filename)
    untouched = deepcopy(latest)
    restored = history.before_v1_3_artifact(latest, filename)
    assert digest(latest, filename) == AFTER[filename]
    assert digest(restored, filename) == BASELINE[filename]
    assert latest == untouched and restored is not latest
    twice = history.before_v1_3_artifact(restored, filename)
    assert twice == restored and twice is not restored


@pytest.mark.parametrize("filename", BASELINE)
@pytest.mark.parametrize("part", ["head", "row", "order", "duplicate"])
def test_v1_3_inverse_refuses_current_byte_or_record_drift(filename, part):
    latest = current(filename)
    table = "kg_nodes" if filename in {
        "kg_sample.json", "cat_mobile_app_pack_contract.json",
    } else "boards"
    if part == "head":
        latest["manifest" if filename.startswith("cat_mobile") else "meta"]["forged"] = True
    elif part == "row":
        latest[table][0]["forged"] = True
    elif part == "order":
        latest[table][0], latest[table][1] = latest[table][1], latest[table][0]
    else:
        latest[table].append(deepcopy(latest[table][0]))
    untouched = deepcopy(latest)
    with pytest.raises(AssertionError):
        history.before_v1_3_artifact(latest, filename)
    assert latest == untouched


def test_v1_3_graph_inverse_is_only_three_nodes_twelve_edges_and_eleven_degrees():
    latest = current("kg_sample.json")
    previous = history.before_v1_3_artifact(latest, "kg_sample.json")
    old = {row["id"]: row for row in previous["kg_nodes"]}
    new = {row["id"]: row for row in latest["kg_nodes"]}
    assert set(new) - set(old) == set(history._V1_3_NODE_IDS)
    assert len(latest["kg_nodes"]) == 2419 and len(previous["kg_nodes"]) == 2416
    assert len(latest["kg_edges"]) == 9471 and len(previous["kg_edges"]) == 9459
    changed = {
        key: {field for field in old[key] if old[key][field] != new[key][field]}
        for key in old if old[key] != new[key]
    }
    assert changed == {key: {"degree"} for key in history._V1_3_DEGREES}
    assert latest["kg_edges"][:-12] == previous["kg_edges"]
    assert latest["kg_puzzles"] == previous["kg_puzzles"]
    assert len(previous["kg_puzzles"]) == 180
    assert sum(len(row.get("aliases", [])) for row in latest["kg_nodes"]) == 8675
    assert sum(len(row.get("aliases", [])) for row in previous["kg_nodes"]) == 8663


def test_v1_3_rank_inverse_preserves_real_five_row_change_and_finite_row_move():
    latest = current("board_rankings_v37.json")
    previous = history.before_v1_3_artifact(latest, "board_rankings_v37.json")
    old = {row["id"]: row for row in previous["boards"]}
    new = {row["id"]: row for row in latest["boards"]}
    assert len(old) == len(new) == 716
    changed = {
        key: {field: (old[key][field], new[key][field]) for field in old[key]
              if old[key][field] != new[key][field]}
        for key in old if old[key] != new[key]
    }
    assert changed == history._V1_3_RANK_FIELDS
    assert [row["id"] for row in previous["boards"]] != [
        row["id"] for row in latest["boards"]
    ]
    assert all(old[key] == new[key] for key in old if key not in changed)


def test_v1_3_derived_inverse_preserves_all_336_board_records():
    latest = current("derived_catalog_v38.json")
    previous = history.before_v1_3_artifact(latest, "derived_catalog_v38.json")
    assert len(latest["boards"]) == 336
    assert previous["boards"] == latest["boards"]
    assert {key for key in latest["meta"]
            if latest["meta"][key] != previous["meta"][key]} == {
                "kg_sha256", "v37_rankings_sha256",
            }


@pytest.mark.parametrize("repin", [False, True])
@pytest.mark.parametrize("forgery", ["before-hash", "review", "degree", "edge", "count"])
def test_v1_3_refuses_forged_or_repinned_graph_receipt(tmp_path, monkeypatch, repin, forgery):
    receipt = json.loads(history._V1_3_GRAPH_RECEIPT.read_bytes())
    if forgery == "before-hash":
        receipt["before_kg_sha256"] = "0" * 64
    elif forgery == "review":
        receipt["raw_quality_review_sha256"] = "0" * 64
    elif forgery == "degree":
        receipt["old_node_metadata_changes"][0]["changes"]["degree"]["before"] += 1
    elif forgery == "edge":
        receipt["new_edge_records"][0]["bidirectional"] = 1
    else:
        receipt["counts"]["new_curated_rounds"] = 1
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path = tmp_path / "forged-v1-3.json"
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_3_GRAPH_RECEIPT", path)
    if repin:
        monkeypatch.setattr(history, "_V1_3_GRAPH_RECEIPT_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(AssertionError):
        history.before_v1_3_artifact(current("kg_sample.json"), "kg_sample.json")


@pytest.mark.parametrize("filename", ["alchimie_recipe_extensions_v92.json"])
def test_v1_3_catalog_inverse_refuses_unknown_unreviewed_bytes(filename):
    with pytest.raises(AssertionError):
        history.before_v1_3_catalog({"unreviewed": "future catalog"}, filename)


def test_v1_3_unknown_artifact_is_refused():
    with pytest.raises(AssertionError):
        history.before_v1_3_artifact({}, "unknown.json")


CATALOG_BEFORE = {
    "alchimie_recipe_extensions_v92.json": (
        "9b7da100fb59f416667c0f23c04947f61d3d0e07d5712d57176293538302f1e3"
    ),
    "quick_games_v92.json": "cc242a902fd4c040f0e52da94ec95683a9bbcdab41f4b9fb72de5a9c5ff5659c",
    "alchimie_discovery_world_v92.json": (
        "4a6056f3138d0231752056fb588554ee8b4aaa9364511103329ea30120bec1c3"
    ),
}
CATALOG_AFTER = {
    "alchimie_recipe_extensions_v92.json": (
        "b1caa2a46f0d9a2e72b25404fd991f62a20b65cf8604c292170d0efa941757a5"
    ),
    "quick_games_v92.json": "99db98d64b5b7c103ee70eab2b2b79b04d4ff62072942a159caa65518375ed9f",
    "alchimie_discovery_world_v92.json": (
        "28d73ca0c51883f24f370becd6c1fde1eb1c7d034c4be60cd64e8e7c94fbf8d6"
    ),
}


@pytest.mark.parametrize("filename", CATALOG_BEFORE)
def test_v1_3_catalog_inverse_restores_complete_v1_2_bytes_without_mutation(filename):
    latest = current(filename)
    untouched = deepcopy(latest)
    previous = history.before_v1_3_catalog(latest, filename)
    assert digest(latest, filename) == CATALOG_AFTER[filename]
    assert digest(previous, filename) == CATALOG_BEFORE[filename]
    assert latest == untouched and previous is not latest
    assert history.before_v1_3_catalog(previous, filename) == previous
    if filename.startswith("quick"):
        assert previous["boards"] == latest["boards"]
        assert previous["authored"] == latest["authored"]
        assert previous["excluded"] == latest["excluded"]
        changed = {key: {field for field in previous["nodes"][key]
                         if previous["nodes"][key][field] != latest["nodes"][key][field]}
                   for key in previous["nodes"]
                   if previous["nodes"][key] != latest["nodes"][key]}
        assert changed == {key: {"degree"} for key in history._V1_3_DEGREES
                           if key != "n_v4via_usa"}
    elif filename == "alchimie_discovery_world_v92.json":
        for key in ("world", "concepts", "recipes", "goals", "unlocks", "compatible_versions"):
            assert previous[key] == latest[key]
    else:
        assert len(latest["boards"]) == 27
        assert sum(len(row["additions"]) for row in latest["boards"]) == 49
        assert [row["id"] for row in previous["boards"]] == [row["id"] for row in latest["boards"]]
        assert [row["core"] for row in previous["boards"]] == [
            row["core"] for row in latest["boards"]
        ]
        assert [row["additions"] for row in previous["boards"]] == [
            row["additions"] for row in latest["boards"]
        ]


@pytest.mark.parametrize("filename", CATALOG_BEFORE)
@pytest.mark.parametrize("part", ["binding", "review", "record", "order"])
def test_v1_3_catalog_inverse_refuses_artifact_metadata_record_or_order_drift(filename, part):
    latest = current(filename)
    table = "recipes" if filename == "alchimie_discovery_world_v92.json" else "boards"
    if part == "binding":
        latest["bindings"]["kg_sha256"] = "0" * 64
    elif part == "review":
        latest["semantic_reviews" if filename.startswith("alchimie_recipe") else "reviews"][0][
            "reviewer"
        ] = "unreviewed"
    elif part == "record":
        latest[table][0]["forged"] = True
    else:
        latest[table][0], latest[table][1] = latest[table][1], latest[table][0]
    untouched = deepcopy(latest)
    with pytest.raises(AssertionError):
        history.before_v1_3_catalog(latest, filename)
    assert latest == untouched


@pytest.mark.parametrize("repin", [False, True])
@pytest.mark.parametrize("forgery", ["baseline", "degree", "review", "document", "scope"])
def test_v1_3_catalog_inverse_refuses_forged_or_repinned_delta(
    tmp_path, monkeypatch, repin, forgery,
):
    receipt = json.loads(history._V1_3_CATALOG_DELTA.read_bytes())
    delta = receipt["files"]["quick_games_v92.json"]
    if forgery == "baseline":
        delta["baseline_sha256"] = "0" * 64
    elif forgery == "degree":
        delta["node_degrees"]["n_v23via_ghiozdan"]["before"] = 12
    elif forgery == "review":
        delta["metadata_after"]["reviews"][0]["reviewer"] = "unreviewed"
    elif forgery == "document":
        key = next(iter(receipt["staging_documents_sha256"]))
        receipt["staging_documents_sha256"][key] = "0" * 64
    else:
        receipt["scope"] = "Broader unreviewed snapshot repair"
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path = tmp_path / "forged-catalog-v1-3.json"
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_3_CATALOG_DELTA", path)
    if repin:
        monkeypatch.setattr(history, "_V1_3_CATALOG_DELTA_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(AssertionError):
        history.before_v1_3_catalog(current("quick_games_v92.json"), "quick_games_v92.json")
