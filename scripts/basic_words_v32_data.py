"""Audited source data for the v32 face, workshop, and garden wave.

V32 adds concrete beginner vocabulary without serving a new game board.  Exact,
conservative inflections stay owned by one concept, while three small directed
meshes provide semantic choices.  Inbound-only legacy bridges make every new node
reachable without adding a route from the new content back into the mature graph.
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from basic_words_v31_data import BEGINNER_BENCHMARK as V31_BEGINNER_BENCHMARK
from basic_words_v31_data import (
    DEFERRED_AMBIGUOUS_TERMS,
    DEFERRED_V31_CONCEPTS,
    REVIEW_ITEM_IDS,
)

BUILD_VERSION = "fixture-v32-face-workshop-garden"
NOTE = (
    "v32: eighteen concrete beginner concepts across facial anatomy, hand tools, "
    "and garden equipment, with conservative inflections and explicit semantic "
    "links; no game boards or promotions."
)
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
GAME_ITEM_IDS: tuple[str, ...] = ()
V32_BEGINNER_EXTENSION: tuple[str, ...] = (
    "Buză",
    "Obraz",
    "Frunte",
    "Nară",
    "Sprânceană",
    "Pleoapă",
    "Ciocan",
    "Cui",
    "Șurubelniță",
    "Șurub",
    "Clește",
    "Fierăstrău",
    "Ghiveci de flori",
    "Lopată",
    "Greblă",
    "Stropitoare",
    "Roabă",
    "Furtun de grădină",
)
BEGINNER_BENCHMARK = (*V31_BEGINNER_BENCHMARK, *V32_BEGINNER_EXTENSION)


@dataclass(frozen=True, slots=True)
class ConceptSpec:
    node_id: str
    label: str
    category: str
    salience: float
    description: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EdgeSpec:
    source: str
    target: str
    relation: str
    label_ro: str
    strength: float = 0.96
    bidirectional: int = 0


def _norm(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char)).casefold().split()
    )


CONCEPTS: tuple[ConceptSpec, ...] = (
    ConceptSpec(
        "n_v32_body_face_buza",
        "Buză",
        "stiinta",
        0.94,
        "Parte moale a feței care mărginește gura și ajută la vorbire și mâncat.",
        ("buze", "buzele", "buzei"),
    ),
    ConceptSpec(
        "n_v32_body_face_obraz",
        "Obraz",
        "stiinta",
        0.92,
        "Partea laterală a feței, între ochi, ureche și gură.",
        ("obrazul", "obraji", "obrajii", "obrazului"),
    ),
    ConceptSpec(
        "n_v32_body_face_frunte",
        "Frunte",
        "stiinta",
        0.93,
        "Partea de sus a feței, între sprâncene și păr.",
        ("fruntea", "frunți", "frunțile", "frunții"),
    ),
    ConceptSpec(
        "n_v32_body_face_nara",
        "Nară",
        "stiinta",
        0.92,
        "Deschidere a nasului prin care intră și iese aerul.",
        ("nări", "nările", "nării"),
    ),
    ConceptSpec(
        "n_v32_body_face_spranceana",
        "Sprânceană",
        "stiinta",
        0.92,
        "Șir de fire de păr aflat deasupra ochiului.",
        ("sprâncene", "sprâncenele", "sprâncenei"),
    ),
    ConceptSpec(
        "n_v32_body_face_pleoapa",
        "Pleoapă",
        "stiinta",
        0.92,
        "Pliu de piele care acoperă și protejează ochiul.",
        ("pleoape", "pleoapele", "pleoapei"),
    ),
    ConceptSpec(
        "n_v32_workshop_hand_ciocan",
        "Ciocan",
        "viata_de_roman",
        0.94,
        "Unealtă cu mâner și cap greu, folosită pentru a bate cuie.",
        ("ciocanul", "ciocane", "ciocanele", "ciocanului"),
    ),
    ConceptSpec(
        "n_v32_workshop_fastener_cui",
        "Cui",
        "viata_de_roman",
        0.92,
        "Piesă mică și ascuțită din metal, bătută cu ciocanul pentru a prinde obiecte.",
        ("cuiul", "cuie", "cuiele", "cuiului"),
    ),
    ConceptSpec(
        "n_v32_workshop_hand_surubelnita",
        "Șurubelniță",
        "viata_de_roman",
        0.93,
        "Unealtă folosită pentru a strânge sau desface șuruburi.",
        ("șurubelnițe", "șurubelnițele", "șurubelniței"),
    ),
    ConceptSpec(
        "n_v32_workshop_fastener_surub",
        "Șurub",
        "viata_de_roman",
        0.92,
        "Piesă metalică filetată care prinde obiecte prin rotire.",
        ("șurubul", "șuruburi", "șuruburile", "șurubului"),
    ),
    ConceptSpec(
        "n_v32_workshop_hand_cleste",
        "Clește",
        "viata_de_roman",
        0.91,
        "Unealtă cu două brațe, folosită pentru a prinde, îndoi sau tăia.",
        ("cleștele", "clești", "cleștii", "cleștelui"),
    ),
    ConceptSpec(
        "n_v32_workshop_cut_fierastrau",
        "Fierăstrău",
        "viata_de_roman",
        0.92,
        "Unealtă cu lamă dințată, folosită pentru a tăia lemn sau alte materiale.",
        (
            "fierăstrăul",
            "fierăstraie",
            "fierăstraiele",
            "fierăstrăului",
            "ferăstrău",
            "ferăstrăul",
            "ferăstraie",
            "ferăstraiele",
            "ferăstrăului",
        ),
    ),
    ConceptSpec(
        "n_v32_garden_container_ghiveci_flori",
        "Ghiveci de flori",
        "viata_de_roman",
        0.91,
        "Recipient în care se pune pământ pentru a crește flori sau alte plante.",
        (
            "ghiveciul de flori",
            "ghivece de flori",
            "ghivecele de flori",
            "ghiveciului de flori",
        ),
    ),
    ConceptSpec(
        "n_v32_garden_soil_lopata",
        "Lopată",
        "viata_de_roman",
        0.92,
        "Unealtă cu coadă și lamă lată, folosită pentru a muta pământ.",
        ("lopeți", "lopețile", "lopeții"),
    ),
    ConceptSpec(
        "n_v32_garden_soil_grebla",
        "Greblă",
        "viata_de_roman",
        0.90,
        "Unealtă cu dinți și coadă, folosită pentru a strânge frunze și a netezi pământul.",
        ("greble", "greblele", "greblei"),
    ),
    ConceptSpec(
        "n_v32_garden_water_stropitoare",
        "Stropitoare",
        "viata_de_roman",
        0.91,
        "Recipient cu mâner și cioc perforat, folosit pentru a uda plante.",
        ("stropitoarea", "stropitori", "stropitorile", "stropitorii"),
    ),
    ConceptSpec(
        "n_v32_garden_transport_roaba",
        "Roabă",
        "viata_de_roman",
        0.90,
        "Cărucior cu o roată și două mânere, folosit pentru a transporta pământ sau unelte.",
        ("roabe", "roabele", "roabei"),
    ),
    ConceptSpec(
        "n_v32_garden_water_furtun",
        "Furtun de grădină",
        "viata_de_roman",
        0.91,
        "Tub flexibil prin care curge apă pentru a uda grădina.",
        (
            "furtunul de grădină",
            "furtunuri de grădină",
            "furtunurile de grădină",
            "furtunului de grădină",
        ),
    ),
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)

FACE_NODE_IDS: tuple[str, ...] = tuple(
    concept.node_id for concept in CONCEPTS if concept.node_id.startswith("n_v32_body_face_")
)
WORKSHOP_NODE_IDS: tuple[str, ...] = tuple(
    concept.node_id for concept in CONCEPTS if concept.node_id.startswith("n_v32_workshop_")
)
GARDEN_NODE_IDS: tuple[str, ...] = tuple(
    concept.node_id for concept in CONCEPTS if concept.node_id.startswith("n_v32_garden_")
)
DOMAIN_NODE_IDS: tuple[tuple[str, ...], ...] = (
    FACE_NODE_IDS,
    WORKSHOP_NODE_IDS,
    GARDEN_NODE_IDS,
)


# Neighboring concepts, ambiguous bare senses, and distinct tool subtypes do not become
# aliases.  Qualified labels prevent the food sense of "ghiveci" and the weather sense
# of "furtun" from being claimed by garden equipment.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "față",
    "păr",
    "bărbie",
    "barbie",
    "barbă",
    "geană",
    "gene",
    "mustăți",
    "maxilar",
    "ciocănel",
    "baros",
    "patent",
    "clește papagal",
    "clește de rufe",
    "ferestrău",
    "herăstrău",
    "fierăstrău electric",
    "drujbă",
    "burghiu",
    "bormașină",
    "ruletă",
    "cheie",
    "ghiveci",
    "ghiveciul",
    "ghivece",
    "ghivecele",
    "ghiveciului",
    "glastră",
    "jardinieră",
    "cazma",
    "hârleț",
    "sapă",
    "mătura",
    "furtun",
    "furtunul",
    "furtunuri",
    "furtunurile",
    "stropitor",
    "udătoare",
    "găleată",
    "sămânță",
    "tulpină",
    "foarfecă",
)
DEFERRED_V32_CONCEPTS: tuple[str, ...] = (
    *DEFERRED_V31_CONCEPTS,
    "Față",
    "Păr",
    "Bărbie",
    "Barbă",
    "Geană",
    "Ciocănel",
    "Topor",
    "Patent",
    "Bormașină",
    "Burghiu",
    "Ruletă de măsurat",
    "Ghiveci",
    "Sapă",
    "Furtun",
    "Sămânță",
    "Tulpină",
    "Foarfecă",
)


# Every new node has exactly two local outgoing choices and one inbound legacy bridge.
# Each six-node local mesh is strongly connected and gives every member at least three
# distinct local neighbors.  Bridges point only from the mature graph into V32.
SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    # Visible face anatomy: twelve local links.
    EdgeSpec(
        "n_v32_body_face_buza",
        "n_v32_body_face_obraz",
        "near_part",
        "se află lângă obraz",
        0.97,
    ),
    EdgeSpec(
        "n_v32_body_face_buza",
        "n_v32_body_face_pleoapa",
        "movable_face_part",
        "este parte mobilă a feței, ca pleoapa",
        0.92,
    ),
    EdgeSpec(
        "n_v32_body_face_obraz",
        "n_v32_body_face_frunte",
        "near_part",
        "se află sub și lângă frunte",
        0.96,
    ),
    EdgeSpec(
        "n_v32_body_face_obraz",
        "n_v32_body_face_nara",
        "near_part",
        "se află lângă nară",
        0.97,
    ),
    EdgeSpec(
        "n_v32_body_face_frunte",
        "n_v32_body_face_spranceana",
        "above_part",
        "se află deasupra sprâncenei",
        0.99,
    ),
    EdgeSpec(
        "n_v32_body_face_frunte",
        "n_v32_body_face_pleoapa",
        "above_part",
        "se află deasupra pleoapei",
        0.97,
    ),
    EdgeSpec(
        "n_v32_body_face_spranceana",
        "n_v32_body_face_pleoapa",
        "above_part",
        "se află deasupra pleoapei",
        0.99,
    ),
    EdgeSpec(
        "n_v32_body_face_spranceana",
        "n_v32_body_face_nara",
        "near_part",
        "se află aproape de nară",
        0.95,
    ),
    EdgeSpec(
        "n_v32_body_face_pleoapa",
        "n_v32_body_face_nara",
        "near_part",
        "se află aproape de nară",
        0.96,
    ),
    EdgeSpec(
        "n_v32_body_face_pleoapa",
        "n_v32_body_face_obraz",
        "above_part",
        "se află deasupra obrazului",
        0.97,
    ),
    EdgeSpec(
        "n_v32_body_face_nara",
        "n_v32_body_face_buza",
        "above_part",
        "se află deasupra buzei",
        0.98,
    ),
    EdgeSpec(
        "n_v32_body_face_nara",
        "n_v32_body_face_spranceana",
        "below_part",
        "se află sub sprânceană",
        0.95,
    ),
    # Mature face anchors: six inbound-only bridges.
    EdgeSpec(
        "n_v24_body_face_gura",
        "n_v32_body_face_buza",
        "bounded_by",
        "este mărginită de buză",
        0.99,
    ),
    EdgeSpec(
        "n_v24_body_face_cap",
        "n_v32_body_face_obraz",
        "has_part",
        "are ca parte obrazul",
        0.99,
    ),
    EdgeSpec(
        "n_v24_body_face_cap",
        "n_v32_body_face_frunte",
        "has_part",
        "are ca parte fruntea",
        0.99,
    ),
    EdgeSpec(
        "n_v24_body_face_cap",
        "n_v32_body_face_nara",
        "has_part",
        "are pe față o nară",
        0.97,
    ),
    EdgeSpec(
        "n_v4sti_ochi",
        "n_v32_body_face_spranceana",
        "has_above",
        "are sprânceana deasupra",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_ochi",
        "n_v32_body_face_pleoapa",
        "protected_by",
        "este protejat de pleoapă",
        0.99,
    ),
    # Familiar workshop items: twelve local links.
    EdgeSpec(
        "n_v32_workshop_hand_ciocan",
        "n_v32_workshop_fastener_cui",
        "used_with",
        "se folosește pentru a bate cuiul",
        0.99,
    ),
    EdgeSpec(
        "n_v32_workshop_hand_ciocan",
        "n_v32_workshop_hand_cleste",
        "same_kind",
        "este unealtă de mână, ca cleștele",
        0.94,
    ),
    EdgeSpec(
        "n_v32_workshop_fastener_cui",
        "n_v32_workshop_fastener_surub",
        "same_kind",
        "este element de prindere, ca șurubul",
        0.96,
    ),
    EdgeSpec(
        "n_v32_workshop_fastener_cui",
        "n_v32_workshop_hand_cleste",
        "removed_with",
        "poate fi scos cu cleștele",
        0.97,
    ),
    EdgeSpec(
        "n_v32_workshop_fastener_surub",
        "n_v32_workshop_hand_surubelnita",
        "turned_with",
        "se rotește cu șurubelnița",
        0.99,
    ),
    EdgeSpec(
        "n_v32_workshop_fastener_surub",
        "n_v32_workshop_hand_cleste",
        "held_with",
        "poate fi prins cu cleștele",
        0.95,
    ),
    EdgeSpec(
        "n_v32_workshop_hand_surubelnita",
        "n_v32_workshop_hand_cleste",
        "same_kind",
        "este unealtă de mână, ca cleștele",
        0.94,
    ),
    EdgeSpec(
        "n_v32_workshop_hand_surubelnita",
        "n_v32_workshop_hand_ciocan",
        "same_kind",
        "este unealtă de mână, ca ciocanul",
        0.95,
    ),
    EdgeSpec(
        "n_v32_workshop_hand_cleste",
        "n_v32_workshop_cut_fierastrau",
        "same_kind",
        "este unealtă de mână, ca fierăstrăul",
        0.93,
    ),
    EdgeSpec(
        "n_v32_workshop_hand_cleste",
        "n_v32_workshop_fastener_cui",
        "grasps_fastener",
        "poate prinde și scoate cuiul",
        0.97,
    ),
    EdgeSpec(
        "n_v32_workshop_cut_fierastrau",
        "n_v32_workshop_hand_ciocan",
        "same_kind",
        "este unealtă de mână, ca ciocanul",
        0.94,
    ),
    EdgeSpec(
        "n_v32_workshop_cut_fierastrau",
        "n_v32_workshop_fastener_surub",
        "shares_woodwork_task",
        "se folosește la lucrări în care piesele sunt prinse cu șuruburi",
        0.92,
    ),
    # Mature workshop anchors: six inbound-only bridges.
    EdgeSpec(
        "n_v24_action_routine_a_lucra",
        "n_v32_workshop_hand_ciocan",
        "uses_tool",
        "poate folosi un ciocan",
        0.98,
    ),
    EdgeSpec(
        "n_v4sti_metal",
        "n_v32_workshop_fastener_cui",
        "material_for",
        "este material pentru cuie",
        0.98,
    ),
    EdgeSpec(
        "n_v24_action_routine_a_lucra",
        "n_v32_workshop_hand_surubelnita",
        "uses_tool",
        "poate folosi o șurubelniță",
        0.98,
    ),
    EdgeSpec(
        "n_v4sti_metal",
        "n_v32_workshop_fastener_surub",
        "material_for",
        "este material pentru șuruburi",
        0.98,
    ),
    EdgeSpec(
        "n_v24_action_routine_a_lucra",
        "n_v32_workshop_hand_cleste",
        "uses_tool",
        "poate folosi un clește",
        0.98,
    ),
    EdgeSpec(
        "n_v4sti_copac",
        "n_v32_workshop_cut_fierastrau",
        "cut_with",
        "lemnul său poate fi tăiat cu fierăstrăul",
        0.98,
    ),
    # Garden equipment: twelve local links.
    EdgeSpec(
        "n_v32_garden_container_ghiveci_flori",
        "n_v32_garden_water_stropitoare",
        "contents_watered_with",
        "plantele sale se udă cu stropitoarea",
        0.99,
    ),
    EdgeSpec(
        "n_v32_garden_container_ghiveci_flori",
        "n_v32_garden_soil_lopata",
        "filled_with",
        "se poate umple cu pământ folosind lopata",
        0.97,
    ),
    EdgeSpec(
        "n_v32_garden_water_stropitoare",
        "n_v32_garden_water_furtun",
        "same_watering_purpose",
        "udă plantele, ca furtunul de grădină",
        0.98,
    ),
    EdgeSpec(
        "n_v32_garden_water_stropitoare",
        "n_v32_garden_soil_grebla",
        "complements_task",
        "udă pământul îngrijit cu grebla",
        0.93,
    ),
    EdgeSpec(
        "n_v32_garden_water_furtun",
        "n_v32_garden_container_ghiveci_flori",
        "waters_contents",
        "poate uda plantele din ghiveci",
        0.98,
    ),
    EdgeSpec(
        "n_v32_garden_water_furtun",
        "n_v32_garden_water_stropitoare",
        "same_kind",
        "este unealtă pentru udat, ca stropitoarea",
        0.97,
    ),
    EdgeSpec(
        "n_v32_garden_soil_lopata",
        "n_v32_garden_soil_grebla",
        "same_soil_task",
        "pregătește pământul împreună cu grebla",
        0.97,
    ),
    EdgeSpec(
        "n_v32_garden_soil_lopata",
        "n_v32_garden_water_furtun",
        "prepares_before_watering",
        "pregătește pământul care apoi poate fi udat cu furtunul",
        0.93,
    ),
    EdgeSpec(
        "n_v32_garden_soil_grebla",
        "n_v32_garden_transport_roaba",
        "loads_into",
        "adună frunze care pot fi puse în roabă",
        0.97,
    ),
    EdgeSpec(
        "n_v32_garden_soil_grebla",
        "n_v32_garden_soil_lopata",
        "used_with",
        "se folosește împreună cu lopata",
        0.97,
    ),
    EdgeSpec(
        "n_v32_garden_transport_roaba",
        "n_v32_garden_container_ghiveci_flori",
        "carries_item",
        "poate transporta un ghiveci de flori",
        0.95,
    ),
    EdgeSpec(
        "n_v32_garden_transport_roaba",
        "n_v32_garden_water_stropitoare",
        "carries_item",
        "poate transporta o stropitoare",
        0.94,
    ),
    # Mature garden anchors: six inbound-only bridges.
    EdgeSpec(
        "n_v4sti_floare",
        "n_v32_garden_container_ghiveci_flori",
        "grows_in",
        "poate crește într-un ghiveci de flori",
        0.99,
    ),
    EdgeSpec(
        "n_v24_nature_world_pamant",
        "n_v32_garden_soil_lopata",
        "moved_with",
        "poate fi mutat cu lopata",
        0.99,
    ),
    EdgeSpec(
        "n_v24_home_outdoor_gradina",
        "n_v32_garden_soil_grebla",
        "maintained_with",
        "se îngrijește folosind grebla",
        0.98,
    ),
    EdgeSpec(
        "n_v4gas_apa",
        "n_v32_garden_water_stropitoare",
        "carried_in",
        "poate fi dusă într-o stropitoare",
        0.98,
    ),
    EdgeSpec(
        "n_v24_home_outdoor_gradina",
        "n_v32_garden_transport_roaba",
        "uses_tool",
        "poate fi îngrijită folosind roaba",
        0.96,
    ),
    EdgeSpec(
        "n_v4gas_apa",
        "n_v32_garden_water_furtun",
        "flows_through",
        "curge prin furtunul de grădină",
        0.99,
    ),
)

INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = tuple(
    (edge.source, edge.target) for edge in SEMANTIC_EDGES
)


def build_nodes_and_edges() -> dict[str, object]:
    nodes = [
        {
            "id": concept.node_id,
            "node_type": "concept",
            "label_ro": concept.label,
            "category": concept.category,
            "description": concept.description,
            "salience": concept.salience,
            "aliases": list(concept.aliases),
        }
        for concept in CONCEPTS
    ]
    edges = [
        {
            "src": edge.source,
            "dst": edge.target,
            "relation": edge.relation,
            "label_ro": edge.label_ro,
            "strength": edge.strength,
            "is_distractor": 0,
            "bidirectional": edge.bidirectional,
        }
        for edge in SEMANTIC_EDGES
    ]
    return {"nodes": nodes, "edges": edges, "aliases": {}}


def _reachable_within(
    start: str,
    allowed: set[str],
    adjacency: dict[str, set[str]],
) -> set[str]:
    reached: set[str] = set()
    pending = [start]
    while pending:
        current = pending.pop()
        if current in reached:
            continue
        reached.add(current)
        pending.extend(adjacency[current] & allowed - reached)
    return reached


def _validate_source() -> None:
    labels = [_norm(concept.label) for concept in CONCEPTS]
    aliases = [alias for concept in CONCEPTS for alias in concept.aliases]
    normalized_aliases = [_norm(alias) for alias in aliases]
    authored_surfaces = set(labels) | set(normalized_aliases)
    blocked = {_norm(alias) for alias in BLOCKED_ALIAS_FORMS}
    deferred = {_norm(term) for term in DEFERRED_AMBIGUOUS_TERMS}
    deferred_v31 = {_norm(term) for term in DEFERRED_V31_CONCEPTS}
    deferred_v32 = {_norm(term) for term in DEFERRED_V32_CONCEPTS}
    node_ids = set(NEW_NODE_IDS)
    local_neighbors: dict[str, set[str]] = defaultdict(set)
    local_adjacency: dict[str, set[str]] = defaultdict(set)
    local_outgoing: Counter[str] = Counter()
    incoming: Counter[str] = Counter()
    bridge_incoming: Counter[str] = Counter()
    legacy_new_neighbors: dict[str, set[str]] = defaultdict(set)
    edge_keys: set[tuple[str, str, str]] = set()
    directed_pairs: set[tuple[str, str]] = set()
    local_edges: list[EdgeSpec] = []
    legacy_bridges: list[EdgeSpec] = []
    for edge in SEMANTIC_EDGES:
        edge_keys.add((edge.source, edge.target, edge.relation))
        directed_pairs.add((edge.source, edge.target))
        incoming.update((edge.target,))
        if edge.source in node_ids:
            local_edges.append(edge)
            local_outgoing.update((edge.source,))
            local_adjacency[edge.source].add(edge.target)
            local_neighbors[edge.source].add(edge.target)
            local_neighbors[edge.target].add(edge.source)
        else:
            legacy_bridges.append(edge)
            bridge_incoming.update((edge.target,))
            legacy_new_neighbors[edge.source].add(edge.target)

    assert len(CONCEPTS) == len(node_ids) == len(labels) == len(set(labels)) == 18
    assert tuple(map(len, DOMAIN_NODE_IDS)) == (6, 6, 6)
    assert set().union(*(set(domain) for domain in DOMAIN_NODE_IDS)) == node_ids
    assert len(V32_BEGINNER_EXTENSION) == 18
    assert len(BEGINNER_BENCHMARK) == 306
    assert len({_norm(term) for term in BEGINNER_BENCHMARK}) == 306
    assert len(aliases) == len(normalized_aliases) == len(set(normalized_aliases)) == 69
    assert len(authored_surfaces) == 87
    assert not (set(labels) & set(normalized_aliases))
    assert not (authored_surfaces & blocked)
    assert not (authored_surfaces & deferred)
    assert not (authored_surfaces & deferred_v31)
    assert not (authored_surfaces & deferred_v32)
    assert len(BLOCKED_ALIAS_FORMS) == 43
    assert len(blocked) == 42
    assert len(DEFERRED_V32_CONCEPTS) == len(deferred_v32) == 31
    assert len(SEMANTIC_EDGES) == len(edge_keys) == len(directed_pairs) == 54
    assert len(local_edges) == 36
    assert len(legacy_bridges) == 18
    assert all(edge.target in node_ids for edge in SEMANTIC_EDGES)
    assert all(local_outgoing[node_id] == 2 for node_id in node_ids)
    assert all(incoming[node_id] >= 2 for node_id in node_ids)
    assert all(bridge_incoming[node_id] == 1 for node_id in node_ids)
    assert all(len(local_neighbors[node_id]) >= 3 for node_id in node_ids)
    assert len(legacy_new_neighbors) == 10
    assert sum(map(len, legacy_new_neighbors.values())) == 18
    assert max(map(len, legacy_new_neighbors.values())) <= 3
    for domain in DOMAIN_NODE_IDS:
        allowed = set(domain)
        assert all(
            _reachable_within(start, allowed, local_adjacency) == allowed for start in allowed
        )
    assert all(
        edge.source != edge.target
        and (edge.source in node_ids or edge.target in node_ids)
        and edge.relation != "related_to"
        and edge.label_ro.strip()
        and 0.85 <= edge.strength <= 1.0
        and edge.bidirectional == 0
        for edge in SEMANTIC_EDGES
    )
    assert len(REVIEW_ITEM_IDS) == len(set(REVIEW_ITEM_IDS)) == 33


_validate_source()
