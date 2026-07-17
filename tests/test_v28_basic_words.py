"""Regression guards for the bounded v28 missing-basic-concepts wave."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

from cat_de_roman_esti.data import load_fixture, mobile_app_pack_snapshot
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
    path = scripts / "basic_words_v28_data.py"
    spec = importlib.util.spec_from_file_location("basic_words_v28_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DATA = _load_data_module()
import common_words_v24_data as V24_DATA  # noqa: E402


def _fixture() -> dict:
    return json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))


def _service() -> WordGameService:
    return WordGameService(load_fixture(_PACKAGE_KG).graph)


def test_v28_inventory_floor_and_mirrors_survive_later_additive_waves():
    fixture = _fixture()
    alias_count = sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"])

    assert DATA.BUILD_VERSION == "fixture-v28-basic-words"
    assert len(fixture["kg_nodes"]) >= 2199
    assert len(fixture["kg_edges"]) >= 8845
    assert len(fixture["kg_puzzles"]) == 180
    assert alias_count >= 7077
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()


def test_v28_all_15_nodes_and_44_aliases_have_exact_owners():
    fixture = _fixture()
    by_id = {node["id"]: node for node in fixture["kg_nodes"]}
    svc = _service()
    built = DATA.build_nodes_and_edges()
    built_by_id = {node["id"]: node for node in built["nodes"]}

    assert len(DATA.CONCEPTS) == len(DATA.NEW_NODE_IDS) == 15
    assert set(DATA.NEW_NODE_IDS) == set(built_by_id)
    assert sum(len(concept.aliases) for concept in DATA.CONCEPTS) == 44

    normalized_aliases: set[str] = set()
    for concept in DATA.CONCEPTS:
        committed = by_id[concept.node_id]
        assert committed["node_type"] == "concept"
        assert committed["label_ro"] == concept.label
        assert committed["category"] == concept.category
        assert committed["description"] == concept.description
        assert math.isclose(float(committed["salience"]), concept.salience)
        assert set(concept.aliases) <= set(committed.get("aliases", ()))
        assert svc.resolve(concept.label) == concept.node_id
        for alias in concept.aliases:
            normalized = normalize(alias)
            assert normalized not in normalized_aliases
            normalized_aliases.add(normalized)
            assert svc.resolve(alias) == concept.node_id

    assert len(normalized_aliases) == 44


def test_v28_guarded_non_aliases_do_not_acquire_a_v28_owner():
    svc = _service()
    new_ids = set(DATA.NEW_NODE_IDS)
    blocked = {normalize(surface) for surface in DATA.BLOCKED_ALIAS_FORMS}
    authored = {
        normalize(surface)
        for concept in DATA.CONCEPTS
        for surface in (concept.label, *concept.aliases)
    }

    assert len(DATA.BLOCKED_ALIAS_FORMS) == 12
    assert not (authored & blocked)
    for surface in DATA.BLOCKED_ALIAS_FORMS:
        assert svc.resolve(surface) not in new_ids

    assert svc.resolve("lună") == "n_v24_nature_sky_luna"
    assert svc.resolve("luni") is None
    assert svc.resolve("vapori") is None


def test_v28_resolves_all_234_eligible_terms_and_preserves_deferred_senses():
    svc = _service()
    new_ids = set(DATA.NEW_NODE_IDS)

    assert DATA.DEFERRED_AMBIGUOUS_TERMS == V24_DATA.DEFERRED_AMBIGUOUS_TERMS
    deferred = {normalize(term) for term in DATA.DEFERRED_AMBIGUOUS_TERMS}
    assert len(deferred) == 11
    eligible = [
        term for term in DATA.BEGINNER_BENCHMARK if normalize(term) not in deferred
    ]
    resolved = {term: svc.resolve(term) for term in eligible}

    assert len(DATA.BEGINNER_BENCHMARK) == 236
    assert len(eligible) == 234
    assert all(owner is not None for owner in resolved.values())
    assert sum(owner in new_ids for owner in resolved.values()) == 15
    assert {
        normalize(term) for term, owner in resolved.items() if owner in new_ids
    } == {normalize(concept.label) for concept in DATA.CONCEPTS}
    assert all(svc.resolve(term) not in new_ids for term in DATA.DEFERRED_AMBIGUOUS_TERMS)


def test_v28_exact_53_semantic_edges_and_topology():
    fixture = _fixture()
    svc = _service()
    new_ids = set(DATA.NEW_NODE_IDS)
    incident_edges = [
        edge
        for edge in fixture["kg_edges"]
        if edge["src_id"] in new_ids or edge["dst_id"] in new_ids
    ]
    actual = {
        (edge["src_id"], edge["dst_id"], edge["relation"]): edge
        for edge in incident_edges
    }
    expected = {
        (edge.source, edge.target, edge.relation): edge
        for edge in DATA.SEMANTIC_EDGES
    }

    assert len(DATA.SEMANTIC_EDGES) == len(expected) == 53
    assert len(incident_edges) == len(actual) >= 53
    assert set(expected) <= set(actual)
    for key, authored in expected.items():
        committed = actual[key]
        assert committed["label_ro"] == authored.label_ro
        assert math.isclose(float(committed["strength"]), authored.strength)
        assert committed["is_distractor"] == 0
        assert committed["bidirectional"] == authored.bidirectional

    authored_degrees = Counter(
        endpoint
        for edge in DATA.SEMANTIC_EDGES
        for endpoint in (edge.source, edge.target)
        if endpoint in new_ids
    )
    authored_outgoing = Counter(
        edge.source for edge in DATA.SEMANTIC_EDGES if edge.source in new_ids
    )
    expected_degrees = {node_id: 4 for node_id in DATA.NEW_NODE_IDS}
    expected_degrees["n_v28_food_vegetable_spanac"] = 5
    assert dict(authored_degrees) == expected_degrees
    assert all(authored_outgoing[node_id] >= 2 for node_id in DATA.NEW_NODE_IDS)

    by_id = {node["id"]: node for node in fixture["kg_nodes"]}
    for node_id, degree in expected_degrees.items():
        incident = set(svc.neighbor_ids(node_id)) | set(svc.predecessor_ids(node_id))
        same_category = {
            neighbor_id
            for neighbor_id in incident
            if svc.node(neighbor_id) is not None
            and svc.node(neighbor_id).category == svc.node(node_id).category
        }
        assert by_id[node_id]["degree"] >= degree
        assert len(incident) >= degree
        assert len(same_category) >= 2


def test_v28_keeps_the_entire_game_pack_byte_stable_and_unpromoted():
    package_blob = _PACKAGE_PACK.read_bytes()
    pack = json.loads(package_blob)
    statuses = Counter(
        record["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for record in pack[game]
    )

    assert DATA.GAME_ITEM_IDS == ()
    assert hashlib.sha256(package_blob).hexdigest() == DATA.BASELINE_PACK_SHA256
    assert package_blob == _TEST_PACK.read_bytes()
    assert {game: len(pack[game]) for game in ("conexiuni", "contexto", "lant", "alchimie")} == {
        "conexiuni": 288,
        "contexto": 207,
        "lant": 201,
        "alchimie": 98,
    }
    assert statuses == {"approved": 572, "pending": 222}


def test_v28_mobile_contract_stays_current_and_contains_the_v28_nodes():
    checked_in = json.loads(_MOBILE_CONTRACT.read_text(encoding="utf-8"))
    mobile_by_id = {node["id"]: node for node in checked_in["kg_nodes"]}

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    counts = checked_in["manifest"]["counts"]
    assert counts["nodes"] >= 2199
    assert counts["edges"] >= 8845
    assert counts["puzzles"] == 180
    for concept in DATA.CONCEPTS:
        assert mobile_by_id[concept.node_id] == {
            "id": concept.node_id,
            "label_ro": concept.label,
        }
