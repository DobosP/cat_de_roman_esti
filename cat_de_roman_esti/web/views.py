"""Pure serializers: turn a HopGame + Graph + mode into the contract JSON shapes.

These functions hold no state and never mutate the game; they read a
:class:`~.sessions.GameSession` (which already carries the precomputed per-mode node +
edge view) and emit plain dicts matching the WEB APP CONTRACT exactly:

    GraphNode  = { id, label, category, node_type, salience, difficulty_tier, description }
    GraphEdge  = { id, source, target, relation, label, bidirectional }
    PuzzleView = { id, category, difficulty, start_id, target_id, par, optimal_hops }
    GameState  = { game_id, mode, category, puzzle, nodes, edges, current_id, target_id,
                   start_id, hops, won, score, path, neighbors, hint, last_error }

MODE VIEW RULES are applied here at the edge level:

  * easy: edge.label = the Romanian edge label (label_ro); hint = the suggested next
    node id on the solution from the current node.
  * hard: edge.label = "" (decoys look identical to real edges) and no is_distractor
    flag is exposed; hint = null.
"""

from __future__ import annotations

from ..engine import HopGame, Mode, Puzzle
from ..graph import Edge, Node
from .sessions import GameSession


def node_to_json(node: Node) -> dict:
    """Serialize a graph node to the GraphNode contract shape."""
    return {
        "id": node.id,
        "label": node.label_ro,
        "category": node.category,
        "node_type": node.node_type,
        "salience": node.salience,
        "difficulty_tier": node.difficulty_tier,
        "description": node.description,
    }


def edge_to_json(edge: Edge, *, mode: Mode) -> dict:
    """Serialize a graph edge to the GraphEdge contract shape, per mode.

    Easy mode reveals the Romanian edge label; hard mode blanks it so decoy edges are
    indistinguishable from real ones. The ``is_distractor`` flag is NEVER exposed in
    either mode (the client must not be able to tell decoys from real edges in hard).
    """
    label = edge.label_ro if mode is Mode.EASY else ""
    return {
        "id": edge.id,
        "source": edge.src_id,
        "target": edge.dst_id,
        "relation": edge.relation,
        "label": label,
        "bidirectional": edge.bidirectional,
    }


def puzzle_to_json(puzzle: Puzzle, mode: Mode) -> dict:
    """Serialize a puzzle to the PuzzleView contract shape.

    ``difficulty`` reflects the active game mode (easy|hard), which the loader uses as
    the puzzle's own difficulty; ``par``/``optimal_hops`` come straight from the puzzle.
    """
    return {
        "id": puzzle.id,
        "category": puzzle.category,
        "difficulty": mode.value,
        "start_id": puzzle.start_id,
        "target_id": puzzle.target_id,
        "par": puzzle.par,
        "optimal_hops": puzzle.optimal_hops,
    }


def _hint(game: HopGame) -> str | None:
    """Easy-mode next-on-solution node id from the current node, else None.

    Reuses the engine's mode-gated, position-aware ``hint_neighbors`` (which already
    returns [] in hard mode) and surfaces the single suggested next hop. Hard mode and
    a player sitting at the end of the solution both yield ``None``.
    """
    hints = game.hint_neighbors()
    return hints[0] if hints else None


def game_state(session: GameSession, *, last_error: str | None = None) -> dict:
    """Serialize a session into the full GameState contract shape.

    ``last_error`` is set only on the response to a rejected hop (the stored game is
    unchanged); every other endpoint returns it as ``null``.
    """
    game = session.game
    mode = game.mode

    neighbors = [nb.node.id for nb in game.options()]

    return {
        "game_id": session.id,
        "mode": mode.value,
        "category": session.category,
        "puzzle": puzzle_to_json(game.puzzle, mode),
        "nodes": [node_to_json(n) for n in session.view_nodes],
        "edges": [edge_to_json(e, mode=mode) for e in session.view_edges],
        "current_id": game.current_id,
        "target_id": game.puzzle.target_id,
        "start_id": game.puzzle.start_id,
        "hops": game.hops,
        "won": game.won,
        "score": game.score(),
        "path": list(game.path),
        "neighbors": neighbors,
        "hint": _hint(game),
        "last_error": last_error,
    }
