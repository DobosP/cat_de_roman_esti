"""Exact V1.4 reconstruction preserves older assertions and rejects scoped drift."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history as history

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "kg_sample.json": "d035f616b4aef5077d77d9cbbdefbd74c1ce2b360a1874a0533a0bd43bb04f63",
    "board_rankings_v37.json": "e24954508573a06c885be3163b3e25c011a14809a7b358cb0aad004dad9a8f2b",
    "derived_catalog_v38.json": "b4ae19266627b738ebe29928acc5952da9be98415fb8632870243e8634a32ad9",
    "cat_mobile_app_pack_contract.json": (
        "f5ebc91f3cefb2fdc9755ea015d1eae9e58a2edf722621f273e73ef937d82e94"
    ),
    "games_pack.json": "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
}
AFTER = {
    "kg_sample.json": "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6",
    "board_rankings_v37.json": "58fa3d6b02b983cdfed05c9383057acfaccbd200612d3eb97e8279318b1f55ef",
    "derived_catalog_v38.json": "25059439b5c46a04263c229a8a3b9b4fc285240af60e15b7f1fdffa1a98f0c01",
    "cat_mobile_app_pack_contract.json": (
        "2f756c7d71f65a1367648d477c67d6d1af0bd19411149667b77f3cf77a6153b8"
    ),
    "games_pack.json": BASELINE["games_pack.json"],
}


def current(filename: str) -> dict:
    directory = (
        "tests/fixtures" if filename.startswith("cat_mobile") else ("cat_de_roman_esti/fixtures")
    )
    return json.loads((ROOT / directory / filename).read_bytes())


def digest(value: dict, filename: str) -> str:
    indent = 2 if filename == "kg_sample.json" else 1
    return hashlib.sha256(
        (json.dumps(value, ensure_ascii=False, indent=indent) + "\n").encode()
    ).hexdigest()


@pytest.mark.parametrize("filename", BASELINE)
def test_v1_4_inverse_restores_complete_46641d6_bytes_without_mutation(filename):
    latest = current(filename)
    untouched = deepcopy(latest)
    previous = history.before_v1_4_artifact(latest, filename)
    assert digest(latest, filename) == AFTER[filename]
    assert digest(previous, filename) == BASELINE[filename]
    assert latest == untouched and previous is not latest
    twice = history.before_v1_4_artifact(previous, filename)
    assert twice == previous and twice is not previous


@pytest.mark.parametrize("filename", [key for key in BASELINE if key != "games_pack.json"])
@pytest.mark.parametrize("part", ["header", "row", "order", "duplicate", "old-payload"])
def test_v1_4_inverse_refuses_unreviewed_current_bytes(filename, part):
    latest = current(filename)
    table = (
        "kg_nodes"
        if filename in {"kg_sample.json", "cat_mobile_app_pack_contract.json"}
        else "boards"
    )
    if part == "header":
        latest["manifest" if filename.startswith("cat_mobile") else "meta"]["forged"] = True
    elif part == "row":
        latest[table][0]["forged"] = True
    elif part == "order":
        latest[table][0], latest[table][1] = latest[table][1], latest[table][0]
    elif part == "duplicate":
        latest[table].append(deepcopy(latest[table][0]))
    elif filename in {"kg_sample.json", "cat_mobile_app_pack_contract.json"}:
        latest["kg_puzzles"][0]["forged"] = True
    else:
        latest["boards"][-1]["forged"] = True
    untouched = deepcopy(latest)
    with pytest.raises(AssertionError):
        history.before_v1_4_artifact(latest, filename)
    assert latest == untouched


def test_v1_4_graph_scope_is_two_aliases_two_arcs_three_degrees_and_no_other_row_change():
    latest = current("kg_sample.json")
    previous = history.before_v1_4_artifact(latest, "kg_sample.json")
    old = {row["id"]: row for row in previous["kg_nodes"]}
    new = {row["id"]: row for row in latest["kg_nodes"]}
    assert old.keys() == new.keys() and len(old) == 2419
    changed = {
        key: {field for field in old[key] if old[key][field] != new[key][field]}
        for key in old
        if old[key] != new[key]
    }
    assert changed == {
        "n_v24_time_day_ceas": {"aliases"},
        **{key: {"degree"} for key in history._V1_4_DEGREES},
    }
    assert new["n_v24_time_day_ceas"]["aliases"] == [
        *old["n_v24_time_day_ceas"]["aliases"],
        "ceasornic",
        "ceasornice",
    ]
    assert latest["kg_edges"][:-2] == previous["kg_edges"]
    assert latest["kg_edges"][-2:] == history._V1_4_NEW_EDGES
    assert len(latest["kg_edges"]) == 9473 and len(previous["kg_edges"]) == 9471
    assert latest["kg_puzzles"] == previous["kg_puzzles"] and len(previous["kg_puzzles"]) == 180
    assert sum(len(row.get("aliases", [])) for row in latest["kg_nodes"]) == 8677
    assert sum(len(row.get("aliases", [])) for row in previous["kg_nodes"]) == 8675


@pytest.mark.parametrize(
    "filename,total", [("board_rankings_v37.json", 716), ("derived_catalog_v38.json", 336)]
)
def test_v1_4_rank_and_derived_rows_and_order_remain_exact(filename, total):
    latest = current(filename)
    previous = history.before_v1_4_artifact(latest, filename)
    assert latest["boards"] == previous["boards"] and len(latest["boards"]) == total
    expected = {"kg_sha256"}
    if filename == "derived_catalog_v38.json":
        expected.add("v37_rankings_sha256")
    assert {
        key for key in latest["meta"] if latest["meta"][key] != previous["meta"][key]
    } == expected


def test_v1_4_mobile_projection_changes_only_two_public_edges_and_manifest():
    latest = current("cat_mobile_app_pack_contract.json")
    previous = history.before_v1_4_artifact(latest, "cat_mobile_app_pack_contract.json")
    assert latest["kg_nodes"] == previous["kg_nodes"] and len(latest["kg_nodes"]) == 2419
    assert latest["kg_puzzles"] == previous["kg_puzzles"] and len(latest["kg_puzzles"]) == 180
    assert [row for row in latest["kg_edges"] if row["id"] not in {"de8813", "de8814"}] == previous[
        "kg_edges"
    ]
    assert {
        key for key in latest["manifest"] if latest["manifest"][key] != previous["manifest"][key]
    } == {
        "build_version",
        "content_hash",
        "counts",
    }


@pytest.mark.parametrize("repin", [False, True])
@pytest.mark.parametrize(
    "forgery", ["baseline", "module", "review", "alias", "degree", "edge", "scope", "rows"]
)
def test_v1_4_refuses_forged_or_repinned_graph_receipt(tmp_path, monkeypatch, repin, forgery):
    receipt = json.loads(history._V1_4_GRAPH_RECEIPT.read_bytes())
    if forgery == "baseline":
        receipt["kg_before_sha256"] = "0" * 64
    elif forgery == "module":
        receipt["module_sha256"] = "0" * 64
    elif forgery == "review":
        receipt["raw_quality_review_sha256"] = "0" * 64
    elif forgery == "alias":
        receipt["node_field_changes"][0]["changes"]["aliases"]["after"].append("ceasornicul")
    elif forgery == "degree":
        receipt["node_field_changes"][1]["changes"]["degree"]["before"] += 1
    elif forgery == "edge":
        receipt["new_edges"][0]["bidirectional"] = 1
    elif forgery == "scope":
        receipt["new_curated_rounds_or_target_approvals"] = 1
    else:
        receipt["all716_rank_rows_exact"] = False
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path = tmp_path / "forged-v1-4.json"
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_4_GRAPH_RECEIPT", path)
    if repin:
        monkeypatch.setattr(history, "_V1_4_GRAPH_RECEIPT_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(AssertionError):
        history.before_v1_4_artifact(current("kg_sample.json"), "kg_sample.json")


@pytest.mark.parametrize("filename", history._V1_4_CATALOG_BASELINE)
def test_v1_4_unbound_catalog_bytes_are_refused(filename):
    with pytest.raises(AssertionError):
        history.before_v1_4_catalog({"unreviewed": "future or incomplete staging"}, filename)


def test_v1_4_unknown_artifact_is_refused():
    with pytest.raises(AssertionError):
        history.before_v1_4_artifact({}, "unknown.json")


CATALOG_BASELINE = {
    "quick_games_v92.json": "99db98d64b5b7c103ee70eab2b2b79b04d4ff62072942a159caa65518375ed9f",
    "alchimie_discovery_world_v92.json": (
        "28d73ca0c51883f24f370becd6c1fde1eb1c7d034c4be60cd64e8e7c94fbf8d6"
    ),
    "alchimie_recipe_extensions_v92.json": (
        "b1caa2a46f0d9a2e72b25404fd991f62a20b65cf8604c292170d0efa941757a5"
    ),
}
CATALOG_AFTER = {
    "quick_games_v92.json": "a21b3c6e50be6947ea8b9ac181f337566db9e4809dd5165a203338fff20d8609",
    "alchimie_discovery_world_v92.json": (
        "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"
    ),
    "alchimie_recipe_extensions_v92.json": (
        "1dd346c1786ea39d241f534e6a411c1297160771d3fbfa7f89a47fd22f586fb7"
    ),
}


def catalog_digest(value: dict) -> str:
    return hashlib.sha256(
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    ).hexdigest()


@pytest.mark.parametrize("filename", CATALOG_BASELINE)
def test_v1_4_signed_catalog_inverse_restores_complete_v1_3_bytes(filename):
    latest = current(filename)
    untouched = deepcopy(latest)
    previous = history.before_v1_4_catalog(latest, filename)
    assert catalog_digest(latest) == CATALOG_AFTER[filename]
    assert catalog_digest(previous) == CATALOG_BASELINE[filename]
    assert latest == untouched and previous is not latest
    assert history.before_v1_4_catalog(previous, filename) == previous
    if filename.startswith("quick"):
        assert previous["boards"] == latest["boards"]
        assert previous["authored"] == latest["authored"]
        assert previous["excluded"] == latest["excluded"]
        changed = {
            node: {
                field
                for field in previous["nodes"][node]
                if previous["nodes"][node][field] != latest["nodes"][node][field]
            }
            for node in previous["nodes"]
            if previous["nodes"][node] != latest["nodes"][node]
        }
        assert changed == {
            "n_v24_time_day_ceas": {"aliases"},
            **{node: {"degree"} for node in history._V1_4_DEGREES},
        }
    elif filename == "alchimie_discovery_world_v92.json":
        for key in ("world", "concepts", "recipes", "goals", "unlocks", "compatible_versions"):
            assert previous[key] == latest[key]
    else:
        assert previous["boards"] == latest["boards"]
        assert len(latest["boards"]) == 27
        assert sum(len(row["additions"]) for row in latest["boards"]) == 49


@pytest.mark.parametrize("filename", CATALOG_BASELINE)
@pytest.mark.parametrize("part", ["binding", "review", "record", "order"])
def test_v1_4_signed_catalog_inverse_refuses_unreviewed_artifact_drift(filename, part):
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
        history.before_v1_4_catalog(latest, filename)
    assert latest == untouched


@pytest.mark.parametrize("repin", [False, True])
@pytest.mark.parametrize(
    "forgery", ["baseline", "scope", "snapshot", "review", "document", "candidate", "version"]
)
def test_v1_4_signed_catalog_inverse_refuses_forged_or_repinned_delta(
    tmp_path,
    monkeypatch,
    repin,
    forgery,
):
    receipt = json.loads(history._V1_4_CATALOG_DELTA.read_bytes())
    delta = receipt["files"]["quick_games_v92.json"]
    if forgery == "baseline":
        delta["baseline_sha256"] = "0" * 64
    elif forgery == "scope":
        receipt["scope"] = "Broader unreviewed vocabulary/puzzle repair"
    elif forgery == "snapshot":
        delta["quick_node_field_changes"]["n_v24_time_day_ceas"]["aliases"]["after"].append(
            "ceasornicul"
        )
    elif forgery == "review":
        delta["metadata_after"]["reviews"][0]["reviewer"] = "unreviewed"
    elif forgery == "document":
        receipt["staging_documents_sha256"][next(iter(receipt["staging_documents_sha256"]))] = (
            "0" * 64
        )
    elif forgery == "candidate":
        delta["metadata_after"]["candidate_sha256"] = "0" * 64
    else:
        receipt["files"]["alchimie_discovery_world_v92.json"]["metadata_after"][
            "native_source_version"
        ] = 5
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path = tmp_path / "forged-catalog-v1-4.json"
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_4_CATALOG_DELTA", path)
    if repin:
        monkeypatch.setattr(history, "_V1_4_CATALOG_DELTA_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(AssertionError):
        history.before_v1_4_catalog(current("quick_games_v92.json"), "quick_games_v92.json")
