"""Audited source data for the v31 hygiene, lower-limb, and cleaning wave.

V31 adds concrete beginner vocabulary without changing the completed V30
denominator or serving any new game board.  Conservative inflections stay owned by
one concept, and inbound-only legacy bridges make each local mesh a viable target
without introducing routes from the new nodes back into the mature graph.
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from basic_words_v30_data import BEGINNER_BENCHMARK as V30_BEGINNER_BENCHMARK
from basic_words_v30_data import DEFERRED_AMBIGUOUS_TERMS, REVIEW_ITEM_IDS

BUILD_VERSION = "fixture-v31-hygiene-lower-limb-cleaning"
NOTE = (
    "v31: seventeen concrete beginner concepts across personal hygiene, lower-limb "
    "anatomy, and household cleaning, with conservative inflections and explicit "
    "semantic links; no game boards or promotions."
)
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
GAME_ITEM_IDS: tuple[str, ...] = ()
V31_BEGINNER_EXTENSION: tuple[str, ...] = (
    "Prosop",
    "Săpun",
    "Șampon",
    "Pieptene",
    "Periuță de dinți",
    "Pastă de dinți",
    "Genunchi",
    "Coapsă",
    "Gambă",
    "Gleznă",
    "Călcâi",
    "Găleată",
    "Mop",
    "Detergent",
    "Aspirator",
    "Făraș",
    "Burete de vase",
)
BEGINNER_BENCHMARK = (*V30_BEGINNER_BENCHMARK, *V31_BEGINNER_EXTENSION)


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
        "n_v31_hygiene_bath_prosop",
        "Prosop",
        "viata_de_roman",
        0.93,
        "Obiect textil absorbant folosit pentru a șterge și usca mâinile, fața sau corpul.",
        ("prosopul", "prosoape", "prosoapele", "prosopului"),
    ),
    ConceptSpec(
        "n_v31_hygiene_bath_sapun",
        "Săpun",
        "viata_de_roman",
        0.94,
        "Produs folosit cu apă pentru a spăla mâinile și corpul.",
        ("săpunul", "săpunuri", "săpunurile", "săpunului"),
    ),
    ConceptSpec(
        "n_v31_hygiene_hair_sampon",
        "Șampon",
        "viata_de_roman",
        0.92,
        "Produs lichid folosit cu apă pentru a spăla părul.",
        ("șamponul", "șampoane", "șampoanele", "șamponului"),
    ),
    ConceptSpec(
        "n_v31_hygiene_hair_pieptene",
        "Pieptene",
        "viata_de_roman",
        0.91,
        "Obiect cu dinți apropiați, folosit pentru a descurca și aranja părul.",
        ("pieptenele", "piepteni", "pieptenii", "pieptenului"),
    ),
    ConceptSpec(
        "n_v31_hygiene_oral_periuta_dinti",
        "Periuță de dinți",
        "viata_de_roman",
        0.94,
        "Obiect mic cu peri, folosit pentru a curăța dinții.",
        ("periuțe de dinți", "periuțele de dinți", "periuței de dinți"),
    ),
    ConceptSpec(
        "n_v31_hygiene_oral_pasta_dinti",
        "Pastă de dinți",
        "viata_de_roman",
        0.94,
        "Produs pus pe periuță pentru a curăța dinții și gura.",
        ("paste de dinți", "pastele de dinți", "pastei de dinți"),
    ),
    ConceptSpec(
        "n_v31_body_lower_genunchi",
        "Genunchi",
        "stiinta",
        0.94,
        "Articulație a piciorului care leagă coapsa de gambă și permite îndoirea.",
        ("genunchiul", "genunchii", "genunchiului"),
    ),
    ConceptSpec(
        "n_v31_body_lower_coapsa",
        "Coapsă",
        "stiinta",
        0.92,
        "Partea de sus a piciorului, între șold și genunchi.",
        ("coapse", "coapsele", "coapsei"),
    ),
    ConceptSpec(
        "n_v31_body_lower_gamba",
        "Gambă",
        "stiinta",
        0.92,
        "Partea piciorului dintre genunchi și gleznă.",
        ("gambe", "gambele", "gambei"),
    ),
    ConceptSpec(
        "n_v31_body_lower_glezna",
        "Gleznă",
        "stiinta",
        0.93,
        "Articulație dintre gambă și laba piciorului.",
        ("glezne", "gleznele", "gleznei"),
    ),
    ConceptSpec(
        "n_v31_body_lower_calcai",
        "Călcâi",
        "stiinta",
        0.92,
        "Partea din spate a labei piciorului, pe care se sprijină corpul.",
        ("călcâiul", "călcâie", "călcâiele", "călcâiului"),
    ),
    ConceptSpec(
        "n_v31_cleaning_water_galeata",
        "Găleată",
        "viata_de_roman",
        0.91,
        "Recipient cu mâner folosit pentru a duce apă sau alte lichide.",
        ("găleți", "gălețile", "găleții"),
    ),
    ConceptSpec(
        "n_v31_cleaning_floor_mop",
        "Mop",
        "viata_de_roman",
        0.91,
        "Unealtă cu coadă și cap absorbant, folosită pentru a spăla podeaua.",
        ("mopul", "mopuri", "mopurile", "mopului"),
    ),
    ConceptSpec(
        "n_v31_cleaning_supply_detergent",
        "Detergent",
        "viata_de_roman",
        0.93,
        "Produs de curățare folosit pentru vase, haine sau suprafețe.",
        ("detergentul", "detergenți", "detergenții", "detergentului"),
    ),
    ConceptSpec(
        "n_v31_cleaning_floor_aspirator",
        "Aspirator",
        "viata_de_roman",
        0.94,
        "Aparat care trage praful și murdăria de pe podele și covoare.",
        ("aspiratorul", "aspiratoare", "aspiratoarele", "aspiratorului"),
    ),
    ConceptSpec(
        "n_v31_cleaning_floor_faras",
        "Făraș",
        "viata_de_roman",
        0.90,
        "Obiect plat cu mâner, folosit pentru a aduna praful de pe podea.",
        ("fărașul", "fărașe", "fărașele", "fărașului"),
    ),
    ConceptSpec(
        "n_v31_cleaning_dishes_burete_vase",
        "Burete de vase",
        "viata_de_roman",
        0.92,
        "Obiect moale și poros folosit pentru a spăla vasele.",
        ("buretele de vase", "bureți de vase", "bureții de vase", "buretelui de vase"),
    ),
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)


# Neighboring concepts, ambiguous forms, and phrases with a different ordinary sense
# stay unresolved or with their existing owner.  Redundant definite feminine forms are
# omitted because accent/case normalization already maps them to their canonical label.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "ștergar",
    "prosop de hârtie",
    "gel de duș",
    "săpunieră",
    "balsam",
    "perie",
    "periuță",
    "ață dentară",
    "pastă",
    "gel",
    "rotulă",
    "femur",
    "pulpă",
    "maleolă",
    "tendonul lui Ahile",
    "lighean",
    "căldare",
    "recipient",
    "lavetă",
    "înălbitor",
    "dezinfectant",
    "soluție de curățat",
    "aspirație",
    "aspirator nazal",
    "mătură",
    "mătura",
    "matură",
    "matura",
    "burete",
    "burete de mare",
    "ciupercă",
    "talpă",
)
DEFERRED_V31_CONCEPTS: tuple[str, ...] = (
    "Duș",
    "Pod",
    "Somn",
    "Mătură",
    "Burete",
    "Talpă",
    "Cot",
    "Umăr",
    "Braț",
    "Spate",
    "Burtă",
    "Toaletă",
    "Perie",
    "Coș",
)


# Each new node has exactly two local outgoing choices and one inbound legacy bridge.
# The local meshes are strongly connected.  Bridges only point from the mature graph
# into a mesh, preserving every legacy-to-legacy route and score.
SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    # Personal hygiene: twelve local links.
    EdgeSpec(
        "n_v31_hygiene_bath_sapun",
        "n_v31_hygiene_bath_prosop",
        "used_before",
        "se folosește înainte de ștergerea cu prosopul",
        0.97,
    ),
    EdgeSpec(
        "n_v31_hygiene_bath_sapun",
        "n_v31_hygiene_hair_sampon",
        "same_kind",
        "este produs de spălare, ca șamponul",
        0.95,
    ),
    EdgeSpec(
        "n_v31_hygiene_bath_prosop",
        "n_v31_hygiene_oral_pasta_dinti",
        "shares_bathroom_setting",
        "se păstrează în baie, ca pasta de dinți",
        0.92,
    ),
    EdgeSpec(
        "n_v31_hygiene_bath_prosop",
        "n_v31_hygiene_hair_sampon",
        "used_after",
        "poate usca părul după șamponare",
        0.96,
    ),
    EdgeSpec(
        "n_v31_hygiene_hair_sampon",
        "n_v31_hygiene_hair_pieptene",
        "used_before",
        "se folosește înainte de pieptănarea părului",
        0.97,
    ),
    EdgeSpec(
        "n_v31_hygiene_hair_sampon",
        "n_v31_hygiene_bath_prosop",
        "used_before",
        "se folosește înainte de uscarea cu prosopul",
        0.97,
    ),
    EdgeSpec(
        "n_v31_hygiene_hair_pieptene",
        "n_v31_hygiene_bath_prosop",
        "shares_hygiene_routine",
        "face parte din rutina de îngrijire, ca prosopul",
        0.92,
    ),
    EdgeSpec(
        "n_v31_hygiene_hair_pieptene",
        "n_v31_hygiene_oral_periuta_dinti",
        "shares_bathroom_setting",
        "se păstrează în baie, ca periuța de dinți",
        0.92,
    ),
    EdgeSpec(
        "n_v31_hygiene_oral_periuta_dinti",
        "n_v31_hygiene_oral_pasta_dinti",
        "used_with",
        "se folosește cu pastă de dinți",
        0.99,
    ),
    EdgeSpec(
        "n_v31_hygiene_oral_periuta_dinti",
        "n_v31_hygiene_bath_sapun",
        "shares_hygiene_routine",
        "ține de igiena zilnică, la fel ca săpunul",
        0.94,
    ),
    EdgeSpec(
        "n_v31_hygiene_oral_pasta_dinti",
        "n_v31_hygiene_oral_periuta_dinti",
        "placed_on",
        "se pune pe periuța de dinți",
        0.99,
    ),
    EdgeSpec(
        "n_v31_hygiene_oral_pasta_dinti",
        "n_v31_hygiene_bath_sapun",
        "same_kind",
        "este produs de igienă, ca săpunul",
        0.94,
    ),
    EdgeSpec(
        "n_v4via_baie",
        "n_v31_hygiene_bath_prosop",
        "contains_item",
        "poate conține un prosop",
        0.98,
    ),
    EdgeSpec(
        "n_v4via_baie", "n_v31_hygiene_bath_sapun", "contains_item", "poate conține săpun", 0.98
    ),
    EdgeSpec(
        "n_v4via_baie", "n_v31_hygiene_hair_sampon", "contains_item", "poate conține șampon", 0.98
    ),
    EdgeSpec(
        "n_v24_body_face_cap",
        "n_v31_hygiene_hair_pieptene",
        "uses_care_item",
        "părul de pe cap se aranjează cu un pieptene",
        0.97,
    ),
    EdgeSpec(
        "n_v28_body_mouth_dinte",
        "n_v31_hygiene_oral_periuta_dinti",
        "cleaned_with",
        "se curăță cu periuța de dinți",
        0.99,
    ),
    EdgeSpec(
        "n_v28_body_mouth_dinte",
        "n_v31_hygiene_oral_pasta_dinti",
        "cleaned_with",
        "se curăță cu pastă de dinți",
        0.99,
    ),
    # Lower limb: ten local links.
    EdgeSpec(
        "n_v31_body_lower_coapsa",
        "n_v31_body_lower_genunchi",
        "joins_at",
        "se unește cu genunchiul",
        0.99,
    ),
    EdgeSpec(
        "n_v31_body_lower_coapsa",
        "n_v31_body_lower_gamba",
        "same_limb",
        "este parte a aceluiași picior ca gamba",
        0.96,
    ),
    EdgeSpec(
        "n_v31_body_lower_genunchi",
        "n_v31_body_lower_gamba",
        "joins_to",
        "leagă coapsa de gambă",
        0.99,
    ),
    EdgeSpec(
        "n_v31_body_lower_genunchi",
        "n_v31_body_lower_glezna",
        "same_limb",
        "este articulație a piciorului, ca glezna",
        0.96,
    ),
    EdgeSpec(
        "n_v31_body_lower_gamba",
        "n_v31_body_lower_glezna",
        "joins_at",
        "se termină la gleznă",
        0.99,
    ),
    EdgeSpec(
        "n_v31_body_lower_gamba",
        "n_v31_body_lower_calcai",
        "same_limb",
        "este parte a aceluiași picior ca călcâiul",
        0.95,
    ),
    EdgeSpec(
        "n_v31_body_lower_glezna",
        "n_v31_body_lower_calcai",
        "near_part",
        "se află aproape de călcâi",
        0.98,
    ),
    EdgeSpec(
        "n_v31_body_lower_glezna",
        "n_v31_body_lower_coapsa",
        "same_limb",
        "este parte a aceluiași picior ca coapsa",
        0.95,
    ),
    EdgeSpec(
        "n_v31_body_lower_calcai",
        "n_v31_body_lower_coapsa",
        "same_limb",
        "este parte a aceluiași picior ca coapsa",
        0.94,
    ),
    EdgeSpec(
        "n_v31_body_lower_calcai",
        "n_v31_body_lower_genunchi",
        "same_limb",
        "este parte a aceluiași picior ca genunchiul",
        0.95,
    ),
    EdgeSpec(
        "n_v24_body_limbs_picior",
        "n_v31_body_lower_genunchi",
        "has_part",
        "are ca parte genunchiul",
        0.99,
    ),
    EdgeSpec("n_v4sti_corp", "n_v31_body_lower_coapsa", "has_part", "are ca parte coapsa", 0.99),
    EdgeSpec("n_v4sti_corp", "n_v31_body_lower_gamba", "has_part", "are ca parte gamba", 0.99),
    EdgeSpec(
        "n_v24_body_limbs_picior",
        "n_v31_body_lower_glezna",
        "has_part",
        "are ca parte glezna",
        0.99,
    ),
    EdgeSpec(
        "n_v24_body_limbs_picior",
        "n_v31_body_lower_calcai",
        "has_part",
        "are ca parte călcâiul",
        0.99,
    ),
    # Household cleaning: twelve local links.
    EdgeSpec(
        "n_v31_cleaning_water_galeata",
        "n_v31_cleaning_floor_mop",
        "used_with",
        "se folosește cu mopul la spălarea podelei",
        0.98,
    ),
    EdgeSpec(
        "n_v31_cleaning_floor_mop",
        "n_v31_cleaning_water_galeata",
        "rinsed_in",
        "se clătește într-o găleată",
        0.98,
    ),
    EdgeSpec(
        "n_v31_cleaning_supply_detergent",
        "n_v31_cleaning_dishes_burete_vase",
        "used_with",
        "se folosește cu buretele de vase",
        0.99,
    ),
    EdgeSpec(
        "n_v31_cleaning_dishes_burete_vase",
        "n_v31_cleaning_supply_detergent",
        "holds_cleaner",
        "ține detergent în timpul spălării",
        0.99,
    ),
    EdgeSpec(
        "n_v31_cleaning_water_galeata",
        "n_v31_cleaning_supply_detergent",
        "holds_cleaning_solution",
        "poate ține apă cu detergent",
        0.97,
    ),
    EdgeSpec(
        "n_v31_cleaning_dishes_burete_vase",
        "n_v31_cleaning_water_galeata",
        "used_with",
        "se poate clăti folosind apă din găleată",
        0.94,
    ),
    EdgeSpec(
        "n_v31_cleaning_supply_detergent",
        "n_v31_cleaning_floor_mop",
        "used_with",
        "se poate folosi la spălarea cu mopul",
        0.97,
    ),
    EdgeSpec(
        "n_v31_cleaning_floor_mop",
        "n_v31_cleaning_floor_aspirator",
        "same_floor_task",
        "curăță podeaua, ca aspiratorul",
        0.96,
    ),
    EdgeSpec(
        "n_v31_cleaning_floor_aspirator",
        "n_v31_cleaning_floor_faras",
        "same_floor_task",
        "adună murdăria de pe podea, ca fărașul",
        0.96,
    ),
    EdgeSpec(
        "n_v31_cleaning_floor_aspirator",
        "n_v31_cleaning_dishes_burete_vase",
        "shares_cleaning_purpose",
        "este folosit la curățenie, ca buretele de vase",
        0.91,
    ),
    EdgeSpec(
        "n_v31_cleaning_floor_faras",
        "n_v31_cleaning_floor_mop",
        "same_floor_task",
        "se folosește la curățarea podelei, ca mopul",
        0.95,
    ),
    EdgeSpec(
        "n_v31_cleaning_floor_faras",
        "n_v31_cleaning_dishes_burete_vase",
        "shares_cleaning_purpose",
        "este unealtă de curățenie, ca buretele de vase",
        0.91,
    ),
    EdgeSpec(
        "n_v4gas_apa",
        "n_v31_cleaning_water_galeata",
        "carried_in",
        "poate fi dusă într-o găleată",
        0.98,
    ),
    EdgeSpec(
        "n_v24_home_surfaces_podea",
        "n_v31_cleaning_floor_mop",
        "cleaned_with",
        "se curăță cu mopul",
        0.99,
    ),
    EdgeSpec(
        "n_v24_action_home_a_spala",
        "n_v31_cleaning_supply_detergent",
        "uses_cleaner",
        "poate folosi detergent",
        0.98,
    ),
    EdgeSpec(
        "n_v24_home_surfaces_podea",
        "n_v31_cleaning_floor_aspirator",
        "cleaned_with",
        "se curăță cu aspiratorul",
        0.99,
    ),
    EdgeSpec(
        "n_v24_home_surfaces_podea",
        "n_v31_cleaning_floor_faras",
        "cleaned_with",
        "se curăță folosind fărașul",
        0.97,
    ),
    EdgeSpec(
        "n_v24_action_home_a_spala",
        "n_v31_cleaning_dishes_burete_vase",
        "uses_tool",
        "poate folosi un burete de vase",
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
    deferred_v31 = {_norm(term) for term in DEFERRED_V31_CONCEPTS}
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
    assert len(V31_BEGINNER_EXTENSION) == 17
    assert len(BEGINNER_BENCHMARK) == 288
    assert len({_norm(term) for term in BEGINNER_BENCHMARK}) == 288
    assert len(aliases) == len(normalized_aliases) == len(set(normalized_aliases)) == 61
    assert len(authored_surfaces) == 78
    assert not (set(labels) & set(normalized_aliases))
    assert not (authored_surfaces & blocked)
    assert not (authored_surfaces & deferred)
    assert not (authored_surfaces & deferred_v31)
    assert len(BLOCKED_ALIAS_FORMS) == 32
    assert len(blocked) == 29
    assert len(DEFERRED_V31_CONCEPTS) == len(deferred_v31) == 14
    assert len(SEMANTIC_EDGES) == len(edge_keys) == 51
    assert all(edge.target in node_ids for edge in SEMANTIC_EDGES)
    assert all(len(neighbors[node_id]) >= 4 for node_id in node_ids)
    assert all(outgoing[node_id] == 2 for node_id in node_ids)
    assert all(incoming[node_id] >= 1 for node_id in node_ids)
    assert len(legacy_new_neighbors) == 8
    assert sum(map(len, legacy_new_neighbors.values())) == 17
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
