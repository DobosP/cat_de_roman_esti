#!/usr/bin/env python3
"""Deterministic content-critique lints for the curated games pack (ADR-0023).

Complements ``validate_games_pack.py`` (which checks *solvability*): these lints flag
items that are structurally likely to be UNFAIR or LOW-QUALITY for players, per
``docs/CRITIQUE_RUBRIC.md``. Levels:

* FAIL — blocks promotion of the item (``--strict`` exits 1);
* WARN — routes the item to the LLM judge fleet for a rubric verdict.

Checks (rubric section F): ``tile_fairness`` mirrors the engine's mined-board
fairness rule (``conexiuni._board_quality``: a tile must not have more on-board
neighbours in a foreign group than in its own — curated boards historically bypassed
it); ``red_herring_budget`` counts contested tiles; ``mirrored_groups`` detects group
pairs in >=3-way 1:1 strong-edge correspondence (festivals <-> host cities);
``type_coherence`` flags 3+1 / 2+2 node_type mixes inside a group;
``duplicate_groups`` flags quads already used by an approved or selected batch board;
``salience_floor`` flags Contexto/Lant/Alchimie targets below their difficulty band;
``member_overuse`` flags nodes reused across too many approved Conexiuni boards.

Usage::

    python scripts/critique_pack.py [--game G] [--status S] [--ids a,b] \
        [--json OUT] [--dossier DIR] [--strict]

Default is a report over the whole pack (exit 0). Explicit IDs are exact: unknown or
filter-excluded IDs exit 2. ``--dossier`` writes one JSON dossier per selected item for
judge-fleet consumption.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    ALCHIMIE_MAX_ACTIONS,
    ALCHIMIE_MAX_SEARCH_STATES,
    GAME_KINDS,
    STATUSES,
    _closure_generations,
    _opening_pairs,
    lant_branch_profile,
)
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

PACKAGE_PACK = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "games_pack.json"
PACKAGE_KG = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
RUBRIC_PATH = _REPO_ROOT / "docs" / "CRITIQUE_RUBRIC.md"
REVIEW_BINDING_VERSION = 1

# Rubric C6: WARN floor for target/endpoint salience per declared difficulty.
SALIENCE_FLOORS = {"usor": 0.60, "normal": 0.35, "greu": 0.20}
# Rubric B5: an edge this strong makes a cross-group pair "plausibly confusable".
STRONG_EDGE = 0.6
# Rubric B5: this many disjoint strong pairs between two groups = a mirror.
MIRROR_PAIRS = 3
# Rubric B4 (Koster): contested tiles must stay under the 4-mistake budget.
RED_HERRING_WARN = 2
RED_HERRING_FAIL = 4
# Rubric A6: reuse ceiling for one node across approved Conexiuni boards.
MEMBER_OVERUSE = 8
# Rubric A7: non-distinctive region association ("true of all Romania").
REGION_LABELS = frozenset({
    "Moldova", "Transilvania", "Oltenia", "Muntenia", "Dobrogea",
    "Banat", "Bucovina", "Maramureș", "Crișana", "Ardeal",
})
REGION_FANOUT = 2          # linked to >= this many distinct regions = provably generic
NATIONAL_SALIENCE = 0.70   # a concept this famous claiming ONE region is suspect


# --------------------------------------------------------------------- pure helpers
def classify_type_mix(types: list[str]) -> str | None:
    """Rubric B2: '3+1' when one type has len-1 members, '2+2' on an even split.

    None when the group is type-homogeneous (or has another shape, e.g. 2+1+1,
    which reads as deliberate type-agnostic labelling and is left to the judges).
    """
    counts = sorted(Counter(types).values(), reverse=True)
    if len(counts) == 1:
        return None
    if counts == [len(types) - 1, 1]:
        return "3+1"
    if len(types) == 4 and counts == [2, 2]:
        return "2+2"
    return None


def classify_generic_region(
    node_type: str, salience: float, links: list[tuple[str, str, float]]
) -> str | None:
    """Rubric A7: why a node's region link(s) look non-distinctive (None = fine).

    ``links`` is [(region_label, relation, strength), ...]. Two provable smells:
    a node tied to >= REGION_FANOUT distinct regions (Sarmale -> Moldova AND
    Transilvania: true of all Romania), and a national-salience *concept* claiming
    one region via a generic ``related_to`` edge (Mămăligă -> Moldova). Biographic
    or definitional links (person/work/org/place -> region) are left alone —
    Eminescu -> Moldova is distinctive. Judges settle flagged cases on the web.
    """
    if not links:
        return None
    regions = sorted({r for r, _, _ in links})
    if len(regions) >= REGION_FANOUT:
        return f"linked to {len(regions)} regions ({', '.join(regions)})"
    if (
        node_type == "concept"
        and salience >= NATIONAL_SALIENCE
        and any(rel == "related_to" for _, rel, _ in links)
    ):
        return (
            f"national-salience concept ({salience:.2f}) with generic "
            f"related_to edge to {regions[0]}"
        )
    return None


def max_matching(pairs_by_left: dict[str, set[str]]) -> int:
    """Maximum bipartite matching size (augmenting paths; boards are tiny)."""
    match_right: dict[str, str] = {}

    def augment(left: str, seen: set[str]) -> bool:
        for right in pairs_by_left.get(left, ()):
            if right in seen:
                continue
            seen.add(right)
            if right not in match_right or augment(match_right[right], seen):
                match_right[right] = left
                return True
        return False

    return sum(1 for left in pairs_by_left if augment(left, set()))


def fairness_counts(
    groups: dict[str, list[str]],
    neighbors: dict[str, set[str]],
    node_types: dict[str, str],
) -> tuple[list[str], list[str], int]:
    """(unfair_tiles, contested_tiles, engine_unfair) — confusability-aware fairness.

    The engine's mined-board rule (``conexiuni._board_quality``) rejects any tile with
    more on-board neighbours in a foreign group than its own. Mined groups are KG
    categories, so own-group edges are plentiful; curated groups are thematic slices
    (hosts + their shows) where that raw rule over-fires on pairs that play fine
    because the tile could never be *mistaken* for a member of the pulling group.
    Here a foreign group only counts as pulling when it is TYPE-COMPATIBLE with the
    tile (holds >=2 members of the tile's node_type). ``engine_unfair`` reports the
    raw engine-parity count for judge dossiers.
    """
    member_group = {nid: g for g, ids in groups.items() for nid in ids}
    type_census = {
        g: Counter(node_types.get(n, "?") for n in ids) for g, ids in groups.items()
    }
    unfair, contested, engine_unfair = [], [], 0
    for nid, own_g in member_group.items():
        nbrs = neighbors.get(nid, set())
        own_n = sum(1 for x in nbrs if x != nid and member_group.get(x) == own_g)
        worst_foreign = worst_raw = 0
        for g in groups:
            if g == own_g:
                continue
            pull = sum(1 for x in nbrs if member_group.get(x) == g)
            worst_raw = max(worst_raw, pull)
            if type_census[g].get(node_types.get(nid, "?"), 0) >= 2:
                worst_foreign = max(worst_foreign, pull)
        engine_unfair += worst_raw > own_n
        if worst_foreign > own_n:
            unfair.append(nid)
        elif worst_foreign == own_n and own_n > 0:
            contested.append(nid)
    return unfair, contested, engine_unfair


# --------------------------------------------------------------------- data access
def load_all(pack_path: Path, kg_path: Path):
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    kg_raw = json.loads(kg_path.read_text(encoding="utf-8"))
    svc = WordGameService(graph=load_fixture(kg_path).graph)

    strong = defaultdict(dict)  # symmetric strong-edge map (rubric B5)
    node_by_id = {n["id"]: n for n in kg_raw["kg_nodes"]}
    region_ids = {
        nid for nid, n in node_by_id.items()
        if n.get("node_type") == "place" and n.get("label_ro") in REGION_LABELS
    }
    region_links = defaultdict(list)  # non-place node -> [(region_label, rel, s)]
    for e in kg_raw["kg_edges"]:
        if e.get("is_distractor"):
            continue
        s = float(e.get("strength") or 0.0)
        a, b = e["src_id"], e["dst_id"]
        for x, y in ((a, b), (b, a)):
            if y in region_ids and x not in region_ids:
                xn = node_by_id.get(x, {})
                if xn.get("node_type") != "place":
                    region_links[x].append(
                        (node_by_id[y]["label_ro"], e.get("relation", ""), s)
                    )
        if s < STRONG_EDGE:
            continue
        strong[a][b] = max(strong[a].get(b, 0.0), s)
        strong[b][a] = max(strong[b].get(a, 0.0), s)

    generic_nodes = {}  # rubric A7 flags
    for nid, links in region_links.items():
        n = node_by_id.get(nid, {})
        reason = classify_generic_region(
            n.get("node_type", "?"), float(n.get("salience") or 0.0), links
        )
        if reason:
            generic_nodes[nid] = reason
    regions = {"region_ids": region_ids, "generic_nodes": generic_nodes}
    return pack, svc, strong, regions


def node_brief(svc: WordGameService, nid: str) -> dict:
    node = svc.node(nid)
    if node is None:
        return {"id": nid, "label": "<missing>", "node_type": "?", "category": "?",
                "salience": 0.0, "degree": 0, "incoming_degree": 0, "description": ""}
    return {
        "id": nid,
        "label": node.label_ro,
        "node_type": node.node_type,
        "category": node.category,
        "salience": node.salience,
        "degree": len(svc.neighbor_ids(nid)),
        "incoming_degree": len(svc.predecessor_ids(nid)),
        "description": node.description,
    }


# --------------------------------------------------------------------- per-item checks
def check_generic_region(rec: dict, game: str, svc: WordGameService,
                         regions: dict) -> list[dict]:
    """Rubric A7 item-level flags: gameplay leaning on a non-distinctive region link."""
    generic = regions["generic_nodes"]
    region_ids = regions["region_ids"]
    findings = []
    if game == "conexiuni":
        board = [n for ids in rec["groups"].values() for n in ids]
        flagged = [n for n in board if n in generic]
        on_board_regions = [n for n in board if n in region_ids]
        if flagged and on_board_regions:
            pairs = ", ".join(
                f"{node_brief(svc, n)['label']} ({generic[n]})" for n in flagged
            )
            findings.append({
                "check": "generic_region_link", "level": "WARN",
                "detail": "board pairs region tiles ("
                          + ", ".join(node_brief(svc, n)["label"] for n in on_board_regions)
                          + f") with non-distinctive region-linked tiles: {pairs}",
            })
    elif game == "contexto":
        target = rec["target"]
        if target in generic:
            findings.append({
                "check": "generic_region_link", "level": "WARN",
                "detail": f"target {node_brief(svc, target)['label']}: {generic[target]}"
                          " — region guesses rank warm without being distinctive",
            })
        elif target in region_ids:
            polluted = []
            for predecessor in svc.predecessor_ids(target):
                edge = svc.link(predecessor, target)
                if predecessor in generic and edge and edge.strength >= STRONG_EDGE:
                    polluted.append(node_brief(svc, predecessor)['label'])
            if len(polluted) >= 2:
                findings.append({
                    "check": "generic_region_link", "level": "WARN",
                    "detail": "region target's warm zone carries non-distinctive "
                              f"national concepts: {', '.join(sorted(polluted))}",
                })
    return findings


def check_conexiuni(rec: dict, svc: WordGameService, strong: dict,
                    approved_quads: dict[frozenset, list[str]]) -> list[dict]:
    findings = []
    groups = rec["groups"]
    labels = rec.get("group_labels") or {}
    neighbors = {
        nid: set(svc.neighbor_ids(nid)) for ids in groups.values() for nid in ids
    }
    node_types = {nid: node_brief(svc, nid)["node_type"] for nid in neighbors}
    name = lambda nid: node_brief(svc, nid)["label"]  # noqa: E731

    unfair, contested, _ = fairness_counts(groups, neighbors, node_types)
    if unfair:
        findings.append({
            "check": "tile_fairness", "level": "FAIL",
            "detail": "unfair tiles (foreign pull > own): "
                      + ", ".join(sorted(name(n) for n in unfair)),
        })
    if len(contested) >= RED_HERRING_WARN:
        findings.append({
            "check": "red_herring_budget",
            "level": "FAIL" if len(contested) >= RED_HERRING_FAIL else "WARN",
            "detail": f"{len(contested)} contested tiles (budget <{RED_HERRING_FAIL}): "
                      + ", ".join(sorted(name(n) for n in contested)),
        })

    group_keys = sorted(groups)
    for i, ga in enumerate(group_keys):
        types = [node_brief(svc, n)["node_type"] for n in groups[ga]]
        mix = classify_type_mix(types)
        if mix:
            findings.append({
                "check": "type_coherence", "level": "WARN",
                "detail": f'group "{labels.get(ga, ga)}" mixes node_types {mix}: '
                          + ", ".join(
                              f"{name(n)}[{t}]"
                              for n, t in zip(groups[ga], types, strict=True)
                          ),
            })
        for gb in group_keys[i + 1:]:
            pairs = {
                a: {b for b in groups[gb] if b in strong.get(a, ())}
                for a in groups[ga]
            }
            if max_matching({k: v for k, v in pairs.items() if v}) >= MIRROR_PAIRS:
                findings.append({
                    "check": "mirrored_groups", "level": "WARN",
                    "detail": f'"{labels.get(ga, ga)}" <-> "{labels.get(gb, gb)}" are in '
                              f">={MIRROR_PAIRS}-way strong correspondence",
                })

    for gk in group_keys:
        quad = frozenset(groups[gk])
        others = [b for b in approved_quads.get(quad, []) if b != rec["id"]]
        if others:
            findings.append({
                "check": "duplicate_groups",
                "level": "WARN" if rec.get("status") == "approved" else "FAIL",
                "detail": f'group "{labels.get(gk, gk)}" reuses an approved/selected quad '
                          f"(also in: {', '.join(sorted(others))})",
            })
            continue
        near = sorted({
            b for other_quad, boards in approved_quads.items()
            if len(quad & other_quad) == 3
            for b in boards if b != rec["id"]
        })
        if near:
            findings.append({
                "check": "duplicate_groups", "level": "WARN",
                "detail": f'group "{labels.get(gk, gk)}" shares 3 members with an '
                          f"approved/selected quad (near-duplicate; see: {', '.join(near)})",
            })
    return findings


def check_target_salience(rec: dict, svc: WordGameService, *targets: str) -> list[dict]:
    floor = SALIENCE_FLOORS.get(rec.get("difficulty", ""), 0.0)
    findings = []
    for nid in targets:
        brief = node_brief(svc, nid)
        if brief["salience"] < floor:
            findings.append({
                "check": "salience_floor", "level": "WARN",
                "detail": f"{brief['label']} salience {brief['salience']:.2f} "
                          f"< {floor:.2f} ({rec.get('difficulty')} floor)",
            })
    return findings


# --------------------------------------------------------------------- dossiers
def canonical_json_sha256(value: object) -> str:
    '''Stable SHA-256 for JSON-shaped review inputs.'''
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def normalized_text_sha256(path: Path) -> str:
    '''Platform-stable text digest for tracked rubric/fixture files.'''
    text = path.read_text(encoding='utf-8').replace('\r\n', '\n').replace('\r', '\n')
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@lru_cache(maxsize=1)
def rubric_sha256() -> str:
    '''Platform-stable digest of the rubric (normalize checkout line endings).'''
    return normalized_text_sha256(RUBRIC_PATH)


@lru_cache(maxsize=1)
def kg_sha256() -> str:
    '''Bind judgments to the exact graph snapshot used to build their dossiers.'''
    return normalized_text_sha256(PACKAGE_KG)


def dossier_review_binding(dossier: dict) -> str:
    '''Hash the exact judge input plus the current rubric, excluding the hash itself.'''
    payload = {
        'version': REVIEW_BINDING_VERSION,
        'rubric_sha256': rubric_sha256(),
        'dossier': {
            key: value for key, value in dossier.items()
            if key not in {'review_binding', 'rubric_sha256'}
        },
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')
    return 'sha256:' + hashlib.sha256(canonical).hexdigest()


def bind_dossier(dossier: dict) -> dict:
    '''Attach the rubric digest and canonical review binding consumed by the gate.'''
    dossier['rubric_sha256'] = rubric_sha256()
    dossier['review_binding'] = dossier_review_binding(dossier)
    return dossier


def _concept_ref(svc: WordGameService, node_id: str) -> dict:
    brief = node_brief(svc, node_id)
    return {'id': node_id, 'label': brief['label']}


def representative_shortest_paths(
    svc: WordGameService, start: str, target: str, optimal: int, limit: int = 3,
) -> list[dict]:
    '''Return bounded deterministic shortest paths with judge-visible edge semantics.'''
    if optimal < 1 or limit < 1:
        return []
    to_target = svc.distances_to(target)
    node_paths: list[list[str]] = []

    def ordered_next(node_id: str, remaining: int) -> list[str]:
        candidates = [
            neighbor for neighbor in svc.neighbor_ids(node_id)
            if to_target.get(neighbor) == remaining - 1
        ]
        candidates.sort(key=lambda neighbor: (
            -(svc.link(node_id, neighbor).strength if svc.link(node_id, neighbor) else 0),
            neighbor,
        ))
        return candidates

    def complete(node_id: str, path: list[str]) -> list[str] | None:
        if node_id == target:
            return path
        remaining = optimal - len(path) + 1
        for neighbor in ordered_next(node_id, remaining):
            completed = complete(neighbor, [*path, neighbor])
            if completed is not None:
                return completed
        return None

    # One witness per first-hop branch lets judges inspect the actual alternatives
    # behind branch_profile.valid_first_hops instead of seeing one dense subtree thrice.
    for first_hop in ordered_next(start, optimal)[:limit]:
        completed = complete(first_hop, [start, first_hop])
        if completed is not None:
            node_paths.append(completed)
    evidence = []
    for path in node_paths:
        edges = []
        for src, dst in zip(path, path[1:], strict=False):
            edge = svc.link(src, dst)
            edges.append({
                'from': _concept_ref(svc, src),
                'to': _concept_ref(svc, dst),
                'relation': edge.relation if edge else '',
                'label': edge.label_ro if edge else '',
                'strength': round(edge.strength, 2) if edge else 0.0,
            })
        evidence.append({'nodes': [_concept_ref(svc, nid) for nid in path], 'edges': edges})
    return evidence


def productive_opening_pairs(
    svc: WordGameService, seeds: list[str], category: str | None, limit: int = 6,
) -> list[dict]:
    '''Bounded seed-pair outcomes for judging whether Alchimie openings are intuitive.'''
    owned = set(seeds)
    candidates = []
    for left, right in combinations(sorted(owned), 2):
        fresh = [
            node_id for node_id in svc.common_neighbors(left, right, category=category)
            if node_id not in owned
        ]
        if fresh:
            fresh.sort(key=lambda node_id: (
                -node_brief(svc, node_id)['salience'], node_id,
            ))
            candidates.append({
                'pair': [_concept_ref(svc, left), _concept_ref(svc, right)],
                'result_count': len(fresh),
                'results': [_concept_ref(svc, node_id) for node_id in fresh[:4]],
            })
    candidates.sort(key=lambda item: (
        -item['result_count'], item['pair'][0]['id'], item['pair'][1]['id'],
    ))
    return candidates[:limit]


def minimum_alchimie_recipe(
    svc: WordGameService,
    seeds: list[str],
    target: str,
    category: str | None,
    max_actions: int,
) -> list[dict] | None:
    '''One deterministic minimum-action recipe, mirroring the bounded runtime BFS.'''
    max_actions = min(max_actions, ALCHIMIE_MAX_ACTIONS)
    start = frozenset(seeds)
    frontier: set[frozenset[str]] = {start}
    seen: set[frozenset[str]] = {start}
    parents: dict[
        frozenset[str], tuple[frozenset[str], tuple[str, str], frozenset[str]]
    ] = {}
    state_count = 1

    def render_step(
        pair: tuple[str, str], fresh: frozenset[str], required: set[str],
    ) -> dict:
        required_ranked = sorted(required)
        optional = sorted(
            fresh - required,
            key=lambda node_id: (-node_brief(svc, node_id)['salience'], node_id),
        )
        ranked = [*required_ranked, *optional]
        preview_size = max(6, len(required_ranked))
        return {
            'pair': [_concept_ref(svc, pair[0]), _concept_ref(svc, pair[1])],
            'result_count': len(fresh),
            'results': [_concept_ref(svc, node_id) for node_id in ranked[:preview_size]],
        }

    def reconstruct(
        state: frozenset[str], final_pair: tuple[str, str], final_fresh: frozenset[str],
    ) -> list[dict]:
        raw_steps = [(final_pair, final_fresh)]
        while state != start:
            previous, pair, fresh = parents[state]
            raw_steps.append((pair, fresh))
            state = previous
        raw_steps.reverse()
        steps = []
        for index, (pair, fresh) in enumerate(raw_steps):
            later_inputs = {
                node_id
                for later_pair, _ in raw_steps[index + 1:]
                for node_id in later_pair
            }
            required = set(fresh & later_inputs)
            if target in fresh:
                required.add(target)
            steps.append(render_step(pair, fresh, required))
        return steps

    for _action in range(1, max_actions + 1):
        next_layer: set[frozenset[str]] = set()
        for owned in sorted(frontier, key=lambda state: tuple(sorted(state))):
            for left, right in combinations(sorted(owned), 2):
                fresh = frozenset(
                    node_id
                    for node_id in svc.common_neighbors(left, right, category=category)
                    if node_id not in owned
                )
                if not fresh:
                    continue
                pair = (left, right)
                if target in fresh:
                    return reconstruct(owned, pair, fresh)
                state = owned | fresh
                if state in seen or state in next_layer:
                    continue
                state_count += 1
                if state_count > ALCHIMIE_MAX_SEARCH_STATES:
                    return None
                parents[state] = (owned, pair, fresh)
                next_layer.add(state)
        if not next_layer:
            return None
        frontier = next_layer
        seen.update(frontier)
    return None


def build_dossier(rec: dict, game: str, svc: WordGameService, strong: dict,
                  findings: list[dict], regions: dict | None = None) -> dict:
    dossier = {
        "id": rec["id"], "game": game, "category": rec.get("category"),
        "difficulty": rec.get("difficulty"), "status": rec.get("status"),
        "record_sha256": canonical_json_sha256(rec),
        "kg_sha256": kg_sha256(),
        "lint_findings": findings,
    }
    if regions:  # rubric A7 context for judges
        involved = set()
        if game == "conexiuni":
            involved = {n for ids in rec["groups"].values() for n in ids}
        elif game == "contexto":
            involved = {rec["target"]}
        elif game == "lant":
            involved = {rec["start"], rec["target"]}
        elif game == "alchimie":
            involved = {rec["target"], *rec["seeds"]}
        flags = {
            node_brief(svc, n)["label"]: regions["generic_nodes"][n]
            for n in sorted(involved) if n in regions["generic_nodes"]
        }
        if flags:
            dossier["nondistinctive_region_links"] = flags
    if game == "conexiuni":
        group_labels = rec.get("group_labels") or {}
        member_group = {n: g for g, ids in rec["groups"].items() for n in ids}
        neighbors = {n: set(svc.neighbor_ids(n)) for n in member_group}
        node_types = {n: node_brief(svc, n)["node_type"] for n in member_group}
        unfair, contested, engine_unfair = fairness_counts(
            rec["groups"], neighbors, node_types
        )
        dossier["fairness"] = {
            "unfair_tiles": sorted(node_brief(svc, n)["label"] for n in unfair),
            "contested_tiles": sorted(node_brief(svc, n)["label"] for n in contested),
            "engine_unfair_raw": engine_unfair,
        }
        dossier["groups"] = [
            {
                "label": group_labels.get(g, g),
                "members": [node_brief(svc, n) for n in rec["groups"][g]],
            }
            for g in sorted(rec["groups"])
        ]
        cross = []
        for a, others in strong.items():
            if a not in member_group:
                continue
            for b, s in others.items():
                if b in member_group and member_group[a] != member_group[b] and a < b:
                    cross.append({
                        "a": node_brief(svc, a)["label"],
                        "a_group": group_labels.get(member_group[a]),
                        "b": node_brief(svc, b)["label"],
                        "b_group": group_labels.get(member_group[b]),
                        "strength": round(s, 2),
                    })
        dossier["cross_group_strong_edges"] = sorted(
            cross, key=lambda c: (-c["strength"], c["a"], c["b"])
        )
    elif game == "contexto":
        target = rec["target"]
        dossier["target"] = node_brief(svc, target)
        dossier["reachable"] = len(svc.distances_to(target))
        neigh = []
        for predecessor in svc.predecessor_ids(target):
            edge = svc.link(predecessor, target)
            if edge and edge.strength >= STRONG_EDGE:
                neigh.append({
                    **node_brief(svc, predecessor),
                    "strength": round(edge.strength, 2),
                })
        dossier["strong_neighbors"] = sorted(
            neigh, key=lambda item: (-item["strength"], item["id"])
        )[:10]
    elif game == "lant":
        dossier["start"] = node_brief(svc, rec["start"])
        dossier["target"] = node_brief(svc, rec["target"])
        dossier["optimal"] = rec.get("optimal")
        optimal = rec.get('optimal')
        if (
            isinstance(optimal, int)
            and svc.exists(str(rec.get('start')))
            and svc.exists(str(rec.get('target')))
        ):
            first_hops, min_width, total_nodes = lant_branch_profile(
                svc, str(rec['start']), str(rec['target']), optimal,
            )
            dossier['branch_profile'] = {
                'valid_first_hops': first_hops,
                'narrowest_shortest_path_layer': min_width,
                'total_intermediate_shortest_path_nodes': total_nodes,
            }
            dossier['representative_shortest_paths'] = representative_shortest_paths(
                svc, str(rec['start']), str(rec['target']), optimal,
            )
    elif game == "alchimie":
        dossier["target"] = node_brief(svc, rec["target"])
        dossier["seeds"] = [node_brief(svc, s) for s in rec["seeds"]]
        dossier["target_depth"] = rec.get("target_depth")
        seeds = [str(seed) for seed in rec.get('seeds', [])]
        target = str(rec.get('target', ''))
        category = str(rec.get('category') or '') or None
        if target and all(svc.exists(nid) for nid in [*seeds, target]):
            generations = _closure_generations(svc, seeds, category)
            dossier['craft_profile'] = {
                'opening_pairs': _opening_pairs(svc, seeds, category),
                'closure_size': len(generations),
                'target_generation': generations.get(target),
            }
            dossier['productive_openings'] = productive_opening_pairs(
                svc, seeds, category,
            )
            target_depth = rec.get('target_depth')
            if isinstance(target_depth, int):
                dossier['minimum_action_recipe'] = minimum_alchimie_recipe(
                    svc, seeds, target, category, target_depth,
                )
    return bind_dossier(dossier)


# --------------------------------------------------------------------- main
def run(pack: dict, svc: WordGameService, strong: dict, regions: dict,
        games: list[str], statuses: set[str], ids: set[str] | None):
    approved_quads: dict[frozenset, list[str]] = defaultdict(list)
    for rec in pack["conexiuni"]:
        compare_selected = (
            ids is not None
            and rec.get('status') in statuses
            and rec.get('id') in ids
        )
        if rec.get('status') == 'approved' or compare_selected:
            for g in rec["groups"].values():
                approved_quads[frozenset(g)].append(rec["id"])

    approved_use = Counter()
    for rec in pack['conexiuni']:
        if rec.get('status') == 'approved':
            for group in rec['groups'].values():
                approved_use.update(group)
    projected_use = approved_use.copy()
    if ids is not None:
        for rec in pack['conexiuni']:
            if rec.get('status') == 'pending' and rec.get('id') in ids:
                for group in rec['groups'].values():
                    projected_use.update(group)

    items: dict[str, dict] = {}
    selected: list[tuple[str, dict, list[dict]]] = []
    for game in games:
        for rec in pack[game]:
            if rec.get("status") not in statuses:
                continue
            if ids is not None and rec["id"] not in ids:
                continue
            if game == "conexiuni":
                findings = check_conexiuni(rec, svc, strong, approved_quads)
                if ids is not None:
                    board = {nid for group in rec['groups'].values() for nid in group}
                    overused = [
                        f'{node_brief(svc, nid)["label"]} ({projected_use[nid]})'
                        for nid in sorted(board)
                        if projected_use[nid] > MEMBER_OVERUSE
                    ]
                    if overused:
                        findings.append({
                            'check': 'member_overuse',
                            'level': 'WARN',
                            'detail': 'projected approved-batch use exceeds '
                                      f'{MEMBER_OVERUSE}: ' + ', '.join(overused),
                        })
            elif game == "contexto":
                findings = check_target_salience(rec, svc, rec["target"])
            elif game == "lant":
                findings = check_target_salience(rec, svc, rec["start"], rec["target"])
            else:  # alchimie
                findings = check_target_salience(rec, svc, rec["target"])
            findings.extend(check_generic_region(rec, game, svc, regions))
            selected.append((game, rec, findings))
            if findings:
                items[rec["id"]] = {
                    "game": game, "status": rec.get("status"),
                    "difficulty": rec.get("difficulty"), "findings": findings,
                }

    pack_findings = []
    if "conexiuni" in games and ids is None:
        for nid, count in approved_use.most_common():
            if count <= MEMBER_OVERUSE:
                break
            pack_findings.append({
                "check": "member_overuse", "level": "WARN",
                "detail": f"{node_brief(svc, nid)['label']} appears in "
                          f"{count} approved conexiuni boards (> {MEMBER_OVERUSE})",
            })
    return items, pack_findings, selected


def selection_errors(pack: dict, games: list[str], statuses: set[str], ids: set[str] | None,
                     selected: list[tuple[str, dict, list[dict]]]) -> list[str]:
    '''Explain explicit ids that the active filters did not check.'''
    if ids is None:
        return []
    locations = {
        str(rec.get('id')): (game, str(rec.get('status')))
        for game in GAME_KINDS for rec in pack.get(game, [])
    }
    selected_ids = {str(rec['id']) for _, rec, _ in selected}
    errors = []
    for iid in sorted(ids):
        location = locations.get(iid)
        if location is None:
            errors.append(f'unknown item id: {iid}')
        elif location[0] not in games:
            errors.append(f'{iid} belongs to game {location[0]!r}, excluded by --game')
        elif location[1] not in statuses:
            errors.append(f'{iid} has status {location[1]!r}, excluded by --status')
        elif iid not in selected_ids:
            errors.append(f'{iid} was not checked')
    return errors


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Romanian labels on Windows consoles
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=GAME_KINDS, help="limit to one game")
    parser.add_argument("--status", help="comma list (default: approved,pending)")
    parser.add_argument('--ids', help='comma list of item ids to check')
    parser.add_argument("--json", help="write the machine-readable report here")
    parser.add_argument("--dossier", help="write per-item judge dossiers to this dir")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when any selected item has a FAIL finding")
    args = parser.parse_args(argv[1:])

    games = [args.game] if args.game else list(GAME_KINDS)
    statuses = {
        part.strip()
        for part in (args.status or 'approved,pending').split(',')
        if part.strip()
    }
    invalid_statuses = statuses - set(STATUSES)
    if invalid_statuses:
        parser.error('unknown --status value(s): ' + ', '.join(sorted(invalid_statuses)))
    ids = (
        {part.strip() for part in args.ids.split(',') if part.strip()}
        if args.ids is not None
        else None
    )
    if args.ids is not None and not ids:
        parser.error('--ids must contain at least one item id')

    pack, svc, strong, regions = load_all(PACKAGE_PACK, PACKAGE_KG)
    items, pack_findings, selected = run(pack, svc, strong, regions, games, statuses, ids)
    missing = selection_errors(pack, games, statuses, ids, selected)
    if missing:
        for error in missing:
            print(f'critique_pack: ERROR: {error}', file=sys.stderr)
        return 2
    if ids is None:  # pack-level A7 inventory for edge-cleanup batches
        for nid, reason in sorted(regions["generic_nodes"].items()):
            pack_findings.append({
                "check": "nondistinctive_region_link", "level": "WARN",
                "detail": f"{node_brief(svc, nid)['label']}: {reason}",
            })

    by_check = Counter()
    fails = 0
    for info in items.values():
        for f in info["findings"]:
            by_check[(f["check"], f["level"])] += 1
            fails += f["level"] == "FAIL"
    for f in pack_findings:
        by_check[(f["check"], f["level"])] += 1

    print(f"critique_pack: {len(selected)} item(s) checked, "
          f"{len(items)} flagged, {fails} FAIL finding(s)")
    for (check, level), count in sorted(by_check.items()):
        print(f"  {check:<20} {level:<4} x{count}")
    for iid, info in sorted(items.items()):
        for f in info["findings"]:
            if f["level"] == "FAIL":
                print(f"  FAIL {iid}: [{f['check']}] {f['detail']}")

    report = {
        "thresholds": {
            "salience_floors": SALIENCE_FLOORS, "strong_edge": STRONG_EDGE,
            "mirror_pairs": MIRROR_PAIRS, "red_herring_warn": RED_HERRING_WARN,
            "red_herring_fail": RED_HERRING_FAIL, "member_overuse": MEMBER_OVERUSE,
            "region_fanout": REGION_FANOUT, "national_salience": NATIONAL_SALIENCE,
        },
        "items": items,
        "pack_findings": pack_findings,
    }
    if args.json:
        Path(args.json).write_text(
            json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"report -> {args.json}")
    if args.dossier:
        ddir = Path(args.dossier)
        ddir.mkdir(parents=True, exist_ok=True)
        for game, rec, findings in selected:
            dossier = build_dossier(rec, game, svc, strong, findings, regions)
            (ddir / f"{rec['id']}.json").write_text(
                json.dumps(dossier, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8",
            )
        print(f"{len(selected)} dossier(s) -> {ddir}")

    if args.strict and fails:
        print("critique_pack: FAIL (strict)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
