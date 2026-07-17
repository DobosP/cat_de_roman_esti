"""Audited source data for the v29 extended-basic-word wave.

The historical v24 benchmark remains unchanged.  This module adds a separate,
beginner-facing extension of seventeen concrete concepts, conservative Romanian
inflections, and explicit local semantic links.  It adds no game boards.
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from basic_words_v28_data import (
    BEGINNER_BENCHMARK as V28_BEGINNER_BENCHMARK,
)
from basic_words_v28_data import DEFERRED_AMBIGUOUS_TERMS, REVIEW_ITEM_IDS

BUILD_VERSION = "fixture-v29-extended-basic-words"
NOTE = (
    "v29: seventeen concrete beginner concepts, collision-safe Romanian inflections, "
    "and bounded explicit semantic links; no game boards or promotions."
)
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
GAME_ITEM_IDS: tuple[str, ...] = ()
V29_BEGINNER_EXTENSION: tuple[str, ...] = (
    "Câine",
    "Pisică",
    "Porc",
    "Găină",
    "Haină",
    "Cămașă",
    "Cuțit",
    "Pahar",
    "Gât",
    "Minut",
    "Secundă",
    "Noapte",
    "Weekend",
    "Calendar",
    "Cumpărături",
    "Coleg",
    "Trotuar",
)
BEGINNER_BENCHMARK = (*V28_BEGINNER_BENCHMARK, *V29_BEGINNER_EXTENSION)


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
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .casefold()
        .split()
    )


CONCEPTS: tuple[ConceptSpec, ...] = (
    ConceptSpec(
        "n_v29_animal_pets_caine",
        "Câine",
        "stiinta",
        0.94,
        "Animal domestic ținut adesea lângă oameni, cunoscut pentru lătrat.",
        ("câinele", "câini", "câinii", "câinelui"),
    ),
    ConceptSpec(
        "n_v29_animal_pets_pisica",
        "Pisică",
        "stiinta",
        0.94,
        "Animal domestic agil, cunoscut pentru tors și pentru vânătoarea șoarecilor.",
        ("pisici", "pisicile", "pisicii"),
    ),
    ConceptSpec(
        "n_v29_animal_farm_porc",
        "Porc",
        "stiinta",
        0.91,
        "Animal domestic cu rât, crescut în gospodării și ferme.",
        ("porcul", "porci", "porcii", "porcului"),
    ),
    ConceptSpec(
        "n_v29_animal_farm_gaina",
        "Găină",
        "stiinta",
        0.90,
        "Pasăre domestică crescută în gospodării, mai ales pentru ouă.",
        ("găini", "găinile", "găinii"),
    ),
    ConceptSpec(
        "n_v29_clothing_everyday_haina",
        "Haină",
        "viata_de_roman",
        0.93,
        "Obiect de îmbrăcăminte purtat pentru protecție, căldură sau aspect.",
        ("haine", "hainele", "hainei"),
    ),
    ConceptSpec(
        "n_v29_clothing_everyday_camasa",
        "Cămașă",
        "viata_de_roman",
        0.90,
        "Haină pentru partea de sus a corpului, de obicei cu guler și nasturi.",
        ("cămăși", "cămășile", "cămășii"),
    ),
    ConceptSpec(
        "n_v29_kitchen_table_cutit",
        "Cuțit",
        "gastronomie",
        0.92,
        "Unealtă cu lamă și mâner, folosită pentru a tăia alimente sau alte lucruri.",
        ("cuțitul", "cuțite", "cuțitele", "cuțitului"),
    ),
    ConceptSpec(
        "n_v29_kitchen_table_pahar",
        "Pahar",
        "gastronomie",
        0.92,
        "Recipient mic din care se beau apă și alte băuturi.",
        ("paharul", "pahare", "paharele", "paharului"),
    ),
    ConceptSpec(
        "n_v29_body_upper_gat",
        "Gât",
        "stiinta",
        0.93,
        "Parte a corpului care leagă capul de trunchi și prin care trec aerul și hrana.",
        ("gâtul", "gâturi", "gâturile", "gâtului"),
    ),
    ConceptSpec(
        "n_v29_time_units_minut",
        "Minut",
        "societate",
        0.94,
        "Unitate de timp egală cu șaizeci de secunde.",
        ("minutul", "minute", "minutele", "minutului"),
    ),
    ConceptSpec(
        "n_v29_time_units_secunda",
        "Secundă",
        "societate",
        0.93,
        "Unitate scurtă de timp; șaizeci de secunde formează un minut.",
        ("secunde", "secundele", "secundei"),
    ),
    ConceptSpec(
        "n_v29_time_daily_noapte",
        "Noapte",
        "societate",
        0.94,
        "Partea întunecată a zilei, dintre seară și dimineață.",
        ("noaptea", "nopți", "nopțile", "nopții"),
    ),
    ConceptSpec(
        "n_v29_time_weekly_weekend",
        "Weekend",
        "societate",
        0.91,
        "Zilele de la sfârșitul săptămânii, de obicei sâmbăta și duminica.",
        (
            "weekendul",
            "weekenduri",
            "weekendurile",
            "sfârșit de săptămână",
            "sfârșitul săptămânii",
        ),
    ),
    ConceptSpec(
        "n_v29_time_calendar",
        "Calendar",
        "societate",
        0.91,
        "Sistem sau obiect care arată zilele, lunile și datele unui an.",
        ("calendarul", "calendare", "calendarele", "calendarului"),
    ),
    ConceptSpec(
        "n_v29_routine_shopping_cumparaturi",
        "Cumpărături",
        "viata_de_roman",
        0.91,
        "Activitatea de a cumpăra lucrurile necesare din magazine sau piețe.",
        (
            "cumpărăturile",
            "la cumpărături",
            "mers la cumpărături",
            "a face cumpărături",
        ),
    ),
    ConceptSpec(
        "n_v29_people_coleg",
        "Coleg",
        "societate",
        0.93,
        "Persoană cu care cineva învață la școală sau lucrează.",
        ("colegul", "colegi", "colegii", "colegă", "colege", "colegele"),
    ),
    ConceptSpec(
        "n_v29_city_street_trotuar",
        "Trotuar",
        "geografie",
        0.90,
        "Parte ridicată a străzii rezervată mersului pe jos.",
        ("trotuarul", "trotuare", "trotuarele", "trotuarului"),
    ),
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)


# These ordinary forms have distinct senses or existing owners.  Keeping the boundary
# executable prevents a later alias sweep from making plausible guesses feel arbitrary.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "A tăia frunză la câini",
    "Clipuri cu pisici",
    "carne de porc",
    "tăiatul porcului",
    "Povestea porcului",
    "carne de găină",
    "Găina din curte",
    "hain",
    "haini",
    "ie",
    "bluză",
    "Chefi la cuțite",
    "briceag",
    "cană",
    "ceașcă",
    "gât de sticlă",
    "gâtul sticlei",
    "min",
    "sec",
    "O noapte furtunoasă",
    "Ultima noapte de dragoste, întâia noapte de război",
    "punte",
    "minivacanță",
    "dată",
    "agendă",
    "marfă",
    "produse",
    "prieten",
    "coechipier",
    "stradă",
    "pietonal",
    "parcare pe trotuar",
)
DEFERRED_V29_CONCEPTS: tuple[str, ...] = ("Somn", "Duș", "Pod", "Burtă", "Braț")


SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    # Familiar animals, with species/setting predicates instead of generic proximity.
    EdgeSpec("n_v29_animal_pets_caine", "n_v4sti_animal", "is_a", "este un animal", 0.99),
    EdgeSpec(
        "n_v29_animal_pets_caine",
        "n_v24_home_outdoor_curte",
        "may_live_in",
        "poate sta în curte",
        0.92,
    ),
    EdgeSpec(
        "n_v29_animal_pets_caine",
        "n_v29_animal_pets_pisica",
        "shares_pet_role",
        "poate fi animal de companie, ca pisica",
        0.90,
    ),
    EdgeSpec(
        "n_v4soc_copil", "n_v29_animal_pets_caine", "may_have_pet", "poate avea un câine", 0.94
    ),
    EdgeSpec("n_v29_animal_pets_pisica", "n_v4sti_animal", "is_a", "este un animal", 0.99),
    EdgeSpec(
        "n_v29_animal_pets_pisica",
        "n_v4soc_casa",
        "may_live_in",
        "poate locui în casă",
        0.94,
    ),
    EdgeSpec(
        "n_v4soc_copil",
        "n_v29_animal_pets_pisica",
        "may_have_pet",
        "poate avea o pisică",
        0.94,
    ),
    EdgeSpec("n_v29_animal_farm_porc", "n_v4sti_animal", "is_a", "este un animal", 0.99),
    EdgeSpec(
        "n_v29_animal_farm_porc",
        "n_v29_animal_farm_gaina",
        "shares_farm_habitat",
        "poate trăi în aceeași gospodărie cu găina",
        0.90,
    ),
    EdgeSpec(
        "n_v29_animal_farm_porc",
        "n_v4geo_sat",
        "raised_in",
        "este crescut în gospodării de la sat",
        0.91,
    ),
    EdgeSpec(
        "n_v24_home_outdoor_curte",
        "n_v29_animal_farm_porc",
        "may_house_animal",
        "în curte poate fi crescut un porc",
        0.90,
    ),
    EdgeSpec("n_v29_animal_farm_gaina", "n_v4sti_pasare", "is_a", "este o pasăre", 0.99),
    EdgeSpec(
        "n_v29_animal_farm_gaina", "n_v4gas_ou", "produces_food", "face ouă", 0.99
    ),
    EdgeSpec(
        "n_v29_animal_farm_gaina",
        "n_v24_home_outdoor_curte",
        "may_live_in",
        "poate trăi în curte",
        0.94,
    ),
    # Clothes and an everyday shopping loop.
    EdgeSpec(
        "n_v29_clothing_everyday_camasa",
        "n_v29_clothing_everyday_haina",
        "is_a",
        "este o haină",
        0.99,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_haina",
        "n_v24_home_storage_dulap",
        "stored_in",
        "se păstrează în dulap",
        0.97,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_haina",
        "n_v24_action_home_a_spala",
        "cleaned_by",
        "se curăță prin spălare",
        0.96,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_haina", "n_v4sti_corp", "worn_on", "se poartă pe corp", 0.99
    ),
    EdgeSpec(
        "n_v24_home_storage_dulap",
        "n_v29_clothing_everyday_camasa",
        "stores_item",
        "poate păstra o cămașă",
        0.96,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_camasa",
        "n_v24_action_home_a_spala",
        "cleaned_by",
        "se spală pentru a fi curată",
        0.96,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_camasa",
        "n_v3art_costum_popular",
        "part_of_outfit",
        "poate face parte dintr-un costum popular",
        0.94,
    ),
    # Kitchen and table objects.
    EdgeSpec(
        "n_v29_kitchen_table_cutit",
        "n_v4gas_bucatarie",
        "used_in_room",
        "se folosește în bucătărie",
        0.97,
    ),
    EdgeSpec(
        "n_v29_kitchen_table_cutit",
        "n_v4gas_mancare",
        "prepares_food",
        "se folosește la pregătirea mâncării",
        0.98,
    ),
    EdgeSpec(
        "n_v29_kitchen_table_cutit", "n_v4gas_paine", "cuts_food", "taie pâinea", 0.98
    ),
    EdgeSpec(
        "n_v4gas_masa",
        "n_v29_kitchen_table_cutit",
        "holds_utensil",
        "pe masă se poate pune un cuțit",
        0.93,
    ),
    EdgeSpec(
        "n_v29_kitchen_table_pahar",
        "n_v4gas_apa",
        "contains_drink",
        "poate conține apă",
        0.99,
    ),
    EdgeSpec(
        "n_v29_kitchen_table_pahar",
        "n_v4gas_lapte",
        "contains_drink",
        "poate conține lapte",
        0.97,
    ),
    EdgeSpec(
        "n_v29_kitchen_table_pahar", "n_v4gas_masa", "placed_on", "se pune pe masă", 0.98
    ),
    EdgeSpec(
        "n_v4gas_bucatarie",
        "n_v29_kitchen_table_pahar",
        "stores_item",
        "în bucătărie se păstrează pahare",
        0.94,
    ),
    # Anatomy.
    EdgeSpec(
        "n_v29_body_upper_gat", "n_v4sti_corp", "part_of_body", "este parte a corpului", 0.99
    ),
    EdgeSpec(
        "n_v29_body_upper_gat",
        "n_v24_body_face_cap",
        "supports_body_part",
        "susține capul",
        0.98,
    ),
    EdgeSpec(
        "n_v29_body_upper_gat",
        "n_v24_body_face_gura",
        "anatomical_neighbor",
        "se află sub gură",
        0.95,
    ),
    EdgeSpec(
        "n_v3per_medic",
        "n_v29_body_upper_gat",
        "examines_body_part",
        "poate examina gâtul",
        0.97,
    ),
    # Concrete units and periods of time.
    EdgeSpec(
        "n_v29_time_units_minut",
        "n_v24_time_day_ora",
        "part_of_time",
        "șaizeci de minute alcătuiesc o oră",
        0.99,
    ),
    EdgeSpec(
        "n_v29_time_units_minut",
        "n_v29_time_units_secunda",
        "has_part_time",
        "are șaizeci de secunde",
        0.99,
    ),
    EdgeSpec(
        "n_v29_time_units_minut",
        "n_v24_time_day_zi",
        "part_of_time",
        "este o unitate dintr-o zi",
        0.96,
    ),
    EdgeSpec(
        "n_v24_time_day_ceas",
        "n_v29_time_units_minut",
        "displays_unit",
        "indică minutele",
        0.98,
    ),
    EdgeSpec(
        "n_v29_time_units_secunda",
        "n_v24_time_day_ora",
        "part_of_time",
        "este o unitate mai mică decât ora",
        0.95,
    ),
    EdgeSpec(
        "n_v29_time_units_secunda",
        "n_v24_time_day_ceas",
        "measured_by",
        "este măsurată de ceas",
        0.97,
    ),
    EdgeSpec(
        "n_v4spo_alergare",
        "n_v29_time_units_secunda",
        "timed_in",
        "poate fi cronometrată în secunde",
        0.96,
    ),
    EdgeSpec(
        "n_v29_time_daily_noapte",
        "n_v24_time_day_zi",
        "part_of_time",
        "este partea întunecată a zilei",
        0.99,
    ),
    EdgeSpec(
        "n_v29_time_daily_noapte",
        "n_v24_action_routine_a_dormi",
        "usual_time_for",
        "este timpul obișnuit pentru somn",
        0.97,
    ),
    EdgeSpec(
        "n_v29_time_daily_noapte",
        "n_v24_nature_sky_luna",
        "sky_object_visible",
        "luna se vede adesea noaptea",
        0.96,
    ),
    EdgeSpec(
        "n_v28_time_calendar_saptamana",
        "n_v29_time_daily_noapte",
        "has_part_time",
        "cuprinde șapte nopți",
        0.98,
    ),
    EdgeSpec(
        "n_v29_time_weekly_weekend",
        "n_v28_time_calendar_saptamana",
        "part_of_time",
        "este sfârșitul săptămânii",
        0.99,
    ),
    EdgeSpec(
        "n_v29_time_weekly_weekend",
        "n_v4soc_familie",
        "spent_with",
        "poate fi petrecut cu familia",
        0.91,
    ),
    EdgeSpec(
        "n_v29_time_weekly_weekend",
        "n_v24_action_movement_a_se_juca",
        "usual_time_for",
        "oferă timp pentru joacă",
        0.92,
    ),
    EdgeSpec(
        "n_v21via_minivacanta",
        "n_v29_time_weekly_weekend",
        "may_include",
        "poate include un weekend",
        0.96,
    ),
    EdgeSpec(
        "n_v29_time_calendar",
        "n_v28_time_calendar_luna_calendaristica",
        "organizes_time",
        "organizează lunile calendaristice",
        0.98,
    ),
    EdgeSpec(
        "n_v29_time_calendar", "n_v4ist_an", "organizes_time", "arată zilele unui an", 0.98
    ),
    EdgeSpec(
        "n_v29_time_calendar",
        "n_v28_time_calendar_saptamana",
        "organizes_time",
        "grupează zilele în săptămâni",
        0.97,
    ),
    EdgeSpec(
        "n_v24_time_day_zi",
        "n_v29_time_calendar",
        "shown_in",
        "este înscrisă în calendar",
        0.98,
    ),
    # Shopping stays grounded in familiar objects and places.
    EdgeSpec(
        "n_v29_routine_shopping_cumparaturi",
        "n_v29_clothing_everyday_haina",
        "may_include",
        "pot include o haină",
        0.94,
    ),
    EdgeSpec(
        "n_v29_routine_shopping_cumparaturi",
        "n_v29_clothing_everyday_camasa",
        "may_include",
        "pot include o cămașă",
        0.94,
    ),
    EdgeSpec(
        "n_v29_routine_shopping_cumparaturi",
        "n_v18via_mersul_la_mall",
        "includes_activity",
        "pot include mersul la mall",
        0.96,
    ),
    EdgeSpec(
        "n_v4soc_magazin",
        "n_v29_routine_shopping_cumparaturi",
        "enables_activity",
        "este un loc pentru cumpărături",
        0.99,
    ),
    # School/work peers and the pedestrian street layer.
    EdgeSpec(
        "n_v29_people_coleg",
        "n_v4soc_serviciu",
        "peer_context",
        "poate fi coleg de serviciu",
        0.98,
    ),
    EdgeSpec(
        "n_v29_people_coleg",
        "n_v3soc_scoala",
        "peer_context",
        "poate fi coleg de școală",
        0.98,
    ),
    EdgeSpec(
        "n_v29_people_coleg",
        "n_v4soc_elev",
        "peer_role",
        "poate fi elev, ca alt coleg de clasă",
        0.96,
    ),
    EdgeSpec(
        "n_v4per_profesor",
        "n_v29_people_coleg",
        "peer_role",
        "poate avea colegi profesori",
        0.94,
    ),
    EdgeSpec(
        "n_v29_city_street_trotuar",
        "n_v4geo_strada",
        "borders_road",
        "mărginește strada",
        0.99,
    ),
    EdgeSpec(
        "n_v29_city_street_trotuar",
        "n_v2geo_oras",
        "located_in",
        "este amenajat în oraș",
        0.96,
    ),
    EdgeSpec(
        "n_v4per_om",
        "n_v29_city_street_trotuar",
        "walks_on",
        "merge pe trotuar",
        0.98,
    ),
    EdgeSpec(
        "n_v4soc_copil",
        "n_v29_city_street_trotuar",
        "walks_on",
        "merge pe trotuar",
        0.98,
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


def _validate_source() -> None:
    labels = [_norm(concept.label) for concept in CONCEPTS]
    aliases = [alias for concept in CONCEPTS for alias in concept.aliases]
    normalized_aliases = [_norm(alias) for alias in aliases]
    authored_surfaces = set(labels) | set(normalized_aliases)
    blocked = {_norm(alias) for alias in BLOCKED_ALIAS_FORMS}
    deferred = {_norm(term) for term in DEFERRED_AMBIGUOUS_TERMS}
    deferred_v29 = {_norm(term) for term in DEFERRED_V29_CONCEPTS}
    node_ids = set(NEW_NODE_IDS)
    neighbors: dict[str, set[str]] = defaultdict(set)
    outgoing: Counter[str] = Counter()
    incoming: Counter[str] = Counter()
    legacy_new_neighbors: dict[str, set[str]] = defaultdict(set)
    edge_keys: set[tuple[str, str, str]] = set()
    for edge in SEMANTIC_EDGES:
        neighbors[edge.source].add(edge.target)
        neighbors[edge.target].add(edge.source)
        outgoing.update((edge.source,))
        incoming.update((edge.target,))
        edge_keys.add((edge.source, edge.target, edge.relation))
        if edge.source not in node_ids and edge.target in node_ids:
            legacy_new_neighbors[edge.source].add(edge.target)
        if edge.target not in node_ids and edge.source in node_ids:
            legacy_new_neighbors[edge.target].add(edge.source)

    assert len(CONCEPTS) == len(node_ids) == len(labels) == len(set(labels)) == 17
    assert len(V29_BEGINNER_EXTENSION) == 17
    assert len(BEGINNER_BENCHMARK) == 253
    assert len({_norm(term) for term in BEGINNER_BENCHMARK}) == 253
    assert len(aliases) == len(normalized_aliases) == len(set(normalized_aliases)) == 66
    assert len(authored_surfaces) == 83
    assert not (set(labels) & set(normalized_aliases))
    assert not (authored_surfaces & blocked)
    assert not (authored_surfaces & deferred)
    assert not (authored_surfaces & deferred_v29)
    assert len(DEFERRED_V29_CONCEPTS) == len(deferred_v29) == 5
    assert len(SEMANTIC_EDGES) == len(edge_keys) == 64
    assert all(len(neighbors[node_id]) >= 4 for node_id in node_ids)
    assert all(outgoing[node_id] >= 2 for node_id in node_ids)
    assert all(incoming[node_id] >= 1 for node_id in node_ids)
    assert max(map(len, legacy_new_neighbors.values())) <= 3
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
