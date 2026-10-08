"""V1.6 exact input proposal; apply only after complete independent acceptance.

Two qualified singular synonym headwords. No new shared/world concepts, edges,
curated rounds, target approvals or inferred inflection families.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v1-6-everyday-inputs"
NOTE = "V1.6: two qualified singular synonym inputs for existing flag and edible-oil concepts."
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
INTUITIVE_PAIRS = ()
ALIASES = {
    "n_v4ist_steag": ("drapel",),
    "n_v24_food_pantry_ulei": ("untdelemn",),
}
EDGES = ()


def build_nodes_and_edges():
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
