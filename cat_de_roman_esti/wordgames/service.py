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
import time
import unicodedata
import uuid
from collections import OrderedDict, deque
from collections.abc import Callable
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
    # category -> its node ids (for category-scoped combine math; ADR-0013)
    _cat_members: dict[str, frozenset[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        cat_members: dict[str, set[str]] = {}
        for node in self.graph.nodes.values():
            self._index[normalize(node.label_ro)] = node.id
            self._index[normalize(node.id)] = node.id
            cat_members.setdefault(node.category, set()).add(node.id)
        self._cat_members = {c: frozenset(ids) for c, ids in cat_members.items()}
        # Aliases (ADR-0012): alternate exact surface forms — inflections, synonyms,
        # short titles — resolve to the same node. Labels/ids always win, and the
        # deterministic (sorted) order makes any residual collision stable; the
        # fixture validator forbids collisions in shipped data.
        for nid in sorted(self.graph.nodes):
            for alias in self.graph.nodes[nid].aliases:
                self._index.setdefault(normalize(alias), nid)
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

    def common_neighbors(self, a: str, b: str, *, category: str | None = None) -> list[str]:
        """Nodes adjacent (non-distractor) to BOTH a and b — the 'combine' result set.

        With ``category``, the result is restricted to nodes in that category. Alchimie
        uses this so the combine-closure stays within a theme (ADR-0013): on the dense
        graph the unscoped closure reaches ~the whole graph (every target craftable in
        ~2 gens, and slow); a category subgraph (~90 nodes) restores deliberate steps.
        """
        if a not in self._adj or b not in self._adj:
            return []
        common = self._adj[a] & self._adj[b]
        if category is not None:
            common = common & self._cat_members.get(category, frozenset())
        return sorted(common)

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
            # sorted(): set iteration is hash-randomized per process; deterministic
            # order keeps everything derived from BFS reproducible across restarts.
            for nxt in sorted(self._adj.get(cur, ())):
                if nxt in seen:
                    continue
                if nxt == b:
                    return d + 1
                seen.add(nxt)
                frontier.append((nxt, d + 1))
        return None

    def distances_from(self, source: str) -> dict[str, int]:
        """Every node's BFS distance from ``source`` (only reachable nodes included).

        Key order is deterministic (BFS layers, sorted within each expansion): puzzle
        generators sample/slice from this order, so it MUST NOT depend on per-process
        set/hash order — otherwise the same seed (and the shared daily!) produces a
        different puzzle after every server restart, which is exactly the bug this
        sorted() fixes.
        """
        dist = {source: 0}
        frontier: deque[str] = deque([source])
        while frontier:
            cur = frontier.popleft()
            for nxt in sorted(self._adj.get(cur, ())):
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

# Every POST /games mints a fresh uuid-keyed session and nothing ever removed them, so a
# long-lived server (or a bot spamming /games) would leak memory without bound. The store
# therefore self-trims: idle sessions pass a TTL and a hard cap evicts the
# least-recently-used once too many pile up. Defaults are generous — a sitting fits inside
# the TTL and the cap only bites under abuse — but both are tunable per store.
DEFAULT_SESSION_TTL_SECONDS = 6 * 60 * 60  # 6h: long enough to finish, then reclaim.
DEFAULT_MAX_SESSIONS = 10_000  # hard ceiling so a flood of /games can't exhaust memory.


class SessionStore(Generic[S]):
    """Thread-safe uuid4-keyed store for one game's in-progress sessions.

    Bounded in two complementary ways so it cannot grow without limit:

    * **TTL (sliding):** a session untouched for ``ttl_seconds`` is treated as abandoned
      and reclaimed. Every :meth:`get` refreshes the deadline, so an actively played game
      never expires mid-session — only idle ones do. Pass ``ttl_seconds=None`` to disable
      time-based expiry.
    * **Max size (LRU):** at most ``max_sessions`` live at once; creating beyond the cap
      evicts the least-recently-used entry. Pass ``max_sessions=None`` to disable the cap.

    Eviction is lazy — it runs inside :meth:`create`/:meth:`get`/:meth:`__len__` under the
    lock, so there is no background thread to manage. Entries are held in least- to
    most-recently-used order; with a uniform TTL the oldest are always at the front, which
    makes both the TTL sweep and the cap eviction cheap front-pops. ``clock`` is injectable
    (defaults to :func:`time.monotonic`, which is immune to wall-clock jumps) purely so
    tests can drive expiry deterministically without sleeping.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float | None = DEFAULT_SESSION_TTL_SECONDS,
        max_sessions: int | None = DEFAULT_MAX_SESSIONS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_sessions is not None and max_sessions < 1:
            raise ValueError("max_sessions must be >= 1 or None")
        # sid -> (session, last_access_time); insertion/access order == LRU order.
        self._sessions: OrderedDict[str, tuple[S, float]] = OrderedDict()
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._clock = clock
        self._lock = threading.Lock()

    # ----------------------------------------------------------- internal (lock held)
    def _purge_expired(self, now: float) -> int:
        """Drop sessions past their sliding TTL; returns how many were removed.

        Entries sit in least-recently-used order, so with a uniform TTL the soonest to
        expire are at the front: pop from the front until one is still alive.
        """
        if self._ttl is None:
            return 0
        removed = 0
        while self._sessions:
            sid = next(iter(self._sessions))
            _session, last = self._sessions[sid]
            if now - last <= self._ttl:
                break
            self._sessions.popitem(last=False)
            removed += 1
        return removed

    def _evict_to_cap(self) -> None:
        """Drop the least-recently-used entries until the size cap is satisfied."""
        if self._max is None:
            return
        while len(self._sessions) > self._max:
            self._sessions.popitem(last=False)

    # ----------------------------------------------------------- public API
    def create(self, session: S) -> str:
        sid = str(uuid.uuid4())
        with self._lock:
            now = self._clock()
            self._purge_expired(now)
            self._sessions[sid] = (session, now)  # newest -> most-recently-used (at end)
            self._evict_to_cap()
        return sid

    def get(self, sid: str) -> S | None:
        with self._lock:
            now = self._clock()
            self._purge_expired(now)
            entry = self._sessions.get(sid)
            if entry is None:
                return None
            session, _last = entry
            # Sliding TTL: a touched session is alive and becomes most-recently-used.
            self._sessions[sid] = (session, now)
            self._sessions.move_to_end(sid)
            return session

    def delete(self, sid: str) -> bool:
        with self._lock:
            return self._sessions.pop(sid, None) is not None

    def purge_expired(self) -> int:
        """Evict every session past its TTL now; returns the count removed.

        Runs automatically on each access; exposed for an optional periodic sweep and
        for tests.
        """
        with self._lock:
            return self._purge_expired(self._clock())

    def __len__(self) -> int:
        with self._lock:
            self._purge_expired(self._clock())
            return len(self._sessions)
