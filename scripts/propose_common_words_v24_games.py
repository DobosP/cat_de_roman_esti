#!/usr/bin/env python3
"""Mine deterministic v24 game candidates without changing repository files.

The committed fixture does not contain the authored v24 graph until the wave is
applied.  This tool therefore loads the current fixture, merges
``common_words_v24_data.build_nodes_and_edges()`` *in memory*, and evaluates game
ideas with the same :class:`WordGameService` and pack helpers used at runtime.

The JSON written to stdout is an authoring inventory, not an automatic approval:
every selected pack record still belongs behind the normal pending + critique gate.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))

import common_words_v24_data as DATA  # noqa: E402

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.graph import Edge, Graph, Node  # noqa: E402
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    ALCHIMIE_MAX_ACTIONS,
    DEFAULT_PACK,
    LANT_BANDS,
    _closure_generations,
    _opening_pairs,
    lant_branch_profile,
    minimum_alchimie_actions,
    validate_envelope,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService, normalize  # noqa: E402

RESPONSIVE_HOPS = 5
MIN_REACHABLE = 120
MIN_RESPONSIVE = 40
DIFFICULTY_RATIO = {"usor": 0.30, "normal": 0.20, "greu": 0.15}
ALCHIMIE_CLOSURE_RANGE = (15, 60)
ALCHIMIE_POOL_PER_CATEGORY = 22
ALCHIMIE_SEED_FRONTIER = 72


def _bool(value: object, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "t"}
    return bool(value)


def _builder_parts() -> tuple[list[dict], list[dict], dict[str, list[str]], object]:
    result = DATA.build_nodes_and_edges()
    if isinstance(result, Mapping):
        raw_nodes = result.get("nodes", result.get("kg_nodes", ()))
        raw_edges = result.get("edges", result.get("kg_edges", ()))
        raw_aliases = result.get("aliases", {})
        game_items = result.get("game_items")
    elif isinstance(result, (tuple, list)) and len(result) in (2, 3):
        raw_nodes, raw_edges = result[:2]
        raw_aliases = {}
        game_items = result[2] if len(result) == 3 else None
    else:
        raise ValueError("build_nodes_and_edges() returned an unsupported shape")

    if not isinstance(raw_nodes, (list, tuple)) or not all(
        isinstance(item, dict) for item in raw_nodes
    ):
        raise ValueError("builder nodes must be a sequence of objects")
    if not isinstance(raw_edges, (list, tuple)) or not all(
        isinstance(item, dict) for item in raw_edges
    ):
        raise ValueError("builder edges must be a sequence of objects")
    if not isinstance(raw_aliases, Mapping):
        raise ValueError("builder aliases must be a mapping")
    aliases: dict[str, list[str]] = {}
    for node_id, values in raw_aliases.items():
        if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
            raise ValueError(f"aliases for {node_id!r} must be a sequence")
        aliases[str(node_id)] = [str(value) for value in values]
    return list(raw_nodes), list(raw_edges), aliases, game_items


def _edge_key(src: str, dst: str, relation: str) -> tuple[str, str, str]:
    """Mirror densify_content's relation-key de-duplication."""

    left, right = sorted((src, dst))
    return left, right, relation


def _merge_service(
    fixture: str | Path | None,
) -> tuple[WordGameService, set[str], set[str], object, dict[str, int]]:
    new_records, edge_records, alias_map, builder_items = _builder_parts()
    base = load_fixture(fixture).graph
    nodes: dict[str, Node] = dict(base.nodes)
    new_ids: set[str] = set()

    for record in new_records:
        node = Node.from_record(record)
        if node.id in nodes:
            raise ValueError(f"v24 node already exists in the current fixture: {node.id}")
        nodes[node.id] = node
        new_ids.add(node.id)

    for node_id, incoming in sorted(alias_map.items()):
        node = nodes.get(node_id)
        if node is None:
            raise ValueError(f"alias target does not exist: {node_id}")
        aliases = list(node.aliases)
        seen = {alias.strip().casefold() for alias in aliases}
        seen.add(node.label_ro.strip().casefold())
        for value in incoming:
            alias = value.strip()
            if alias and alias.casefold() not in seen:
                aliases.append(alias)
                seen.add(alias.casefold())
        nodes[node_id] = replace(node, aliases=tuple(aliases))

    graph = Graph()
    for node_id in sorted(nodes):
        graph.add_node(nodes[node_id])
    for edge in base.edges:
        graph.add_edge(edge)

    keys = {_edge_key(edge.src_id, edge.dst_id, edge.relation) for edge in base.edges}
    anchors: set[str] = set()
    added_edges = 0
    for index, raw in enumerate(edge_records, 1):
        src = str(raw.get("src", raw.get("src_id", ""))).strip()
        dst = str(raw.get("dst", raw.get("dst_id", ""))).strip()
        relation = str(raw.get("relation", "")).strip()
        if not src or not dst or not relation:
            raise ValueError(f"v24 edge {index} needs src, dst and relation")
        if src == dst or src not in nodes or dst not in nodes:
            raise ValueError(f"invalid v24 edge: {src!r} -> {dst!r}")
        key = _edge_key(src, dst, relation)
        if key in keys:
            continue
        keys.add(key)
        edge_record = dict(raw)
        edge_record.update(
            {
                "id": str(raw.get("id") or f"v24_probe_edge_{index:05d}"),
                "src_id": src,
                "dst_id": dst,
                "relation": relation,
                "label_ro": str(raw.get("label_ro", "")),
                "strength": float(raw.get("strength", 0.5)),
                "is_distractor": _bool(raw.get("is_distractor"), False),
                "bidirectional": _bool(raw.get("bidirectional"), True),
            }
        )
        graph.add_edge(Edge.from_record(edge_record))
        anchors.update(node_id for node_id in (src, dst) if node_id not in new_ids)
        added_edges += 1

    return (
        WordGameService(graph),
        new_ids,
        anchors,
        builder_items,
        {
            "base_nodes": len(base.nodes),
            "base_edges": len(base.edges),
            "added_nodes": len(new_ids),
            "added_edges": added_edges,
        },
    )


