"""cat-de-roman — terminal-playable semantic-hop game.

    cat-de-roman                 # online: fetch puzzles from $ROEDU_API_URL
    cat-de-roman --offline       # play against the bundled fixture (no server)
    cat-de-roman --category istorie --difficulty hard

Flow: pick a category + difficulty, get a puzzle, then at each turn the current node
and its neighbour options are rendered with the hop count. Type the number of the
neighbour to hop there; reach the target to win. Easy mode shows edge labels + a hint;
hard mode hides them and keeps distractor edges in play.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from .data import KgBundle, load_fixture, load_from_client
from .engine import HopGame, Mode, Puzzle
from .graph import Graph
from .roedu_client import RoeduClient


def _eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def _prompt(msg: str, *, stream=sys.stdin) -> str:
    print(msg, end="", flush=True)
    line = stream.readline()
    if not line:  # EOF
        raise EOFError
    return line.strip()


def _choose(
    label: str, options: Sequence[str], *, default: str | None, stream, out=print
) -> str:
    if not options:
        return default or ""
    out(f"\n{label}:")
    for i, opt in enumerate(options, 1):
        marker = "  (default)" if opt == default else ""
        out(f"  [{i}] {opt}{marker}")
    while True:
        try:
            raw = _prompt(f"{label} > ", stream=stream)
        except EOFError:
            return default or options[0]
        if not raw and default:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        out(f"  ? please pick 1-{len(options)} (or a name)")


def _render_turn(game: HopGame, out=print) -> None:
    cur = game.current_node
    tgt = game.target_node
    out("\n" + "=" * 64)
    out(f"  HOPS: {game.hops}   PAR: {game.puzzle.par}   MODE: {game.mode.value}")
    out(f"  TARGET : {tgt.label_ro}  ({tgt.category})")
    if tgt.description:
        out(f"           {tgt.description}")
    out(f"  CURRENT: {cur.label_ro}  ({cur.node_type})")
    if cur.description:
        out(f"           {cur.description}")
    out("-" * 64)
    options = game.options()
    if not options:
        out("  (dead end — no outgoing edges from here)")
        return
    hints = set(game.hint_neighbors())
    out("  Neighbours you can hop to:")
    for i, nb in enumerate(options, 1):
        bits = [f"  [{i}] {nb.node.label_ro}"]
        label = game.edge_label(nb.node.id)
        if label:
            bits.append(f"— {label}")
        if nb.node.id in hints:
            bits.append("  <hint>")
        out(" ".join(bits))


def play(game: HopGame, *, stream=sys.stdin, out=print, max_turns: int = 100) -> dict:
    """Run the interactive loop until win, quit, or turn cap. Returns the summary."""
    out(f"\nStart: {game.current_node.label_ro}  ->  Target: {game.target_node.label_ro}")
    out("Type a number to hop, 'q' to quit.")
    turns = 0
    while not game.won and turns < max_turns:
        turns += 1
        _render_turn(game, out=out)
        if game.won:
            break
        options = game.options()
        try:
            raw = _prompt("\nhop > ", stream=stream)
        except EOFError:
            out("\n(input closed — leaving)")
            break
        if raw.lower() in {"q", "quit", "exit"}:
            out("Bye.")
            break
        if not raw.isdigit() or not (1 <= int(raw) <= len(options)):
            out(f"  ? enter 1-{len(options)} or 'q'")
            continue
        target = options[int(raw) - 1].node
        result = game.hop(target.id)
        if not result.ok:
            out(f"  ✗ invalid hop: {result.reason}")
            continue
        out(f"  → hopped to {target.label_ro}")

    summary = game.summary()
    out("\n" + "#" * 64)
    if summary["won"]:
        out(f"  WIN! {summary['hops']} hops (par {summary['par']}).  SCORE: {summary['score']}")
    else:
        out(f"  Not solved. {summary['hops']} hops taken.  SCORE: {summary['score']}")
    out("#" * 64)
    return summary


def _load_bundle(args: argparse.Namespace) -> KgBundle:
    if args.offline:
        return load_fixture(args.fixture)
    base_url = args.api_url or os.environ.get("ROEDU_API_URL", "http://localhost:8077")
    api_key = args.api_key or os.environ.get("ROEDU_API_KEY", "cat-de-roman-dev")
    client = RoeduClient(base_url, api_key=api_key)
    try:
        health = client.health()
    except Exception as exc:  # network down, server absent, etc.
        _eprint(f"! could not reach RO-EDU server at {base_url}: {exc}")
        _eprint("! falling back to the bundled offline fixture (use --offline to skip the probe)")
        return load_fixture(args.fixture)
    if not health.get("ok", True):
        _eprint("! server reports unhealthy; falling back to offline fixture")
        return load_fixture(args.fixture)
    return load_from_client(client, category=args.category, difficulty=args.difficulty)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cat-de-roman", description=__doc__)
    p.add_argument("--offline", action="store_true", help="play against the bundled fixture")
    p.add_argument("--fixture", help="path to a KG fixture JSON (offline mode)")
    p.add_argument("--category", help="game category (e.g. istorie, literatura)")
    p.add_argument("--difficulty", choices=["easy", "hard"], help="game mode")
    p.add_argument("--api-url", help="override ROEDU_API_URL")
    p.add_argument("--api-key", help="override ROEDU_API_KEY")
    p.add_argument("--list", action="store_true", help="list categories/puzzles and exit")
    return p


def main(argv: Sequence[str] | None = None, *, stream=sys.stdin, out=print) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = _load_bundle(args)
    except FileNotFoundError as exc:
        _eprint(f"! fixture not found: {exc}")
        return 2

    if not bundle.puzzles:
        _eprint("! no puzzles available (product blocked, store empty, or wrong filters)")
        return 1

    categories = sorted({p.category for p in bundle.puzzles})
    if args.list:
        out("Categories:", ", ".join(bundle.categories()) or "(none)")
        out(f"Puzzles available: {len(bundle.puzzles)}")
        for cat in categories:
            n = len(bundle.puzzles_for(category=cat))
            out(f"  {cat}: {n}")
        return 0

    category = args.category or _choose(
        "Pick a category", categories, default=categories[0], stream=stream, out=out
    )
    difficulty = args.difficulty or _choose(
        "Pick a difficulty", ["easy", "hard"], default="easy", stream=stream, out=out
    )

    candidates = bundle.puzzles_for(category=category, difficulty=difficulty)
    if not candidates:
        _eprint(f"! no '{difficulty}' puzzles in category '{category}'")
        return 1
    puzzle = candidates[0]

    game = _start_game(bundle.graph, puzzle, difficulty)
    play(game, stream=stream, out=out)
    return 0


def _start_game(graph: Graph, puzzle: Puzzle, difficulty: str) -> HopGame:
    return HopGame.load(graph, puzzle, Mode.parse(difficulty))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
