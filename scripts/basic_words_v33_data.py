"""Audited source data for the v33 bathroom, electrical, and forest wave.

V33 adds concrete beginner vocabulary without serving a new game board. Exact,
conservative inflections stay owned by one concept, while three small directed
meshes provide semantic choices. Inbound-only legacy bridges make every new node
reachable without adding routes from the new content back into the mature graph.
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from basic_words_v32_data import BEGINNER_BENCHMARK as V32_BEGINNER_BENCHMARK
from basic_words_v32_data import (
    DEFERRED_AMBIGUOUS_TERMS,
    DEFERRED_V32_CONCEPTS,
    REVIEW_ITEM_IDS,
)

BUILD_VERSION = "fixture-v33-bathroom-electric-forest"
NOTE = (
    "v33: eighteen concrete beginner concepts across bathroom fixtures, home "
    "electrical equipment, and forest animals, with conservative inflections and "
    "explicit semantic links; no game boards or promotions."
)
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
GAME_ITEM_IDS: tuple[str, ...] = ()
V33_BEGINNER_EXTENSION: tuple[str, ...] = (
    "Chiuvetă",
    "Cadă de baie",
    "Robinet",
    "Vas de toaletă",
    "Hârtie igienică",
    "Halat de baie",
    "Bec",
    "Priză electrică",
    "Ștecher",
    "Întrerupător de lumină",
    "Prelungitor electric",
    "Cablu electric",
    "Urs",
    "Lup",
    "Vulpe",
    "Cerb",
    "Căprioară",
    "Veveriță",
)
BEGINNER_BENCHMARK = (*V32_BEGINNER_BENCHMARK, *V33_BEGINNER_EXTENSION)


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
        "".join(
            char for char in decomposed if not unicodedata.combining(char)
        ).casefold().split()
    )


CONCEPTS: tuple[ConceptSpec, ...] = (
    ConceptSpec(
        "n_v33_bathroom_fixture_chiuveta",
        "Chiuvetă",
        "viata_de_roman",
        0.94,
        "Recipient fix cu scurgere și robinet, folosit pentru spălat mâinile sau obiecte.",
        ("chiuvete", "chiuvetele", "chiuvetei"),
    ),
    ConceptSpec(
        "n_v33_bathroom_fixture_cada_baie",
        "Cadă de baie",
        "viata_de_roman",
        0.93,
        "Recipient mare din baie, umplut cu apă pentru spălarea corpului.",
        ("căzi de baie", "căzile de baie", "căzii de baie"),
    ),
    ConceptSpec(
        "n_v33_bathroom_fixture_robinet",
        "Robinet",
        "viata_de_roman",
        0.94,
        "Dispozitiv care deschide, oprește și reglează curgerea apei.",
        ("robinetul", "robinete", "robinetele", "robinetului"),
    ),
    ConceptSpec(
        "n_v33_bathroom_fixture_vas_toaleta",
        "Vas de toaletă",
        "viata_de_roman",
        0.94,
        "Obiect sanitar din baie, legat la rezervor și canalizare.",
        (
            "vasul de toaletă",
            "vase de toaletă",
            "vasele de toaletă",
            "vasului de toaletă",
        ),
    ),
    ConceptSpec(
        "n_v33_bathroom_supply_hartie_igienica",
        "Hârtie igienică",
        "viata_de_roman",
        0.93,
        "Produs moale din hârtie, folosit pentru igiena după folosirea toaletei.",
        (
            "hârtia igienică",
            "hârtii igienice",
            "hârtiile igienice",
            "hârtiei igienice",
        ),
    ),
    ConceptSpec(
        "n_v33_bathroom_clothing_halat_baie",
        "Halat de baie",
        "viata_de_roman",
        0.90,
        "Îmbrăcăminte largă purtată înainte sau după baie.",
        (
            "halatul de baie",
            "halate de baie",
            "halatele de baie",
            "halatului de baie",
        ),
    ),
    ConceptSpec(
        "n_v33_electric_light_bec",
        "Bec",
        "viata_de_roman",
        0.94,
        "Obiect care produce lumină când primește energie electrică.",
        ("becul", "becuri", "becurile", "becului"),
    ),
    ConceptSpec(
        "n_v33_electric_outlet_priza",
        "Priză electrică",
        "viata_de_roman",
        0.94,
        "Punct fix în care se introduce un ștecher pentru alimentarea unui aparat.",
        ("prize electrice", "prizele electrice", "prizei electrice"),
    ),
    ConceptSpec(
        "n_v33_electric_plug_stecher",
        "Ștecher",
        "viata_de_roman",
        0.93,
        "Piesă cu pini introdusă într-o priză electrică.",
        ("ștecherul", "ștechere", "ștecherele", "ștecherului"),
    ),
    ConceptSpec(
        "n_v33_electric_control_intrerupator",
        "Întrerupător de lumină",
        "viata_de_roman",
        0.94,
        "Dispozitiv care aprinde sau stinge lumina.",
        (
            "întrerupătorul de lumină",
            "întrerupătoare de lumină",
            "întrerupătoarele de lumină",
            "întrerupătorului de lumină",
        ),
    ),
    ConceptSpec(
        "n_v33_electric_extension_prelungitor",
        "Prelungitor electric",
        "viata_de_roman",
        0.91,
        "Cablu cu una sau mai multe prize care duce curentul mai departe.",
        (
            "prelungitorul electric",
            "prelungitoare electrice",
            "prelungitoarele electrice",
            "prelungitorului electric",
        ),
    ),
    ConceptSpec(
        "n_v33_electric_wire_cablu",
        "Cablu electric",
        "viata_de_roman",
        0.92,
        "Ansamblu de fire izolate care transportă energie electrică.",
        (
            "cablul electric",
            "cabluri electrice",
            "cablurile electrice",
            "cablului electric",
        ),
    ),
    ConceptSpec(
        "n_v33_forest_animal_urs",
        "Urs",
        "stiinta",
        0.94,
        "Mamifer mare de pădure, cu blană deasă și corp puternic.",
        ("ursul", "urși", "urșii", "ursului"),
    ),
    ConceptSpec(
        "n_v33_forest_animal_lup",
        "Lup",
        "stiinta",
        0.94,
        "Mamifer carnivor de pădure care trăiește și vânează adesea în haită.",
        ("lupul", "lupi", "lupii", "lupului"),
    ),
    ConceptSpec(
        "n_v33_forest_animal_vulpe",
        "Vulpe",
        "stiinta",
        0.93,
        "Mamifer de pădure cu bot ascuțit și coadă stufoasă.",
        ("vulpea", "vulpi", "vulpile", "vulpii"),
    ),
    ConceptSpec(
        "n_v33_forest_animal_cerb",
        "Cerb",
        "stiinta",
        0.92,
        "Mamifer erbivor de pădure, al cărui mascul are coarne ramificate.",
        ("cerbul", "cerbi", "cerbii", "cerbului"),
    ),
    ConceptSpec(
        "n_v33_forest_animal_caprioara",
        "Căprioară",
        "stiinta",
        0.93,
        "Mamifer erbivor suplu care trăiește în păduri și la marginea lor.",
        ("căprioare", "căprioarele", "căprioarei"),
    ),
    ConceptSpec(
        "n_v33_forest_animal_veverita",
        "Veveriță",
        "stiinta",
        0.93,
        "Mamifer mic cu coadă stufoasă, care se cațără în copaci.",
        ("veverițe", "veverițele", "veveriței"),
    ),
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)

BATHROOM_NODE_IDS: tuple[str, ...] = tuple(
    concept.node_id
    for concept in CONCEPTS
    if concept.node_id.startswith("n_v33_bathroom_")
)
ELECTRIC_NODE_IDS: tuple[str, ...] = tuple(
    concept.node_id
    for concept in CONCEPTS
    if concept.node_id.startswith("n_v33_electric_")
)
FOREST_NODE_IDS: tuple[str, ...] = tuple(
    concept.node_id
    for concept in CONCEPTS
    if concept.node_id.startswith("n_v33_forest_")
)
DOMAIN_NODE_IDS: tuple[tuple[str, ...], ...] = (
    BATHROOM_NODE_IDS,
    ELECTRIC_NODE_IDS,
    FOREST_NODE_IDS,
)


BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "lavoar",
    "chiuvetă de bucătărie",
    "cadă",
    "cada",
    "căzi",
    "căzile",
    "duș",
    "robinet de gaz",
    "toaletă",
    "toaleta",
    "WC",
    "closet",
    "hârtie",
    "șervețel",
    "halat",
    "halat medical",
    "uscător de păr",
    "covoraș de baie",
    "priză",
    "priza",
    "priză multiplă",
    "fișă",
    "întrerupător",
    "comutator",
    "prelungitor",
    "cablu",
    "fir",
    "beculeț",
    "lampă",
    "baterie",
    "lanternă",
    "ursoaică",
    "pui de urs",
    "lupoaică",
    "vulpoi",
    "cerboaică",
    "ren",
    "elan",
    "cerb lopătar",
    "veveriță zburătoare",
    "leu",
    "tigru",
    "elefant",
    "maimuță",
    "mistreț",
)
DEFERRED_V33_CONCEPTS: tuple[str, ...] = (
    *DEFERRED_V32_CONCEPTS,
    "Lavoar",
    "Cadă",
    "Uscător de păr",
    "Covoraș de baie",
    "Priză",
    "Întrerupător",
    "Prelungitor",
    "Cablu",
    "Baterie",
    "Lanternă",
    "Leu",
    "Tigru",
    "Elefant",
    "Maimuță",
    "Mistreț",
)


SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    # Bathroom: twelve local links.
    EdgeSpec(
        "n_v33_bathroom_fixture_chiuveta",
        "n_v33_bathroom_fixture_robinet",
        "fitted_with",
        "este prevăzută cu robinet",
        0.99,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_chiuveta",
        "n_v33_bathroom_fixture_cada_baie",
        "same_plumbing_fixture",
        "este obiect sanitar cu apă, ca cada de baie",
        0.96,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_robinet",
        "n_v33_bathroom_fixture_cada_baie",
        "fills_fixture",
        "poate umple cada de baie",
        0.99,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_robinet",
        "n_v33_bathroom_fixture_vas_toaleta",
        "shares_water_supply",
        "face parte din aceeași instalație de apă ca vasul de toaletă",
        0.94,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_cada_baie",
        "n_v33_bathroom_clothing_halat_baie",
        "used_before",
        "se folosește înainte de îmbrăcarea halatului de baie",
        0.98,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_cada_baie",
        "n_v33_bathroom_fixture_chiuveta",
        "shares_bathroom_setting",
        "se află în baie, ca chiuveta",
        0.95,
    ),
    EdgeSpec(
        "n_v33_bathroom_clothing_halat_baie",
        "n_v33_bathroom_fixture_vas_toaleta",
        "shares_bathroom_setting",
        "poate fi păstrat în baia unde se află vasul de toaletă",
        0.91,
    ),
    EdgeSpec(
        "n_v33_bathroom_clothing_halat_baie",
        "n_v33_bathroom_supply_hartie_igienica",
        "stored_in_same_room",
        "poate fi păstrat în baie, ca hârtia igienică",
        0.91,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_vas_toaleta",
        "n_v33_bathroom_supply_hartie_igienica",
        "used_with",
        "se folosește împreună cu hârtia igienică",
        0.99,
    ),
    EdgeSpec(
        "n_v33_bathroom_fixture_vas_toaleta",
        "n_v33_bathroom_fixture_robinet",
        "connected_to_water_supply",
        "este racordat la o instalație de apă, ca robinetul",
        0.95,
    ),
    EdgeSpec(
        "n_v33_bathroom_supply_hartie_igienica",
        "n_v33_bathroom_fixture_chiuveta",
        "shares_bathroom_setting",
        "se păstrează în baie, unde se află chiuveta",
        0.92,
    ),
    EdgeSpec(
        "n_v33_bathroom_supply_hartie_igienica",
        "n_v33_bathroom_clothing_halat_baie",
        "stored_with",
        "poate fi păstrată în baie, ca halatul de baie",
        0.91,
    ),
    # Bathroom: six inbound-only legacy bridges.
    EdgeSpec(
        "n_v4via_baie",
        "n_v33_bathroom_fixture_chiuveta",
        "contains_fixture",
        "poate conține o chiuvetă",
        0.99,
    ),
    EdgeSpec(
        "n_v4via_baie",
        "n_v33_bathroom_fixture_cada_baie",
        "contains_fixture",
        "poate conține o cadă de baie",
        0.99,
    ),
    EdgeSpec(
        "n_v4gas_apa",
        "n_v33_bathroom_fixture_robinet",
        "flows_through",
        "curge prin robinet",
        0.99,
    ),
    EdgeSpec(
        "n_v4soc_casa",
        "n_v33_bathroom_fixture_vas_toaleta",
        "contains_fixture",
        "poate conține un vas de toaletă",
        0.98,
    ),
    EdgeSpec(
        "n_v4via_baie",
        "n_v33_bathroom_supply_hartie_igienica",
        "contains_supply",
        "poate conține hârtie igienică",
        0.98,
    ),
    EdgeSpec(
        "n_v31_hygiene_bath_prosop",
        "n_v33_bathroom_clothing_halat_baie",
        "used_with",
        "se folosește după baie, ca halatul de baie",
        0.96,
    ),
    # Home electrical equipment: twelve local links.
    EdgeSpec(
        "n_v33_electric_light_bec",
        "n_v33_electric_control_intrerupator",
        "controlled_by",
        "este aprins și stins de întrerupătorul de lumină",
        0.99,
    ),
    EdgeSpec(
        "n_v33_electric_light_bec",
        "n_v33_electric_wire_cablu",
        "receives_power_through",
        "primește energie prin cablul electric",
        0.98,
    ),
    EdgeSpec(
        "n_v33_electric_control_intrerupator",
        "n_v33_electric_wire_cablu",
        "connected_by",
        "este legat prin cablu electric",
        0.98,
    ),
    EdgeSpec(
        "n_v33_electric_control_intrerupator",
        "n_v33_electric_light_bec",
        "controls",
        "aprinde și stinge becul",
        0.99,
    ),
    EdgeSpec(
        "n_v33_electric_wire_cablu",
        "n_v33_electric_plug_stecher",
        "terminates_in",
        "se poate termina cu un ștecher",
        0.98,
    ),
    EdgeSpec(
        "n_v33_electric_wire_cablu",
        "n_v33_electric_extension_prelungitor",
        "component_of",
        "este componentă a prelungitorului electric",
        0.99,
    ),
    EdgeSpec(
        "n_v33_electric_plug_stecher",
        "n_v33_electric_outlet_priza",
        "inserted_into",
        "se introduce în priza electrică",
        0.99,
    ),
    EdgeSpec(
        "n_v33_electric_plug_stecher",
        "n_v33_electric_extension_prelungitor",
        "component_of",
        "poate fi componentă a prelungitorului electric",
        0.97,
    ),
    EdgeSpec(
        "n_v33_electric_outlet_priza",
        "n_v33_electric_extension_prelungitor",
        "receives_plug_from",
        "primește ștecherul prelungitorului electric",
        0.99,
    ),
    EdgeSpec(
        "n_v33_electric_outlet_priza",
        "n_v33_electric_control_intrerupator",
        "shares_wiring_circuit",
        "face parte din instalația casei, ca întrerupătorul de lumină",
        0.95,
    ),
    EdgeSpec(
        "n_v33_electric_extension_prelungitor",
        "n_v33_electric_light_bec",
        "supplies_power_to",
        "poate alimenta o lampă cu bec",
        0.96,
    ),
    EdgeSpec(
        "n_v33_electric_extension_prelungitor",
        "n_v33_electric_outlet_priza",
        "plugs_into",
        "se conectează la priza electrică",
        0.99,
    ),
    # Home electrical equipment: six inbound-only legacy bridges.
    EdgeSpec(
        "n_v24_home_appliances_lampa",
        "n_v33_electric_light_bec",
        "contains_part",
        "conține un bec",
        0.99,
    ),
    EdgeSpec(
        "n_v3sti_electricitate",
        "n_v33_electric_outlet_priza",
        "available_through",
        "este disponibilă prin priza electrică",
        0.98,
    ),
    EdgeSpec(
        "n_v2sti_calculator",
        "n_v33_electric_plug_stecher",
        "powered_with",
        "poate fi alimentat printr-un ștecher",
        0.97,
    ),
    EdgeSpec(
        "n_v3sti_electricitate",
        "n_v33_electric_control_intrerupator",
        "controlled_with",
        "este controlată local prin întrerupător",
        0.97,
    ),
    EdgeSpec(
        "n_v4soc_casa",
        "n_v33_electric_extension_prelungitor",
        "contains_item",
        "poate conține un prelungitor electric",
        0.96,
    ),
    EdgeSpec(
        "n_v3sti_electricitate",
        "n_v33_electric_wire_cablu",
        "carried_by",
        "este transportată prin cablul electric",
        0.99,
    ),
    # Forest animals: twelve local links.
    EdgeSpec(
        "n_v33_forest_animal_urs",
        "n_v33_forest_animal_lup",
        "shares_forest_habitat",
        "trăiește în pădure, ca lupul",
        0.95,
    ),
    EdgeSpec(
        "n_v33_forest_animal_urs",
        "n_v33_forest_animal_vulpe",
        "shares_forest_habitat",
        "trăiește în pădure, ca vulpea",
        0.95,
    ),
    EdgeSpec(
        "n_v33_forest_animal_lup",
        "n_v33_forest_animal_vulpe",
        "shares_prey_type",
        "vânează animale mici, ca vulpea",
        0.94,
    ),
    EdgeSpec(
        "n_v33_forest_animal_lup",
        "n_v33_forest_animal_cerb",
        "hunts",
        "poate vâna cerbul",
        0.97,
    ),
    EdgeSpec(
        "n_v33_forest_animal_vulpe",
        "n_v33_forest_animal_veverita",
        "hunts",
        "poate vâna veverița",
        0.95,
    ),
    EdgeSpec(
        "n_v33_forest_animal_vulpe",
        "n_v33_forest_animal_caprioara",
        "shares_forest_habitat",
        "trăiește în aceeași pădure cu căprioara",
        0.94,
    ),
    EdgeSpec(
        "n_v33_forest_animal_veverita",
        "n_v33_forest_animal_caprioara",
        "shares_plant_food",
        "mănâncă părți de plante, ca și căprioara",
        0.93,
    ),
    EdgeSpec(
        "n_v33_forest_animal_veverita",
        "n_v33_forest_animal_urs",
        "shares_forest_food",
        "mănâncă fructe și semințe de pădure, ca ursul",
        0.92,
    ),
    EdgeSpec(
        "n_v33_forest_animal_caprioara",
        "n_v33_forest_animal_cerb",
        "same_family",
        "face parte din aceeași familie de animale ca cerbul",
        0.98,
    ),
    EdgeSpec(
        "n_v33_forest_animal_caprioara",
        "n_v33_forest_animal_lup",
        "prey_of",
        "poate fi vânată de lup",
        0.97,
    ),
    EdgeSpec(
        "n_v33_forest_animal_cerb",
        "n_v33_forest_animal_urs",
        "shares_forest_habitat",
        "trăiește în pădure, ca ursul",
        0.94,
    ),
    EdgeSpec(
        "n_v33_forest_animal_cerb",
        "n_v33_forest_animal_veverita",
        "shares_forest_habitat",
        "trăiește în pădure, ca veverița",
        0.93,
    ),
    # Forest animals: six inbound-only legacy bridges.
    EdgeSpec(
        "n_v4geo_padure",
        "n_v33_forest_animal_urs",
        "contains_animal",
        "poate adăposti ursul",
        0.99,
    ),
    EdgeSpec(
        "n_v4geo_padure",
        "n_v33_forest_animal_lup",
        "contains_animal",
        "poate adăposti lupul",
        0.99,
    ),
    EdgeSpec(
        "n_v4geo_padure",
        "n_v33_forest_animal_vulpe",
        "contains_animal",
        "poate adăposti vulpea",
        0.99,
    ),
    EdgeSpec(
        "n_v24_nature_plant_parts_iarba",
        "n_v33_forest_animal_cerb",
        "eaten_by",
        "poate fi mâncată de cerb",
        0.98,
    ),
    EdgeSpec(
        "n_v24_nature_plant_parts_iarba",
        "n_v33_forest_animal_caprioara",
        "eaten_by",
        "poate fi mâncată de căprioară",
        0.98,
    ),
    EdgeSpec(
        "n_v4sti_copac",
        "n_v33_forest_animal_veverita",
        "shelters_animal",
        "poate adăposti veverița",
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
        pending.extend((adjacency[current] & allowed) - reached)
    return reached


def _validate_source() -> None:
    labels = [_norm(concept.label) for concept in CONCEPTS]
    aliases = [alias for concept in CONCEPTS for alias in concept.aliases]
    normalized_aliases = [_norm(alias) for alias in aliases]
    authored_surfaces = set(labels) | set(normalized_aliases)
    blocked = {_norm(alias) for alias in BLOCKED_ALIAS_FORMS}
    deferred = {_norm(term) for term in DEFERRED_AMBIGUOUS_TERMS}
    deferred_v32 = {_norm(term) for term in DEFERRED_V32_CONCEPTS}
    deferred_v33 = {_norm(term) for term in DEFERRED_V33_CONCEPTS}
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
    assert len(V33_BEGINNER_EXTENSION) == 18
    assert len(BEGINNER_BENCHMARK) == 324
    assert len({_norm(term) for term in BEGINNER_BENCHMARK}) == 324
    assert len(aliases) == len(normalized_aliases) == len(set(normalized_aliases)) == 67
    assert len(authored_surfaces) == 85
    assert not (set(labels) & set(normalized_aliases))
    assert not (authored_surfaces & blocked)
    assert not (authored_surfaces & deferred)
    assert not (authored_surfaces & deferred_v32)
    assert not (authored_surfaces & deferred_v33)
    assert len(BLOCKED_ALIAS_FORMS) == 45
    assert len(blocked) == 42
    assert len(DEFERRED_V33_CONCEPTS) == len(deferred_v33) == 46
    assert deferred_v32 <= deferred_v33

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
            _reachable_within(start, allowed, local_adjacency) == allowed
            for start in allowed
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