def _surfaces() -> tuple[str, ...]:
    benchmark = getattr(DATA, "BEGINNER_BENCHMARK", ())
    deferred = {normalize(str(value)) for value in getattr(DATA, "DEFERRED_AMBIGUOUS_TERMS", ())}
    return tuple(
        str(value)
        for value in benchmark
        if str(value).strip() and normalize(str(value)) not in deferred
    )


def _familiar_ids(svc: WordGameService) -> tuple[set[str], dict[str, tuple[str, ...]]]:
    surfaces_by_id: dict[str, list[str]] = defaultdict(list)
    for surface in _surfaces():
        node_id = svc.resolve(surface)
        if node_id is not None and surface not in surfaces_by_id[node_id]:
            surfaces_by_id[node_id].append(surface)
    return set(surfaces_by_id), {
        node_id: tuple(values) for node_id, values in sorted(surfaces_by_id.items())
    }


def _existing_payloads(path: str | Path | None) -> dict[str, set[tuple[Any, ...]]]:
    pack_path = Path(path) if path else DEFAULT_PACK
    result: dict[str, set[tuple[Any, ...]]] = {
        "contexto": set(),
        "lant": set(),
        "alchimie": set(),
    }
    if not pack_path.exists():
        return result
    raw = json.loads(pack_path.read_text(encoding="utf-8"))
    result["contexto"] = {
        (str(item.get("target")),) for item in raw.get("contexto", ())
    }
    result["lant"] = {
        (str(item.get("start")), str(item.get("target")))
        for item in raw.get("lant", ())
    }
    result["alchimie"] = {
        (
            str(item.get("category")),
            tuple(sorted(str(seed) for seed in item.get("seeds", ()))),
            str(item.get("target")),
        )
        for item in raw.get("alchimie", ())
    }
    return result


def _approved_pack_impact(
    svc: WordGameService, path: str | Path | None
) -> dict[str, object]:
    """Revalidate served records against the prospective graph, without reauthoring them."""

    pack_path = Path(path) if path else DEFAULT_PACK
    if not pack_path.exists():
        return {"checked": False, "reason": f"pack not found: {pack_path}"}
    raw = json.loads(pack_path.read_text(encoding="utf-8"))
    counts: dict[str, dict[str, int]] = {}
    invalid: list[dict[str, object]] = []
    for game in ("conexiuni", "contexto", "lant", "alchimie"):
        approved = [item for item in raw.get(game, ()) if item.get("status") == "approved"]
        valid_count = 0
        for item in approved:
            errors = validate_payload(item, game, svc)
            if not errors:
                valid_count += 1
                continue
            detail: dict[str, object] = {
                "game": game,
                "id": str(item.get("id")),
                "errors": errors,
            }
            if game == "lant":
                detail["stored_optimal"] = item.get("optimal")
                detail["prospective_optimal"] = svc.distance(
                    str(item.get("start")), str(item.get("target"))
                )
            invalid.append(detail)
        counts[game] = {
            "approved": len(approved),
            "valid": valid_count,
            "invalid": len(approved) - valid_count,
        }
    return {
        "checked": True,
        "pack": str(pack_path),
        "counts": counts,
        "invalid_items": invalid,
        "approved_payloads_stable": not invalid,
    }


