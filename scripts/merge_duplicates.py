#!/usr/bin/env python3
"""Merge duplicate KG concepts from a verdict file (v20 generalization of refine_dataset).

Same survivor-absorbs-duplicate mechanics as ``refine_dataset.py`` (v11) — dropped node's
label + aliases fold onto the survivor, edges are redirected + de-duplicated, games-pack
payloads are rewritten and re-derived, everything re-validated with rollback — but the
pair list comes from ``--merges <file.json>`` (``{"merges": [{"dup": id, "survivor": id,
"reason": str}, ...]}``) instead of a hardcoded dict, and salience is NOT recalibrated
(v11's one-off; tiers are healthy now).

    python scripts/merge_duplicates.py --merges <verdicts.json> [--note "..."]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import densify_content  # noqa: E402
import validate_games_pack  # noqa: E402
from import_candidates import GAME_KINDS, rederive_existing_items  # noqa: E402
from refine_dataset import _redirect_pack  # noqa: E402

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merges", required=True, help="JSON file with a 'merges' list")
    ap.add_argument("--note", default="merged judged duplicate concepts (v20 cleanup)")
    ap.add_argument("--version", default="fixture-v20-dedup")
    args = ap.parse_args(argv)

    verdicts = json.loads(Path(args.merges).read_text(encoding="utf-8"))
    merges = {m["dup"]: m["survivor"] for m in verdicts["merges"]}
    if not merges:
        print("merge_duplicates: nothing to merge")
        return 0
    # a survivor must never itself be merged away (no chains), and ids must exist
    chained = set(merges) & set(merges.values())
    if chained:
        raise SystemExit(f"merge chains not allowed (survivor also a dup): {sorted(chained)}")

    base_raw = densify_content.PACKAGE_FIXTURE.read_text(encoding="utf-8")
    tests_base = densify_content.TESTS_FIXTURE.read_text(encoding="utf-8")
    data = json.loads(base_raw)
    nodes = data["kg_nodes"]
    edges = data["kg_edges"]
    known = {n["id"] for n in nodes}
    missing = (set(merges) | set(merges.values())) - known
    if missing:
        raise SystemExit(f"unknown node ids in merge list: {sorted(missing)}")

    surviving_ids = known - set(merges)

    def rm(nid: str) -> str:
        return merges.get(nid, nid)

    survivor_by_id = {n["id"]: n for n in nodes if n["id"] in surviving_ids}
    for dup in nodes:
        if dup["id"] not in merges:
            continue
        surv = survivor_by_id[merges[dup["id"]]]
        merged = list(surv.get("aliases", []) or [])
        seen = {a.casefold() for a in merged} | {str(surv["label_ro"]).casefold()}
        for cand in [dup["label_ro"], *(dup.get("aliases", []) or [])]:
            if str(cand).casefold() not in seen:
                merged.append(str(cand))
                seen.add(str(cand).casefold())
        if merged:
            surv["aliases"] = merged
    nodes = [n for n in nodes if n["id"] in surviving_ids]

    seen_edges: set[tuple] = set()
    redirected: list[dict] = []
    for e in edges:
        src, dst = rm(e["src_id"]), rm(e["dst_id"])
        if src == dst:
            continue
        key = tuple(sorted((src, dst))) + (e["relation"],)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        redirected.append({**e, "src_id": src, "dst_id": dst})
    edges = redirected

    rc = densify_content.rebuild(data, nodes, edges, args.version, args.note, base_raw, tests_base)
    if rc != 0:
        raise SystemExit("fixture merge failed (rolled back) — aborting")

    svc = WordGameService(graph=load_fixture(validate_games_pack.PACKAGE_KG).graph)
    pack_originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    pack = json.loads(pack_originals[validate_games_pack.PACKAGE_PACK].decode("utf-8"))
    _redirect_pack(pack, rm)
    report: list[str] = []
    survivors = rederive_existing_items(pack, svc, report)
    for game in GAME_KINDS:
        pack[game] = sorted(survivors[game], key=lambda r: r["id"])
    pack["meta"]["counts"] = {g: len(pack[g]) for g in GAME_KINDS}
    out = json.dumps(pack, ensure_ascii=False, indent=1) + "\n"
    for copy in PACK_COPIES:
        copy.write_text(out, encoding="utf-8")
    if validate_games_pack.main(["validate_games_pack.py"]) != 0:
        for copy, blob in pack_originals.items():
            copy.write_bytes(blob)
        raise SystemExit("pack validation failed after merge — pack ROLLED BACK")

    dropped = [r for r in report if r.startswith("DROPPED")]
    print(f"\nmerge_duplicates: merged {len(merges)} duplicates; pack counts "
          f"{pack['meta']['counts']}; pack re-derivation dropped: {len(dropped)}")
    for line in dropped:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
