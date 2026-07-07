#!/usr/bin/env python3
"""Import an alias + play-density enrichment batch (ADR-0012).

Consumes a directory of per-category generation output:

    <dir>/<category>/candidates.json   # {"aliases": {id: [...]}, "nodes": [...], "edges": [...]}
    <dir>/<category>/verify.json       # {"issues":[{"ref","severity","issue","correction"}]}

Verifier refs: ``alias:<node_id>:<alias text>`` / ``<node_id>`` / ``edge <src>-><dst>``.
``block`` drops the alias / node (+ its edges) / edge; ``fix``/``nit`` are kept and
listed in the human-review report.

Mechanical hygiene before the merge (the resolver needs one meaning per typed word):
  * aliases are dropped when they normalize-collide with ANY node label/id, with an
    already-claimed alias, or exceed 5 words;
  * a NEW node whose normalized label matches an existing label/id is treated as a
    duplicate concept: its definition is skipped and its edges are remapped to the
    existing node.

Then: densify_content.run() merges nodes+edges+aliases (fixture regenerated,
validated, rolled back on failure), every games-pack item is RE-DERIVED on the
denser graph (distances/closures change), and both validators gate the result.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import densify_content  # noqa: E402
import validate_games_pack  # noqa: E402
from import_candidates import GAME_KINDS, rederive_existing_items  # noqa: E402

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)
BUILD_VERSION = "fixture-v6-enriched"
NOTE = (
    "v6: alias + play-density enrichment (ADR-0012) — exact alias surface forms on "
    "most nodes, guess-vocabulary hub concepts, and intuitive edges lifting "
    "low-degree nodes, so Cald sau Rece and Lantul Cuvintelor stay responsive; "
    "kg_puzzles regenerated on the enriched graph."
)
MAX_ALIAS_WORDS = 5


def _norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text))
    no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(no_accents.casefold().split())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="enrichment output dir")
    args = parser.parse_args(argv[1:])
    gen_dir = Path(args.dir)

    categories = sorted(d.name for d in gen_dir.iterdir() if (d / "candidates.json").exists())
    if not categories:
        raise SystemExit(f"no <category>/candidates.json under {gen_dir}")

    fixture = json.loads(
        validate_games_pack.PACKAGE_KG.read_text(encoding="utf-8")
    )
    existing_keys: dict[str, str] = {}
    for n in fixture["kg_nodes"]:
        existing_keys.setdefault(_norm(n["label_ro"]), str(n["id"]))
        existing_keys.setdefault(_norm(n["id"]), str(n["id"]))
        for alias in n.get("aliases", []) or []:
            existing_keys.setdefault(_norm(alias), str(n["id"]))

    report: list[str] = []
    stats = {"aliases": 0, "aliases_dropped": 0, "nodes": 0, "edges": 0,
             "nodes_remapped": 0, "blocked": 0}
    alias_claims: dict[str, str] = {}  # normalized alias -> owning node id
    merged_aliases: dict[str, list[str]] = {}
    merged_nodes: list[dict] = []
    merged_edges: list[dict] = []
    label_remap: dict[str, str] = {}  # duplicate new-node id -> canonical id

    def claim_alias(nid: str, alias: str, source: str) -> None:
        text = str(alias).strip()
        if not text or len(text.split()) > MAX_ALIAS_WORDS:
            stats["aliases_dropped"] += 1
            return
        key = _norm(text)
        owner_label = existing_keys.get(key)
        if owner_label is not None:
            if owner_label != nid:
                stats["aliases_dropped"] += 1
                report.append(
                    f"ALIAS-DROP ({source}) {nid}:{text!r} collides with node {owner_label!r}"
                )
            else:
                stats["aliases_dropped"] += 1  # redundant with its own label
            return
        prev = alias_claims.get(key)
        if prev is not None:
            if prev != nid:
                stats["aliases_dropped"] += 1
                report.append(
                    f"ALIAS-DROP ({source}) {nid}:{text!r} already claimed by {prev!r}"
                )
            return
        alias_claims[key] = nid
        merged_aliases.setdefault(nid, []).append(text)
        stats["aliases"] += 1

    for cat in categories:
        cdir = gen_dir / cat
        cand = json.loads((cdir / "candidates.json").read_text(encoding="utf-8"))
        vpath = cdir / "verify.json"
        issues = (
            json.loads(vpath.read_text(encoding="utf-8")).get("issues", [])
            if vpath.exists()
            else []
        )

        blocked_aliases: set[tuple[str, str]] = set()
        blocked_nodes: set[str] = set()
        blocked_edges: set[tuple[str, str]] = set()
        for issue in issues:
            ref, sev = str(issue.get("ref", "")), issue.get("severity")
            if sev != "block":
                if sev == "fix":
                    report.append(
                        f"REVIEW ({cat}) {ref}: {issue.get('issue')} -> {issue.get('correction')}"
                    )
                continue
            stats["blocked"] += 1
            alias_m = re.match(r"alias:([^:]+):(.+)", ref)
            edge_m = re.search(r"(\S+?)\s*->\s*(\S+)", ref)
            if alias_m:
                blocked_aliases.add((alias_m.group(1).strip(), _norm(alias_m.group(2))))
                report.append(f"BLOCKED alias ({cat}) {ref}: {issue.get('issue')}")
            elif edge_m:
                blocked_edges.add((edge_m.group(1), edge_m.group(2)))
                report.append(f"BLOCKED edge ({cat}) {ref}: {issue.get('issue')}")
            else:
                blocked_nodes.add(ref.strip())
                report.append(f"BLOCKED node ({cat}) {ref}: {issue.get('issue')}")

        for nid, incoming in (cand.get("aliases") or {}).items():
            for alias in incoming or []:
                if (str(nid), _norm(alias)) in blocked_aliases:
                    stats["aliases_dropped"] += 1
                    continue
                claim_alias(str(nid), alias, cat)

        for n in cand.get("nodes", []) or []:
            nid = str(n.get("id"))
            if nid in blocked_nodes:
                continue
            key = _norm(str(n.get("label_ro", "")))
            canonical = existing_keys.get(key) or alias_claims.get(key)
            if canonical is not None:
                # Duplicate concept: remap references instead of growing a twin.
                label_remap[nid] = canonical
                stats["nodes_remapped"] += 1
                report.append(f"REMAP ({cat}) new node {nid} -> existing {canonical}")
                continue
            node = {**n, "category": str(n.get("category") or cat)}
            node_aliases = node.pop("aliases", []) or []
            merged_nodes.append(node)
            existing_keys.setdefault(key, nid)
            stats["nodes"] += 1
            for alias in node_aliases:
                claim_alias(nid, alias, cat)

        for e in cand.get("edges", []) or []:
            src = label_remap.get(str(e.get("src")), str(e.get("src")))
            dst = label_remap.get(str(e.get("dst")), str(e.get("dst")))
            if (src, dst) in blocked_edges or (dst, src) in blocked_edges:
                continue
            if src in blocked_nodes or dst in blocked_nodes or src == dst:
                continue
            merged_edges.append({**e, "src": src, "dst": dst})
            stats["edges"] += 1

    dense = {"nodes": merged_nodes, "edges": merged_edges, "aliases": merged_aliases}
    rc = densify_content.run(dense, BUILD_VERSION, NOTE)
    if rc != 0:
        raise SystemExit("enrichment merge failed (fixture rolled back) — aborting")

    # Re-derive every pack item on the denser graph (distances/closures moved).
    svc = WordGameService(graph=load_fixture(validate_games_pack.PACKAGE_KG).graph)
    pack_originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    pack = json.loads(pack_originals[validate_games_pack.PACKAGE_PACK].decode("utf-8"))
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
        raise SystemExit(
            "pack validation failed after re-derivation — pack ROLLED BACK "
            "(fixture keeps the enriched graph)"
        )

    report_path = gen_dir / "enrichment_report.txt"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nimport_enrichment: {stats}")
    print(f"pack counts after re-derivation: {pack['meta']['counts']}")
    print(f"human-review report: {report_path} ({len(report)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
