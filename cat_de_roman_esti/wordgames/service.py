"""Shared word-game service: one in-memory KG + the primitives all 3 games need.

This is the single contract the per-game routers import. It wraps the bundled
:class:`~cat_de_roman_esti.graph.Graph` (loaded once from the offline fixture) with the
operations the text games are built from — neighbour lookup, link checking, shared
neighbours (the "combine" rule), BFS distance / distance map (the "hot-cold" rule), and
fuzzy text→node resolution so a player can TYPE a concept instead of clicking a graph.

All distances/links use the NON-distractor subgraph by default (the real semantic web);
the weak decoy edges (``is_distractor``) are ignored so the games stay meaningful.
"""

from __future__ import annotations

import hashlib
import threading
import unicodedata
import uuid
from collections import deque
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Generic, TypeVar

from ..data import load_fixture
from ..graph import Edge, Graph, Node


def normalize(text: str) -> str:
    """Canonical form for fuzzy matching: strip accents, casefold, collapse whitespace.

    "Ștefan cel Mare " / "stefan cel mare" / "STEFAN  CEL  MARE" all normalize equal.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(no_accents.casefold().split())


@dataclass
class WordGameService:
    """Read-only operations over one KG, shared by every word game."""

    graph: Graph
    # normalized label / id -> node id (built once)
    _index: dict[str, str] = field(default_factory=dict)
    _adj: dict[str, set[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for node in self.graph.nodes.values():
            self._index[normalize(node.label_ro)] = node.id
            self._index[normalize(node.id)] = node.id
        # Undirected non-distractor adjacency for distance/closure math.
        for nid in self.graph.nodes:
            nbrs = self.graph.neighbors(nid, include_distractors=False)
            self._adj[nid] = {nb.node.id for nb in nbrs}

    # --------------------------------------------------------------- lookup
    def node(self, node_id: str) -> Node | None:
        return self.graph.node(node_id)

    def exists(self, node_id: str) -> bool:
        return self.graph.has_node(node_id)

    def label(self, node_id: str) -> str:
        n = self.graph.node(node_id)
        return n.label_ro if n else node_id

    def description(self, node_id: str) -> str:
        n = self.graph.node(node_id)
        return n.description if n else ""

    def resolve(self, text: str) -> str | None:
        """Map free-typed text to a node id (exact id or normalized label), else None."""
        if not text:
            return None
        key = normalize(text)
        return self._index.get(key)

    # --------------------------------------------------------------- graph ops
    def neighbor_ids(self, node_id: str, *, include_distractors: bool = False) -> list[str]:
        if not include_distractors:
            return sorted(self._adj.get(node_id, set()))
        nbrs = self.graph.neighbors(node_id, include_distractors=True)
        return sorted({nb.node.id for nb in nbrs})

    def link(self, a: str, b: str, *, include_distractors: bool = False) -> Edge | None:
        """The (strongest) real edge a->b in the chosen view, or None if not linked."""
        return self.graph.edge_between(a, b, include_distractors=include_distractors)

    def link_label(self, a: str, b: str) -> str:
        e = self.link(a, b)
        return e.label_ro if e else ""

    def common_neighbors(self, a: str, b: str) -> list[str]:
        """Nodes adjacent (non-distractor) to BOTH a and b — the 'combine' result set."""
        if a not in self._adj or b not in self._adj:
            return []
        return sorted(self._adj[a] & self._adj[b])

    def distance(self, a: str, b: str) -> int | None:
        """BFS hop count on the non-distractor subgraph, or None if unreachable."""
        if a == b:
            return 0
        if a not in self._adj or b not in self._adj:
            return None
        seen = {a}
        frontier: deque[tuple[str, int]] = deque([(a, 0)])
        while frontier:
            cur, d = frontier.popleft()
            for nxt in self._adj.get(cur, ()):  # noqa: SIM118
                if nxt in seen:
                    continue
                if nxt == b:
                    return d + 1
                seen.add(nxt)
                frontier.append((nxt, d + 1))
        return None

    def distances_from(self, source: str) -> dict[str, int]:
        """Every node's BFS distance from ``source`` (only reachable nodes included)."""
        dist = {source: 0}
        frontier: deque[str] = deque([source])
        while frontier:
            cur = frontier.popleft()
            for nxt in self._adj.get(cur, ()):  # noqa: SIM118
                if nxt not in dist:
                    dist[nxt] = dist[cur] + 1
                    frontier.append(nxt)
        return dist

    # --------------------------------------------------------------- pools
    def all_ids(self) -> list[str]:
        return sorted(self.graph.nodes)

    def by_category(self, category: str) -> list[str]:
        return sorted(n.id for n in self.graph.nodes.values() if n.category == category)

    def by_salience(self, *, minimum: float = 0.0, descending: bool = True) -> list[str]:
        """Node ids with salience >= ``minimum``, ordered by salience."""
        items = [n for n in self.graph.nodes.values() if n.salience >= minimum]
        items.sort(key=lambda n: (n.salience, n.id), reverse=descending)
        return [n.id for n in items]

    def degree(self, node_id: str) -> int:
        return len(self._adj.get(node_id, ()))


def daily_seed(date_str: str, salt: str = "") -> int:
    """Deterministic seed from a calendar date (+ per-game salt).

    The client passes its LOCAL date (``YYYY-MM-DD``) so a game's "daily" instance is the
    same for everyone that day, but differs per game (via ``salt``). Pure function of its
    inputs — no server clock — so it is reproducible and testable.
    """
    digest = hashlib.blake2b(f"{date_str}:{salt}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


@lru_cache(maxsize=1)
def get_service() -> WordGameService:
    """The process-wide word-game service (offline fixture, built once)."""
    bundle = load_fixture()
    return WordGameService(graph=bundle.graph)


# --------------------------------------------------------------------- sessions
S = TypeVar("S")


class SessionStore(Generic[S]):
    """Thread-safe uuid4-keyed store for one game's in-progress sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, S] = {}
        self._lock = threading.Lock()

    def create(self, session: S) -> str:
        sid = str(uuid.uuid4())
        with self._lock:
            self._sessions[sid] = session
        return sid

    def get(self, sid: str) -> S | None:
        with self._lock:
            return self._sessions.get(sid)

    def delete(self, sid: str) -> bool:
        with self._lock:
            return self._sessions.pop(sid, None) is not None

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)
