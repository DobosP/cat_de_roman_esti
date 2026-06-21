"""HopGame — the playable semantic-hop game engine.

A puzzle gives the player a START and a TARGET concept inside a category subgraph.
The player hops along real edges; reaching the target wins. The score is computed
against the puzzle's ``par`` (== ``optimal_hops``, the shortest path on the
non-distractor subgraph).

Difficulty (the four contract levers) maps onto the data like this:

  1. HOP DISTANCE   — encoded in the puzzle (``optimal_hops``/``par``); the engine
                      doesn't change it, it only scores against it.
  2. OBSCURITY      — encoded in node ``salience``/``difficulty_tier`` at puzzle pick
                      time; the engine surfaces it but doesn't alter it.
  3. EDGE VISIBILITY / HINTS — *engine-controlled*: easy mode exposes ``label_ro`` on
                      each option and ``hint_neighbors`` (the suggested next hop along
                      the solution); hard mode hides both.
  4. DISTRACTOR DENSITY — *engine-controlled*: easy mode filters ``is_distractor``
                      edges out of the neighbour view; hard mode keeps the decoys.

The engine never mutates the graph — it filters the *view* per mode.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from .graph import Graph, Neighbor, Node


class Mode(StrEnum):
    EASY = "easy"
    HARD = "hard"

    @classmethod
    def parse(cls, value: str | Mode) -> Mode:
        if isinstance(value, Mode):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"unknown mode {value!r} (expected easy|hard)") from exc


@dataclass(frozen=True)
class Puzzle:
    """A served ``kg_puzzles`` record, normalized."""

    id: str
    start_id: str
    target_id: str
    category: str
    difficulty: str
    optimal_hops: int
    par: int
    solution_path: list[str] = field(default_factory=list)
    hint_neighbors: list[str] = field(default_factory=list)

    @classmethod
    def from_record(cls, rec: Mapping[str, object]) -> Puzzle:
        return cls(
            id=str(rec["id"]),
            start_id=str(rec["start_id"]),
            target_id=str(rec["target_id"]),
            category=str(rec.get("category", "")),
            difficulty=str(rec.get("difficulty", "easy")).strip().lower(),
            optimal_hops=int(rec.get("optimal_hops", 0) or 0),
            par=int(rec.get("par", rec.get("optimal_hops", 0)) or 0),
            solution_path=_as_id_list(rec.get("solution_path")),
            hint_neighbors=_as_id_list(rec.get("hint_neighbors")),
        )


def _as_id_list(value: object) -> list[str]:
    """Coerce a served json-array-ish field into a list of id strings."""
    if value is None:
        return []
    if isinstance(value, str):
        import json

        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        return [str(x) for x in parsed] if isinstance(parsed, list) else [str(parsed)]
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    return [str(value)]


@dataclass(frozen=True)
class HopResult:
    """Outcome of a single attempted hop."""

    ok: bool
    reason: str = ""
    won: bool = False


@dataclass
class HopGame:
    """A loaded, in-progress game of one puzzle over one category subgraph."""

    graph: Graph
    puzzle: Puzzle
    mode: Mode
    path: list[str] = field(default_factory=list)

    # --------------------------------------------------------------- loading
    @classmethod
    def load(cls, graph: Graph, puzzle: Puzzle | Mapping[str, object], mode: str | Mode) -> HopGame:
        """Load a puzzle + its category subgraph into a fresh game.

        Validates that the puzzle is playable on the given graph: start and target
        nodes must both be present. Fail-closed: an unplayable puzzle raises rather
        than silently producing an unwinnable game.
        """
        pz = puzzle if isinstance(puzzle, Puzzle) else Puzzle.from_record(puzzle)
        m = Mode.parse(mode)
        if not graph.has_node(pz.start_id):
            raise ValueError(f"puzzle start node {pz.start_id!r} missing from graph")
        if not graph.has_node(pz.target_id):
            raise ValueError(f"puzzle target node {pz.target_id!r} missing from graph")
        return cls(graph=graph, puzzle=pz, mode=m, path=[pz.start_id])

    # --------------------------------------------------------------- view
    @property
    def include_distractors(self) -> bool:
        """Hard mode keeps decoy edges; easy mode filters them out (lever 4)."""
        return self.mode is Mode.HARD

    @property
    def show_labels(self) -> bool:
        """Easy mode reveals edge labels; hard mode hides them (lever 3)."""
        return self.mode is Mode.EASY

    @property
    def current_id(self) -> str:
        return self.path[-1]

    @property
    def current_node(self) -> Node:
        node = self.graph.node(self.current_id)
        assert node is not None  # guaranteed: every hop lands on a real node
        return node

    @property
    def target_node(self) -> Node:
        node = self.graph.node(self.puzzle.target_id)
        assert node is not None
        return node

    @property
    def hops(self) -> int:
        """Number of hops taken so far (path length minus the start node)."""
        return len(self.path) - 1

    def options(self) -> list[Neighbor]:
        """Neighbours of the current node, filtered for the active mode."""
        return self.graph.neighbors(self.current_id, include_distractors=self.include_distractors)

    def hint_neighbors(self) -> list[str]:
        """Easy-mode suggested next hop along the solution, gated by mode + position.

        The hint is the IMMEDIATE next node on the solution, not any downstream solution
        node that merely happens to be a direct neighbour (which could mislead after a
        detour or via a side edge). Specifically:

          * Hard mode hides hints entirely (lever 3) — returns ``[]``.
          * If the player's current node is on ``solution_path`` at index ``i`` (and is
            not already the final/target node), the only hint is ``solution_path[i+1]``,
            and only when it is a real neighbour in the active view.
          * If the player is OFF the solution path, fall back to the previous behaviour:
            surface every ``hint_neighbors`` id that is currently reachable, so the hint
            stays useful while the player works their way back onto the solution.
        """
        if self.mode is not Mode.EASY:
            return []
        reachable = {nb.node.id for nb in self.options()}
        path = self.puzzle.solution_path
        cur = self.current_id
        # On-solution: gate to the single immediate next step (if any remains).
        if cur in path:
            i = path.index(cur)
            if i + 1 < len(path):
                nxt = path[i + 1]
                return [nxt] if nxt in reachable else []
            return []  # already at the end of the solution path (the target)
        # Off-solution: previous reachability behaviour (any reachable hint node).
        return [nid for nid in self.puzzle.hint_neighbors if nid in reachable]

    def edge_label(self, dst_id: str) -> str:
        """Human edge label for hopping to ``dst_id`` — only shown in easy mode."""
        if not self.show_labels:
            return ""
        edge = self.graph.edge_between(
            self.current_id, dst_id, include_distractors=self.include_distractors
        )
        return edge.label_ro if edge else ""

    # --------------------------------------------------------------- play
    @property
    def won(self) -> bool:
        return self.current_id == self.puzzle.target_id

    def hop(self, dst_id: str) -> HopResult:
        """Attempt to move the player to ``dst_id``.

        A hop is valid only if there is a real edge from the current node to the
        target in the active mode's view (distractor edges are not traversable in easy
        mode). On success the path is extended and a win is reported when the target is
        reached.
        """
        if self.won:
            return HopResult(ok=False, reason="game already won", won=True)
        if dst_id == self.current_id:
            return HopResult(ok=False, reason="already at this node")
        edge = self.graph.edge_between(
            self.current_id, dst_id, include_distractors=self.include_distractors
        )
        if edge is None:
            return HopResult(ok=False, reason="no edge from current node to that node")
        self.path.append(dst_id)
        return HopResult(ok=True, won=self.won)

    # --------------------------------------------------------------- score
    def score(self) -> int:
        """Score the (won) game vs par.

        Base 1000. Reaching the target at or under par gives a perfect 1000; each hop
        over par deducts 100 (floored at 100 so a finished game always scores). A game
        that isn't won scores 0.
        """
        if not self.won:
            return 0
        over = max(0, self.hops - self.puzzle.par)
        return max(100, 1000 - 100 * over)

    def summary(self) -> dict:
        """Compact end-of-game summary (used by the CLI and tests)."""
        return {
            "puzzle_id": self.puzzle.id,
            "mode": self.mode.value,
            "won": self.won,
            "hops": self.hops,
            "par": self.puzzle.par,
            "optimal_hops": self.puzzle.optimal_hops,
            "score": self.score(),
            "path": list(self.path),
        }
