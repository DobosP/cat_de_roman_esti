"""In-memory semantic graph built from served ``kg_nodes`` / ``kg_edges`` records.

The graph is the playable substrate of the hop game. It is intentionally a thin,
pure-stdlib structure: nodes and edges are loaded from the records returned by the
RO-EDU data products (see ``docs/KG_CONTRACT.md`` for field definitions) and indexed
by ``src_id`` so neighbour lookups during a game are O(degree).

Difficulty levers that live on the edges (``is_distractor``, ``label_ro``) are kept
on the graph verbatim; the *engine* decides whether to expose or hide them per mode.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field


def _as_bool(value: object) -> bool:
    """Coerce a served field (1/0, "1"/"0", true/false) to a bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "t"}
    return bool(value)


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Node:
    """A KG node — one concept/person/place/work/... in a game category."""

    id: str
    node_type: str
    label_ro: str
    category: str
    description: str = ""
    salience: float = 0.0
    difficulty_tier: str = ""
    degree: int = 0

    @classmethod
    def from_record(cls, rec: Mapping[str, object]) -> Node:
        return cls(
            id=str(rec["id"]),
            node_type=str(rec.get("node_type", "concept")),
            label_ro=str(rec.get("label_ro", rec["id"])),
            category=str(rec.get("category", "")),
            description=str(rec.get("description") or ""),
            salience=_as_float(rec.get("salience")),
            difficulty_tier=str(rec.get("difficulty_tier") or ""),
            degree=int(_as_float(rec.get("degree"))),
        )


@dataclass(frozen=True)
class Edge:
    """A KG edge — a semantic relation connecting two nodes.

    ``is_distractor`` marks weak/decoy edges (hard-mode density lever); ``label_ro``
    is the human-facing edge label revealed only in easy mode.
    """

    id: str
    src_id: str
    dst_id: str
    relation: str
    label_ro: str = ""
    strength: float = 0.0
    is_distractor: bool = False
    bidirectional: bool = True

    @classmethod
    def from_record(cls, rec: Mapping[str, object]) -> Edge:
        return cls(
            id=str(rec["id"]),
            src_id=str(rec["src_id"]),
            dst_id=str(rec["dst_id"]),
            relation=str(rec.get("relation", "related_to")),
            label_ro=str(rec.get("label_ro") or ""),
            strength=_as_float(rec.get("strength")),
            is_distractor=_as_bool(rec.get("is_distractor", 0)),
            bidirectional=_as_bool(rec.get("bidirectional", 1)),
        )


@dataclass
class Neighbor:
    """A reachable node plus the edge the player would traverse to get there."""

    node: Node
    edge: Edge

    @property
    def is_distractor(self) -> bool:
        return self.edge.is_distractor


@dataclass
class Graph:
    """An in-memory directed graph with bidirectional edges expanded both ways."""

    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    # adjacency: src_id -> list of (dst_id, edge). Bidirectional edges appear twice.
    _adj: dict[str, list[tuple[str, Edge]]] = field(default_factory=dict)

    # ------------------------------------------------------------------ build
    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        self._adj.setdefault(edge.src_id, []).append((edge.dst_id, edge))
        if edge.bidirectional:
            self._adj.setdefault(edge.dst_id, []).append((edge.src_id, edge))

    @classmethod
    def from_records(
        cls,
        node_records: Iterable[Mapping[str, object]],
        edge_records: Iterable[Mapping[str, object]],
    ) -> Graph:
        """Build a graph from raw served records (kg_nodes + kg_edges)."""
        g = cls()
        for rec in node_records:
            g.add_node(Node.from_record(rec))
        for rec in edge_records:
            g.add_edge(Edge.from_record(rec))
        return g

    # ------------------------------------------------------------------ query
    def node(self, node_id: str) -> Node | None:
        """Return the node with ``node_id``, or ``None`` if not in the graph."""
        return self.nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def neighbors(self, node_id: str, *, include_distractors: bool = True) -> list[Neighbor]:
        """Neighbours reachable in one hop from ``node_id``.

        When ``include_distractors`` is False, decoy edges are filtered out — this is
        the easy-mode view. Neighbours whose target node is missing from the graph are
        skipped (a category subgraph may reference out-of-scope nodes). Results are
        de-duplicated by destination, keeping the strongest edge, and sorted by
        descending edge strength for stable, deterministic option ordering.
        """
        best: dict[str, Neighbor] = {}
        for dst_id, edge in self._adj.get(node_id, ()):
            if edge.is_distractor and not include_distractors:
                continue
            dst = self.nodes.get(dst_id)
            if dst is None:
                continue
            current = best.get(dst_id)
            if current is None or edge.strength > current.edge.strength:
                best[dst_id] = Neighbor(node=dst, edge=edge)
        return sorted(
            best.values(),
            key=lambda n: (-n.edge.strength, n.node.label_ro, n.node.id),
        )

    def edge_between(
        self, src_id: str, dst_id: str, *, include_distractors: bool = True
    ) -> Edge | None:
        """The (strongest) edge a player could traverse from ``src_id`` to ``dst_id``."""
        for nb in self.neighbors(src_id, include_distractors=include_distractors):
            if nb.node.id == dst_id:
                return nb.edge
        return None

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.nodes)