def _node_rank(svc: WordGameService, node_id: str, new_ids: set[str]) -> tuple[float, str]:
    node = svc.node(node_id)
    salience = node.salience if node else 0.0
    return (float(node_id in new_ids) * 2.0 + salience, node_id)


def _difficulty_for_contexto(salience: float) -> str:
    if salience >= 0.70:
        return "usor"
    if salience >= 0.48:
        return "normal"
    return "greu"


def _resolved_intuitive_pairs(svc: WordGameService) -> set[frozenset[str]]:
    result: set[frozenset[str]] = set()
    for raw in getattr(DATA, "INTUITIVE_PAIRS", ()):
        if not isinstance(raw, (tuple, list)) or len(raw) != 2:
            continue
        left = svc.resolve(str(raw[0]))
        right = svc.resolve(str(raw[1]))
        if left and right and left != right:
            result.add(frozenset((left, right)))
    return result


def _contexto_candidates(
    svc: WordGameService,
    familiar: set[str],
    surface_map: dict[str, tuple[str, ...]],
    new_ids: set[str],
    existing: set[tuple[Any, ...]],
    limit: int,
) -> list[dict[str, object]]:
    intuitive = _resolved_intuitive_pairs(svc)
    # Existing edge anchors may be obscure connective tissue. They remain useful as
    # guesses/routes, but only benchmark-resolved or explicitly new common words are
    # eligible secrets.
    target_pool = sorted(familiar | new_ids)
    ranked: list[tuple[tuple[float, ...], dict[str, object]]] = []
    far_pool = sorted(familiar, key=lambda node_id: _node_rank(svc, node_id, new_ids), reverse=True)

    for target in target_pool:
        if (target,) in existing:
            continue
        node = svc.node(target)
        if node is None:
            continue
        distances = svc.distances_to(target)
        reachable = len(distances)
        responsive = sum(1 for distance in distances.values() if 1 <= distance <= RESPONSIVE_HOPS)
        if reachable < MIN_REACHABLE or responsive < MIN_RESPONSIVE:
            continue
        weighted = svc.weighted_distances_to(target)
        near_ids = [
            node_id
            for node_id in svc.predecessor_ids(target)
            if node_id in familiar and node_id != target
        ]
        near_ids.sort(
            key=lambda node_id: (
                frozenset((node_id, target)) in intuitive,
                svc.node(node_id).category == node.category if svc.node(node_id) else False,
                _node_rank(svc, node_id, new_ids),
            ),
            reverse=True,
        )
        far_ids = [
            node_id
            for node_id in far_pool
            if node_id != target
            and distances.get(node_id, 0) >= 3
            and (svc.node(node_id).category != node.category if svc.node(node_id) else True)
        ]
        if not far_ids:
            far_ids = [
                node_id
                for node_id in far_pool
                if node_id != target and distances.get(node_id, 0) >= 3
            ]
        probes: list[dict[str, object]] = []
        for near, far in zip(near_ids[:3], far_ids[:3], strict=False):
            near_hops = distances[near]
            far_hops = distances[far]
            near_weight = weighted.get(near, math.inf)
            far_weight = weighted.get(far, math.inf)
            probes.append(
                {
                    "near": near,
                    "near_label": svc.label(near),
                    "near_hops": near_hops,
                    "far": far,
                    "far_label": svc.label(far),
                    "far_hops": far_hops,
                    "ordering_ok": near_hops < far_hops and near_weight < far_weight,
                    "declared_intuitive": frozenset((near, target)) in intuitive,
                }
            )
        if not probes or not all(bool(probe["ordering_ok"]) for probe in probes):
            continue
        record = {
            "category": node.category,
            "difficulty": _difficulty_for_contexto(node.salience),
            "target": target,
            "target_label": node.label_ro,
            "benchmark_surfaces": list(surface_map.get(target, ())),
            "reachable": reachable,
            "responsive_1_5": responsive,
            "responsive_share": round(responsive / reachable, 4),
            "probes": probes,
        }
        score = (
            float(target in new_ids),
            float(any(bool(probe["declared_intuitive"]) for probe in probes)),
            float(len(probes)),
            float(responsive),
            node.salience,
        )
        ranked.append((score, record))

    ranked.sort(key=lambda item: (item[0], str(item[1]["target"])), reverse=True)
    selected: list[dict[str, object]] = []
    selected_targets: set[str] = set()
    category_uses: dict[str, int] = defaultdict(int)
    categories = {str(record["category"]) for _, record in ranked}
    category_cap = max(1, math.ceil(limit / max(1, len(categories))) + 1)
    for enforce_diversity in (True, False):
        for _, record in ranked:
            target = str(record["target"])
            category = str(record["category"])
            if target in selected_targets:
                continue
            if enforce_diversity and category_uses[category] >= category_cap:
                continue
            selected.append(record)
            selected_targets.add(target)
            category_uses[category] += 1
            if len(selected) >= limit:
                return selected
    return selected


