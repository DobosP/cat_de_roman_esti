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

import difflib
import hashlib
import heapq
import math
import os
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


def _edge_cost(strength: float) -> float:
    """Dijkstra cost for a semantic edge, from its ``strength`` (see ADR-0021).

    A strong link is cheap to traverse (feels closer), a weak one is dear:
    ``cost = 2.0 - clamp(strength, 0, 1)`` so strength 1.0 -> 1.0 and strength 0.0 -> 2.0.
    A missing/invalid strength (non-finite or non-positive) has no signal, so it takes the
    neutral middle cost 1.5 rather than being punished as the weakest possible edge.
    """
    if not math.isfinite(strength) or strength <= 0.0:
        return 1.5
    return 2.0 - min(max(strength, 0.0), 1.0)


# Confident auto-accept thresholds (ADR-0022): a fuzzy correction is played silently only
# when the best candidate is BOTH high-confidence (ratio floor) AND unambiguous (no second
# distinct node scores within the margin of it). Everything weaker stays advisory.
AUTO_ACCEPT_RATIO = 0.90
AUTO_ACCEPT_MARGIN = 0.06


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
    _rev_adj: dict[str, set[str]] = field(default_factory=dict)
    # forward edge Dijkstra cost: src -> {dst: cost} over the strongest non-distractor edge
    _fwd_cost: dict[str, dict[str, float]] = field(default_factory=dict)
    # category -> node ids (for scoped Alchimie projection construction; ADR-0044)
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
        # Traversable non-distractor adjacency. Directed fixture edges remain directed;
        # keep a reverse index as well so "distance to target" math is exact.
        for nid in self.graph.nodes:
            nbrs = self.graph.neighbors(nid, include_distractors=False)
            self._adj[nid] = {nb.node.id for nb in nbrs}
            # Per-edge cost for the graded (Dijkstra) distance (ADR-0021); the hop-count
            # BFS in distances_to() deliberately ignores this and stays unweighted.
            self._fwd_cost[nid] = {nb.node.id: _edge_cost(nb.edge.strength) for nb in nbrs}
            self._rev_adj.setdefault(nid, set())
        for src, destinations in self._adj.items():
            for dst in destinations:
                self._rev_adj.setdefault(dst, set()).add(src)

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

    def suggest(self, text: str, limit: int = 3) -> list[str]:
        """Fuzzy "did you mean" labels for a typo that :meth:`resolve` could not place.

        Runs :func:`difflib.get_close_matches` over the same normalized index keys
        resolution uses (labels, ids and aliases), maps each matched key back to its node's
        display label, and de-duplicates so a node that matched via several surface forms
        is offered once. Order is the close-match ranking (best first); ties are broken by
        label then id so the result is deterministic. :meth:`resolve` stays exact-match —
        this only powers advisory hints; silent acceptance is :meth:`resolve_fuzzy`'s
        (much stricter) job.
        """
        key = normalize(text)
        if not key:
            return []
        # A generous pool of candidate keys, then collapse to distinct nodes preserving
        # difflib's best-first order (its score already ranks closeness).
        matches = difflib.get_close_matches(key, self._index.keys(), n=limit * 4, cutoff=0.78)
        seen: set[str] = set()
        out: list[str] = []
        for matched_key in matches:
            nid = self._index.get(matched_key)
            if nid is None or nid in seen:
                continue
            seen.add(nid)
            out.append(self.label(nid))
            if len(out) >= limit:
                break
        return out

    def resolve_fuzzy(self, text: str) -> str | None:
        """Confidently auto-correct a near-miss to its node id, or None (ADR-0022).

        Where :meth:`suggest` is advisory, this is the resolver the games may ACT on:
        it scores every normalized index key (labels, ids, aliases) against the
        normalized input with :class:`difflib.SequenceMatcher` and keeps each node's
        best ratio. The correction is returned only when the top node clears
        ``AUTO_ACCEPT_RATIO`` **and** no second distinct node scores within
        ``AUTO_ACCEPT_MARGIN`` of it; anything weaker or ambiguous returns None so the
        caller falls back to the advisory suggestion flow. Deterministic: ratios are
        pure functions of the keys, and an exact tie between two nodes always reads as
        ambiguity rather than an arbitrary pick.
        """
        key = normalize(text)
        if not key:
            return None
        exact = self._index.get(key)
        if exact is not None:
            return exact
        # Any node able to win — or to block a winner as a close second — scores at
        # least this floor, so the scan can skip everything below it cheaply.
        floor = AUTO_ACCEPT_RATIO - AUTO_ACCEPT_MARGIN
        matcher = difflib.SequenceMatcher()
        matcher.set_seq2(key)
        best: dict[str, float] = {}
        for cand in self._index:
            matcher.set_seq1(cand)
            # The same cheap upper bounds difflib.get_close_matches applies.
            if matcher.real_quick_ratio() < floor or matcher.quick_ratio() < floor:
                continue
            ratio = matcher.ratio()
            if ratio < floor:
                continue
            nid = self._index[cand]
            if ratio > best.get(nid, 0.0):
                best[nid] = ratio
        if not best:
            return None
        ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))
        top_id, top_ratio = ranked[0]
        if top_ratio < AUTO_ACCEPT_RATIO:
            return None
        if len(ranked) > 1 and top_ratio - ranked[1][1] <= AUTO_ACCEPT_MARGIN:
            return None
        return top_id

    # --------------------------------------------------------------- graph ops
    def neighbor_ids(self, node_id: str, *, include_distractors: bool = False) -> list[str]:
        if not include_distractors:
            return sorted(self._adj.get(node_id, set()))
        nbrs = self.graph.neighbors(node_id, include_distractors=True)
        return sorted({nb.node.id for nb in nbrs})

    def predecessor_ids(self, node_id: str) -> list[str]:
        '''Direct non-distractor predecessors in the runtime directed graph.'''
        return sorted(self._rev_adj.get(node_id, set()))

    def link(self, a: str, b: str, *, include_distractors: bool = False) -> Edge | None:
        """The (strongest) real edge a->b in the chosen view, or None if not linked."""
        return self.graph.edge_between(a, b, include_distractors=include_distractors)

    def link_label(self, a: str, b: str) -> str:
        e = self.link(a, b)
        return e.label_ro if e else ""

    def common_neighbors(self, a: str, b: str, *, category: str | None = None) -> list[str]:
        """Nodes adjacent (non-distractor) to BOTH a and b — the 'combine' result set.

        With ``category``, results are restricted to that category. Alchimie uses this
        only while constructing its private sparse projection (ADR-0044): the unscoped
        candidate closure reaches nearly the whole graph, while a category subgraph
        remains bounded and themed.
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

    def distances_to(self, target: str) -> dict[str, int]:
        """Every node's directed BFS distance *to* ``target``.

        This is a reverse traversal over the same non-distractor graph used by
        :meth:`distance`. On a fully bidirectional graph it equals
        ``distances_from(target)``; on directed edges it answers the distinct question
        Lanț needs: which forward moves can still reach the target, and in how many hops.
        Ordering is deterministic for the same daily/seed guarantees as
        :meth:`distances_from`.
        """
        dist = {target: 0}
        frontier: deque[str] = deque([target])
        while frontier:
            cur = frontier.popleft()
            for previous in sorted(self._rev_adj.get(cur, ())):
                if previous not in dist:
                    dist[previous] = dist[cur] + 1
                    frontier.append(previous)
        return dist

    def weighted_distances_to(self, target: str) -> dict[str, float]:
        """Graded directed distance *to* ``target`` — Dijkstra, not hop count (ADR-0021).

        Same reversed non-distractor adjacency as :meth:`distances_to` (guess -> target,
        ADR-0018), but each edge carries the cost from :func:`_edge_cost` (strong links are
        cheap, weak ones dear). Two guesses the same number of hops away are thus separated
        by how *tight* their path is, which is what makes Contexto rank within a hop bucket.
        Reaches exactly the same node set as the hop-count BFS. Tie-breaking is deterministic
        (the heap orders equal costs by node id), so the same target yields the same map.
        """
        dist: dict[str, float] = {target: 0.0}
        # (cumulative_cost, node); node in the key makes equal-cost pops deterministic.
        heap: list[tuple[float, str]] = [(0.0, target)]
        while heap:
            d, cur = heapq.heappop(heap)
            if d > dist.get(cur, math.inf):
                continue
            for previous in sorted(self._rev_adj.get(cur, ())):
                # Edge is the FORWARD link previous -> cur; its cost is what a guess sitting
                # at ``previous`` pays to move one step toward the target.
                step = self._fwd_cost.get(previous, {}).get(cur, 1.5)
                nd = d + step
                if nd < dist.get(previous, math.inf):
                    dist[previous] = nd
                    heapq.heappush(heap, (nd, previous))
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


def _positive_env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a positive number") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive number")
    return value


def _positive_env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a positive integer") from None
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


# Two hours is ample for a short word game. A 1,000-entry cap per game keeps the
# worst-case live-session footprint modest on a 4 GB launch VM; operators can
# raise either bound explicitly after observing real concurrency.
DEFAULT_SESSION_TTL_SECONDS = _positive_env_float(
    "CAT_SESSION_TTL_SECONDS", 2 * 60 * 60
)
DEFAULT_MAX_SESSIONS = _positive_env_int("CAT_MAX_SESSIONS_PER_GAME", 1_000)


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
