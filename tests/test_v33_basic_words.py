"""Regression guards for the bounded v33 beginner-word wave."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

from cat_de_roman_esti.data import load_fixture, mobile_app_pack_snapshot
from cat_de_roman_esti.wordgames.contexto import (
    MIN_REACHABLE,
    MIN_RESPONSIVE,
    RESPONSIVE_MAX_HOPS,
)
from cat_de_roman_esti.wordgames.packs import (
    _closure_generations,
    _opening_pairs,
    lant_branch_profile,
)
from cat_de_roman_esti.wordgames.service import WordGameService, normalize

_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_TEST_KG = _ROOT / "tests/fixtures/kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_MOBILE_CONTRACT = _ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json"
_V48_AUDIT = (
    _ROOT / "docs/reviews/v48-alchimie-pending-gate/projection-audit.json"
)
_EXPECTED_NODE_COUNT = 2364
_EXPECTED_EDGE_COUNT = 9217
_EXPECTED_AUTHORED_EDGE_COUNT = 54
_EXPECTED_LOCAL_EDGE_COUNT = 36
_V32_ALIAS_COUNT = 7333

# These are fingerprints of current legacy behavior. Profile pins move only with a gated
# content wave; ADR-0067's removal of two false e-SIGUR edges intentionally changed the
# Contexto closure; V45-V47 strict cleanup narrows dormant pending inventory.
_V32_CONTEXTO_PROFILE_SHA256 = (
    "7ed3bd1237d4ee7c1b4ff332da191ad6bd2ac9e8eb005b4ea4a25753fea57ca8"
)
_V32_LANT_PROFILE_SHA256 = (
    "6fe32a7aacb464d8d30ae2d97bc02e9ed0ef5413ee264e2424f13388a7f8e8c2"
)
_V32_ALCHIMIE_PROFILE_SHA256 = (
    "07aa42811a48c3851313b6075380f2a1e11b5557f4e1c56591c1b545a98536d7"
)
_EXACT_REVIEW_REPORT_SHA256 = (
    "5a01894e6e89fe29aaffee09210949e81cb0505385cc5c65615bf9c4b75f3349"
)
_FULL_PENDING_REPORT_SHA256 = (
    "ac8d764b401e930ba91d34f82f78e43f6ff348d4b34b93e65ff4ed9e4ad7fa6e"
)
_V48_REVIEW_ITEM_IDS = {
    "al_literatura_097",
    "al_viata_de_roman_098",
    "al_viata_de_roman_099",
    "al_viata_de_roman_100",
    "al_viata_de_roman_101",
    "al_viata_de_roman_102",
    "al_viata_de_roman_103",
    "al_viata_de_roman_104",
}


def _load_data_module():
    scripts = _ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    path = scripts / "basic_words_v33_data.py"
    spec = importlib.util.spec_from_file_location("basic_words_v33_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DATA = _load_data_module()
import apply_common_words_v24 as APPLIER  # noqa: E402
import basic_words_v32_data as V32_DATA  # noqa: E402
import critique_pack  # noqa: E402


def _fixture() -> dict:
    return json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))


def _pack() -> dict:
    return json.loads(_PACKAGE_PACK.read_text(encoding="utf-8"))


def _service() -> WordGameService:
    return WordGameService(load_fixture(_PACKAGE_KG).graph)


def _accentless(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _digest(value: object) -> str:
    blob = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _reachable_locally(start: str, adjacency: dict[str, set[str]]) -> frozenset[str]:
    seen: set[str] = set()
    pending = [start]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(adjacency[current] - seen)
    return frozenset(seen)


def _critique_report(ids: set[str] | None) -> tuple[int, int, int, str]:
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK,
        critique_pack.PACKAGE_KG,
    )
    games = list(critique_pack.GAME_KINDS)
    items, pack_findings, selected = critique_pack.run(
        pack,
        svc,
        strong,
        regions,
        games,
        {"pending"},
        ids,
    )
    assert not critique_pack.selection_errors(
        pack,
        games,
        {"pending"},
        ids,
        selected,
    )
    if ids is None:
        for node_id, reason in sorted(regions["generic_nodes"].items()):
            label = critique_pack.node_brief(svc, node_id)["label"]
            pack_findings.append(
                {
                    "check": "nondistinctive_region_link",
                    "level": "WARN",
                    "detail": f"{label}: {reason}",
                }
            )
    report = {
        "thresholds": {
            "salience_floors": critique_pack.SALIENCE_FLOORS,
            "strong_edge": critique_pack.STRONG_EDGE,
            "mirror_pairs": critique_pack.MIRROR_PAIRS,
            "red_herring_warn": critique_pack.RED_HERRING_WARN,
            "red_herring_fail": critique_pack.RED_HERRING_FAIL,
            "member_overuse": critique_pack.MEMBER_OVERUSE,
            "region_fanout": critique_pack.REGION_FANOUT,
            "national_salience": critique_pack.NATIONAL_SALIENCE,
        },
        "items": items,
        "pack_findings": pack_findings,
    }
    report_blob = (json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode()
    return (
        len(selected),
        len(items),
        len(pack_findings),
        hashlib.sha256(report_blob).hexdigest(),
    )


def test_v33_source_inventory_builder_application_counts_and_mirrors():
    fixture = _fixture()
    built = DATA.build_nodes_and_edges()
    edge_keys = {
        (edge.source, edge.target, edge.relation) for edge in DATA.SEMANTIC_EDGES
    }
    alias_count = sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"])
    authored_alias_count = sum(len(concept.aliases) for concept in DATA.CONCEPTS)
    authored_alias_count += sum(len(aliases) for aliases in built["aliases"].values())

    # ADR-0068: the V44 alias-only wave re-stamped the merged fixture.
    assert DATA.BUILD_VERSION == "fixture-v44-contexto-common-words"
    assert len(DATA.CONCEPTS) == len(DATA.NEW_NODE_IDS) == 18
    assert len(set(DATA.NEW_NODE_IDS)) == 18
    assert tuple(map(len, DATA.DOMAIN_NODE_IDS)) == (6, 6, 6)
    assert set().union(*(set(domain) for domain in DATA.DOMAIN_NODE_IDS)) == set(
        DATA.NEW_NODE_IDS
    )
    assert len(DATA.V33_BEGINNER_EXTENSION) == 18
    assert len(DATA.SEMANTIC_EDGES) == len(edge_keys) == _EXPECTED_AUTHORED_EDGE_COUNT
    assert len(built["nodes"]) == 18
    assert len(built["edges"]) == _EXPECTED_AUTHORED_EDGE_COUNT
    assert built == DATA.build_nodes_and_edges()
    assert fixture["meta"]["build_version"] == "fixture-v60-sports-ecosystem-morphology"
    assert (len(fixture["kg_nodes"]), len(fixture["kg_edges"])) == (
        _EXPECTED_NODE_COUNT,
        _EXPECTED_EDGE_COUNT,
    )
    assert len(fixture["kg_puzzles"]) == 180
    # ADR-0065 contributed 40 aliases, ADR-0068 twelve, ADR-0074 eight,
    # ADR-0075 thirty-two, ADR-0076 through ADR-0079 forty-eight each, and
    # ADR-0080 contributed forty-six aliases; ADR-0081 through ADR-0084
    # contributed forty-eight each.
    assert alias_count == _V32_ALIAS_COUNT + authored_alias_count + 522
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()


def test_v33_normalized_canonicals_and_aliases_have_one_safe_owner():
    fixture = _fixture()
    by_id = {node["id"]: node for node in fixture["kg_nodes"]}
    svc = _service()
    labels = [normalize(concept.label) for concept in DATA.CONCEPTS]
    aliases = [alias for concept in DATA.CONCEPTS for alias in concept.aliases]
    alias_keys = [normalize(alias) for alias in aliases]
    authored = set(labels) | set(alias_keys)
    blocked = {normalize(surface) for surface in DATA.BLOCKED_ALIAS_FORMS}
    deferred = {normalize(surface) for surface in DATA.DEFERRED_AMBIGUOUS_TERMS}
    deferred_v32 = {normalize(surface) for surface in V32_DATA.DEFERRED_V32_CONCEPTS}
    deferred_v33 = {normalize(surface) for surface in DATA.DEFERRED_V33_CONCEPTS}

    assert len(labels) == len(set(labels)) == 18
    assert len(alias_keys) == len(set(alias_keys))
    assert not (set(labels) & set(alias_keys))
    assert len(authored) == 18 + len(alias_keys)
    assert deferred_v32 <= deferred_v33
    assert not (authored & blocked)
    assert not (authored & deferred)
    assert not (authored & deferred_v33)

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
            assert svc.resolve(alias) == concept.node_id
            assert svc.resolve(_accentless(alias)) == concept.node_id

    for surface in (*DATA.BLOCKED_ALIAS_FORMS, *DATA.DEFERRED_V33_CONCEPTS):
        assert svc.resolve(surface) not in set(DATA.NEW_NODE_IDS)


def test_v33_exact_edges_form_three_inbound_only_six_node_sccs():
    fixture = _fixture()
    svc = _service()
    new_ids = set(DATA.NEW_NODE_IDS)
    by_id = {node["id"]: node for node in fixture["kg_nodes"]}
    legacy_ids = set(by_id) - new_ids
    incident = [
        edge
        for edge in fixture["kg_edges"]
        if edge["src_id"] in new_ids or edge["dst_id"] in new_ids
    ]
    actual = {
        (edge["src_id"], edge["dst_id"], edge["relation"]): edge
        for edge in incident
    }
    expected = {
        (edge.source, edge.target, edge.relation): edge
        for edge in DATA.SEMANTIC_EDGES
    }
    local_edges = [
        edge
        for edge in DATA.SEMANTIC_EDGES
        if edge.source in new_ids and edge.target in new_ids
    ]
    legacy_bridges = [
        edge
        for edge in DATA.SEMANTIC_EDGES
        if edge.source in legacy_ids and edge.target in new_ids
    ]
    local_outgoing = Counter(edge.source for edge in local_edges)
    bridge_incoming = Counter(edge.target for edge in legacy_bridges)
    local_adjacency = {node_id: set() for node_id in new_ids}
    legacy_new_neighbors: dict[str, set[str]] = {}

    assert len(incident) == len(actual) == len(expected) == _EXPECTED_AUTHORED_EDGE_COUNT
    assert set(actual) == set(expected)
    assert len(local_edges) == _EXPECTED_LOCAL_EDGE_COUNT
    assert len(legacy_bridges) == 18
    assert all(edge.target in new_ids for edge in DATA.SEMANTIC_EDGES)
    assert not any(
        edge.source in new_ids and edge.target in legacy_ids
        for edge in DATA.SEMANTIC_EDGES
    )

    for edge in local_edges:
        local_adjacency[edge.source].add(edge.target)
    for key, authored_edge in expected.items():
        committed = actual[key]
        assert committed["label_ro"] == authored_edge.label_ro
        assert math.isclose(float(committed["strength"]), authored_edge.strength)
        assert committed["relation"] != "related_to"
        assert committed["is_distractor"] == 0
        assert committed["bidirectional"] == 0
        assert committed["label_ro"].strip()
        if authored_edge.source in legacy_ids:
            legacy_new_neighbors.setdefault(authored_edge.source, set()).add(
                authored_edge.target
            )

    components = {_reachable_locally(node_id, local_adjacency) for node_id in new_ids}
    expected_components = {frozenset(domain) for domain in DATA.DOMAIN_NODE_IDS}
    assert components == expected_components
    assert max(map(len, legacy_new_neighbors.values())) <= 3

    for node_id in DATA.NEW_NODE_IDS:
        local_neighbors = set(local_adjacency[node_id]) | {
            edge.source for edge in local_edges if edge.target == node_id
        }
        neighbors = set(svc.neighbor_ids(node_id)) | set(svc.predecessor_ids(node_id))
        same_category = {
            neighbor_id
            for neighbor_id in neighbors
            if svc.node(neighbor_id) is not None
            and svc.node(neighbor_id).category == svc.node(node_id).category
        }
        assert by_id[node_id]["difficulty_tier"] == "easy"
        assert local_outgoing[node_id] == 2
        assert bridge_incoming[node_id] == 1
        assert len(local_neighbors) >= 3
        assert len(neighbors) >= 4
        assert len(same_category) >= 2
        inbound = svc.distances_to(node_id)
        assert len(inbound) >= MIN_REACHABLE
        assert (
            sum(
                1
                for distance in inbound.values()
                if 1 <= distance <= RESPONSIVE_MAX_HOPS
            )
            >= MIN_RESPONSIVE
        )
        assert not (legacy_ids & set(svc.distances_from(node_id)))


def test_v33_extends_the_combined_benchmark_without_rewriting_v32():
    svc = _service()
    prior = V32_DATA.BEGINNER_BENCHMARK
    extension = DATA.V33_BEGINNER_EXTENSION
    deferred = {normalize(term) for term in DATA.DEFERRED_AMBIGUOUS_TERMS}
    prior_eligible = [term for term in prior if normalize(term) not in deferred]
    all_eligible = [
        term for term in DATA.BEGINNER_BENCHMARK if normalize(term) not in deferred
    ]

    assert len(prior) == 306
    assert len(prior_eligible) == 304
    assert DATA.BEGINNER_BENCHMARK == (*prior, *extension)
    assert len(DATA.BEGINNER_BENCHMARK) == 324
    assert len({normalize(term) for term in DATA.BEGINNER_BENCHMARK}) == 324
    assert not ({normalize(term) for term in prior} & {normalize(term) for term in extension})
    assert len(all_eligible) == len(prior_eligible) + 18
    assert all(svc.resolve(term) is not None for term in all_eligible)
    assert {svc.resolve(term) for term in extension} == set(DATA.NEW_NODE_IDS)


def test_v33_replay_is_rejected_without_mutating_transaction_files():
    fixture = _fixture()
    before = {path: path.read_bytes() for path in APPLIER.TRANSACTION_FILES}
    batch = APPLIER._load_batch("basic_words_v33_data")

    assert len(batch.nodes) == 18
    assert len(batch.edges) == _EXPECTED_AUTHORED_EDGE_COUNT
    assert batch.expected_node_ids == DATA.NEW_NODE_IDS
    assert batch.build_version == DATA.BUILD_VERSION
    with pytest.raises(APPLIER.ApplyError, match="already applied"):
        APPLIER._detect_already_applied(batch, fixture)
    assert {path: path.read_bytes() for path in APPLIER.TRANSACTION_FILES} == before


def test_v33_keeps_curated_pack_and_both_critique_reports_stable():
    package_blob = _PACKAGE_PACK.read_bytes()
    pack = _pack()
    statuses = Counter(
        record["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for record in pack[game]
    )

    assert DATA.GAME_ITEM_IDS == ()
    assert hashlib.sha256(package_blob).hexdigest() == DATA.BASELINE_PACK_SHA256
    assert package_blob == _TEST_PACK.read_bytes()
    assert {
        game: len(pack[game])
        for game in ("conexiuni", "contexto", "lant", "alchimie")
    } == {
        "conexiuni": 232,
        "contexto": 207,
        "lant": 97,
        "alchimie": 82,
    }
    # ADR-0068 promotes two bound Contexto targets; V47 promotes one more; V48 promotes
    # one Alchimie board, archives 17 rejects, and retains three A5 holds.
    assert statuses == {"approved": 610, "pending": 8}
    assert len(DATA.REVIEW_ITEM_IDS) == len(set(DATA.REVIEW_ITEM_IDS)) == 33
    v48_audit = json.loads(_V48_AUDIT.read_text(encoding="utf-8"))
    v48_source_records = {
        row["id"]: row["source_record"] for row in v48_audit["items"]
    }
    assert _V48_REVIEW_ITEM_IDS <= set(v48_source_records)
    assert all(
        v48_source_records[item_id]["status"] == "pending"
        for item_id in _V48_REVIEW_ITEM_IDS
    )
    resolved_review_ids = {
        "ct_literatura_298",
        "ct_viata_de_roman_299",
        "ct_gastronomie_300",
        "ct_gastronomie_301",
        "ct_limba_307",
        "ct_societate_303",
        "ct_societate_305",
        "ct_stiinta_306",
        "ct_viata_de_roman_302",
        "ct_viata_de_roman_304",
        "lt_gastronomie_212",
        "lt_gastronomie_218",
        "lt_stiinta_215",
        "lt_stiinta_219",
        "lt_viata_de_roman_213",
        "lt_viata_de_roman_214",
        "lt_viata_de_roman_217",
        "cx_viata_de_roman_291",
        "cx_gastronomie_292",
        "cx_viata_de_roman_293",
        "cx_societate_294",
        "cx_societate_295",
    } | _V48_REVIEW_ITEM_IDS
    pending_review_ids = set(DATA.REVIEW_ITEM_IDS) - resolved_review_ids
    assert _critique_report(pending_review_ids) == (
        3,
        0,
        0,
        _EXACT_REVIEW_REPORT_SHA256,
    )
    assert _critique_report(None) == (
        8,
        0,
        81,
        _FULL_PENDING_REPORT_SHA256,
    )


def test_v33_preserves_legacy_contexto_lant_and_alchimie_profiles():
    pack = _pack()
    svc = _service()
    contexto = {
        record["id"]: sorted(svc.distances_to(record["target"]).items())
        for record in pack["contexto"]
    }
    lant = {
        record["id"]: [
            svc.distance(record["start"], record["target"]),
            *lant_branch_profile(
                svc,
                record["start"],
                record["target"],
                record["optimal"],
            ),
        ]
        for record in pack["lant"]
    }
    alchimie = {
        record["id"]: {
            "opening_pairs": _opening_pairs(
                svc,
                record["seeds"],
                record.get("category"),
            ),
            "generations": sorted(
                _closure_generations(
                    svc,
                    record["seeds"],
                    record.get("category"),
                ).items()
            ),
        }
        for record in pack["alchimie"]
    }

    assert _digest(contexto) == _V32_CONTEXTO_PROFILE_SHA256
    assert _digest(lant) == _V32_LANT_PROFILE_SHA256
    assert _digest(alchimie) == _V32_ALCHIMIE_PROFILE_SHA256


def test_v33_mobile_contract_is_exact_current_and_public():
    checked_in = json.loads(_MOBILE_CONTRACT.read_text(encoding="utf-8"))
    mobile_by_id = {node["id"]: node for node in checked_in["kg_nodes"]}

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert checked_in["manifest"]["build_version"] == (
        "fixture-v60-sports-ecosystem-morphology"
    )
    assert checked_in["manifest"]["counts"] == {
        "nodes": _EXPECTED_NODE_COUNT,
        "edges": _EXPECTED_EDGE_COUNT,
        "puzzles": 180,
    }
    for concept in DATA.CONCEPTS:
        assert mobile_by_id[concept.node_id] == {
            "id": concept.node_id,
            "label_ro": concept.label,
        }
