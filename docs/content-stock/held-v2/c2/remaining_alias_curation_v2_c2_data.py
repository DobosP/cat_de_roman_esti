"""C2 existing-owner morphology proposal; apply only after fresh dual acceptance.

Twenty existing owners, 80 proposed aliases, no nodes, edges or game items.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v2-c2-remaining-alias-curation"
NOTE = "C2: twenty existing-owner morphology families with 80 proposed input aliases."
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
INTUITIVE_PAIRS = ()
ALIASES = {
    'n_v2via_rude': ('rudă', 'rudei', 'rudelor'),
    'n_v3muz_melodie': ('cântece', 'cântecele', 'cântecului', 'cântecelor'),
    'n_prim_ministru': ('premier', 'premieri', 'premierii', 'premierului', 'premierilor'),
    'n_primar': ('edil', 'edili', 'edilii', 'edilului', 'edililor'),
    'n_v2fil_actor': ('actrițele', 'actriței', 'actrițelor'),
    'n_v3lit_poveste': ('istorisirea', 'istorisiri', 'istorisirile', 'istorisirii', 'istorisirilor'),
    'n_v3soc_protest': ('mitingul', 'mitinguri', 'mitingurile', 'mitingului', 'mitingurilor'),
    'n_v24_people_relationships_sotie': ('neveste', 'nevestele', 'nevestei', 'nevestelor'),
    'n_v2lim_cuvant': ('vorbe', 'vorbele', 'vorbei', 'vorbelor'),
    'n_v4muz_trupa': ('formația', 'formații', 'formațiile', 'formației', 'formațiilor'),
    'n_gas_placinte_poale_brau': ('brânzoaică', 'brânzoaicele', 'brânzoaicei', 'brânzoaicelor'),
    'n_v4lim_nume': ('denumiri', 'denumirile', 'denumirii', 'denumirilor'),
    'n_v4lim_greseala': ('eroarea', 'erori', 'erorile', 'erorii', 'erorilor'),
    'n_v2soc_alegeri': ('scrutinul', 'scrutinuri', 'scrutinurile', 'scrutinului', 'scrutinurilor'),
    'n_v3spo_meci': ('meciuri', 'meciurile', 'meciului', 'meciurilor'),
    'n_v20gas_chiftele': ('chifteaua', 'chiftelei', 'chiftelelor'),
    'n_v20gas_snitel': ('șnițelele', 'șnițelului', 'șnițelelor'),
    'n_v20gas_cascaval': ('cașcavaluri', 'cașcavalurile', 'cașcavalului', 'cașcavalurilor'),
    'n_v4sti_virus': ('virusului', 'virusurilor'),
    'n_v2via_vecini': ('vecinul', 'vecinului', 'vecinilor'),
}
EDGES = ()


def build_nodes_and_edges():
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
