#!/usr/bin/env python3
"""Import AI-generated curated content (subgraph + game instances) into the repo.

Consumes a directory of per-category generation output (the codex-fleet /
verification pipeline of ADR-0011):

    <dir>/<category>/candidates.json       # nodes, edges, conexiuni/contexto/lant/alchimie
    <dir>/<category>/verify_factual.json   # {"issues":[{"ref","severity","issue","correction"}]}
    <dir>/<category>/verify_quality.json   # {"instances":[{"ref","scores","verdict","note"}]}

Curation policy (quality over quantity):
  * factual ``block`` on a node -> the node, its edges and every instance touching
    it are dropped; ``block`` on an instance -> that instance is dropped;
  * quality verdict ``keep`` -> imported as ``status: approved``; ``fix`` ->
    imported as ``status: pending`` (invisible to players until reviewed);
    ``drop``/missing -> not imported;
  * every surviving instance is re-derived against the MERGED graph (Lant optimal
    via BFS, Alchimie closure depth + opening pairs, Contexto floors, Conexiuni
    board shape) — the generator's numbers are never trusted;
  * existing pack items are re-derived too (the denser graph can shorten paths).

Steps: merge accepted nodes/edges via densify_content.run() (fixture regenerated +
validated + rolled back on failure), rebuild games_pack.json (both copies), run
the pack validator, roll the pack back if it fails. A human-review report of every
``fix``-severity factual issue is written next to the input dir.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
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

# Generated nodes that duplicate an existing concept under another id: the new node
# definition is dropped and every reference (edges, tiles, targets, seeds) is remapped
# to the canonical id, so the graph never grows same-label twins of one concept.
DUPLICATE_ALIASES = {
    "n_ftv_cristian_mungiu": "n_cristian_mungiu",
    "n_net_lasa_ca_merge_si_asa": "n_vdr_lasa_ca_merge",
}

LANT_BANDS = {"usor": (2, 3), "normal": (3, 4), "greu": (4, 6)}
ALCH_BANDS = {"usor": (2, 2), "normal": (2, 3), "greu": (3, 5)}
BUILD_VERSION = "fixture-v5-pop"
NOTE = (
    "v5: pop-culture + serious curated-content batch (ADR-0011) — AI-generated, "
    "fact/quality-verified subgraph merged on the v4 dense graph; kg_puzzles "
    "regenerated on the merged graph via the validator-mirroring BFS builder."
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
                # Combines are category-scoped (ADR-0013): re-derive the depth in-category
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
        m = rx.search(str(issue.get("ref", "")))
        if m:
            idx = int(m.group(1))
            sev = str(issue.get("severity", "nit"))
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

    categories = sorted(d.name for d in gen_dir.iterdir() if (d / "candidates.json").exists())
    if not categories:
        raise SystemExit(f"no <category>/candidates.json under {gen_dir}")

    report: list[str] = []
    all_nodes: list[dict] = []
    all_edges: list[dict] = []
    blocked_nodes: set[str] = set()
    per_cat: dict[str, dict] = {}

    for cat in categories:
        cdir = gen_dir / cat
        cand = _apply_aliases(_load(cdir / "candidates.json"))
        fpath = cdir / "verify_factual.json"
        qpath = cdir / "verify_quality.json"
        factual = _load(fpath) if fpath.exists() else {}
        quality = _load(qpath) if qpath.exists() else {}
        issues = list(factual.get("issues", []))

        node_ids_here = {str(n["id"]) for n in cand.get("nodes", [])}
        blocked_edges: set[tuple[str, str]] = set()
        for issue in issues:
            ref = str(issue.get("ref", ""))
            severity = issue.get("severity")
            edge_ref = re.search(r"(\S+?)\s*->\s*(\S+)", ref)
            if severity == "block" and ref in node_ids_here:
                blocked_nodes.add(ref)
                report.append(f"BLOCKED node {ref} ({cat}): {issue.get('issue')}")
            elif severity == "block" and edge_ref:
                blocked_edges.add((edge_ref.group(1), edge_ref.group(2)))
                report.append(f"BLOCKED edge {ref} ({cat}): {issue.get('issue')}")
            elif severity == "fix":
                report.append(
                    f"REVIEW ({cat}) {ref}: {issue.get('issue')} -> {issue.get('correction')}"
                )

        def _edge_ok(e: dict, blocked_pairs: set[tuple[str, str]] = blocked_edges) -> bool:
            src, dst = str(e.get("src")), str(e.get("dst"))
            if src in blocked_nodes or dst in blocked_nodes:
                return False
            return (src, dst) not in blocked_pairs and (dst, src) not in blocked_pairs

        # The generator emits nodes without a category (it is implicit per file).
        kept_nodes = [
            {**n, "category": str(n.get("category") or cat)}
            for n in cand.get("nodes", [])
            if str(n["id"]) not in blocked_nodes
        ]
        kept_edges = [e for e in cand.get("edges", []) if _edge_ok(e)]
        all_nodes.extend(kept_nodes)
        all_edges.extend(kept_edges)

        verdicts = {
            str(inst.get("ref", "")): str(inst.get("verdict", "drop"))
            for inst in quality.get("instances", [])
        }
        per_cat[cat] = {
            "cand": cand,
            "verdicts": verdicts,
            "factual_by_game": {g: _instance_refs(issues, g) for g in GAME_KINDS},
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

    counters = {g: len(survivors[g]) for g in GAME_KINDS}
    stats = {"approved": 0, "pending": 0, "skipped": 0}

    def add_item(game: str, cat: str, rec: dict, verdict: str) -> None:
        counters[game] += 1
        rec["id"] = f"{PREFIX[game]}_{cat}_{counters[game]:03d}"
        rec["category"] = cat
        rec["source"] = "ai"
        rec["status"] = "approved" if verdict == "keep" else "pending"
        errors = validate_envelope(rec, game) or validate_payload(rec, game, svc)
        if errors:
            counters[game] -= 1
            stats["skipped"] += 1
            report.append(f"INVALID {game} candidate ({cat}): {errors[:2]}")
            return
        survivors[game].append(rec)
        stats[rec["status"]] += 1

    for cat, bundle in per_cat.items():
        cand, verdicts = bundle["cand"], bundle["verdicts"]
        for game in GAME_KINDS:
            factual_flags = bundle["factual_by_game"][game]
            for idx, inst in enumerate(cand.get(game, []) or []):
                verdict = verdicts.get(f"{game}[{idx}]", "drop")
                if verdict == "drop" or factual_flags.get(idx) == "block":
                    stats["skipped"] += 1
                    continue
                # A factual 'fix' flag demotes a keep to pending: only items that are
                # BOTH quality-kept and factually clean ship as approved.
                if factual_flags.get(idx) == "fix":
                    verdict = "fix"
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
                add_item(game, cat, rec, verdict)

    for game in GAME_KINDS:
        pack[game] = sorted(survivors[game], key=lambda r: r["id"])
    pack["meta"]["counts"] = {g: len(pack[g]) for g in GAME_KINDS}
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
