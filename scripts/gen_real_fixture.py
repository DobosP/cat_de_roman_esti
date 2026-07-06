#!/usr/bin/env python3
"""Generate the real offline KG fixture (``fixtures/kg_real.json``) from a live
ro_data_server, trimmed to the bundled-fixture shape.

The app ships two offline bundles: the hand-curated ``kg_sample.json`` and this
``kg_real.json`` — the actual KG built from the RO-EDU corpus. Regenerate the real
one whenever the corpus KG is rebuilt (`romania-scraper kg build --commit`) and
served:

    python scripts/gen_real_fixture.py --url http://127.0.0.1:8077 \
        --key cat-de-roman-dev --out cat_de_roman_esti/fixtures/kg_real.json

Then validate:  python scripts/validate_fixture.py cat_de_roman_esti/fixtures/kg_real.json

Stdlib only — no app deps — so it runs anywhere the server is reachable.
"""
from __future__ import annotations

import argparse
import json
import urllib.request

# The offline-fixture record shapes (validate_fixture.py enforces these). The served
# records carry extra provenance fields (access_type/legal_basis/…) we drop here.
_NODE_KEEP = ("id", "label_ro", "node_type", "category", "description", "salience",
              "degree", "difficulty_tier")
_EDGE_KEEP = ("id", "src_id", "dst_id", "relation", "label_ro", "strength",
              "is_distractor", "bidirectional")


def _fetch_all(base: str, key: str, product: str) -> list[dict]:
    out: list[dict] = []
    cursor = ""
    while True:
        url = f"{base}/v1/products/{product}?limit=500&cursor={cursor}"
        req = urllib.request.Request(url, headers={"X-API-Key": key})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
        out.extend(body.get("records", []))
        cursor = body.get("next_cursor")
        if not cursor:
            break
    return out


def _trim(rec: dict, keep: tuple[str, ...]) -> dict:
    return {k: rec[k] for k in keep if k in rec}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8077")
    ap.add_argument("--key", default="cat-de-roman-dev")
    ap.add_argument("--out", default="cat_de_roman_esti/fixtures/kg_real.json")
    args = ap.parse_args()

    nodes = [_trim(n, _NODE_KEEP) for n in _fetch_all(args.url, args.key, "kg_nodes")]
    edges = [_trim(e, _EDGE_KEEP) for e in _fetch_all(args.url, args.key, "kg_edges")]
    puzzles = _fetch_all(args.url, args.key, "kg_puzzles")
    fixture = {
        "meta": {
            "build_version": "kg-build@1-real",
            "note": "Real KG built from the RO-EDU corpus (curriculum + connections), "
                    "fetched from ro_data_server /v1. Corpus concept layer pending index-build.",
            "counts": {"nodes": len(nodes), "edges": len(edges), "puzzles": len(puzzles)},
        },
        "kg_nodes": nodes,
        "kg_edges": edges,
        "kg_puzzles": puzzles,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)
    print(f"wrote {args.out}: {len(nodes)} nodes, {len(edges)} edges, {len(puzzles)} puzzles")


if __name__ == "__main__":
    main()
