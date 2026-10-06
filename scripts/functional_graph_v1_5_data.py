"""V1.5 draft functional-direction proposal; no application approval.

Existing endpoint definitions/forms remain fixed. New directed counterparts
require exact independent factual/quality and prospective acceptance before apply.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v1-5-functional-directions"
NOTE = "V1.5: two qualified existing-object functional directions; no new concepts or forms."
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
ALIASES = {}
EDGES = (
    {
        "bidirectional": 0,
        "dst": "n_v29_kitchen_table_cutit",
        "id": "e_v15i02_bread_knife",
        "is_distractor": 0,
        "label_ro": "se poate felia cu",
        "relation": "used_with",
        "src": "n_v4gas_paine",
        "strength": 0.98,
    },
    {
        "bidirectional": 0,
        "dst": "n_v4gas_apa",
        "id": "e_v15i02_tap_water",
        "is_distractor": 0,
        "label_ro": "controlează curgerea",
        "relation": "controls",
        "src": "n_v33_bathroom_fixture_robinet",
        "strength": 0.99,
    },
)
INTUITIVE_PAIRS = tuple((edge["src"], edge["dst"]) for edge in EDGES)


def build_nodes_and_edges():
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
