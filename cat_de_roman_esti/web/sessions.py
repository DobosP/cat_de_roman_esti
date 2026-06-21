"""In-memory game-session store, keyed by uuid4.

Each :class:`GameSession` owns one in-progress :class:`HopGame` plus the precomputed,
per-mode *view* (the category subgraph nodes + the mode-filtered edges) so the
serializer in :mod:`.views` can render :class:`GameState` JSON without recomputing the
subgraph on every request. The store is thread-safe enough for uvicorn's default
worker model: all mutations of the shared dict are guarded by a lock, and per-session
mutation (the only thing a hop touches) is also serialized so two concurrent requests
against the same game can't corrupt the path.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field

from ..engine import HopGame, Mode, Puzzle
from ..graph import Edge, Graph, Node


@dataclass
class GameSession:
    """One live game: the engine + the precomputed per-mode view of the subgraph."""

    id: str
    game: HopGame
    category: str
    # Precomputed per-mode view (built once at creation; the subgraph never changes).
    view_nodes: list[Node]
    view_edges: list[Edge]
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def mode(self) -> Mode:
        return self.game.mode

    @property
    def puzzle(self) -> Puzzle:
        return self.game.puzzle

    def reset(self) -> None:
        """Restart the same puzzle from its start node (view is unchanged)."""
        with self.lock:
            self.game.path = [self.game.puzzle.start_id]


class SessionStore:
    """Thread-safe uuid4-keyed registry of live game sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, GameSession] = {}
        self._lock = threading.Lock()

    def create(
        self,
        game: HopGame,
        *,
        category: str,
        view_nodes: list[Node],
        view_edges: list[Edge],
    ) -> GameSession:
        session_id = str(uuid.uuid4())
        session = GameSession(
            id=session_id,
            game=game,
            category=category,
            view_nodes=view_nodes,
            view_edges=view_edges,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> GameSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)


def build_view(graph: Graph, puzzle: Puzzle, mode: Mode) -> tuple[list[Node], list[Edge]]:
    """Compute the per-mode subgraph view (nodes + mode-filtered edges) for a puzzle.

    The view is the category subgraph the player navigates. Both modes send the full
    set of category nodes (so the player sees the whole network map) plus every node on
    the puzzle's ``solution_path`` (the loader already widened mixed puzzles, so those
    nodes are present in the graph). Edge filtering is the visible difficulty lever:

      * easy: only NON-distractor edges of the subgraph;
      * hard: ALL edges including distractors (decoys look real).

    An edge is part of the view when both endpoints are in the node view.
    """
    category = puzzle.category

    # --- node view: every node of the puzzle category + every solution_path node ---
    wanted_ids: set[str] = set(puzzle.solution_path)
    wanted_ids.add(puzzle.start_id)
    wanted_ids.add(puzzle.target_id)
    for node in graph.nodes.values():
        # "mixed" puzzles have no single category; include the union the loader widened
        # to (every node we have), so the cross-category map is fully visible.
        if category in ("", "mixed") or node.category == category:
            wanted_ids.add(node.id)

    node_view = [graph.nodes[nid] for nid in wanted_ids if nid in graph.nodes]
    node_view.sort(key=lambda n: (-n.salience, n.id))
    view_id_set = {n.id for n in node_view}

    # --- edge view: mode-filtered edges with both endpoints in the node view --------
    include_distractors = mode is Mode.HARD
    seen_edge_ids: set[str] = set()
    edge_view: list[Edge] = []
    for edge in graph.edges:
        if edge.is_distractor and not include_distractors:
            continue
        if edge.src_id not in view_id_set or edge.dst_id not in view_id_set:
            continue
        if edge.id in seen_edge_ids:
            continue
        seen_edge_ids.add(edge.id)
        edge_view.append(edge)
    edge_view.sort(key=lambda e: e.id)
    return node_view, edge_view
