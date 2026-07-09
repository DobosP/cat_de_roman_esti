#!/usr/bin/env python3
"""Densify the bundled KG: merge a dense content batch + REGENERATE the puzzle layer.

The word games (alchimie/contexto/lant/conexiuni) play over the nodes+edges graph and
benefit from a DENSER graph (more shared neighbours = richer "combine"; more bridges =
more diverse journeys). But adding edges shortens the legacy ``kg_puzzles`` (used only by
the terminal HopGame + checked by ``validate_fixture.py``), so we cannot keep the old
puzzles. This builder therefore:

  1. merges ``scripts/dense_data.json`` (new nodes + new edges incl. cross-category
     bridges) into the current fixture, de-duplicating edges;
  2. recomputes node degree (= incident-edge count) and difficulty_tier (from the
     rounded salience the fixture stores);
  3. REGENERATES the entire puzzle set on the dense graph using the SAME direction-aware
     BFS + bucket scoping that ``validate_fixture.py`` re-derives, so every puzzle is a
     valid in-band shortest path with no distractor shortcut — GREEN by construction;
  4. rebuilds ``meta`` and writes both byte-identical fixture copies;
  5. self-validates and rolls back on any failure.

Re-run after restoring the base:  git checkout cat_de_roman_esti/fixtures/kg_sample.json
tests/fixtures/kg_sample.json  &&  python scripts/densify_content.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_fixture import (  # noqa: E402
    CATEGORIES,
    HOP_BANDS,
    MIXED_CATEGORY,
    PACKAGE_FIXTURE,
    TESTS_FIXTURE,
    _bfs_distance,
    _edges_within_category,
    bfs_shortest_path,
    build_adjacency,
    tier_for_salience,
)
from validate_fixture import validate as validate_fixture  # noqa: E402

DENSE_DATA = Path(__file__).resolve().parent / "dense_data.json"
NEW_BUILD_VERSION = "fixture-v4-dense"
# How many puzzles to (re)generate per (category, difficulty) bucket + mixed.
PUZZLES_PER_BUCKET = {"easy": 6, "hard": 6}
SALIENCE_ANCHOR = 0.42  # at least one puzzle endpoint must be reasonably recognizable
# The `mixed` bucket would otherwise pair EVERY node with every other (O(n^2) BFS) —
# ~900k pairs at ~1,350 nodes, which exhausts the machine. Puzzles are ranked by
# combined endpoint salience and only the top PUZZLES_PER_BUCKET are kept, and every
# puzzle needs an endpoint with salience >= SALIENCE_ANCHOR, so the winners always come
# from the salient head; capping the mixed generation pool to the top-N most salient
# nodes yields the same puzzles in O(N^2). Per-category pools are already small and stay
# uncapped. (kg_puzzles is legacy — only the terminal HopGame reads it; validate_fixture
# VALIDATES existing puzzles, it does not regenerate them, so a bounded pool stays green.)
MIXED_POOL_CAP = 150

NEW_NOTE = (
    "Densified Romanian KG fixture for the word-game arcade. v4 merges a fact-checked "
    "dense content batch (new nodes + many edges incl. cross-category bridges) onto the "
    "v3 graph to raise mean degree (richer 'combine'/'connect' play), then REGENERATES "
    "the whole kg_puzzles layer on the dense graph via the same direction-aware BFS that "
    "validate_fixture.py re-derives (par==optimal_hops==len(path)-1, easy [2,3]/hard "
    "[4,7], hint_neighbors==solution_path[1:], in-category scope, no distractor shortcut; "
    "mixed crosses >=2 categories). degree = incident-edge count; tier from salience band."
)


def die(msg: str) -> NoReturn:
    print(f"densify_content: ERROR — {msg}", file=sys.stderr)
    sys.exit(1)


def _edge_key(src: str, dst: str, relation: str) -> tuple:
    a, b = sorted((src, dst))
    return (a, b, relation)


def main() -> int:
    if not DENSE_DATA.exists():
        die(f"dense data not found: {DENSE_DATA}")
    dense = json.loads(DENSE_DATA.read_text(encoding="utf-8"))
    return run(dense, NEW_BUILD_VERSION, NEW_NOTE)


def run(dense: dict, build_version: str, note: str) -> int:
    """Merge a dense content batch into the fixture (both copies), regenerate the
    puzzle layer, self-validate and roll back on failure. Reused by
    ``import_candidates.py`` to land generated curated-content subgraphs."""
    base_raw = PACKAGE_FIXTURE.read_text(encoding="utf-8")
    tests_base = TESTS_FIXTURE.read_text(encoding="utf-8")
    data = json.loads(base_raw)

    new_nodes_in: list[dict] = dense.get("nodes", [])
    new_edges_in: list[dict] = dense.get("edges", [])

    nodes: list[dict] = list(data["kg_nodes"])
    edges: list[dict] = list(data["kg_edges"])
    node_ids = {n["id"] for n in nodes}
    existing_edge_ids = {e["id"] for e in edges}
    edge_keys = {_edge_key(e["src_id"], e["dst_id"], e["relation"]) for e in edges}

    # ---- merge new nodes ----
    seen_new: set[str] = set()
    for n in new_nodes_in:
        nid = n["id"]
        if nid in node_ids or nid in seen_new:
            continue
        if n["category"] not in CATEGORIES:
            die(f"new node {nid!r} category {n['category']!r} not a game category")
        sal = round(float(n["salience"]), 4)
        record = {
            "id": nid,
            "node_type": n["node_type"],
            "label_ro": n["label_ro"],
            "category": n["category"],
            "description": n["description"],
            "salience": sal,
            "difficulty_tier": tier_for_salience(sal),
            "degree": 0,
        }
        new_aliases = [str(a).strip() for a in n.get("aliases", []) or [] if str(a).strip()]
        if new_aliases:
            record["aliases"] = new_aliases
        nodes.append(record)
        seen_new.add(nid)
    node_ids |= seen_new

    # ---- merge aliases onto EXISTING nodes (ADR-0012) ----
    # dense["aliases"] = {node_id: [surface forms]} extends a node's alias list;
    # per-node duplicates (vs its label or existing aliases) are dropped here, and
    # cross-node collisions are caught by the validator afterwards.
    alias_map = dense.get("aliases", {}) or {}
    added_aliases = 0
    if alias_map:
        by_id = {n["id"]: n for n in nodes}
        for nid, incoming in alias_map.items():
            node = by_id.get(str(nid))
            if node is None:
                continue
            current = list(node.get("aliases", []) or [])
            seen = {a.strip().casefold() for a in current}
            seen.add(str(node["label_ro"]).strip().casefold())
            for alias in incoming or []:
                text = str(alias).strip()
                if text and text.casefold() not in seen:
                    current.append(text)
                    seen.add(text.casefold())
                    added_aliases += 1
            if current:
                node["aliases"] = current

    # ---- merge new edges (resolve + dedup) ----
    edge_seq = 0

    def next_edge_id(distractor: bool) -> str:
        nonlocal edge_seq
        while True:
            edge_seq += 1
            eid = f"{'dd' if distractor else 'de'}{edge_seq}"
            if eid not in existing_edge_ids:
                return eid

    added_edges = 0
    skipped_edges = 0
    for e in new_edges_in:
        src, dst = e.get("src"), e.get("dst")
        if src not in node_ids or dst not in node_ids or src == dst:
            skipped_edges += 1
            continue
        key = _edge_key(src, dst, e["relation"])
        if key in edge_keys:
            skipped_edges += 1
            continue
        edge_keys.add(key)
        is_d = int(e.get("is_distractor", 0))
        edges.append(
            {
                "id": next_edge_id(bool(is_d)),
                "src_id": src,
                "dst_id": dst,
                "relation": e["relation"],
                "label_ro": e.get("label_ro", ""),
                "strength": round(float(e.get("strength", 0.5)), 3),
                "is_distractor": is_d,
                "bidirectional": int(e.get("bidirectional", 1)),
            }
        )
        added_edges += 1

    print("densify_content: merged batch")
    print(f"  nodes:   +{len(seen_new):<3} -> {len(nodes)}")
    print(f"  aliases: +{added_aliases}")
    print(f"  edges:   +{added_edges:<3} -> {len(edges)}  (skipped {skipped_edges} dup/invalid)")
    return rebuild(data, nodes, edges, build_version, note, base_raw, tests_base)


def rebuild(
    data: dict,
    nodes: list[dict],
    edges: list[dict],
    build_version: str,
    note: str,
    base_raw: str,
    tests_base: str,
) -> int:
    """Recompute degree/tier, regenerate the puzzle layer, rebuild meta, write both
    fixture copies, validate, and roll back on failure. The shared finalize step for
    ``run()`` (content merges) and ``refine_dataset.py`` (in-place refinement) so the
    puzzle-regeneration rules never diverge between the two paths."""
    # ---- recompute degree (= incident-edge count) + tier from salience ----
    deg: Counter[str] = Counter()
    for e in edges:
        deg[e["src_id"]] += 1
        deg[e["dst_id"]] += 1
    for n in nodes:
        n["degree"] = deg.get(n["id"], 0)
        n["difficulty_tier"] = tier_for_salience(float(n["salience"]))

    cat_by_id = {n["id"]: n["category"] for n in nodes}
    sal_by = {n["id"]: n["salience"] for n in nodes}

    # ---- bucket adjacencies (mirror validate_fixture) ----
    full_play = build_adjacency(edges, include_distractors=False)
    full_all = build_adjacency(edges, include_distractors=True)
    cat_play: dict[str, dict] = {}
    cat_all: dict[str, dict] = {}
    nodes_by_cat: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    for nid, c in cat_by_id.items():
        nodes_by_cat.setdefault(c, []).append(nid)
    for cat in CATEGORIES:
        in_cat = {nid for nid, c in cat_by_id.items() if c == cat}
        be = _edges_within_category(edges, in_cat)
        cat_play[cat] = build_adjacency(be, include_distractors=False)
        cat_all[cat] = build_adjacency(be, include_distractors=True)

    def pick(cat: str):
        if cat == MIXED_CATEGORY:
            return full_play, full_all
        return cat_play[cat], cat_all[cat]

    # ---- REGENERATE puzzles fresh on the dense graph ----
    puzzles: list[dict] = []
    all_ids_sorted = sorted(cat_by_id)
    gen_counter: Counter[tuple] = Counter()

    def emit(cat: str, diff: str, start: str, target: str, path: list[str]) -> None:
        hops = len(path) - 1
        gen_counter[(cat, diff)] += 1
        idx = gen_counter[(cat, diff)]
        puzzles.append(
            {
                "id": f"pz_{cat}_{diff}_{idx}",
                "start_id": start,
                "target_id": target,
                "category": cat,
                "difficulty": diff,
                "optimal_hops": hops,
                "par": hops,
                "solution_path": list(path),
                "hint_neighbors": list(path[1:]),
                "start_salience": round(float(sal_by[start]), 4),
                "target_salience": round(float(sal_by[target]), 4),
            }
        )

    for cat in [*CATEGORIES, MIXED_CATEGORY]:
        adj_play, adj_all = pick(cat)
        pool = sorted(nodes_by_cat.get(cat, [])) if cat != MIXED_CATEGORY else all_ids_sorted
        if cat == MIXED_CATEGORY and len(pool) > MIXED_POOL_CAP:
            # Keep the most-salient head (deterministic), then restore id-order so pair
            # iteration/tie-breaking matches the uncapped path for the retained nodes.
            top = sorted(pool, key=lambda nid: (-sal_by[nid], nid))[:MIXED_POOL_CAP]
            pool = sorted(top)
        for diff in ("easy", "hard"):
            lo, hi = HOP_BANDS[diff]
            found: list[tuple] = []
            seen_pairs: set[tuple] = set()
            for i, a in enumerate(pool):
                for b in pool[i + 1 :]:
                    if max(sal_by[a], sal_by[b]) < SALIENCE_ANCHOR:
                        continue
                    path = bfs_shortest_path(adj_play, a, b)
                    if path is None:
                        continue
                    hops = len(path) - 1
                    if not (lo <= hops <= hi):
                        continue
                    pcats = {cat_by_id.get(n) for n in path}
                    if cat == MIXED_CATEGORY:
                        if len({c for c in pcats if c}) < 2:
                            continue
                    elif pcats - {cat}:
                        continue
                    full = _bfs_distance(adj_all, a, b)
                    if full is not None and full < hops:
                        continue
                    found.append((a, b, path))
            found.sort(key=lambda x: (-(sal_by[x[0]] + sal_by[x[1]]), x[0], x[1]))
            for a, b, path in found[: PUZZLES_PER_BUCKET[diff]]:
                if (a, b) in seen_pairs:
                    continue
                seen_pairs.add((a, b))
                emit(cat, diff, a, b, path)

    # ---- rebuild meta ----
    by_cat = dict(sorted(Counter(n["category"] for n in nodes).items()))
    pcd = dict(sorted(Counter(f"{p['category']}/{p['difficulty']}" for p in puzzles).items()))
    data["meta"]["build_version"] = build_version
    data["meta"]["note"] = note
    data["meta"]["counts"] = {
        "nodes": len(nodes),
        "edges": len(edges),
        "puzzles": len(puzzles),
        "by_category": by_cat,
        "puzzles_by_cat_diff": pcd,
    }
    data["kg_nodes"] = nodes
    data["kg_edges"] = edges
    data["kg_puzzles"] = puzzles

    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    PACKAGE_FIXTURE.write_text(out, encoding="utf-8")
    TESTS_FIXTURE.write_text(out, encoding="utf-8")

    mean_deg = sum(deg.values()) / max(1, len(nodes))
    nd_mean = sum(1 for e in edges if not e["is_distractor"]) * 2 / max(1, len(nodes))
    print("densify_content: wrote both fixture copies")
    print(f"  nodes: {len(nodes)} | edges: {len(edges)} | puzzles regenerated: {len(puzzles)}")
    print(f"  by bucket: {dict(sorted(gen_counter.items()))}")
    print(f"  mean degree (all): {mean_deg:.2f} | non-distractor: {nd_mean:.2f}")

    errors = validate_fixture(PACKAGE_FIXTURE)
    if errors:
        PACKAGE_FIXTURE.write_text(base_raw, encoding="utf-8")
        TESTS_FIXTURE.write_text(tests_base, encoding="utf-8")
        msg = f"\ndensify_content: VALIDATION FAILED ({len(errors)}); rolled back."
        print(msg, file=sys.stderr)
        for e in errors[:40]:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("\ndensify_content: GREEN — dense fixture is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
