"""cat_de_roman_esti — thin client + terminal game over the Romanian KG products.

Consumes the ``kg_nodes`` / ``kg_edges`` / ``kg_puzzles`` data products served by
the RO-EDU platform (romania_scraper.dataapi via ro_data_server), builds an
in-memory semantic graph, and runs a "semantic network hop" game in the terminal.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .engine import HopGame, HopResult
from .graph import Edge, Graph, Node
from .roedu_client import RoeduClient

__all__ = [
    "Edge",
    "Graph",
    "HopGame",
    "HopResult",
    "Node",
    "RoeduClient",
]
