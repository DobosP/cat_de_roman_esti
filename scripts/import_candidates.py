#!/usr/bin/env python3
"""Import AI-generated curated content (subgraph + game instances) into the repo.

Consumes a directory of per-category generation output (the codex-fleet /
verification pipeline of ADR-0011):

    <dir>/<category>/candidates.json       # nodes, edges, conexiuni/contexto/lant/alchimie
    <dir>/<category>/verify_factual.json   # category, reviewed_refs, issues, coverage_note
    <dir>/<category>/verify_quality.json   # {"instances":[{"ref","scores","verdict","note"}]}

Curation policy (quality over quantity):
  * every raw node, edge and game instance must be named exactly once in the factual
    ``reviewed_refs`` inventory; quality must contain exactly one row per instance;
  * missing, partial, duplicate or category-mismatched verification aborts the whole
    batch before graph or pack mutation;
  * factual ``block`` on a node -> the node, its edges and every instance touching
    it are dropped; ``block`` on an instance -> that instance is dropped;
  * unresolved factual ``fix`` issues or quality ``fix`` verdicts abort the batch;
    factual ``block`` and quality ``drop`` are explicit, verified exclusions;
  * quality verdict ``keep`` -> imported as ``status: pending``;
    ADR-0023's strict lint + two-agent judge gate is the only promotion path;
  * every surviving instance is re-derived against the MERGED graph (Lanț distance +
    branch floor, Alchimie exact action par + opening pairs, Contexto floors,
    Conexiuni board shape) — the generator's numbers are never trusted;
  * existing pack items are re-derived too (the denser graph can shorten paths).

Steps: merge accepted nodes/edges via densify_content.run() (fixture regenerated +
validated + rolled back on failure), rebuild games_pack.json (both copies), run
the pack validator, and roll the pack back if it fails.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import densify_content  # noqa: E402
import validate_games_pack  # noqa: E402

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    ALCHIMIE_MAX_ACTIONS,
    GAME_KINDS,
    _closure_generations,
    _opening_pairs,
    minimum_alchimie_actions,
    validate_envelope,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)
PREFIX = {"conexiuni": "cx", "contexto": "ct", "lant": "lt", "alchimie": "al"}
FACTUAL_SEVERITIES = frozenset({"block", "fix", "note"})
QUALITY_VERDICTS = frozenset({"keep", "fix", "drop"})
EDGE_REF_RE = re.compile(r"^edge:(?P<src>\S+)->(?P<dst>\S+)$")

# Generated nodes that duplicate an existing concept under another id: the new node
# definition is dropped and every reference (edges, tiles, targets, seeds) is remapped
# to the canonical id, so the graph never grows same-label twins of one concept.
DUPLICATE_ALIASES = {
    "n_ftv_cristian_mungiu": "n_cristian_mungiu",
    "n_net_lasa_ca_merge_si_asa": "n_vdr_lasa_ca_merge",
}

LANT_BANDS = {"usor": (2, 3), "normal": (3, 4), "greu": (4, 6)}
ALCH_BANDS = {"usor": (2, 2), "normal": (2, 3), "greu": (3, 5)}
BUILD_VERSION = "fixture-v42-pegas-colind-damigeana"
NOTE = (
    "v5: pop-culture + serious curated-content batch (ADR-0011) — AI-generated, "
    "fact/quality-verified subgraph merged on the v4 dense graph; kg_puzzles "
    "regenerated on the merged graph via the validator-mirroring BFS builder."
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_import_status(verdict: str) -> str | None:
    """Stage fully pre-screened candidates pending; critique is the promotion path."""
    return "pending" if verdict == "keep" else None


def _nonblank(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value.strip() else None


def _reference(value: object) -> str | None:
    value = _nonblank(value)
    if value is None or value != value.strip() or any(char.isspace() for char in value):
        return None
    return value


def _duplicate_values(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def _load_object(path: Path, label: str, errors: list[str]) -> dict | None:
    if not path.exists():
        errors.append(f"{label}: missing {path.name}")
        return None
    try:
        payload = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot read {path.name}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label}: {path.name} must contain an object")
        return None
    return payload


def _object_rows(
    payload: dict,
    key: str,
    label: str,
    errors: list[str],
) -> list[dict]:
    value = payload.get(key)
    if not isinstance(value, list):
        errors.append(f"{label}: {key} must be an array")
        return []
    rows: list[dict] = []
    for idx, row in enumerate(value):
        if not isinstance(row, dict):
            errors.append(f"{label}: {key}[{idx}] must be an object")
            continue
        rows.append(row)
    return rows


def _raw_reference_inventory(
    category: str,
    candidate: dict,
    errors: list[str],
) -> tuple[set[str], set[str], set[str]]:
    """Return all/node/instance references before any alias or block transformation."""
    label = f"{category}/candidates.json"
    refs: list[str] = []
    node_refs: set[str] = set()
    instance_refs: set[str] = set()

    for idx, node in enumerate(_object_rows(candidate, "nodes", label, errors)):
        node_id = _reference(node.get("id"))
        if node_id is None:
            errors.append(f"{label}: nodes[{idx}].id must be a nonblank string")
            continue
        refs.append(node_id)
        node_refs.add(node_id)

    for idx, edge in enumerate(_object_rows(candidate, "edges", label, errors)):
        src = _reference(edge.get("src"))
        dst = _reference(edge.get("dst"))
        if src is None or dst is None:
            errors.append(f"{label}: edges[{idx}] needs nonblank string src and dst")
            continue
        refs.append(f"edge:{src}->{dst}")

    for game in GAME_KINDS:
        rows = candidate.get(game)
        if not isinstance(rows, list):
            errors.append(f"{label}: {game} must be an array")
            continue
        for idx, row in enumerate(rows):
            ref = f"{game}[{idx}]"
            refs.append(ref)
            instance_refs.add(ref)
            if not isinstance(row, dict):
                errors.append(f"{label}: {ref} must be an object")

    duplicates = _duplicate_values(refs)
    if duplicates:
        errors.append(f"{label}: raw references are not unique: {duplicates}")
    return set(refs), node_refs, instance_refs


def _validate_header(
    category: str,
    name: str,
    artifact: dict,
    errors: list[str],
) -> None:
    label = f"{category}/{name}"
    if artifact.get("category") != category:
        errors.append(f"{label}: category must equal {category!r}")
    if _nonblank(artifact.get("coverage_note")) is None:
        errors.append(f"{label}: coverage_note must be a nonblank string")


def _validate_factual(
    category: str,
    artifact: dict,
    expected_refs: set[str],
    errors: list[str],
) -> None:
    label = f"{category}/verify_factual.json"
    _validate_header(category, "verify_factual.json", artifact, errors)

    reviewed = artifact.get("reviewed_refs")
    reviewed_values: list[str] = []
    if not isinstance(reviewed, list):
        errors.append(f"{label}: reviewed_refs must be an array")
    else:
        for idx, ref in enumerate(reviewed):
            canonical = _reference(ref)
            if canonical is None:
                errors.append(
                    f"{label}: reviewed_refs[{idx}] must be a canonical nonblank ref"
                )
            else:
                reviewed_values.append(canonical)
        duplicates = _duplicate_values(reviewed_values)
        if duplicates:
            errors.append(f"{label}: reviewed_refs contains duplicates: {duplicates}")
        reviewed_set = set(reviewed_values)
        missing = sorted(expected_refs - reviewed_set)
        extra = sorted(reviewed_set - expected_refs)
        if missing:
            errors.append(f"{label}: reviewed_refs missing {missing}")
        if extra:
            errors.append(f"{label}: reviewed_refs contains unknown refs {extra}")

    issues = artifact.get("issues")
    if not isinstance(issues, list):
        errors.append(f"{label}: issues must be an array")
        return
    for idx, issue in enumerate(issues):
        issue_label = f"{label}: issues[{idx}]"
        if not isinstance(issue, dict):
            errors.append(f"{issue_label} must be an object")
            continue
        ref = _reference(issue.get("ref"))
        if ref is None:
            errors.append(f"{issue_label}.ref must be a canonical nonblank ref")
        elif ref not in expected_refs:
            errors.append(f"{issue_label}.ref is unknown: {ref!r}")
        severity = issue.get("severity")
        if severity not in FACTUAL_SEVERITIES:
            errors.append(f"{issue_label}.severity is unknown: {severity!r}")
        elif severity == "fix":
            errors.append(f"{issue_label} is an unresolved factual fix")
        if _nonblank(issue.get("issue")) is None:
            errors.append(f"{issue_label}.issue must be a nonblank string")


def _validate_quality(
    category: str,
    artifact: dict,
    expected_refs: set[str],
    errors: list[str],
) -> None:
    label = f"{category}/verify_quality.json"
    _validate_header(category, "verify_quality.json", artifact, errors)

    instances = artifact.get("instances")
    if not isinstance(instances, list):
        errors.append(f"{label}: instances must be an array")
        return
    seen: list[str] = []
    for idx, instance in enumerate(instances):
        instance_label = f"{label}: instances[{idx}]"
        if not isinstance(instance, dict):
            errors.append(f"{instance_label} must be an object")
            continue
        ref = _reference(instance.get("ref"))
        if ref is None:
            errors.append(f"{instance_label}.ref must be a canonical nonblank ref")
        else:
            seen.append(ref)
            if ref not in expected_refs:
                errors.append(f"{instance_label}.ref is unknown: {ref!r}")
        verdict = instance.get("verdict")
        if verdict not in QUALITY_VERDICTS:
            errors.append(f"{instance_label}.verdict is unknown: {verdict!r}")
        elif verdict == "fix":
            errors.append(f"{instance_label} is an unresolved quality fix")
        if _nonblank(instance.get("note")) is None:
            errors.append(f"{instance_label}.note must be a nonblank string")

    duplicates = _duplicate_values(seen)
    if duplicates:
        errors.append(f"{label}: duplicate instance refs: {duplicates}")
    seen_set = set(seen)
    missing = sorted(expected_refs - seen_set)
    extra = sorted(seen_set - expected_refs)
    if missing:
        errors.append(f"{label}: instances missing {missing}")
    if extra:
        errors.append(f"{label}: instances contains unknown refs {extra}")


def preflight_candidates(gen_dir: Path) -> dict[str, dict]:
    """Validate the complete raw batch without mutating candidate data or repo files."""
    if not gen_dir.is_dir():
        raise SystemExit(f"candidate batch directory does not exist: {gen_dir}")

    filenames = {"candidates.json", "verify_factual.json", "verify_quality.json"}
    category_dirs = sorted(
        directory
        for directory in gen_dir.iterdir()
        if directory.is_dir() and any((directory / name).exists() for name in filenames)
    )
    if not category_dirs:
        raise SystemExit(f"no candidate category artifacts under {gen_dir}")

    errors: list[str] = []
    bundles: dict[str, dict] = {}
    for category_dir in category_dirs:
        category = category_dir.name
        candidate = _load_object(
            category_dir / "candidates.json",
            f"{category}/candidates.json",
            errors,
        )
        factual = _load_object(
            category_dir / "verify_factual.json",
            f"{category}/verify_factual.json",
            errors,
        )
        quality = _load_object(
            category_dir / "verify_quality.json",
            f"{category}/verify_quality.json",
            errors,
        )
        if candidate is None or factual is None or quality is None:
            continue
        expected, node_refs, instance_refs = _raw_reference_inventory(
            category, candidate, errors
        )
        _validate_factual(category, factual, expected, errors)
        _validate_quality(category, quality, instance_refs, errors)
        bundles[category] = {
            "cand": candidate,
            "factual": factual,
            "quality": quality,
            "node_refs": node_refs,
        }

    if errors:
        details = "\n- ".join(errors)
        raise SystemExit(f"invalid candidate verification contract:\n- {details}")
    return bundles


def next_item_number(items: list[dict], prefix: str) -> int:
    '''Allocate after the highest occupied global suffix, never after list length.'''
    numbers = []
    for item in items:
        iid = str(item.get('id', ''))
        head, separator, suffix = iid.rpartition('_')
        if separator and head.startswith(f'{prefix}_') and suffix.isdigit():
            numbers.append(int(suffix))
    return max(numbers, default=0) + 1


def item_high_water(pack: dict) -> dict[str, int]:
    '''Merge observed suffixes with persistent marks so retired IDs stay reserved.'''
    persisted = pack.get('meta', {}).get('id_high_water', {})
    if not isinstance(persisted, dict):
        persisted = {}
    result = {}
    for game in GAME_KINDS:
        observed = next_item_number(list(pack.get(game, [])), PREFIX[game]) - 1
        try:
            prior = max(0, int(persisted.get(game, 0)))
        except (TypeError, ValueError):
            prior = 0
        result[game] = max(observed, prior)
    return result


def initial_item_numbers(pack: dict) -> dict[str, int]:
    '''Allocate strictly above observed or persistently reserved suffixes.'''
    return {game: mark + 1 for game, mark in item_high_water(pack).items()}


def _apply_aliases(cand: dict) -> dict:
    """Remap DUPLICATE_ALIASES ids everywhere and drop the aliased node definitions."""
    if not DUPLICATE_ALIASES:
        return cand

    def rm(value: object) -> str:
        return DUPLICATE_ALIASES.get(str(value), str(value))

    cand["nodes"] = [
        n for n in cand.get("nodes", []) or [] if str(n.get("id")) not in DUPLICATE_ALIASES
    ]
    for e in cand.get("edges", []) or []:
        e["src"], e["dst"] = rm(e.get("src")), rm(e.get("dst"))
    for inst in cand.get("conexiuni", []) or []:
        for g in inst.get("groups") or []:
            g["tiles"] = [rm(t) for t in (g.get("tiles") or [])]
    for inst in cand.get("contexto", []) or []:
        inst["target"] = rm(inst.get("target"))
    for inst in cand.get("lant", []) or []:
        inst["start"], inst["target"] = rm(inst.get("start")), rm(inst.get("target"))
    for inst in cand.get("alchimie", []) or []:
        inst["seeds"] = [rm(s) for s in (inst.get("seeds") or [])]
        inst["target"] = rm(inst.get("target"))
    return cand


def _edge_ref_pair(ref: object) -> tuple[str, str] | None:
    """Parse only the canonical factual edge ref, without retaining the ``edge:`` prefix."""
    match = EDGE_REF_RE.fullmatch(str(ref))
    if match is None:
        return None
    return match.group("src"), match.group("dst")


def _instance_node_refs(game: str, instance: dict) -> set[str]:
    if game == "conexiuni":
        return {
            str(tile)
            for group in instance.get("groups", []) or []
            for tile in group.get("tiles", []) or []
        }
    if game == "contexto":
        return {str(instance.get("target"))}
    if game == "lant":
        return {str(instance.get("start")), str(instance.get("target"))}
    refs = {str(seed) for seed in instance.get("seeds", []) or []}
    refs.add(str(instance.get("target")))
    return refs


def _prepare_candidate(
    raw_candidate: dict,
    issues: list[dict],
    blocked_nodes: set[str],
) -> tuple[dict, dict[str, dict[int, str]]]:
    """Apply verified exclusions to a copy, then alias-map the surviving raw content."""
    candidate = deepcopy(raw_candidate)
    blocked_edges = {
        pair
        for issue in issues
        if issue.get("severity") == "block"
        if (pair := _edge_ref_pair(issue.get("ref"))) is not None
    }
    candidate["nodes"] = [
        node
        for node in candidate.get("nodes", []) or []
        if str(node.get("id")) not in blocked_nodes
    ]
    candidate["edges"] = [
        edge
        for edge in candidate.get("edges", []) or []
        if str(edge.get("src")) not in blocked_nodes
        and str(edge.get("dst")) not in blocked_nodes
        and (str(edge.get("src")), str(edge.get("dst"))) not in blocked_edges
    ]

    factual_by_game = {game: _instance_refs(issues, game) for game in GAME_KINDS}
    for game in GAME_KINDS:
        for idx, instance in enumerate(raw_candidate.get(game, []) or []):
            if _instance_node_refs(game, instance) & blocked_nodes:
                factual_by_game[game][idx] = "block"
    return _apply_aliases(candidate), factual_by_game


def _band_for(actual: int, declared: str, bands: dict[str, tuple[int, int]]) -> str | None:
    lo, hi = bands.get(declared, (None, None))
    if lo is not None and lo <= actual <= hi:
        return declared
    for name, (lo, hi) in bands.items():
        if lo <= actual <= hi:
            return name
    return None


def rederive_existing_items(pack: dict, svc, report: list[str]) -> dict[str, list[dict]]:
    """Re-derive every pack item's graph-dependent numbers on the CURRENT graph.

    New edges shorten BFS distances and deepen combine closures, so Lant optimal /
    Alchimie target_depth must be recomputed after any graph merge; items that no
    longer hold a playable shape are dropped (reported). Shared by
    ``import_candidates`` and ``import_enrichment``.
    """
    survivors: dict[str, list[dict]] = {g: [] for g in GAME_KINDS}
    for game in GAME_KINDS:
        for rec in pack.get(game, []):
            rec = dict(rec)
            if game == "lant":
                actual = svc.distance(str(rec["start"]), str(rec["target"]))
                band = _band_for(actual, str(rec["difficulty"]), LANT_BANDS) if actual else None
                if band is None:
                    report.append(f"DROPPED {rec['id']}: distance now {actual} (out of band)")
                    continue
                rec["optimal"], rec["difficulty"] = actual, band
            elif game == "alchimie":
                # Projection input is category-scoped (ADR-0044): derive depth in-theme.
                # and drop items whose target is no longer craftable within the theme.
                cat = str(rec.get("category") or "") or None
                seeds = [str(s) for s in rec["seeds"]]
                depth = _closure_generations(svc, seeds, cat).get(str(rec["target"]))
                band = _band_for(depth, str(rec["difficulty"]), ALCH_BANDS) if depth else None
                if band is None or _opening_pairs(svc, seeds, cat) < 2:
                    report.append(f"DROPPED {rec['id']}: in-category closure depth now {depth}")
                    continue
                par = minimum_alchimie_actions(
                    svc,
                    seeds,
                    str(rec["target"]),
                    cat,
                    max_actions=ALCHIMIE_MAX_ACTIONS,
                )
                if par is None:
                    report.append(
                        f"DROPPED {rec['id']}: target exceeds the {ALCHIMIE_MAX_ACTIONS}-action cap"
                    )
                    continue
                rec["target_depth"], rec["difficulty"] = par, band
            if validate_envelope(rec, game) or (
                rec.get("status") == "approved" and validate_payload(rec, game, svc)
            ):
                report.append(f"DROPPED {rec['id']}: no longer validates on merged graph")
                continue
            survivors[game].append(rec)
    return survivors


def _instance_refs(issues: list[dict], game: str) -> dict[int, str]:
    """Map instance index -> worst severity for refs like 'conexiuni[3]'."""
    out: dict[int, str] = {}
    rx = re.compile(rf"{game}\[(\d+)\]")
    for issue in issues:
        m = rx.fullmatch(str(issue.get("ref", "")))
        if m:
            idx = int(m.group(1))
            sev = str(issue.get("severity", "note"))
            if sev == "block" or out.get(idx) != "block":
                out[idx] = sev
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir", required=True, help="generation output dir (one subdir per category)"
    )
    parser.add_argument(
        "--skip-merge", action="store_true", help="pack rebuild only (graph already merged)"
    )
    args = parser.parse_args(argv[1:])
    gen_dir = Path(args.dir)
    raw_bundles = preflight_candidates(gen_dir)

    report: list[str] = []
    all_nodes: list[dict] = []
    all_edges: list[dict] = []
    blocked_nodes = {
        str(issue["ref"])
        for bundle in raw_bundles.values()
        for issue in bundle["factual"]["issues"]
        if issue["severity"] == "block" and issue["ref"] in bundle["node_refs"]
    }
    per_cat: dict[str, dict] = {}

    for cat, raw_bundle in raw_bundles.items():
        factual = raw_bundle["factual"]
        quality = raw_bundle["quality"]
        issues = list(factual.get("issues", []))
        cand, factual_by_game = _prepare_candidate(
            raw_bundle["cand"], issues, blocked_nodes
        )

        for issue in issues:
            ref = str(issue.get("ref", ""))
            severity = issue.get("severity")
            if severity == "block" and ref in raw_bundle["node_refs"]:
                report.append(f"BLOCKED node {ref} ({cat}): {issue.get('issue')}")
            elif severity == "block" and _edge_ref_pair(ref) is not None:
                report.append(f"BLOCKED edge {ref} ({cat}): {issue.get('issue')}")

        # The generator emits nodes without a category (it is implicit per file).
        kept_nodes = [
            {**n, "category": str(n.get("category") or cat)}
            for n in cand.get("nodes", [])
        ]
        all_nodes.extend(kept_nodes)
        all_edges.extend(cand.get("edges", []))

        verdicts = {
            str(instance["ref"]): str(instance["verdict"])
            for instance in quality.get("instances", [])
        }
        per_cat[cat] = {
            "cand": cand,
            "verdicts": verdicts,
            "factual_by_game": factual_by_game,
        }

    # ---- 1. merge the accepted subgraph (validated + rolled back inside run()) ----
    if not args.skip_merge:
        rc = densify_content.run({"nodes": all_nodes, "edges": all_edges}, BUILD_VERSION, NOTE)
        if rc != 0:
            raise SystemExit("subgraph merge failed (fixture rolled back) — aborting import")

    # ---- 2. rebuild the pack against the MERGED graph ----
    svc = WordGameService(graph=load_fixture(validate_games_pack.PACKAGE_KG).graph)
    pack_originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    pack = json.loads(pack_originals[validate_games_pack.PACKAGE_PACK].decode("utf-8"))

    # Existing items: re-derive graph-dependent numbers; drop what no longer holds.
    survivors = rederive_existing_items(pack, svc, report)

    # Persist the original/reserved high-water marks before re-derivation can retire
    # an ID. Future import sessions must never reuse progress/editorial identifiers.
    high_water = item_high_water(pack)
    next_numbers = {game: mark + 1 for game, mark in high_water.items()}
    stats = {"approved": 0, "pending": 0, "skipped": 0}

    def add_item(game: str, cat: str, rec: dict, status: str) -> None:
        rec["id"] = f"{PREFIX[game]}_{cat}_{next_numbers[game]:03d}"
        rec["category"] = cat
        rec["source"] = "ai"
        rec["status"] = status
        errors = validate_envelope(rec, game) or validate_payload(rec, game, svc)
        if errors:
            stats["skipped"] += 1
            report.append(f"INVALID {game} candidate ({cat}): {errors[:2]}")
            return
        next_numbers[game] += 1
        high_water[game] = max(high_water[game], next_numbers[game] - 1)
        survivors[game].append(rec)
        stats[rec["status"]] += 1

    for cat, bundle in per_cat.items():
        cand, verdicts = bundle["cand"], bundle["verdicts"]
        for game in GAME_KINDS:
            factual_flags = bundle["factual_by_game"][game]
            for idx, inst in enumerate(cand.get(game, []) or []):
                verdict = verdicts.get(f"{game}[{idx}]", "drop")
                status = candidate_import_status(verdict)
                if status is None or factual_flags.get(idx) == "block":
                    stats["skipped"] += 1
                    continue
                if game == "conexiuni":
                    groups_in = inst.get("groups") or []
                    tiles = [str(t) for g in groups_in for t in (g.get("tiles") or [])]
                    if len(groups_in) != 4 or len(tiles) != 16 or len(set(tiles)) != 16:
                        stats["skipped"] += 1
                        continue
                    order = list(tiles)
                    random.Random(f"{cat}:{idx}").shuffle(order)
                    rec = {
                        "difficulty": str(inst.get("difficulty", "normal")),
                        "groups": {
                            f"g{i + 1}": [str(t) for t in g["tiles"]]
                            for i, g in enumerate(groups_in)
                        },
                        "group_labels": {
                            f"g{i + 1}": str(g.get("label", ""))
                            for i, g in enumerate(groups_in)
                        },
                        "order": order,
                    }
                elif game == "contexto":
                    rec = {
                        "difficulty": str(inst.get("difficulty", "normal")),
                        "target": str(inst.get("target", "")),
                    }
                elif game == "lant":
                    start, target = str(inst.get("start", "")), str(inst.get("target", ""))
                    if not (svc.exists(start) and svc.exists(target)):
                        stats["skipped"] += 1
                        continue
                    actual = svc.distance(start, target)
                    band = (
                        _band_for(actual, str(inst.get("difficulty", "normal")), LANT_BANDS)
                        if actual
                        else None
                    )
                    if band is None:
                        stats["skipped"] += 1
                        continue
                    rec = {"difficulty": band, "start": start, "target": target, "optimal": actual}
                else:  # alchimie
                    seeds = [str(s) for s in inst.get("seeds") or []]
                    target = str(inst.get("target", ""))
                    ok = len(seeds) >= 5 and all(svc.exists(s) for s in seeds)
                    if not ok or not svc.exists(target):
                        stats["skipped"] += 1
                        continue
                    # New candidates use the same category scope and exact sequential
                    # action par as runtime play and validation.
                    depth = _closure_generations(svc, seeds[:7], cat).get(target)
                    band = (
                        _band_for(depth, str(inst.get("difficulty", "normal")), ALCH_BANDS)
                        if depth
                        else None
                    )
                    if band is None:
                        stats["skipped"] += 1
                        continue
                    par = minimum_alchimie_actions(
                        svc,
                        seeds[:7],
                        target,
                        cat,
                        max_actions=ALCHIMIE_MAX_ACTIONS,
                    )
                    if par is None:
                        stats["skipped"] += 1
                        continue
                    rec = {
                        "difficulty": band,
                        "seeds": seeds[:7],
                        "target": target,
                        "target_depth": par,
                    }
                add_item(game, cat, rec, status)

    for game in GAME_KINDS:
        pack[game] = sorted(survivors[game], key=lambda r: r["id"])
    pack["meta"]["counts"] = {g: len(pack[g]) for g in GAME_KINDS}
    pack['meta']['id_high_water'] = high_water
    pack["meta"]["note"] = (
        "Curated games pack (ADR-0011): AI-generated, fact/quality-verified batch + "
        "hand-crafted starters. Only status=approved items are served."
    )

    out = json.dumps(pack, ensure_ascii=False, indent=1) + "\n"
    for copy in PACK_COPIES:
        copy.write_text(out, encoding="utf-8")

    if validate_games_pack.main(["validate_games_pack.py"]) != 0:
        for copy, blob in pack_originals.items():
            copy.write_bytes(blob)
        raise SystemExit(
            "pack validation failed — pack ROLLED BACK (fixture keeps the merged graph)"
        )

    report_path = gen_dir / "curation_report.txt"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nimport_candidates: {stats['approved']} approved, {stats['pending']} pending, "
          f"{stats['skipped']} skipped; counts={pack['meta']['counts']}")
    print(f"human-review report: {report_path} ({len(report)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
