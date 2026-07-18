"""Regression guards for the bounded v31 beginner-word wave."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from cat_de_roman_esti.data import load_fixture, mobile_app_pack_snapshot
from cat_de_roman_esti.wordgames.contexto import (
    MIN_REACHABLE,
    MIN_RESPONSIVE,
    RESPONSIVE_MAX_HOPS,
)
from cat_de_roman_esti.wordgames.service import WordGameService, normalize

_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_TEST_KG = _ROOT / "tests/fixtures/kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_MOBILE_CONTRACT = _ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json"
_EXPECTED_EDGE_COUNT = 51


def _load_data_module():
    scripts = _ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    path = scripts / "basic_words_v31_data.py"
    spec = importlib.util.spec_from_file_location("basic_words_v31_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DATA = _load_data_module()
import basic_words_v30_data as V30_DATA  # noqa: E402


def _fixture() -> dict:
    return json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))


def _service() -> WordGameService:
    return WordGameService(load_fixture(_PACKAGE_KG).graph)


def _accentless(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def test_v31_source_inventory_floor_and_mirrors_survive_additive_waves():
    fixture = _fixture()
    alias_count = sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"])
    surfaces = [
        normalize(surface)
        for concept in DATA.CONCEPTS
        for surface in (concept.label, *concept.aliases)
    ]
    edge_keys = {(edge.source, edge.target, edge.relation) for edge in DATA.SEMANTIC_EDGES}

    assert DATA.BUILD_VERSION == "fixture-v31-hygiene-lower-limb-cleaning"
    assert len(DATA.CONCEPTS) == len(DATA.NEW_NODE_IDS) == 17
    assert len(DATA.V31_BEGINNER_EXTENSION) == 17
    assert sum(len(concept.aliases) for concept in DATA.CONCEPTS) == 61
    assert len(surfaces) == len(set(surfaces)) == 78
    assert len(DATA.SEMANTIC_EDGES) == len(edge_keys) == _EXPECTED_EDGE_COUNT
    assert len(fixture["kg_nodes"]) >= 2251
    assert len(fixture["kg_edges"]) >= 9014
    assert len(fixture["kg_puzzles"]) == 180
    assert alias_count >= 7264
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()


def test_v31_all_canonicals_and_aliases_have_one_exact_owner():
    fixture = _fixture()
    by_id = {node["id"]: node for node in fixture["kg_nodes"]}
    svc = _service()
    observed: set[str] = set()

    for concept in DATA.CONCEPTS:
        committed = by_id[concept.node_id]
        assert committed["node_type"] == "concept"
        assert committed["label_ro"] == concept.label
        assert committed["category"] == concept.category
        assert committed["description"] == concept.description
        assert math.isclose(float(committed["salience"]), concept.salience)
        assert tuple(committed.get("aliases", ())) == concept.aliases
        assert svc.resolve(concept.label) == concept.node_id
        assert svc.resolve(_accentless(concept.label)) == concept.node_id
        for alias in concept.aliases:
            key = normalize(alias)
            assert key not in observed
            observed.add(key)
            assert svc.resolve(alias) == concept.node_id
            assert svc.resolve(_accentless(alias)) == concept.node_id

    assert len(observed) == 61


def test_v31_sense_guards_keep_ambiguous_and_neighboring_forms_separate():
    svc = _service()
    new_ids = set(DATA.NEW_NODE_IDS)
    authored = {
        normalize(surface)
        for concept in DATA.CONCEPTS
        for surface in (concept.label, *concept.aliases)
    }
    guarded = (*DATA.BLOCKED_ALIAS_FORMS, *DATA.DEFERRED_V31_CONCEPTS)

    assert len(DATA.BLOCKED_ALIAS_FORMS) == 32
    assert len({normalize(surface) for surface in DATA.BLOCKED_ALIAS_FORMS}) == 29
    assert len(DATA.DEFERRED_V31_CONCEPTS) == 14
    assert not (authored & {normalize(surface) for surface in guarded})
    for surface in guarded:
        assert svc.resolve(surface) not in new_ids

    assert svc.resolve("periuță") != "n_v31_hygiene_oral_periuta_dinti"
    assert svc.resolve("pastă") != "n_v31_hygiene_oral_pasta_dinti"
    assert svc.resolve("burete") != "n_v31_cleaning_dishes_burete_vase"
    assert svc.resolve("mătură") not in new_ids


def test_v31_exact_semantic_edges_and_inbound_beginner_topology():
    fixture = _fixture()
    svc = _service()
    new_ids = set(DATA.NEW_NODE_IDS)
    by_id = {node["id"]: node for node in fixture["kg_nodes"]}
    legacy_ids = set(by_id) - new_ids
    later_wave_ids = {
        node_id
        for node_id in legacy_ids
        if (match := re.match(r"n_v(\d+)_", node_id))
        and int(match.group(1)) > 31
    }
    mature_legacy_ids = legacy_ids - later_wave_ids
    incident = [
        edge
        for edge in fixture["kg_edges"]
        if edge["src_id"] in new_ids or edge["dst_id"] in new_ids
    ]
    actual = {(edge["src_id"], edge["dst_id"], edge["relation"]): edge for edge in incident}
    expected = {(edge.source, edge.target, edge.relation): edge for edge in DATA.SEMANTIC_EDGES}
    legacy_bridges = [edge for edge in DATA.SEMANTIC_EDGES if edge.source not in new_ids]
    outgoing = Counter(edge.source for edge in DATA.SEMANTIC_EDGES)
    incoming = Counter(edge.target for edge in DATA.SEMANTIC_EDGES)
    legacy_new_neighbors: dict[str, set[str]] = {}

    assert len(incident) == len(actual) >= _EXPECTED_EDGE_COUNT
    assert len(expected) == _EXPECTED_EDGE_COUNT
    assert set(expected) <= set(actual)
    assert len(legacy_bridges) == 17
    assert all(edge.target in new_ids for edge in DATA.SEMANTIC_EDGES)
    for key, authored in expected.items():
        committed = actual[key]
        assert committed["label_ro"] == authored.label_ro
        assert math.isclose(float(committed["strength"]), authored.strength)
        assert committed["relation"] != "related_to"
        assert committed["is_distractor"] == 0
        assert committed["bidirectional"] == 0
        assert committed["label_ro"].strip()
        if authored.source not in new_ids:
            legacy_new_neighbors.setdefault(authored.source, set()).add(authored.target)

    assert len(legacy_new_neighbors) == 8
    assert max(map(len, legacy_new_neighbors.values())) <= 3
    for node_id in DATA.NEW_NODE_IDS:
        neighbors = set(svc.neighbor_ids(node_id)) | set(svc.predecessor_ids(node_id))
        same_category = {
            neighbor_id
            for neighbor_id in neighbors
            if svc.node(neighbor_id) is not None
            and svc.node(neighbor_id).category == svc.node(node_id).category
        }
        assert by_id[node_id]["difficulty_tier"] == "easy"
        assert len(neighbors) >= 4
        assert len(same_category) >= 2
        assert outgoing[node_id] >= 2
        assert incoming[node_id] >= 1
        inbound = svc.distances_to(node_id)
        assert len(inbound) >= MIN_REACHABLE
        assert (
            sum(1 for distance in inbound.values() if 1 <= distance <= RESPONSIVE_MAX_HOPS)
            >= MIN_RESPONSIVE
        )
        assert not (mature_legacy_ids & set(svc.distances_from(node_id)))


def test_v31_preserves_prior_coverage_and_resolves_its_extension():
    svc = _service()
    deferred = {normalize(term) for term in DATA.DEFERRED_AMBIGUOUS_TERMS}
    v30_eligible = [term for term in V30_DATA.BEGINNER_BENCHMARK if normalize(term) not in deferred]
    all_eligible = [term for term in DATA.BEGINNER_BENCHMARK if normalize(term) not in deferred]

    assert len(V30_DATA.BEGINNER_BENCHMARK) == 271
    assert len(v30_eligible) == 269
    assert all(svc.resolve(term) is not None for term in v30_eligible)
    assert len(DATA.BEGINNER_BENCHMARK) == 288
    assert len(all_eligible) == 286
    assert all(svc.resolve(term) is not None for term in all_eligible)
    assert {svc.resolve(term) for term in DATA.V31_BEGINNER_EXTENSION} == set(DATA.NEW_NODE_IDS)


def test_v31_keeps_the_entire_game_pack_byte_stable_and_unpromoted():
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


def test_v31_mobile_contract_stays_current_and_keeps_v31_public():
    checked_in = json.loads(_MOBILE_CONTRACT.read_text(encoding="utf-8"))
    mobile_by_id = {node["id"]: node for node in checked_in["kg_nodes"]}

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    counts = checked_in["manifest"]["counts"]
    assert counts["nodes"] >= 2251
    assert counts["edges"] >= 9014
    assert counts["puzzles"] == 180
    for concept in DATA.CONCEPTS:
        assert mobile_by_id[concept.node_id] == {
            "id": concept.node_id,
            "label_ro": concept.label,
        }
