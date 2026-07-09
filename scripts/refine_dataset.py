#!/usr/bin/env python3
"""Refine the KG in place (v11): merge duplicate concepts + recalibrate salience.

Two data-quality fixes, both deterministic:

1. MERGE DUPLICATES — several concepts exist twice under different ids (split across
   generation batches, e.g. two "O scrisoare pierdută", two "Henri Coandă"). For each
   listed pair the survivor (higher-degree) absorbs the other's edges; the duplicate node
   is dropped and every reference to it — edges AND games-pack payloads — is redirected to
   the survivor. Genuine homonyms (e.g. Moldova the historical land vs the region) are
   intentionally NOT merged.

2. RECALIBRATE SALIENCE — generation defaulted most nodes to 0.8-0.9, so ~70% landed in
   the "easy" tier and difficulty selection (Contexto "greu" wants obscure targets, etc.)
   had almost nothing to pick from. Salience is re-spread as a blend of the declared value
   and degree-centrality, rank-normalized to a balanced tier split. Difficulty games read
   salience/tier, so this makes "usor/normal/greu" meaningful again. (Node identity, edges
   and game payloads are untouched by the recalibration — only the salience number moves.)

Then the shared ``densify_content.rebuild`` recomputes degree + tier, regenerates the
legacy puzzle layer, rebuilds meta, writes both fixture copies, validates and rolls back
on failure. Finally the games pack is redirected (dup ids) + re-derived and re-validated.

    python scripts/refine_dataset.py
"""

from __future__ import annotations

import json
import sys
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
BUILD_VERSION = "fixture-v11-refined"
NOTE = (
    "v11: merged duplicate concepts (edges+games redirected to the survivor) and "
    "recalibrated salience (declared + degree-centrality blend, rank-normalized) so the "
    "usor/normal/greu tiers are balanced and difficulty selection is meaningful."
)

# duplicate id -> survivor id (survivor kept; both are the SAME concept). Chosen by degree
# / better category from the v11 audit. Moldova (istorie land vs geografie region) is a
# genuine homonym and deliberately NOT here.
DUPLICATE_MERGES = {
    "n_independenta_1877": "n_razboiul_independenta_1877",
    "n_amintiri_din_copilarie": "n_amintiri_copilarie",
    "n_scrisoarea_pierduta": "n_o_scrisoare_pierduta",
    "n_dadaism": "n_dadaism_lit",
    "n_nobel": "n_premiul_nobel",
    "n_emil_racovita_pers": "n_emil_racovita",
    "n_henri_coanda_pers": "n_henri_coanda",
    "n_dacoromana": "n_dialectul_dacoroman",
    "n_trianon_1920": "n_tratatul_trianon",
    "n_chirilica_romaneasca": "n_alfabetul_chirilic",
}

# Target tier split after recalibration (fractions of all nodes): a balanced spread so
# every difficulty has a real pool. easy = most salient, hard = most obscure.
TIER_FRACTIONS = {"easy": 0.34, "medium": 0.40, "hard": 0.26}


def _recalibrate_salience(nodes: list[dict], edges: list[dict]) -> None:
    """Re-spread salience as a rank-normalized blend of declared value + degree."""
    import collections

    deg: collections.Counter[str] = collections.Counter()
    for e in edges:
        if not e.get("is_distractor"):
            deg[e["src_id"]] += 1
            deg[e["dst_id"]] += 1
    n = len(nodes)
    # percentile rank (0..1) by declared salience and by degree, then blend
    by_sal = sorted(nodes, key=lambda x: (float(x["salience"]), x["id"]))
    sal_rank = {node["id"]: i / max(1, n - 1) for i, node in enumerate(by_sal)}
    by_deg = sorted(nodes, key=lambda x: (deg[x["id"]], x["id"]))
    deg_rank = {node["id"]: i / max(1, n - 1) for i, node in enumerate(by_deg)}
    # blended score -> re-rank -> map onto tier bands so the split matches TIER_FRACTIONS.
    scored = sorted(
        nodes,
        key=lambda x: (0.6 * sal_rank[x["id"]] + 0.4 * deg_rank[x["id"]], x["id"]),
    )
    hard_cut = int(n * TIER_FRACTIONS["hard"])
    medium_cut = hard_cut + int(n * TIER_FRACTIONS["medium"])
    for i, node in enumerate(scored):
        if i < hard_cut:  # most obscure -> hard band (< 0.33)
            node["salience"] = round(0.15 + 0.17 * (i / max(1, hard_cut)), 4)
        elif i < medium_cut:  # medium band (0.33..0.66)
            j = (i - hard_cut) / max(1, medium_cut - hard_cut)
            node["salience"] = round(0.34 + 0.31 * j, 4)
        else:  # most salient -> easy band (>= 0.66)
            j = (i - medium_cut) / max(1, n - medium_cut)
            node["salience"] = round(0.67 + 0.31 * j, 4)


