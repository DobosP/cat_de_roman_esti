"""Loading layer — turns served records (or a bundled fixture) into a Graph + puzzle.

Two sources, one shape:

  * ``load_from_client`` — pulls ``kg_nodes`` / ``kg_edges`` / ``kg_puzzles`` from a
    live Ro-data-server via the vendored ``RoeduClient`` (fail-closed: an unavailable
    product yields no records, so an empty/blocked product simply yields no puzzles).
  * ``load_fixture`` — reads a bundled JSON snapshot for ``--offline`` play and tests.

Both return the same ``KgBundle`` so the CLI and engine are source-agnostic.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .engine import Puzzle, _as_id_list
from .graph import Graph

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_FIXTURE = FIXTURE_DIR / "kg_sample.json"


class ClientLike(Protocol):
    """Structural type the loader needs — satisfied by RoeduClient and the fake."""

    def iter(self, product: str, **filters: object): ...


@dataclass
class KgBundle:
    """Everything needed to start games for one category scope."""

    graph: Graph
    puzzles: list[Puzzle]

    def puzzles_for(self, *, category: str | None = None, difficulty: str | None = None):
        """Strict filter: a puzzle belongs to exactly its own ``.category``.

        Return the puzzles where ``category`` is None or ``p.category == category`` AND
        ``difficulty`` is None or ``p.difficulty == difficulty``. The "mixed" bucket is
        not special-cased: ``category="mixed"`` returns only genuinely cross-category
        puzzles (``p.category == "mixed"``), and a single category never surfaces the
        mixed puzzle. A category+difficulty with no matching puzzle legitimately yields
        an empty list (e.g. the bundled fixture has no hard mixed puzzle).
        """
        out = self.puzzles
        if category is not None:
            out = [p for p in out if p.category == category]
        if difficulty is not None:
            out = [p for p in out if p.difficulty == difficulty]
        return out

    def categories(self) -> list[str]:
        cats = {n.category for n in self.graph.nodes.values() if n.category}
        return sorted(cats)


def _bundle_from_records(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
) -> KgBundle:
    graph = Graph.from_records(nodes, edges)
    parsed = [Puzzle.from_record(p) for p in puzzles]
    return KgBundle(graph=graph, puzzles=parsed)


def load_fixture(path: str | Path | None = None) -> KgBundle:
    """Load a bundled KG snapshot from JSON (offline play / tests)."""
    fpath = Path(path) if path else DEFAULT_FIXTURE
    raw = json.loads(fpath.read_text(encoding="utf-8"))
    return _bundle_from_records(
        raw.get("kg_nodes", []),
        raw.get("kg_edges", []),
        raw.get("kg_puzzles", []),
    )


def _puzzle_node_ids(puzzles: Sequence[Mapping[str, object]]) -> set[str]:
    """Every node id any puzzle references (endpoints + solution_path + hints)."""
    wanted: set[str] = set()
    for rec in puzzles:
        for key in ("start_id", "target_id"):
            val = rec.get(key)
            if val is not None:
                wanted.add(str(val))
        for key in ("solution_path", "hint_neighbors"):
            for nid in _as_id_list(rec.get(key)):
                wanted.add(nid)
    return wanted


def load_from_client(
    client: ClientLike,
    *,
    category: str | None = None,
    difficulty: str | None = None,
    max_nodes: int | None = None,
) -> KgBundle:
    """Pull the KG products from a live server (or fake) into a bundle.

    Fail-closed flows naturally from ``RoeduClient.iter``: if a product reports
    ``available=false`` (gate refusal / store not built) it yields nothing, and the
    resulting bundle simply has fewer records — never fabricated ones.

    Mixed / cross-category puzzles (``category == "mixed"``) and any puzzle whose
    ``solution_path`` strays outside the requested category would otherwise reference
    nodes the single-category node fetch never loaded, leaving a solution node missing
    from the graph (an unwinnable game). To stay robust we fetch puzzles first — the
    requested category *plus* the ``mixed`` bucket — then, if any referenced node is not
    covered by the category node fetch, widen to the UNION of categories by loading the
    full node set. Single-category puzzles whose nodes are all in scope keep loading just
    the requested category. The post-condition: no solution_path node id is ever missing.
    """
    puzzle_filters: list[dict[str, str]] = []
    if category:
        # The requested start-category, and the cross-category "mixed" bucket, which the
        # producer emits separately (its category is literally "mixed", so a plain
        # category filter would exclude it).
        puzzle_filters.append({"category": category})
        if category != "mixed":
            puzzle_filters.append({"category": "mixed"})
    else:
        puzzle_filters.append({})
    if difficulty:
        for pf in puzzle_filters:
            pf["difficulty"] = difficulty

    puzzles: list[Mapping[str, object]] = []
    seen_pids: set[str] = set()
    for pf in puzzle_filters:
        for rec in client.iter("kg_puzzles", **pf):
            pid = str(rec.get("id"))
            if pid in seen_pids:
                continue
            seen_pids.add(pid)
            puzzles.append(rec)

    node_filter = {"category": category} if category else {}
    nodes = list(client.iter("kg_nodes", max_records=max_nodes, **node_filter))
    loaded_ids = {str(n.get("id")) for n in nodes}

    # If a (mixed / cross-category) puzzle references a node the category fetch missed,
    # widen to the union: load the full node set so every solution node is present.
    needed = _puzzle_node_ids(puzzles)
    if category and not needed <= loaded_ids:
        nodes = list(client.iter("kg_nodes", max_records=max_nodes))

    # Edges are not category-scoped at the product level; pull all and let the graph
    # index them. Cross-category edges are harmless — neighbours() skips out-of-scope
    # destinations that aren't loaded as nodes.
    edges = list(client.iter("kg_edges"))
    return _bundle_from_records(nodes, edges, puzzles)
