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
``duplicate_groups`` flags quads already used by an approved board;
``salience_floor`` flags Contexto/Lant/Alchimie targets below their difficulty band;
``member_overuse`` flags nodes reused across too many approved Conexiuni boards.

Usage::

    python scripts/critique_pack.py [--game G] [--status S] [--ids a,b] \
        [--json OUT] [--dossier DIR] [--strict]

Default is a report over the whole pack (exit 0). ``--dossier`` writes one JSON
dossier per selected item for judge-fleet consumption.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.packs import GAME_KINDS  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

PACKAGE_PACK = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "games_pack.json"
PACKAGE_KG = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"

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
                "salience": 0.0, "degree": 0, "description": ""}
    return {
        "id": nid,
        "label": node.label_ro,
        "node_type": node.node_type,
        "category": node.category,
        "salience": node.salience,
        "degree": node.degree,
        "description": node.description,
    }


# --------------------------------------------------------------------- per-item checks
def check_generic_region(rec: dict, game: str, svc: WordGameService,
                         strong: dict, regions: dict) -> list[dict]:
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
            polluted = [
                node_brief(svc, b)["label"]
                for b in strong.get(target, ())
                if b in generic
            ]
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
                "detail": f'group "{labels.get(gk, gk)}" reuses an approved quad '
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
                          f"approved quad (near-duplicate; see: {', '.join(near)})",
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
def build_dossier(rec: dict, game: str, svc: WordGameService, strong: dict,
                  findings: list[dict], regions: dict | None = None) -> dict:
    dossier = {
        "id": rec["id"], "game": game, "category": rec.get("category"),
        "difficulty": rec.get("difficulty"), "status": rec.get("status"),
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
            for n in involved if n in regions["generic_nodes"]
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
            cross, key=lambda c: -c["strength"]
        )
    elif game == "contexto":
        target = rec["target"]
        dossier["target"] = node_brief(svc, target)
        dossier["reachable"] = len(svc.distances_to(target))
        neigh = [
            {**node_brief(svc, b), "strength": round(s, 2)}
            for b, s in sorted(strong.get(target, {}).items(), key=lambda kv: -kv[1])
        ]
        dossier["strong_neighbors"] = neigh[:10]
    elif game == "lant":
        dossier["start"] = node_brief(svc, rec["start"])
        dossier["target"] = node_brief(svc, rec["target"])
        dossier["optimal"] = rec.get("optimal")
    elif game == "alchimie":
        dossier["target"] = node_brief(svc, rec["target"])
        dossier["seeds"] = [node_brief(svc, s) for s in rec["seeds"]]
        dossier["target_depth"] = rec.get("target_depth")
    return dossier


# --------------------------------------------------------------------- main
def run(pack: dict, svc: WordGameService, strong: dict, regions: dict,
        games: list[str], statuses: set[str], ids: set[str] | None):
    approved_quads: dict[frozenset, list[str]] = defaultdict(list)
    for rec in pack["conexiuni"]:
        if rec.get("status") == "approved":
            for g in rec["groups"].values():
                approved_quads[frozenset(g)].append(rec["id"])

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
            elif game == "contexto":
                findings = check_target_salience(rec, svc, rec["target"])
            elif game == "lant":
                findings = check_target_salience(rec, svc, rec["start"], rec["target"])
            else:  # alchimie
                findings = check_target_salience(rec, svc, rec["target"])
            findings.extend(check_generic_region(rec, game, svc, strong, regions))
            selected.append((game, rec, findings))
            if findings:
                items[rec["id"]] = {
                    "game": game, "status": rec.get("status"),
                    "difficulty": rec.get("difficulty"), "findings": findings,
                }

    pack_findings = []
    if "conexiuni" in games and ids is None:
        use = Counter()
        for rec in pack["conexiuni"]:
            if rec.get("status") == "approved":
                for g in rec["groups"].values():
                    use.update(g)
        for nid, count in use.most_common():
            if count <= MEMBER_OVERUSE:
                break
            pack_findings.append({
                "check": "member_overuse", "level": "WARN",
                "detail": f"{node_brief(svc, nid)['label']} appears in "
                          f"{count} approved conexiuni boards (> {MEMBER_OVERUSE})",
            })
    return items, pack_findings, selected


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Romanian labels on Windows consoles
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=GAME_KINDS, help="limit to one game")
    parser.add_argument("--status", help="comma list (default: approved,pending)")
    parser.add_argument("--ids", help="comma list of item ids to check")
    parser.add_argument("--json", help="write the machine-readable report here")
    parser.add_argument("--dossier", help="write per-item judge dossiers to this dir")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when any selected item has a FAIL finding")
    args = parser.parse_args(argv[1:])

    games = [args.game] if args.game else list(GAME_KINDS)
    statuses = set((args.status or "approved,pending").split(","))
    ids = set(args.ids.split(",")) if args.ids else None

    pack, svc, strong, regions = load_all(PACKAGE_PACK, PACKAGE_KG)
    items, pack_findings, selected = run(pack, svc, strong, regions, games, statuses, ids)
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
