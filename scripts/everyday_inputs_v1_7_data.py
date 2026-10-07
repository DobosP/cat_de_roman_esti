"""V1.7 exact singular employee-pay input proposal; independent gates pending.

One qualified synonym headword, leafă, for existing Salariu. No new concepts,
links, curated rounds, targets or inferred inflection expansion.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v1-7-employee-pay-input"
NOTE = "V1.7: one qualified singular employee-pay synonym input for existing Salariu."
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
INTUITIVE_PAIRS = ()
ALIASES = {"n_v4soc_salariu": ("leafă",)}
EDGES = ()


def build_nodes_and_edges():
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