def _cached_branch_profile(
    svc: WordGameService,
    start: str,
    target: str,
    optimal: int,
    dist_from: Mapping[str, int],
    dist_to: Mapping[str, int],
) -> tuple[int, int, int]:
    layers: dict[int, int] = defaultdict(int)
    for node_id, start_distance in dist_from.items():
        target_distance = dist_to.get(node_id)
        if target_distance is not None and start_distance + target_distance == optimal:
            layers[start_distance] += 1
    intermediate = [layers.get(layer, 0) for layer in range(1, optimal)]
    first_hops = sum(
        1
        for node_id in svc.neighbor_ids(start)
        if dist_to.get(node_id) == optimal - 1
    )
    return first_hops, min(intermediate, default=1), sum(intermediate)


def _lant_difficulty(distance: int) -> str:
    if distance <= 3:
        return "usor"
    if distance == 4:
        return "normal"
    return "greu"


def _lant_candidates(
    svc: WordGameService,
    eligible: set[str],
    new_ids: set[str],
    existing: set[tuple[Any, ...]],
    limit: int,
    pool_limit: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    pool = sorted(
        (node_id for node_id in eligible if svc.node(node_id) is not None),
        key=lambda node_id: _node_rank(svc, node_id, new_ids),
        reverse=True,
    )[:pool_limit]
    by_category: dict[str, list[str]] = defaultdict(list)
    for node_id in pool:
        node = svc.node(node_id)
        if node:
            by_category[node.category].append(node_id)

    ranked: list[tuple[tuple[float, ...], dict[str, object]]] = []
    profiled_pairs = 0
    runtime_branching_pairs = 0
    runtime_new_endpoint_pairs = 0
    ranked_by_difficulty: dict[str, int] = defaultdict(int)
    for category in sorted(by_category):
        category_pool = by_category[category]
        to_cache = {target: svc.distances_to(target) for target in category_pool}
        for start in category_pool:
            dist_from = svc.distances_from(start)
            targets = [
                target
                for target in category_pool
                if target != start
                and (start, target) not in existing
                and 2 <= dist_from.get(target, 99) <= 6
            ]
            targets.sort(
                key=lambda target: _node_rank(svc, target, new_ids), reverse=True
            )
            # Bound the expensive profile stage while keeping every start represented.
            for target in targets[:24]:
                profiled_pairs += 1
                distance = dist_from[target]
                difficulty = _lant_difficulty(distance)
                lo, hi = LANT_BANDS[difficulty]
                if not lo <= distance <= hi:
                    continue
                profile = _cached_branch_profile(
                    svc, start, target, distance, dist_from, to_cache[target]
                )
                first_hops, min_width, total = profile
                if first_hops < 2 or min_width < 2:
                    continue
                runtime_branching_pairs += 1
                if start in new_ids or target in new_ids:
                    runtime_new_endpoint_pairs += 1
                preferred_branch_profile = difficulty != "usor" or (
                    first_hops >= 3 and min_width >= 3
                )
                start_node = svc.node(start)
                target_node = svc.node(target)
                assert start_node is not None and target_node is not None
                record = {
                    "category": category,
                    "difficulty": difficulty,
                    "start": start,
                    "start_label": start_node.label_ro,
                    "target": target,
                    "target_label": target_node.label_ro,
                    "optimal": distance,
                    "branch_profile": {
                        "valid_first_hops": first_hops,
                        "narrowest_layer": min_width,
                        "total_intermediate": total,
                    },
                    "preferred_branch_profile": preferred_branch_profile,
                }
                errors = validate_payload(record, "lant", svc)
                if errors:
                    continue
                score = (
                    float(difficulty == "usor" and preferred_branch_profile),
                    float(preferred_branch_profile),
                    float(start in new_ids) + float(target in new_ids),
                    float(min_width),
                    float(first_hops),
                    float(total),
                    (start_node.salience + target_node.salience) / 2,
                )
                ranked.append((score, record))
                ranked_by_difficulty[difficulty] += 1

    ranked.sort(
        key=lambda item: (item[0], str(item[1]["start"]), str(item[1]["target"])),
        reverse=True,
    )
    selected: list[dict[str, object]] = []
    selected_pairs: set[tuple[str, str]] = set()
    endpoint_uses: dict[str, int] = defaultdict(int)
    category_uses: dict[str, int] = defaultdict(int)
    difficulty_uses: dict[str, int] = defaultdict(int)
    category_cap = max(2, math.ceil(limit / max(1, len(by_category))) + 1)
    difficulty_cap = max(1, math.ceil(limit / 3))

    def finish() -> tuple[list[dict[str, object]], dict[str, object]]:
        selected_by_difficulty: dict[str, int] = defaultdict(int)
        for record in selected:
            selected_by_difficulty[str(record["difficulty"])] += 1
        return selected, {
            "endpoint_pool": len(pool),
            "categories": len(by_category),
            "profiled_pairs": profiled_pairs,
            "runtime_branching_pairs": runtime_branching_pairs,
            "runtime_branching_pairs_with_new_endpoint": runtime_new_endpoint_pairs,
            "ranked_by_difficulty": dict(sorted(ranked_by_difficulty.items())),
            "selected_by_difficulty": dict(sorted(selected_by_difficulty.items())),
            "selected_with_new_endpoint": sum(
                1
                for record in selected
                if str(record["start"]) in new_ids or str(record["target"]) in new_ids
            ),
        }

    def select(record: dict[str, object], *, enforce_diversity: bool) -> bool:
        start = str(record["start"])
        target = str(record["target"])
        category = str(record["category"])
        difficulty = str(record["difficulty"])
        if (start, target) in selected_pairs:
            return False
        if endpoint_uses[start] >= 2 or endpoint_uses[target] >= 2:
            return False
        if enforce_diversity and (
            category_uses[category] >= category_cap
            or difficulty_uses[difficulty] >= difficulty_cap
        ):
            return False
        # Final proposals use the canonical helper, not only the cached equivalent.
        verified = lant_branch_profile(svc, start, target, int(record["optimal"]))
        profile = record["branch_profile"]
        assert isinstance(profile, dict)
        expected = (
            profile["valid_first_hops"],
            profile["narrowest_layer"],
            profile["total_intermediate"],
        )
        if verified != expected:
            raise AssertionError(f"cached Lanț profile drifted: {verified} != {expected}")
        selected.append(record)
        selected_pairs.add((start, target))
        endpoint_uses[start] += 1
        endpoint_uses[target] += 1
        category_uses[category] += 1
        difficulty_uses[difficulty] += 1
        return True

    # Seed the inventory with every available distance band before filling by score.
    for desired in ("usor", "normal", "greu"):
        for _, record in ranked:
            if record["difficulty"] == desired and select(record, enforce_diversity=True):
                break
        if len(selected) >= limit:
            return finish()
    for enforce_diversity in (True, False):
        for _, record in ranked:
            if select(record, enforce_diversity=enforce_diversity) and len(selected) >= limit:
                return finish()
    return finish()


def _opening_profile(
    svc: WordGameService, seeds: tuple[str, ...], category: str
) -> tuple[int, int, int, tuple[int, ...]]:
    owned = set(seeds)
    productive = 0
    preferred = 0
    counts: list[int] = []
    for left, right in combinations(seeds, 2):
        fresh = [
            node_id
            for node_id in svc.common_neighbors(left, right, category=category)
            if node_id not in owned
        ]
        if not fresh:
            continue
        productive += 1
        counts.append(len(fresh))
        if 1 <= len(fresh) <= 3:
            preferred += 1
    return productive, preferred, math.comb(len(seeds), 2), tuple(sorted(counts))


def _seed_score(
    svc: WordGameService,
    seeds: tuple[str, ...],
    category: str,
    new_ids: set[str],
) -> tuple[float, ...] | None:
    productive, preferred, pair_count, counts = _opening_profile(svc, seeds, category)
    if productive < 2 or productive / pair_count < DIFFICULTY_RATIO["greu"]:
        return None
    preference = preferred / productive
    if preference < 0.50:
        return None
    mean_salience = sum(svc.node(seed).salience for seed in seeds if svc.node(seed)) / len(seeds)
    # Roughly one-third productive is lively without turning every tap into a result cloud.
    ratio = productive / pair_count
    return (
        preference,
        -abs(ratio - 0.34),
        float(sum(seed in new_ids for seed in seeds)),
        mean_salience,
        -float(max(counts, default=0)),
    )


def _seed_frontier(
    svc: WordGameService,
    pool: list[str],
    category: str,
    new_ids: set[str],
) -> list[tuple[str, ...]]:
    ranked_five: list[tuple[tuple[float, ...], tuple[str, ...]]] = []
    for seeds in combinations(pool, 5):
        score = _seed_score(svc, seeds, category, new_ids)
        if score is not None:
            ranked_five.append((score, seeds))
    ranked_five.sort(key=lambda item: (item[0], item[1]), reverse=True)
    frontier: dict[tuple[str, ...], tuple[float, ...]] = {
        seeds: score for score, seeds in ranked_five[:ALCHIMIE_SEED_FRONTIER]
    }

    previous = [seeds for _, seeds in ranked_five[:ALCHIMIE_SEED_FRONTIER]]
    for size in (6, 7):
        expanded: dict[tuple[str, ...], tuple[float, ...]] = {}
        for seeds in previous:
            for node_id in pool:
                if node_id in seeds:
                    continue
                candidate = tuple(sorted((*seeds, node_id)))
                if len(candidate) != size or candidate in expanded:
                    continue
                score = _seed_score(svc, candidate, category, new_ids)
                if score is not None:
                    expanded[candidate] = score
        ranked = sorted(expanded.items(), key=lambda item: (item[1], item[0]), reverse=True)
        previous = [seeds for seeds, _ in ranked[:ALCHIMIE_SEED_FRONTIER]]
        frontier.update((seeds, score) for seeds, score in ranked[:ALCHIMIE_SEED_FRONTIER])
    return [
        seeds
        for seeds, _ in sorted(
            frontier.items(), key=lambda item: (item[1], item[0]), reverse=True
        )
    ]


def _difficulty_for_alchimie(par: int) -> str:
    if par <= 3:
        return "usor"
    if par == 4:
        return "normal"
    return "greu"


def _alchimie_candidates(
    svc: WordGameService,
    eligible: set[str],
    familiar: set[str],
    new_ids: set[str],
    existing: set[tuple[Any, ...]],
    limit: int,
    exact_budget: int,
) -> tuple[list[dict[str, object]], int, list[dict[str, object]]]:
    by_category: dict[str, list[str]] = defaultdict(list)
    for node_id in eligible:
        node = svc.node(node_id)
        if node:
            by_category[node.category].append(node_id)

    ranked: list[tuple[tuple[float, ...], dict[str, object]]] = []
    diagnostics: list[dict[str, object]] = []
    exact_calls = 0
    categories = [
        category for category in sorted(by_category) if len(set(by_category[category])) >= 5
    ]
    for category_index, category in enumerate(categories):
        category_exact_budget = exact_budget // max(1, len(categories))
        if category_index < exact_budget % max(1, len(categories)):
            category_exact_budget += 1
        category_calls = 0
        raw_pool = sorted(set(by_category[category]))
        productive_degree: dict[str, float] = defaultdict(float)
        for left, right in combinations(raw_pool, 2):
            result_count = len(svc.common_neighbors(left, right, category=category))
            if 1 <= result_count <= 3:
                productive_degree[left] += 1.0
                productive_degree[right] += 1.0
            elif result_count:
                productive_degree[left] += 0.1
                productive_degree[right] += 0.1
        topology_pool = sorted(
            raw_pool,
            key=lambda node_id: (
                productive_degree[node_id],
                _node_rank(svc, node_id, new_ids),
            ),
            reverse=True,
        )[:ALCHIMIE_POOL_PER_CATEGORY]
        authored_pool = sorted(
            (node_id for node_id in raw_pool if node_id in new_ids),
            key=lambda node_id: (
                productive_degree[node_id],
                _node_rank(svc, node_id, new_ids),
            ),
            reverse=True,
        )[:ALCHIMIE_POOL_PER_CATEGORY]
        pool_variants = [topology_pool]
        if len(authored_pool) >= 5 and authored_pool != topology_pool:
            pool_variants.append(authored_pool)
        frontier_set: set[tuple[str, ...]] = set()
        for pool in pool_variants:
            frontier_set.update(_seed_frontier(svc, pool, category, new_ids))
        frontier = sorted(
            frontier_set,
            key=lambda seeds: (_seed_score(svc, seeds, category, new_ids), seeds),
            reverse=True,
        )
        closure_sizes: list[int] = []
        closure_eligible = 0
        deep_target_sets = 0
        candidates_before = len(ranked)
        for seeds in frontier:
            productive, preferred, pair_count, fresh_counts = _opening_profile(
                svc, seeds, category
            )
            canonical_openings = _opening_pairs(svc, list(seeds), category)
            if canonical_openings != productive:
                raise AssertionError(
                    f"opening-pair profile drifted: {productive} != {canonical_openings}"
                )
            closure = _closure_generations(svc, list(seeds), category)
            closure_size = len(closure)
            closure_sizes.append(closure_size)
            if not ALCHIMIE_CLOSURE_RANGE[0] <= closure_size <= ALCHIMIE_CLOSURE_RANGE[1]:
                continue
            closure_eligible += 1
            targets = [
                node_id
                for node_id, generation in closure.items()
                if node_id not in seeds and generation >= 2
            ]
            if targets:
                deep_target_sets += 1
            targets.sort(
                key=lambda node_id: (
                    node_id in new_ids,
                    node_id in familiar,
                    closure[node_id],
                    _node_rank(svc, node_id, new_ids),
                ),
                reverse=True,
            )
            for target in targets[:4]:
                if category_calls >= category_exact_budget or exact_calls >= exact_budget:
                    break
                exact_calls += 1
                category_calls += 1
                par = minimum_alchimie_actions(
                    svc,
                    list(seeds),
                    target,
                    category,
                    max_actions=ALCHIMIE_MAX_ACTIONS,
                )
                if par is None or not 2 <= par <= 6:
                    continue
                difficulty = _difficulty_for_alchimie(par)
                ratio = productive / pair_count
                if ratio < DIFFICULTY_RATIO[difficulty]:
                    continue
                key = (category, tuple(sorted(seeds)), target)
                if key in existing:
                    continue
                target_node = svc.node(target)
                assert target_node is not None
                record = {
                    "category": category,
                    "difficulty": difficulty,
                    "seeds": list(seeds),
                    "seed_labels": [svc.label(seed) for seed in seeds],
                    "target": target,
                    "target_label": target_node.label_ro,
                    "target_depth": par,
                    "closure_size": closure_size,
                    "target_closure_generation": closure[target],
                    "opening_productive_pairs": productive,
                    "opening_pair_count": pair_count,
                    "opening_productive_ratio": round(ratio, 4),
                    "opening_pairs_with_1_3_fresh": preferred,
                    "fresh_result_counts": list(fresh_counts),
                }
                if validate_payload(record, "alchimie", svc):
                    continue
                score = (
                    float(target in new_ids),
                    float(target in familiar),
                    preferred / productive,
                    -abs(ratio - max(DIFFICULTY_RATIO[difficulty], 0.30)),
                    float(par),
                    target_node.salience,
                )
                ranked.append((score, record))
            if category_calls >= category_exact_budget or exact_calls >= exact_budget:
                break
        diagnostics.append(
            {
                "category": category,
                "eligible_nodes": len(raw_pool),
                "search_pool": max(map(len, pool_variants)),
                "search_pool_variants": len(pool_variants),
                "seed_sets_scored": len(frontier),
                "closure_min": min(closure_sizes, default=None),
                "closure_max": max(closure_sizes, default=None),
                "seed_sets_with_closure_15_60": closure_eligible,
                "seed_sets_with_par_2_plus_targets": deep_target_sets,
                "exact_searches": category_calls,
                "valid_candidates": len(ranked) - candidates_before,
            }
        )

    ranked.sort(
        key=lambda item: (
            item[0],
            str(item[1]["category"]),
            tuple(item[1]["seeds"]),
            str(item[1]["target"]),
        ),
        reverse=True,
    )
    selected: list[dict[str, object]] = []
    selected_keys: set[tuple[str, tuple[str, ...], str]] = set()
    target_uses: dict[str, int] = defaultdict(int)
    category_uses: dict[str, int] = defaultdict(int)
    difficulty_uses: dict[str, int] = defaultdict(int)
    category_count = max(1, len(by_category))
    category_cap = max(2, math.ceil(limit / category_count) + 1)
    difficulty_cap = max(1, math.ceil(limit / 3))
    for enforce_diversity in (True, False):
        for _, record in ranked:
            target = str(record["target"])
            category = str(record["category"])
            difficulty = str(record["difficulty"])
            key = (category, tuple(str(seed) for seed in record["seeds"]), target)
            if key in selected_keys or target_uses[target]:
                continue
            if enforce_diversity and (
                category_uses[category] >= category_cap
                or difficulty_uses[difficulty] >= difficulty_cap
            ):
                continue
            selected.append(record)
            selected_keys.add(key)
            target_uses[target] += 1
            category_uses[category] += 1
            difficulty_uses[difficulty] += 1
            if len(selected) >= limit:
                return selected, exact_calls, diagnostics
    return selected, exact_calls, diagnostics


def _as_board_list(value: object) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        if "groups" in value:
            return [dict(value)]
        boards: list[dict] = []
        for key, raw in value.items():
            if not isinstance(raw, Mapping):
                continue
            board = dict(raw)
            board.setdefault("id", str(key))
            boards.append(board)
        return boards
    if isinstance(value, (list, tuple)):
        return [dict(raw) for raw in value if isinstance(raw, Mapping)]
    return []


def _conexiuni_boards(builder_items: object) -> list[dict]:
    sources: list[object] = [getattr(DATA, "CONEXIUNI_BOARDS", None)]
    explicit = getattr(DATA, "GAME_ITEMS", None)
    for value in (builder_items, explicit):
        if isinstance(value, Mapping):
            sources.append(value.get("conexiuni"))
        elif isinstance(value, (list, tuple)):
            sources.append(
                [
                    raw
                    for raw in value
                    if isinstance(raw, Mapping) and raw.get("game") == "conexiuni"
                ]
            )
    boards: dict[str, dict] = {}
    for source in sources:
        for index, board in enumerate(_as_board_list(source), 1):
            board.pop("game", None)
            key = str(board.get("id") or f"manual_{index:03d}")
            boards.setdefault(key, board)
    return [boards[key] for key in sorted(boards)]


def _validate_conexiuni(svc: WordGameService, builder_items: object) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for index, board in enumerate(_conexiuni_boards(builder_items), 1):
        payload_errors = validate_payload(board, "conexiuni", svc)
        envelope_errors = validate_envelope(board, "conexiuni") if "id" in board else []
        labels: list[list[str]] = []
        groups = board.get("groups")
        if isinstance(groups, Mapping):
            for group_id in sorted(groups):
                ids = groups[group_id]
                if isinstance(ids, Sequence) and not isinstance(ids, (str, bytes)):
                    labels.append([svc.label(str(node_id)) for node_id in ids])
        results.append(
            {
                "id": str(board.get("id") or f"manual_{index:03d}"),
                "valid": not payload_errors and not envelope_errors,
                "payload_errors": payload_errors,
                "envelope_errors": envelope_errors,
                "group_labels_preview": labels,
            }
        )
    return results


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", help="optional current KG fixture path")
    parser.add_argument("--pack", help="optional games-pack path used only for de-duplication")
    parser.add_argument("--contexto-limit", type=int, default=12)
    parser.add_argument("--lant-limit", type=int, default=12)
    parser.add_argument("--alchimie-limit", type=int, default=12)
    parser.add_argument("--lant-pool-limit", type=int, default=180)
    parser.add_argument("--alchimie-exact-budget", type=int, default=360)
    parser.add_argument(
        "--skip-approved-impact",
        action="store_true",
        help="skip canonical revalidation of approved pack records",
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    positive = {
        "contexto-limit": args.contexto_limit,
        "lant-limit": args.lant_limit,
        "alchimie-limit": args.alchimie_limit,
        "lant-pool-limit": args.lant_pool_limit,
        "alchimie-exact-budget": args.alchimie_exact_budget,
    }
    invalid = [name for name, value in positive.items() if value < 1]
    if invalid:
        raise SystemExit(f"positive integer required for: {', '.join(invalid)}")

    try:
        svc, new_ids, anchors, builder_items, graph_meta = _merge_service(args.fixture)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"propose_common_words_v24_games: ERROR — {exc}", file=sys.stderr)
        return 1
    if not new_ids:
        print(
            "propose_common_words_v24_games: v24 data builder has no nodes yet",
            file=sys.stderr,
        )
        return 2

    familiar, surface_map = _familiar_ids(svc)
    existing = _existing_payloads(args.pack)
    eligible = familiar | new_ids | anchors
    contexto = _contexto_candidates(
        svc,
        familiar,
        surface_map,
        new_ids,
        existing["contexto"],
        args.contexto_limit,
    )
    lant, lant_diagnostics = _lant_candidates(
        svc,
        eligible,
        new_ids,
        existing["lant"],
        args.lant_limit,
        args.lant_pool_limit,
    )
    alchimie, exact_calls, alchimie_diagnostics = _alchimie_candidates(
        svc,
        eligible,
        familiar,
        new_ids,
        existing["alchimie"],
        args.alchimie_limit,
        args.alchimie_exact_budget,
    )
    output = {
        "meta": {
            **graph_meta,
            "merged_nodes": len(svc.graph.nodes),
            "merged_edges": len(svc.graph.edges),
            "benchmark_surfaces": len(_surfaces()),
            "resolved_familiar_nodes": len(familiar),
            "existing_anchor_nodes": len(anchors),
            "alchimie_exact_searches": exact_calls,
            "read_only": True,
        },
        "contexto": contexto,
        "lant": lant,
        "lant_diagnostics": lant_diagnostics,
        "alchimie": alchimie,
        "alchimie_diagnostics": alchimie_diagnostics,
        "conexiuni_validation": _validate_conexiuni(svc, builder_items),
        "approved_pack_impact": (
            {"checked": False, "reason": "disabled by flag"}
            if args.skip_approved_impact
            else _approved_pack_impact(svc, args.pack)
        ),
    }
    indent = None if args.compact else 2
    print(json.dumps(output, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
