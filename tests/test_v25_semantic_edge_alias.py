"""Regression guards for the bounded v25 semantic-edge and alias wave (ADR-0033)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace

import pytest

from cat_de_roman_esti.data import load_fixture, mobile_app_pack_snapshot
from cat_de_roman_esti.wordgames.packs import (
    _closure_generations,
    _opening_pairs,
    lant_branch_profile,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService, normalize

_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_TEST_KG = _ROOT / "tests/fixtures/kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_MOBILE_CONTRACT = _ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json"


def _load_data_module():
    scripts = _ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    path = scripts / "semantic_edge_alias_v25_data.py"
    spec = importlib.util.spec_from_file_location("semantic_edge_alias_v25_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DATA = _load_data_module()
import apply_common_words_v24 as APPLIER  # noqa: E402


def _service() -> WordGameService:
    return WordGameService(load_fixture(_PACKAGE_KG).graph)


def _pack() -> dict:
    return json.loads(_PACKAGE_PACK.read_text(encoding="utf-8"))


def test_v25_inventory_and_mirrors_are_exact():
    fixture = json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))
    aliases = sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"])

    assert fixture["meta"]["build_version"] == DATA.BUILD_VERSION
    assert (len(fixture["kg_nodes"]), len(fixture["kg_edges"])) == (2184, 8792)
    assert len(fixture["kg_puzzles"]) == 180
    assert aliases == 7033
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()


def test_v25_all_168_aliases_resolve_to_the_declared_owner_without_blocked_forms():
    svc = _service()
    fixture = json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in fixture["kg_nodes"]}
    blocked = {normalize(value) for value in DATA.BLOCKED_ALIAS_FORMS}
    blocked |= {normalize(value) for value in DATA.DEFERRED_AMBIGUOUS_TERMS}

    assert len(DATA.ALIAS_ADDITIONS) == 132
    assert len(DATA.ALIAS_PROBES) == 168
    for alias, node_id in DATA.ALIAS_PROBES:
        assert normalize(alias) not in blocked
        assert alias in nodes[node_id]["aliases"]
        assert svc.resolve(alias) == node_id

    assert svc.resolve("vecin") == "n_v2via_vecini"
    assert svc.resolve("morcovii") == "n_v24_food_salad_veg_morcov"
    assert svc.resolve("sandvici") == "n_v24_food_snack_sandvis"
    assert svc.resolve("mănânci") == "n_v24_action_food_a_manca"


def test_v25_beginner_probe_improves_only_through_same_referent_vecin_alias():
    svc = _service()
    deferred = {normalize(value) for value in DATA.DEFERRED_AMBIGUOUS_TERMS}
    eligible = [
        term for term in DATA.BEGINNER_BENCHMARK if normalize(term) not in deferred
    ]
    unresolved = [term for term in eligible if svc.resolve(term) is None]

    assert len(eligible) == 234
    assert len(eligible) - len(unresolved) == 219
    assert unresolved == [
        "conopidă",
        "spanac",
        "dinte",
        "curcubeu",
        "piatră",
        "vapor",
        "meserie",
        "săptămână",
        "lună calendaristică",
        "surpriză",
        "rușine",
        "mândrie",
        "speranță",
        "iubire",
        "liniște",
    ]


def test_v25_semantic_edges_land_with_the_exact_reviewed_predicates():
    fixture = json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))
    actual = {
        (edge["src_id"], edge["dst_id"], edge["relation"]): edge
        for edge in fixture["kg_edges"]
    }

    assert len(DATA.SEMANTIC_EDGES) == 25
    for expected in DATA.SEMANTIC_EDGES:
        edge = actual[(expected.source, expected.target, expected.relation)]
        assert edge["label_ro"] == expected.label_ro
        assert math.isclose(float(edge["strength"]), expected.strength)
        assert edge["is_distractor"] == 0
        assert edge["bidirectional"] == expected.bidirectional


def test_v25_edge_catalog_is_specific_and_has_bounded_endpoint_fanout():
    endpoint_counts: dict[str, int] = {}
    for edge in DATA.SEMANTIC_EDGES:
        assert edge.relation != "related_to"
        assert edge.label_ro.strip()
        assert edge.source.startswith("n_v24") or edge.target.startswith("n_v24")
        endpoint_counts[edge.source] = endpoint_counts.get(edge.source, 0) + 1
        endpoint_counts[edge.target] = endpoint_counts.get(edge.target, 0) + 1

    assert max(endpoint_counts.values()) <= 3


def test_v25_pack_is_byte_stable_and_the_33_review_items_remain_playable():
    assert hashlib.sha256(_PACKAGE_PACK.read_bytes()).hexdigest() == DATA.BASELINE_PACK_SHA256
    pack = _pack()
    svc = _service()
    records = {
        record["id"]: (game, record)
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for record in pack[game]
        if record["id"] in set(DATA.REVIEW_ITEM_IDS)
    }

    assert set(records) == set(DATA.REVIEW_ITEM_IDS)
    for item_id in DATA.REVIEW_ITEM_IDS:
        game, record = records[item_id]
        assert record["status"] == "pending"
        assert validate_payload(record, game, svc) == []


def test_v25_intended_topology_changes_stay_inside_reviewed_game_bounds():
    pack = _pack()
    svc = _service()
    by_id = {
        record["id"]: record
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for record in pack[game]
    }

    lant = by_id["lt_gastronomie_218"]
    assert svc.distance(lant["start"], lant["target"]) == 4
    assert lant_branch_profile(svc, lant["start"], lant["target"], 4) == (6, 2, 16)

    alchimie = by_id["al_viata_de_roman_098"]
    closure = _closure_generations(svc, alchimie["seeds"], alchimie["category"])
    assert len(closure) == 111
    assert _opening_pairs(svc, alchimie["seeds"], alchimie["category"]) == 9
    max_fresh = max(
        len(
            [
                result
                for result in svc.common_neighbors(left, right, category=alchimie["category"])
                if result not in alchimie["seeds"]
            ]
        )
        for left, right in combinations(alchimie["seeds"], 2)
    )
    assert max_fresh == 1

    for item_id, responsive_floor in {
        "ct_viata_de_roman_302": 1500,
        "ct_limba_307": 1800,
    }.items():
        target = by_id[item_id]["target"]
        distances = svc.distances_to(target)
        responsive = sum(1 for distance in distances.values() if 1 <= distance <= 5)
        assert len(distances) == 2184
        assert responsive >= responsive_floor


def test_v25_mobile_contract_is_refreshed_in_the_same_transaction():
    checked_in = json.loads(_MOBILE_CONTRACT.read_text(encoding="utf-8"))
    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert checked_in["manifest"]["counts"] == {
        "nodes": 2184,
        "edges": 8792,
        "puzzles": 180,
    }


def test_v25_mobile_refresh_failure_restores_all_five_transaction_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    transaction_files = tuple(tmp_path / f"artifact-{index}.json" for index in range(5))
    originals = {
        path: f'{{"artifact": {index}}}\n'.encode()
        for index, path in enumerate(transaction_files)
    }
    for path, blob in originals.items():
        path.write_bytes(blob)

    fixture_copies = transaction_files[:2]
    pack_copies = transaction_files[2:4]
    mobile_contract = transaction_files[4]
    batch = SimpleNamespace(
        nodes=(),
        edges=(),
        aliases={},
        beginner_benchmark=(),
        intuitive_pairs=(),
        build_version="fixture-v25-rollback-test",
        note="rollback test",
    )
    baseline_fixture = {"kg_nodes": [], "kg_edges": [], "kg_puzzles": [], "meta": {}}
    baseline_pack = {"meta": {}}

    monkeypatch.setattr(APPLIER, "FIXTURE_COPIES", fixture_copies)
    monkeypatch.setattr(APPLIER, "PACK_COPIES", pack_copies)
    monkeypatch.setattr(APPLIER, "MOBILE_CONTRACT", mobile_contract)
    monkeypatch.setattr(APPLIER, "TRANSACTION_FILES", transaction_files)
    monkeypatch.setattr(APPLIER, "_assert_mirrors_identical", lambda: None)
    monkeypatch.setattr(
        APPLIER,
        "_load_json",
        lambda _blob, label: baseline_pack if "pack" in label else baseline_fixture,
    )
    monkeypatch.setattr(APPLIER, "_load_batch", lambda _module_name: batch)
    monkeypatch.setattr(APPLIER, "_detect_already_applied", lambda *_args: None)
    monkeypatch.setattr(APPLIER, "_preflight", lambda *_args: object())
    monkeypatch.setattr(APPLIER.densify_content, "run", lambda *_args: 0)
    monkeypatch.setattr(APPLIER, "_verify_merged_graph", lambda *_args: None)
    monkeypatch.setattr(
        APPLIER, "load_fixture", lambda _path: SimpleNamespace(graph=object())
    )
    monkeypatch.setattr(
        APPLIER, "WordGameService", lambda *, graph: SimpleNamespace(graph=graph)
    )
    monkeypatch.setattr(APPLIER, "_assert_approved_stable", lambda *_args: None)
    monkeypatch.setattr(
        APPLIER, "_stage_explicit_game_items", lambda *_args: (b"", ())
    )

    def fail_mobile_refresh() -> None:
        for path in transaction_files:
            path.write_bytes(b"partially mutated\n")
        raise APPLIER.ApplyError("forced mobile refresh failure")

    monkeypatch.setattr(APPLIER, "_refresh_mobile_contract", fail_mobile_refresh)

    with pytest.raises(APPLIER.ApplyError, match="forced mobile refresh failure"):
        APPLIER.apply(module_name="semantic_edge_alias_v25_data")

    assert {path: path.read_bytes() for path in transaction_files} == originals
