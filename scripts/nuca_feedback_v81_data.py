"""Reviewed V81 walnut recipe links for the shared enrichment transaction.

The batch adds one ordinary culinary concept and four directed ingredient links.
It neither stages game records nor changes existing aliases.
"""

from __future__ import annotations

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import (
    DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v81-nuca-feedback"
NOTE = (
    "v81: one reviewed walnut concept with four directed recipe ingredient links; "
    "no game records or existing aliases, legacy puzzles regenerated deterministically."
)
NEW_NODE_IDS = ("n_v81_food_pantry_nuca",)
GAME_ITEM_IDS: tuple[str, ...] = ()

NUCA = "n_v81_food_pantry_nuca"
TARGETS = (
    "n_gas_cozonac",
    "n_v17gas_coliva",
    "n_gas_baclava_dobrogeana",
    "n_v21gas_cornulete",
)
INTUITIVE_PAIRS = tuple((NUCA, target) for target in TARGETS)

_RECIPE_STRENGTHS = {
    "n_gas_cozonac": 0.97,
    "n_v17gas_coliva": 0.97,
    "n_gas_baclava_dobrogeana": 0.95,
    "n_v21gas_cornulete": 0.90,
}


def build_nodes_and_edges() -> dict[str, object]:
    """Keep recipe direction explicit; dish nodes gain no walnut fan-out."""

    return {
        "nodes": [
            {
                "id": NUCA,
                "node_type": "concept",
                "label_ro": "Nucă",
                "category": "gastronomie",
                "description": (
                    "Fructul nucului, cu coajă tare și miez comestibil folosit "
                    "în preparate dulci."
                ),
                "salience": 0.90,
                "aliases": ["nucile"],
            }
        ],
        "aliases": {},
        "edges": [
            {
                "src": NUCA,
                "dst": target,
                "relation": "part_of",
                "label_ro": "ingredient pentru",
                "strength": _RECIPE_STRENGTHS[target],
                "bidirectional": 0,
                "is_distractor": 0,
            }
            for target in TARGETS
        ],
    }
