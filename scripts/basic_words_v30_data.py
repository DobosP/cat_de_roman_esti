"""Audited source data for the v30 farm, wardrobe, and kitchen word wave.

V30 extends the beginner probe without rewriting the completed v24 or v29
denominators.  It adds concrete first-class concepts, conservative Romanian
inflections, and explicit local semantic links; it adds no game boards.
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from basic_words_v29_data import (
    BEGINNER_BENCHMARK as V29_BEGINNER_BENCHMARK,
)
from basic_words_v29_data import DEFERRED_AMBIGUOUS_TERMS, REVIEW_ITEM_IDS

BUILD_VERSION = "fixture-v30-farm-wardrobe-kitchen"
NOTE = (
    "v30: eighteen concrete beginner concepts across farm animals, clothing, and "
    "kitchen/table items, with conservative inflections and explicit semantic links; "
    "no game boards or promotions."
)
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
GAME_ITEM_IDS: tuple[str, ...] = ()
V30_BEGINNER_EXTENSION: tuple[str, ...] = (
    "Vacă",
    "Cal",
    "Oaie",
    "Capră",
    "Iepure",
    "Pantaloni",
    "Rochie",
    "Fustă",
    "Pantof",
    "Șosetă",
    "Geacă",
    "Farfurie",
    "Lingură",
    "Furculiță",
    "Oală",
    "Tigaie",
    "Cană",
    "Castron",
)
BEGINNER_BENCHMARK = (*V29_BEGINNER_BENCHMARK, *V30_BEGINNER_EXTENSION)


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
        "n_v30_animal_farm_vaca",
        "Vacă",
        "stiinta",
        0.93,
        "Animal domestic mare, crescut în gospodării și ferme mai ales pentru lapte.",
        ("vaci", "vacile", "vacii"),
    ),
    ConceptSpec(
        "n_v30_animal_farm_cal",
        "Cal",
        "stiinta",
        0.93,
        "Animal domestic puternic, folosit la călărie și uneori la muncă.",
        ("calul", "calului"),
    ),
    ConceptSpec(
        "n_v30_animal_farm_oaie",
        "Oaie",
        "stiinta",
        0.91,
        "Animal domestic crescut în turme pentru lână, lapte și hrană.",
        ("oaia", "oile", "oii"),
    ),
    ConceptSpec(
        "n_v30_animal_farm_capra",
        "Capră",
        "stiinta",
        0.90,
        "Animal domestic agil, cu coarne, crescut adesea pentru lapte.",
        ("capre", "caprele", "caprei"),
    ),
    ConceptSpec(
        "n_v30_animal_field_iepure",
        "Iepure",
        "stiinta",
        0.92,
        "Animal cu urechi lungi și picioare puternice, care se mișcă prin salturi.",
        ("iepurele", "iepuri", "iepurii", "iepurelui"),
    ),
    ConceptSpec(
        "n_v30_clothing_everyday_pantaloni",
        "Pantaloni",
        "viata_de_roman",
        0.94,
        "Haină purtată de la talie în jos, cu câte o parte pentru fiecare picior.",
        ("pantalon", "pantalonul", "pantalonii", "pantalonilor"),
    ),
    ConceptSpec(
        "n_v30_clothing_everyday_rochie",
        "Rochie",
        "viata_de_roman",
        0.92,
        "Haină dintr-o singură piesă care acoperă trunchiul și o parte din picioare.",
        ("rochia", "rochii", "rochiile", "rochiei"),
    ),
    ConceptSpec(
        "n_v30_clothing_everyday_fusta",
        "Fustă",
        "viata_de_roman",
        0.91,
        "Haină purtată de la talie în jos, fără părți separate pentru picioare.",
        ("fuste", "fustele", "fustei"),
    ),
    ConceptSpec(
        "n_v30_clothing_footwear_pantof",
        "Pantof",
        "viata_de_roman",
        0.93,
        "Obiect de încălțăminte care protejează laba piciorului.",
        ("pantoful", "pantofi", "pantofii", "pantofului"),
    ),
    ConceptSpec(
        "n_v30_clothing_footwear_soseta",
        "Șosetă",
        "viata_de_roman",
        0.92,
        "Piesă moale de îmbrăcăminte purtată pe picior, în interiorul pantofului.",
        ("șosete", "șosetele", "șosetei"),
    ),
    ConceptSpec(
        "n_v30_clothing_outer_geaca",
        "Geacă",
        "viata_de_roman",
        0.92,
        "Haină scurtă purtată peste alte haine pentru protecție și căldură.",
        ("geci", "gecile", "gecii"),
    ),
    ConceptSpec(
        "n_v30_kitchen_table_farfurie",
        "Farfurie",
        "gastronomie",
        0.94,
        "Vas plat din care se servește și se mănâncă mâncarea.",
        ("farfuria", "farfurii", "farfuriile", "farfuriei"),
    ),
    ConceptSpec(
        "n_v30_kitchen_utensil_lingura",
        "Lingură",
        "gastronomie",
        0.94,
        "Ustensilă cu mâner și cap adâncit, folosită pentru a lua mâncare lichidă.",
        ("linguri", "lingurile", "lingurii"),
    ),
    ConceptSpec(
        "n_v30_kitchen_utensil_furculita",
        "Furculiță",
        "gastronomie",
        0.93,
        "Ustensilă cu mâner și dinți, folosită pentru a prinde bucăți de mâncare.",
        ("furculițe", "furculițele", "furculiței"),
    ),
    ConceptSpec(
        "n_v30_kitchen_cookware_oala",
        "Oală",
        "gastronomie",
        0.93,
        "Vas adânc folosit pe aragaz pentru a fierbe și a găti mâncare.",
        ("oale", "oalele", "oalei"),
    ),
    ConceptSpec(
        "n_v30_kitchen_cookware_tigaie",
        "Tigaie",
        "gastronomie",
        0.93,
        "Vas de gătit puțin adânc, cu mâner, folosit mai ales pentru prăjire.",
        ("tigaia", "tigăi", "tigăile", "tigăii"),
    ),
    ConceptSpec(
        "n_v30_kitchen_drink_cana",
        "Cană",
        "gastronomie",
        0.93,
        "Recipient cu toartă din care se beau apă, lapte, ceai sau alte băuturi.",
        ("căni", "cănile", "cănii"),
    ),
    ConceptSpec(
        "n_v30_kitchen_table_castron",
        "Castron",
        "gastronomie",
        0.91,
        "Vas adânc folosit pentru a servi supă, cereale sau alte alimente.",
        ("castronul", "castroane", "castroanele", "castronului"),
    ),
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)


# These forms are mechanically tempting but would merge a different ordinary sense or
# a neighboring concept. Feminine definite forms that normalize to their base label are
# intentionally omitted as redundant rather than listed here.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "cai",
    "căi",
    "caii",
    "căii",
    "cailor",
    "căilor",
    "oi",
    "vită",
    "armăsar",
    "miel",
    "ied",
    "iepuraș",
    "blugi",
    "încălțăminte",
    "ciorap",
    "jachetă",
    "ie",
    "vas",
    "bol",
    "cratiță",
    "ceașcă",
    "pahar",
)
DEFERRED_V30_CONCEPTS: tuple[str, ...] = ("Duș", "Pod", "Spate", "Umăr")


# The three compact local meshes give every word several meaningful routes.  Every
# legacy bridge points into a mesh and no edge returns to the legacy graph: the new
# targets inherit mature inbound reachability without creating an old-to-old shortcut.
SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    # Farm animals.
    EdgeSpec(
        "n_v30_animal_farm_vaca",
        "n_v30_animal_farm_oaie",
        "shares_farm_setting",
        "este crescută în gospodărie, ca oaia",
        0.94,
    ),
    EdgeSpec(
        "n_v30_animal_farm_oaie",
        "n_v30_animal_farm_capra",
        "shares_diet",
        "mănâncă plante, ca și capra",
        0.94,
    ),
    EdgeSpec(
        "n_v30_animal_farm_capra",
        "n_v30_animal_farm_cal",
        "shares_farm_setting",
        "poate fi crescută la fermă, ca și calul",
        0.93,
    ),
    EdgeSpec(
        "n_v30_animal_farm_cal",
        "n_v30_animal_field_iepure",
        "same_kind",
        "este mamifer, ca și iepurele",
        0.95,
    ),
    EdgeSpec(
        "n_v30_animal_field_iepure",
        "n_v30_animal_farm_vaca",
        "same_kind",
        "este mamifer, ca și vaca",
        0.95,
    ),
    EdgeSpec(
        "n_v30_animal_farm_vaca",
        "n_v30_animal_farm_capra",
        "produces_same_food",
        "poate da lapte, ca și capra",
        0.97,
    ),
    EdgeSpec(
        "n_v30_animal_farm_oaie",
        "n_v30_animal_farm_cal",
        "shares_farm_setting",
        "poate fi crescută la fermă, ca și calul",
        0.93,
    ),
    EdgeSpec(
        "n_v30_animal_field_iepure",
        "n_v30_animal_farm_oaie",
        "shares_diet",
        "mănâncă plante, ca și oaia",
        0.94,
    ),
    EdgeSpec(
        "n_v30_animal_farm_cal",
        "n_v30_animal_farm_vaca",
        "shares_farm_setting",
        "poate fi crescut la fermă, ca și vaca",
        0.94,
    ),
    EdgeSpec(
        "n_v30_animal_farm_capra",
        "n_v30_animal_field_iepure",
        "shares_diet",
        "mănâncă plante, ca și iepurele",
        0.94,
    ),
    EdgeSpec(
        "n_v4sti_animal",
        "n_v30_animal_farm_vaca",
        "has_kind",
        "vaca este un tip de animal",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_animal",
        "n_v30_animal_farm_cal",
        "has_kind",
        "calul este un tip de animal",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_animal",
        "n_v30_animal_farm_oaie",
        "has_kind",
        "oaia este un tip de animal",
        0.99,
    ),
    EdgeSpec(
        "n_v24_nature_plant_parts_iarba",
        "n_v30_animal_farm_capra",
        "eaten_by",
        "poate fi mâncată de capră",
        0.98,
    ),
    EdgeSpec(
        "n_v24_food_salad_veg_morcov",
        "n_v30_animal_field_iepure",
        "eaten_by",
        "poate fi mâncat de iepure",
        0.98,
    ),
    # Clothing.
    EdgeSpec(
        "n_v30_clothing_everyday_pantaloni",
        "n_v30_clothing_footwear_soseta",
        "worn_with",
        "se pot purta împreună cu șosete",
        0.94,
    ),
    EdgeSpec(
        "n_v30_clothing_footwear_soseta",
        "n_v30_clothing_outer_geaca",
        "shares_cold_weather_use",
        "poate ține de cald, ca geaca",
        0.91,
    ),
    EdgeSpec(
        "n_v30_clothing_outer_geaca",
        "n_v30_clothing_everyday_rochie",
        "worn_over",
        "se poate purta peste o rochie",
        0.95,
    ),
    EdgeSpec(
        "n_v30_clothing_everyday_rochie",
        "n_v30_clothing_footwear_pantof",
        "worn_with",
        "se poate purta cu pantofi",
        0.96,
    ),
    EdgeSpec(
        "n_v30_clothing_footwear_pantof",
        "n_v30_clothing_everyday_fusta",
        "worn_with",
        "se poate purta cu o fustă",
        0.94,
    ),
    EdgeSpec(
        "n_v30_clothing_everyday_fusta",
        "n_v30_clothing_everyday_pantaloni",
        "shares_body_area",
        "acoperă partea de jos a corpului, ca pantalonii",
        0.95,
    ),
    EdgeSpec(
        "n_v30_clothing_everyday_pantaloni",
        "n_v30_clothing_outer_geaca",
        "worn_with",
        "se pot purta împreună cu o geacă",
        0.95,
    ),
    EdgeSpec(
        "n_v30_clothing_footwear_soseta",
        "n_v30_clothing_footwear_pantof",
        "worn_inside",
        "se poartă în pantof",
        0.99,
    ),
    EdgeSpec(
        "n_v30_clothing_everyday_rochie",
        "n_v30_clothing_everyday_fusta",
        "same_kind",
        "este o haină, ca fusta",
        0.96,
    ),
    EdgeSpec(
        "n_v30_clothing_outer_geaca",
        "n_v30_clothing_footwear_pantof",
        "worn_with",
        "se poate purta împreună cu pantofi",
        0.94,
    ),
    EdgeSpec(
        "n_v30_clothing_footwear_pantof",
        "n_v30_clothing_everyday_pantaloni",
        "worn_with",
        "se poate purta împreună cu pantaloni",
        0.94,
    ),
    EdgeSpec(
        "n_v30_clothing_everyday_fusta",
        "n_v30_clothing_footwear_soseta",
        "worn_with",
        "se poate purta împreună cu șosete",
        0.93,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_haina",
        "n_v30_clothing_everyday_pantaloni",
        "has_kind",
        "pantalonii sunt un tip de haină",
        0.99,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_haina",
        "n_v30_clothing_everyday_rochie",
        "has_kind",
        "rochia este un tip de haină",
        0.99,
    ),
    EdgeSpec(
        "n_v29_clothing_everyday_haina",
        "n_v30_clothing_everyday_fusta",
        "has_kind",
        "fusta este un tip de haină",
        0.99,
    ),
    EdgeSpec(
        "n_v4soc_magazin",
        "n_v30_clothing_footwear_pantof",
        "sells_item",
        "poate vinde pantofi",
        0.97,
    ),
    EdgeSpec(
        "n_v24_action_home_a_spala",
        "n_v30_clothing_footwear_soseta",
        "cleans_item",
        "poate curăța o șosetă",
        0.97,
    ),
    EdgeSpec(
        "n_v24_home_storage_dulap",
        "n_v30_clothing_outer_geaca",
        "stores_item",
        "poate păstra o geacă",
        0.98,
    ),
    # Kitchen and table items.
    EdgeSpec(
        "n_v30_kitchen_drink_cana",
        "n_v30_kitchen_table_farfurie",
        "placed_with",
        "se pune pe masă lângă farfurie",
        0.94,
    ),
    EdgeSpec(
        "n_v30_kitchen_table_farfurie",
        "n_v30_kitchen_cookware_tigaie",
        "receives_food_from",
        "primește mâncarea gătită în tigaie",
        0.96,
    ),
    EdgeSpec(
        "n_v30_kitchen_cookware_tigaie",
        "n_v30_kitchen_cookware_oala",
        "same_kind",
        "este vas de gătit, ca oala",
        0.97,
    ),
    EdgeSpec(
        "n_v30_kitchen_cookware_oala",
        "n_v30_kitchen_table_castron",
        "serves_into",
        "mâncarea din oală se poate servi în castron",
        0.97,
    ),
    EdgeSpec(
        "n_v30_kitchen_table_castron",
        "n_v30_kitchen_utensil_furculita",
        "used_with",
        "poate fi folosit cu furculița",
        0.93,
    ),
    EdgeSpec(
        "n_v30_kitchen_utensil_furculita",
        "n_v30_kitchen_utensil_lingura",
        "same_kind",
        "este tacâm, ca lingura",
        0.98,
    ),
    EdgeSpec(
        "n_v30_kitchen_utensil_lingura",
        "n_v30_kitchen_drink_cana",
        "used_with",
        "amestecă o băutură în cană",
        0.96,
    ),
    EdgeSpec(
        "n_v30_kitchen_drink_cana",
        "n_v30_kitchen_table_castron",
        "shares_container_role",
        "este recipient, ca și castronul",
        0.92,
    ),
    EdgeSpec(
        "n_v30_kitchen_table_farfurie",
        "n_v30_kitchen_utensil_furculita",
        "used_with",
        "se folosește împreună cu furculița",
        0.98,
    ),
    EdgeSpec(
        "n_v30_kitchen_utensil_lingura",
        "n_v30_kitchen_cookware_oala",
        "used_in",
        "se folosește la amestecarea mâncării din oală",
        0.97,
    ),
    EdgeSpec(
        "n_v30_kitchen_utensil_furculita",
        "n_v30_kitchen_cookware_tigaie",
        "moves_cooked_food",
        "poate lua mâncare din tigaie",
        0.93,
    ),
    EdgeSpec(
        "n_v30_kitchen_cookware_tigaie",
        "n_v30_kitchen_table_castron",
        "serves_into",
        "mâncarea din tigaie se poate servi în castron",
        0.95,
    ),
    EdgeSpec(
        "n_v30_kitchen_cookware_oala",
        "n_v30_kitchen_table_farfurie",
        "serves_into",
        "mâncarea din oală se poate pune în farfurie",
        0.95,
    ),
    EdgeSpec(
        "n_v30_kitchen_table_castron",
        "n_v30_kitchen_utensil_lingura",
        "used_with",
        "se folosește împreună cu lingura",
        0.97,
    ),
    EdgeSpec(
        "n_v4gas_masa",
        "n_v30_kitchen_table_farfurie",
        "holds_tableware",
        "pe masă se poate pune o farfurie",
        0.99,
    ),
    EdgeSpec(
        "n_v4gas_supa",
        "n_v30_kitchen_utensil_lingura",
        "eaten_with",
        "se mănâncă folosind lingura",
        0.99,
    ),
    EdgeSpec(
        "n_v4gas_mancare",
        "n_v30_kitchen_utensil_furculita",
        "eaten_with",
        "se poate mânca folosind furculița",
        0.98,
    ),
    EdgeSpec(
        "n_v4gas_bucatarie",
        "n_v30_kitchen_cookware_oala",
        "stores_item",
        "în bucătărie se păstrează oale",
        0.98,
    ),
    EdgeSpec(
        "n_v24_home_appliances_aragaz",
        "n_v30_kitchen_cookware_tigaie",
        "heats_cookware",
        "poate încălzi o tigaie",
        0.99,
    ),
    EdgeSpec(
        "n_v24_food_snack_ceai",
        "n_v30_kitchen_drink_cana",
        "served_in",
        "se poate servi în cană",
        0.98,
    ),
    EdgeSpec(
        "n_v2gas_ciorba",
        "n_v30_kitchen_table_castron",
        "served_in",
        "se poate servi în castron",
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
    deferred_v30 = {_norm(term) for term in DEFERRED_V30_CONCEPTS}
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

    assert len(CONCEPTS) == len(node_ids) == len(labels) == len(set(labels)) == 18
    assert len(V30_BEGINNER_EXTENSION) == 18
    assert len(BEGINNER_BENCHMARK) == 271
    assert len({_norm(term) for term in BEGINNER_BENCHMARK}) == 271
    assert len(aliases) == len(normalized_aliases) == len(set(normalized_aliases)) == 60
    assert len(authored_surfaces) == 78
    assert not (set(labels) & set(normalized_aliases))
    assert not (authored_surfaces & blocked)
    assert not (authored_surfaces & deferred)
    assert not (authored_surfaces & deferred_v30)
    assert len(DEFERRED_V30_CONCEPTS) == len(deferred_v30) == 4
    assert len(SEMANTIC_EDGES) == len(edge_keys) == 54
    assert all(edge.target in node_ids for edge in SEMANTIC_EDGES)
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