def main() -> int:
    base_raw = densify_content.PACKAGE_FIXTURE.read_text(encoding="utf-8")
    tests_base = densify_content.TESTS_FIXTURE.read_text(encoding="utf-8")
    data = json.loads(base_raw)
    nodes = data["kg_nodes"]
    edges = data["kg_edges"]

    surviving_ids = {n["id"] for n in nodes} - set(DUPLICATE_MERGES)

    def rm(nid: str) -> str:
        return DUPLICATE_MERGES.get(nid, nid)

    # 1a. drop duplicate nodes; fold any aliases + the label of the dropped node onto the
    #     survivor so the merged concept keeps resolving under every surface form.
    survivor_by_id = {n["id"]: n for n in nodes if n["id"] in surviving_ids}
    for dup in nodes:
        if dup["id"] not in DUPLICATE_MERGES:
            continue
        surv = survivor_by_id.get(DUPLICATE_MERGES[dup["id"]])
        if surv is None:
            continue
        merged = list(surv.get("aliases", []) or [])
        seen = {a.casefold() for a in merged} | {str(surv["label_ro"]).casefold()}
        for cand in [dup["label_ro"], *(dup.get("aliases", []) or [])]:
            if str(cand).casefold() not in seen:
                merged.append(str(cand))
                seen.add(str(cand).casefold())
        if merged:
            surv["aliases"] = merged
    nodes = [n for n in nodes if n["id"] in surviving_ids]

    # 1b. redirect + de-duplicate edges onto the survivors.
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

    # 2. recalibrate salience (tier re-derived inside rebuild()).
    _recalibrate_salience(nodes, edges)

    rc = densify_content.rebuild(data, nodes, edges, BUILD_VERSION, NOTE, base_raw, tests_base)
    if rc != 0:
        raise SystemExit("fixture refine failed (rolled back) — aborting")

    # 3. redirect dup ids in the games pack, then re-derive on the refined graph.
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
        raise SystemExit("pack validation failed after refine — pack ROLLED BACK")

    print(f"\nrefine_dataset: merged {len(DUPLICATE_MERGES)} duplicates, recalibrated "
          f"{len(nodes)} node salience; pack counts {pack['meta']['counts']}")
    print(f"pack re-derivation dropped: {len([r for r in report if r.startswith('DROPPED')])}")
    return 0


def _redirect_pack(pack: dict, rm) -> None:
    """Rewrite any merged-away node ids inside game payloads to the survivor."""
    for it in pack.get("conexiuni", []):
        for key, ids in it["groups"].items():
            it["groups"][key] = [rm(t) for t in ids]
        it["order"] = [rm(t) for t in it["order"]]
        # a merge could collapse two tiles to one id -> board becomes invalid; the
        # re-derivation's validate step will drop such a board.
    for it in pack.get("contexto", []):
        it["target"] = rm(it["target"])
    for it in pack.get("lant", []):
        it["start"], it["target"] = rm(it["start"]), rm(it["target"])
    for it in pack.get("alchimie", []):
        it["seeds"] = [rm(s) for s in it["seeds"]]
        it["target"] = rm(it["target"])


if __name__ == "__main__":
    raise SystemExit(main())
