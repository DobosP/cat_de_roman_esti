"""Regression guards for the v24 beginner common-word dataset wave.

The generation inventory lives in ``scripts/common_words_v24_data.py``.  Keeping
the benchmark and intended IDs there gives the content builder and these tests one
shared contract instead of duplicating a long vocabulary list in two places.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections.abc import Iterable, Mapping
from itertools import combinations
from pathlib import Path

from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.wordgames.packs import (
    GAME_KINDS,
    _closure_generations,
    _opening_pairs,
    lant_branch_profile,
    validate_envelope,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService, normalize

_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_KG = _ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
_TEST_KG = _ROOT / "tests" / "fixtures" / "kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti" / "fixtures" / "games_pack.json"
_TEST_PACK = _ROOT / "tests" / "fixtures" / "games_pack.json"


def _load_data_module():
    path = _ROOT / "scripts" / "common_words_v24_data.py"
    spec = importlib.util.spec_from_file_location("common_words_v24_data", path)
    assert spec is not None and spec.loader is not None, f"cannot import {path}"
    module = importlib.util.module_from_spec(spec)
    # Dataclass decorators and similar helpers may consult sys.modules while the
    # module body is executing, so register this file-backed module first.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DATA = _load_data_module()


def _built_content() -> tuple[list[dict], list[dict], Mapping[str, Iterable[str]]]:
    """Accept both builder shapes used by enrichment scripts during authoring."""

    built = DATA.build_nodes_and_edges()
    aliases: Mapping[str, Iterable[str]] = {}
    if isinstance(built, Mapping):
        assert "nodes" in built and "edges" in built, (
            "build_nodes_and_edges() mapping must contain 'nodes' and 'edges'"
        )
        nodes = built["nodes"]
        edges = built["edges"]
        raw_aliases = built.get("aliases", {})
        assert isinstance(raw_aliases, Mapping), "builder 'aliases' must be a mapping"
        aliases = raw_aliases
    else:
        assert isinstance(built, tuple) and len(built) == 2, (
            "build_nodes_and_edges() must return {'nodes', 'edges', 'aliases'?} "
            "or (nodes, edges)"
        )
        nodes, edges = built

    assert isinstance(nodes, (list, tuple)) and all(
        isinstance(node, dict) for node in nodes
    )
    assert isinstance(edges, (list, tuple)) and all(
        isinstance(edge, dict) for edge in edges
    )
    return list(nodes), list(edges), aliases


def _fixture_service() -> WordGameService:
    return WordGameService(load_fixture(_PACKAGE_KG).graph)


def _new_ids() -> set[str]:
    ids = {str(node_id) for node_id in DATA.NEW_NODE_IDS}
    assert ids, "NEW_NODE_IDS must declare the v24 graph inventory"
    assert all(node_id.startswith("n_v24") for node_id in ids), ids
    return ids


def _candidate_item_ids() -> dict[str, tuple[str, ...]]:
    """Normalize either game->IDs, ID->game, or a flat iterable of IDs."""

    raw = getattr(DATA, "GAME_ITEM_IDS", None)
    assert raw, (
        "GAME_ITEM_IDS must declare at least one pending v24 game candidate; "
        "do not silently omit game coverage"
    )
    by_game: dict[str, list[str]] = {game: [] for game in GAME_KINDS}
    prefixes = {"cx": "conexiuni", "ct": "contexto", "lt": "lant", "al": "alchimie"}

    if isinstance(raw, Mapping):
        if set(raw) <= set(GAME_KINDS):
            for game, values in raw.items():
                values = (values,) if isinstance(values, str) else values
                by_game[str(game)].extend(str(value) for value in values)
        else:
            for item_id, game in raw.items():
                assert game in GAME_KINDS, f"unknown game for {item_id!r}: {game!r}"
                by_game[str(game)].append(str(item_id))
    else:
        assert not isinstance(raw, (str, bytes))
        for value in raw:
            item_id = str(value)
            game = prefixes.get(item_id.split("_", 1)[0])
            assert game is not None, f"cannot infer game from candidate id {item_id!r}"
            by_game[game].append(item_id)

    normalized = {game: tuple(ids) for game, ids in by_game.items() if ids}
    assert normalized, "GAME_ITEM_IDS resolved to an empty candidate inventory"
    assert len({item_id for ids in normalized.values() for item_id in ids}) == sum(
        len(ids) for ids in normalized.values()
    ), "GAME_ITEM_IDS must not repeat an item ID"
    return normalized


def test_v24_builder_inventory_matches_the_committed_fixture_and_resolves_labels():
    built_nodes, _, built_aliases = _built_content()
    intended_ids = _new_ids()
    built_by_id = {str(node["id"]): node for node in built_nodes}
    fixture = json.loads(_PACKAGE_KG.read_text(encoding="utf-8"))
    fixture_by_id = {str(node["id"]): node for node in fixture["kg_nodes"]}
    svc = _fixture_service()

    assert set(built_by_id) == intended_ids, (
        "NEW_NODE_IDS and build_nodes_and_edges() must describe the same new nodes"
    )
    assert intended_ids <= set(fixture_by_id), "the intended v24 nodes were not merged"

    failures: list[str] = []
    for node_id in sorted(intended_ids):
        intended = built_by_id[node_id]
        committed = fixture_by_id[node_id]
        for field in ("label_ro", "category", "node_type"):
            if committed.get(field) != intended.get(field):
                failures.append(
                    f"{node_id}: {field}={committed.get(field)!r}, "
                    f"expected {intended.get(field)!r}"
                )
        label = str(intended["label_ro"])
        if svc.resolve(label) != node_id:
            failures.append(f"{label!r} resolves to {svc.resolve(label)!r}, expected {node_id}")

        declared_aliases = {str(alias) for alias in built_aliases.get(node_id, ())}
        committed_aliases = {str(alias) for alias in committed.get("aliases", ())}
        if not declared_aliases <= committed_aliases:
            failures.append(
                f"{node_id}: missing declared aliases "
                f"{sorted(declared_aliases - committed_aliases)!r}"
            )

    assert not failures, "\n" + "\n".join(failures)


def test_v24_beginner_benchmark_has_at_least_ninety_percent_semantic_coverage():
    benchmark = tuple(str(term) for term in DATA.BEGINNER_BENCHMARK)
    deferred = {normalize(str(term)) for term in DATA.DEFERRED_AMBIGUOUS_TERMS}
    eligible = [term for term in benchmark if normalize(term) not in deferred]
    svc = _fixture_service()

    assert benchmark, "BEGINNER_BENCHMARK must not be empty"
    assert eligible, "all benchmark terms were incorrectly marked deferred"
    resolved = [term for term in eligible if svc.resolve(term) is not None]
    unresolved = [term for term in eligible if svc.resolve(term) is None]

    assert len(resolved) * 10 >= len(eligible) * 9, (
        f"semantic exact-resolution coverage is {len(resolved)}/{len(eligible)} "
        f"({len(resolved) / len(eligible):.1%}); unresolved={unresolved!r}; "
        f"deferred={sorted(deferred)!r}"
    )


def test_v24_new_nodes_have_playable_incident_and_same_category_degree():
    svc = _fixture_service()
    low_incident: dict[str, list[str]] = {}
    low_same_category: dict[str, list[str]] = {}

    for node_id in sorted(_new_ids()):
        node = svc.node(node_id)
        assert node is not None, f"missing intended node {node_id}"
        # Both indexes exclude distractors. Treat the quality requirement as incident
        # degree so a deliberately directed relation still contributes to graph support.
        incident = set(svc.neighbor_ids(node_id)) | set(svc.predecessor_ids(node_id))
        same_category = sorted(
            neighbor_id
            for neighbor_id in incident
            if svc.node(neighbor_id) is not None
            and svc.node(neighbor_id).category == node.category
        )
        if len(incident) < 4:
            low_incident[node_id] = sorted(incident)
        if len(same_category) < 2:
            low_same_category[node_id] = same_category

    assert not low_incident and not low_same_category, (
        f"new nodes below incident degree 4: {low_incident!r}; "
        f"below two same-category neighbors: {low_same_category!r}"
    )


def test_v24_intuitive_pair_direct_edge_coverage_is_at_least_eighty_percent():
    pairs = tuple((str(a), str(b)) for a, b in DATA.INTUITIVE_PAIRS)
    svc = _fixture_service()
    assert pairs, "INTUITIVE_PAIRS must not be empty"

    covered: list[tuple[str, str]] = []
    missing: list[tuple[str, str, str]] = []
    for left, right in pairs:
        left_id, right_id = svc.resolve(left), svc.resolve(right)
        if left_id is None or right_id is None:
            missing.append((left, right, "unresolved endpoint"))
            continue
        if svc.link(left_id, right_id) is not None or svc.link(right_id, left_id) is not None:
            covered.append((left, right))
        else:
            missing.append((left, right, "no direct non-distractor edge"))

    assert len(covered) * 5 >= len(pairs) * 4, (
        f"intuitive direct-edge coverage is {len(covered)}/{len(pairs)} "
        f"({len(covered) / len(pairs):.1%}); missing={missing!r}"
    )


def test_v24_morcov_mancare_and_tabla_beginner_examples():
    built_nodes, _, _ = _built_content()
    morcov_ids = [
        str(node["id"])
        for node in built_nodes
        if normalize(str(node["label_ro"])) == normalize("Morcov")
    ]
    assert len(morcov_ids) == 1, f"expected one intended Morcov node, got {morcov_ids!r}"
    morcov_id = morcov_ids[0]
    svc = _fixture_service()

    assert svc.resolve("morcov") == morcov_id
    assert svc.resolve("morcovi") == morcov_id
    assert svc.resolve("morcovul") == morcov_id

    mancare_id = svc.resolve("mâncare")
    assert mancare_id == "n_v4gas_mancare"
    assert svc.resolve("mancare") == mancare_id

    tabla_id = svc.resolve("tablă")
    assert tabla_id == "n_v23via_tabla_scolara"
    assert svc.resolve("tabla") == tabla_id
    tabla = svc.node(tabla_id)
    assert tabla is not None
    assert "tablă" in set(tabla.aliases)


def test_v24_declared_game_candidates_are_present_pending_and_playable():
    declared = _candidate_item_ids()
    pack = json.loads(_PACKAGE_PACK.read_text(encoding="utf-8"))
    svc = _fixture_service()
    actual: dict[str, tuple[str, dict]] = {}
    for game in GAME_KINDS:
        for record in pack[game]:
            item_id = str(record["id"])
            assert item_id not in actual, f"duplicate pack item id {item_id!r}"
            actual[item_id] = (game, record)

    failures: list[str] = []
    for expected_game, item_ids in declared.items():
        for item_id in item_ids:
            found = actual.get(item_id)
            if found is None:
                failures.append(f"{expected_game}:{item_id}: missing from games pack")
                continue
            actual_game, record = found
            if actual_game != expected_game:
                failures.append(
                    f"{item_id}: stored under {actual_game}, expected {expected_game}"
                )
                continue
            if record.get("status") != "pending":
                failures.append(
                    f"{expected_game}:{item_id}: status={record.get('status')!r}, expected pending"
                )
            errors = validate_envelope(record, expected_game)
            errors.extend(validate_payload(record, expected_game, svc))
            failures.extend(f"{expected_game}:{item_id}: {error}" for error in errors)

    assert not failures, "\n" + "\n".join(failures)


def test_v24_fixture_and_pack_mirrors_are_byte_identical():
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()


def _declared_records() -> dict[str, list[dict]]:
    declared = _candidate_item_ids()
    pack = json.loads(_PACKAGE_PACK.read_text(encoding="utf-8"))
    return {
        game: [record for record in pack[game] if record["id"] in set(declared.get(game, ()))]
        for game in GAME_KINDS
    }


def test_v24_game_wave_has_the_reviewed_per_game_sizes():
    records = _declared_records()
    assert {game: len(items) for game, items in records.items()} == {
        "conexiuni": 4,
        "contexto": 8,
        "lant": 8,
        "alchimie": 6,
    }


def test_v24_contexto_targets_are_familiar_broad_and_responsive():
    svc = _fixture_service()
    records = _declared_records()["contexto"]
    benchmark = {normalize(str(term)) for term in DATA.BEGINNER_BENCHMARK}
    graph_size = len(svc.graph.nodes)

    for record in records:
        target = str(record["target"])
        distances = svc.distances_to(target)
        responsive = sum(1 for distance in distances.values() if 1 <= distance <= 5)
        benchmark_predecessors = [
            node_id
            for node_id in svc.predecessor_ids(target)
            if normalize(svc.label(node_id)) in benchmark
        ]
        far_benchmark = [
            node_id
            for node_id, distance in distances.items()
            if distance >= 3 and normalize(svc.label(node_id)) in benchmark
        ]

        assert normalize(svc.label(target)) in benchmark
        assert len(distances) >= math.ceil(graph_size * 0.90)
        assert responsive >= max(40, math.ceil(graph_size * 0.10))
        assert benchmark_predecessors, f"{record['id']} has no familiar one-hop hint"
        assert far_benchmark, f"{record['id']} has no familiar cold comparison"


def test_v24_lant_routes_keep_short_bands_and_real_choices():
    svc = _fixture_service()
    records = _declared_records()["lant"]
    bands = {"usor": (2, 3), "normal": (3, 4), "greu": (4, 6)}
    preferred_easy = 0

    for record in records:
        optimal = svc.distance(str(record["start"]), str(record["target"]))
        assert optimal == record["optimal"]
        lo, hi = bands[str(record["difficulty"])]
        assert lo <= optimal <= hi
        first_hops, min_width, _ = lant_branch_profile(
            svc, str(record["start"]), str(record["target"]), optimal
        )
        assert first_hops >= 2
        assert min_width >= 2
        if record["difficulty"] == "usor" and first_hops >= 3 and min_width >= 3:
            preferred_easy += 1

    assert preferred_easy >= 2


def test_v24_alchimie_recipes_are_sparse_bounded_and_distinct():
    svc = _fixture_service()
    records = _declared_records()["alchimie"]
    seen_seed_sets: set[frozenset[str]] = set()

    for record in records:
        seeds = [str(seed) for seed in record["seeds"]]
        category = str(record["category"])
        closure = _closure_generations(svc, seeds, category)
        productive = _opening_pairs(svc, seeds, category)
        pair_count = math.comb(len(seeds), 2)
        ratio_floor = {"usor": 0.30, "normal": 0.20, "greu": 0.15}[
            str(record["difficulty"])
        ]

        assert 15 <= len(closure) <= 60
        assert productive / pair_count >= ratio_floor
        assert 2 <= int(record["target_depth"]) <= 6
        assert frozenset(seeds) not in seen_seed_sets
        seen_seed_sets.add(frozenset(seeds))

        for left, right in combinations(seeds, 2):
            fresh = [
                node_id
                for node_id in svc.common_neighbors(left, right, category=category)
                if node_id not in seeds
            ]
            if fresh:
                assert 1 <= len(fresh) <= 3


def test_v24_conexiuni_boards_are_familiar_unique_and_type_coherent():
    svc = _fixture_service()
    records = _declared_records()["conexiuni"]
    benchmark = {normalize(str(term)) for term in DATA.BEGINNER_BENCHMARK}
    all_tiles: list[str] = []

    for record in records:
        tiles = [node_id for group in record["groups"].values() for node_id in group]
        familiar = sum(normalize(svc.label(node_id)) in benchmark for node_id in tiles)
        assert len(tiles) == len(set(tiles)) == 16
        assert familiar >= 15
        assert all(
            len({svc.node(node_id).node_type for node_id in group}) == 1
            for group in record["groups"].values()
        )
        all_tiles.extend(tiles)

    assert len(all_tiles) == len(set(all_tiles)) == 64
