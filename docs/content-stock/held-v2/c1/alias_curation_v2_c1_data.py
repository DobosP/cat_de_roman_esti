"""C1 existing-owner morphology proposal; apply only after fresh dual acceptance.

Twenty existing owners, 44 proposed aliases, no nodes, edges or game items.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v2-c1-alias-curation"
NOTE = "C1: twenty existing-owner morphology families with 44 proposed input aliases."
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
INTUITIVE_PAIRS = ()
ALIASES = {
    'n_v2sti_avion': ('avioane', 'avioanele', 'avionului', 'avioanelor'),
    'n_v3fil_cinematograf': ('cinematograful', 'cinematografe', 'cinematografele', 'cinematografului', 'cinematografelor'),
    'n_vdr_interfon': ('interfoane', 'interfoanele', 'interfonului', 'interfoanelor'),
    'n_v4soc_casa': ('casei', 'caselor'),
    'n_v4soc_familie': ('familiei', 'familiilor'),
    'n_v4via_baie': ('băii', 'băilor'),
    'n_v24_nature_plant_parts_ramura': ('ramurii', 'ramurilor'),
    'n_v24_nature_plant_parts_radacina': ('rădăcinii', 'rădăcinilor'),
    'n_v24_school_writing_pix': ('pixului', 'pixurilor'),
    'n_v24_school_classroom_lectie': ('lecției', 'lecțiilor'),
    'n_v24_school_assessment_examen': ('examenului', 'examenelor'),
    'n_v24_people_relatives_frate': ('fratelui', 'fraților'),
    'n_v24_people_descendants_nepot': ('nepotului', 'nepoților'),
    'n_v24_people_descendants_fiu': ('fiului', 'fiilor'),
    'n_v24_people_descendants_fiica': ('fiicei', 'fiicelor'),
    'n_v24_people_grandparents_matusa': ('mătușii', 'mătușilor'),
    'n_v24_people_relatives_unchi': ('unchilor',),
    'n_v24_people_parents_bebelus': ('bebelușului', 'bebelușilor'),
    'n_v32_garden_water_stropitoare': ('stropitorilor',),
    'n_v3soc_spital': ('spitalele',),
}
EDGES = ()


def build_nodes_and_edges():
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
