"""Non-interactive end-to-end smoke: live server -> client -> engine auto-win.

Drives the REAL vendored ``RoeduClient`` against a running ro_data_server, loads a
puzzle plus its category subgraph through the same ``load_from_client`` loader the
CLI uses, then has the ``HopGame`` engine auto-play the served ``solution_path`` hop
by hop and asserts a win at par. No interactive input, no fixture — this exercises
the whole chain (transport -> products -> client -> graph -> engine).

    ROEDU_API_URL=http://127.0.0.1:8077 ROEDU_API_KEY=cat-de-roman-dev \
        python scripts/e2e_smoke.py [easy|hard]
"""

from __future__ import annotations

import os
import sys

from cat_de_roman_esti.data import load_from_client
from cat_de_roman_esti.engine import HopGame, Mode
from cat_de_roman_esti.roedu_client import RoeduClient


def main(difficulty: str = "easy") -> int:
    url = os.environ.get("ROEDU_API_URL", "http://127.0.0.1:8077")
    key = os.environ.get("ROEDU_API_KEY", "cat-de-roman-dev")
    client = RoeduClient(url, api_key=key)

    health = client.health()
    print(f"[health] {health.get('status')} | kg_nodes available="
          f"{health.get('products', {}).get('kg_nodes')}")

    bundle = load_from_client(client, difficulty=difficulty)
    print(f"[load] graph: {len(bundle.graph.nodes)} nodes, "
          f"{len(bundle.graph.edges)} edges | puzzles: {len(bundle.puzzles)}")

    candidates = bundle.puzzles_for(difficulty=difficulty)
    if not candidates:
        print(f"[FAIL] no '{difficulty}' puzzles served")
        return 1
    puzzle = candidates[0]
    start = bundle.graph.node(puzzle.start_id)
    target = bundle.graph.node(puzzle.target_id)
    print(f"[puzzle] {puzzle.id[:12]} | {start.label_ro} -> {target.label_ro} "
          f"| category={puzzle.category} difficulty={puzzle.difficulty} "
          f"par={puzzle.par} solution_hops={len(puzzle.solution_path) - 1}")

    game = HopGame.load(bundle.graph, puzzle, Mode.parse(difficulty))

    # Auto-play the served shortest path, validating every hop is a real edge.
    print(f"[autoplay] start at {game.current_node.label_ro}")
    for nid in puzzle.solution_path[1:]:
        nxt = bundle.graph.node(nid)
        result = game.hop(nid)
        label = nxt.label_ro if nxt else nid
        if not result.ok:
            print(f"[FAIL] illegal hop to {label!r}: {result.reason}")
            return 1
        print(f"  -> hop to {label}  (won={result.won})")

    summary = game.summary()
    print(f"[result] won={summary['won']} hops={summary['hops']} "
          f"par={summary['par']} score={summary['score']}")

    if not summary["won"]:
        print("[FAIL] engine did not reach the target")
        return 1
    if summary["hops"] != puzzle.optimal_hops:
        print(f"[FAIL] solved in {summary['hops']} hops, expected optimal "
              f"{puzzle.optimal_hops}")
        return 1
    if summary["score"] != 1000:
        print(f"[FAIL] expected perfect 1000 at par, got {summary['score']}")
        return 1
    print("[OK] end-to-end win at par confirmed")
    return 0


if __name__ == "__main__":
    diff = sys.argv[1] if len(sys.argv) > 1 else "easy"
    raise SystemExit(main(diff))
