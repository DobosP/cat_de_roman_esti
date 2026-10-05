"""V1.3 graph proposal; apply only after exact independent reviews.

The supported graph transaction owns generated fixture writes. These new concepts
are outward-only guesses, with no new curated round or hidden target approval.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = "fixture-v1-3-everyday-concepts"
NOTE = "V1.3: three reviewed everyday concepts, twelve grammatical forms and twelve one-way links."
GAME_ITEM_IDS = ()

NODES = (
    {
        "id": "n_v1_3_home_balama",
        "node_type": "concept",
        "label_ro": "Balama",
        "category": "viata_de_roman",
        "description": "Piesă articulată care permite rotirea unei uși sau a unui canat; aici, "
        "balamaua fizică de feronerie.",
        "salience": 0.85,
        "aliases": ["balamaua", "balamale", "balamalele", "balamalei", "balamalelor"],
    },
    {
        "id": "n_v1_3_material_lemn",
        "node_type": "concept",
        "label_ro": "Lemn",
        "category": "viata_de_roman",
        "description": (
            "Material provenit din părțile lemnoase ale arborilor, "
            "folosit la construcții și obiecte din gospodărie; aici, sensul de material."
        ),
        "salience": 0.9,
        "aliases": ["lemnul", "lemnului"],
    },
    {
        "id": "n_v1_3_clothing_fermoar",
        "node_type": "concept",
        "label_ro": "Fermoar",
        "category": "viata_de_roman",
        "description": "Dispozitiv de închidere cu două șiruri de elemente care se îmbină prin "
        "deplasarea unui cursor, folosit la îmbrăcăminte și genți.",
        "salience": 0.85,
        "aliases": ["fermoarul", "fermoare", "fermoarele", "fermoarului", "fermoarelor"],
    },
)

EDGES = (
    {
        "src": "n_v1_3_home_balama",
        "dst": "n_v4via_usa",
        "relation": "allows_pivoting",
        "label_ro": "permite rotirea unei uși batante",
        "strength": 0.9,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_home_balama",
        "dst": "n_v24_home_surfaces_fereastra",
        "relation": "allows_pivoting",
        "label_ro": "poate permite rotirea canatului mobil al unei ferestre",
        "strength": 0.85,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_home_balama",
        "dst": "n_v24_home_storage_dulap",
        "relation": "used_in",
        "label_ro": "se poate monta la ușile batante ale unui dulap",
        "strength": 0.85,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_home_balama",
        "dst": "n_v32_workshop_fastener_surub",
        "relation": "fastened_with",
        "label_ro": "unele balamale se fixează cu șuruburi",
        "strength": 0.8,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_material_lemn",
        "dst": "n_v4sti_copac",
        "relation": "obtained_from",
        "label_ro": "material provenit din părțile lemnoase ale unui copac",
        "strength": 0.9,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_material_lemn",
        "dst": "n_v24_home_seating_scaun",
        "relation": "used_to_make",
        "label_ro": "poate fi folosit la fabricarea unor scaune",
        "strength": 0.8,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_material_lemn",
        "dst": "n_v32_workshop_fastener_surub",
        "relation": "joined_with",
        "label_ro": "piesele de lemn se pot îmbina cu șuruburi pentru lemn",
        "strength": 0.8,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_material_lemn",
        "dst": "n_v32_workshop_cut_fierastrau",
        "relation": "cut_with",
        "label_ro": "se poate tăia cu fierăstrăul",
        "strength": 0.85,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_clothing_fermoar",
        "dst": "n_v30_clothing_everyday_pantaloni",
        "relation": "used_to_close",
        "label_ro": "poate fi folosit la închiderea pantalonilor",
        "strength": 0.85,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_clothing_fermoar",
        "dst": "n_v30_clothing_everyday_fusta",
        "relation": "used_to_close",
        "label_ro": "poate fi folosit la închiderea unei fuste",
        "strength": 0.8,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_clothing_fermoar",
        "dst": "n_v30_clothing_outer_geaca",
        "relation": "used_to_close",
        "label_ro": "poate fi folosit la închiderea unei geci",
        "strength": 0.9,
        "is_distractor": 0,
        "bidirectional": 0,
    },
    {
        "src": "n_v1_3_clothing_fermoar",
        "dst": "n_v23via_ghiozdan",
        "relation": "used_to_close",
        "label_ro": "poate fi folosit la închiderea compartimentelor unui ghiozdan",
        "strength": 0.85,
        "is_distractor": 0,
        "bidirectional": 0,
    },
)

NEW_NODE_IDS = tuple(node["id"] for node in NODES)
INTUITIVE_PAIRS = tuple((edge["src"], edge["dst"]) for edge in EDGES)


def build_nodes_and_edges():
    return {"nodes": NODES, "edges": EDGES, "aliases": {}}
