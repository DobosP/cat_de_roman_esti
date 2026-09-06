"""Two reviewed ingredient links, applied through the shared enrichment transaction.

Evidence and bounded graph impacts: docs/reviews/v77-flour-associations/README.md.
No nodes, aliases or game records are added by this batch.
"""

from __future__ import annotations

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import (
    DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v77-flour-associations"
NOTE = (
    "v77: two reviewed directed flour-to-dish ingredient links; existing nodes, "
    "aliases and game records preserved, legacy puzzles regenerated deterministically."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()
FLOUR = "n_v24_food_pantry_faina"
TARGETS = ("n_gas_cozonac", "n_v3gas_clatite")
INTUITIVE_PAIRS = tuple((FLOUR, target) for target in TARGETS)


def build_nodes_and_edges() -> dict[str, object]:
    """Keep recipe direction explicit; the links do not add reverse dish fan-out."""
    return {
        "nodes": [],
        "aliases": {},
        "edges": [
            {
                "src": FLOUR,
                "dst": target,
                "relation": "part_of",
                "label_ro": "ingredient pentru",
                "strength": 0.97,
                "bidirectional": 0,
                "is_distractor": 0,
            }
            for target in TARGETS
        ],
    }
