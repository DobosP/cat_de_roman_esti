"""V1.4 exact graph proposal; only independently accepted bytes may be applied.

No new concepts, curated rounds or hidden-target approval. Distinct unit senses
remain qualified; article/case forms beyond direct DOOM lemma/plural are held.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v1-4-time-links"
NOTE = "V1.4: one qualified clock synonym family (two forms) and two directed duration-unit links."
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
ALIASES = {"n_v24_time_day_ceas": ("ceasornic", "ceasornice")}
EDGES = (
    {
        "src": "n_v24_time_day_ora",
        "dst": "n_v29_time_units_minut",
        "relation": "has_part_time",
        "label_ro": "ca unitate de durată, are șaizeci de minute",
        "strength": 0.99,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v24_time_day_zi",
        "dst": "n_v24_time_day_ora",
        "relation": "has_part_time",
        "label_ro": "ca unitate de durată, are douăzeci și patru de ore",
        "strength": 0.99,
        "is_distractor": 0,
        "bidirectional": 0,
    },
)
INTUITIVE_PAIRS = tuple((edge["src"], edge["dst"]) for edge in EDGES)


def build_nodes_and_edges():
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
