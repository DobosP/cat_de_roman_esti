"""Non-interactive end-to-end smoke: live server -> client -> engine auto-win.

Drives the REAL vendored ``RoeduClient`` against a running ro_data_server, loads a
puzzle plus its category subgraph through the same ``load_from_client`` loader the
CLI uses, then has the ``HopGame`` engine auto-play the served ``solution_path`` hop
by hop and asserts a win at par. No interactive input, no fixture — this exercises
the whole chain (transport -> products -> client -> graph -> engine).

    ROEDU_API_URL=<ro_data_server_url> ROEDU_API_KEY=<api_key> \
        python scripts/e2e_smoke.py --require-live [easy|hard]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
from pathlib import Path

SKIP_EXIT = 77
RERUN_COMMAND = (
    "ROEDU_API_URL=<ro_data_server_url> ROEDU_API_KEY=<api_key> "
    "python scripts/e2e_smoke.py --require-live easy"
)

if sys.version_info < (3, 11):  # noqa: UP036 — friendly message on old interpreters
    version = ".".join(str(part) for part in sys.version_info[:3])
    print(f"[FAIL] Python >=3.11 is required for this smoke script; got {version}")
    print(f"[hint] rerun with: {RERUN_COMMAND}")
    raise SystemExit(1)

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cat_de_roman_esti.data import load_from_client  # noqa: E402 — after sys.path setup
from cat_de_roman_esti.engine import HopGame, Mode  # noqa: E402
from cat_de_roman_esti.roedu_client import RoeduClient  # noqa: E402


def _unavailable(exc: BaseException, *, require_live: bool) -> int:
    status = "FAIL" if require_live else "SKIP"
    detail = f"{type(exc).__name__}: {exc}"
    print(f"[{status}] live ro_data_server unavailable or unhealthy ({detail})")
    print(f"[hint] rerun with: {RERUN_COMMAND}")
    if require_live:
        return 1
    return SKIP_EXIT


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "difficulty",
        nargs="?",
        default="easy",
        choices=("easy", "hard"),
        help="Puzzle difficulty to smoke through.",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help=(
            "Exit 1 instead of the skip code when ro_data_server is unavailable. "
            "Use this for release gates on hosts where live infrastructure is expected."
        ),
    )
    return parser.parse_args(argv)


def main(difficulty: str = "easy", *, require_live: bool = False) -> int:
    url = os.environ.get("ROEDU_API_URL", "http://127.0.0.1:8077")
    key = os.environ.get("ROEDU_API_KEY", "cat-de-roman-dev")
    client = RoeduClient(url, api_key=key)

    try:
        health = client.health()
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return _unavailable(exc, require_live=require_live)
    print(f"[health] {health.get('status')} | kg_nodes available="
          f"{health.get('products', {}).get('kg_nodes')}")

    try:
        bundle = load_from_client(client, difficulty=difficulty)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return _unavailable(exc, require_live=require_live)
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
    args = _parse_args(sys.argv[1:])
    raise SystemExit(main(args.difficulty, require_live=args.require_live))
