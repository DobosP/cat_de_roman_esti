"""Audited source data for the v28 missing-basic-concepts wave.

V25 deliberately left these fifteen benchmark terms unresolved because aliases could
not honestly represent them.  This module adds real concepts with conservative
inflections and concrete local links through the shared rollback-safe applier.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import dataclass

from common_words_v24_data import (
    BEGINNER_BENCHMARK as V24_BEGINNER_BENCHMARK,
)
from common_words_v24_data import DEFERRED_AMBIGUOUS_TERMS
from semantic_edge_alias_v25_data import REVIEW_ITEM_IDS

BUILD_VERSION = "fixture-v28-basic-words"
NOTE = (
    "v28: fifteen previously missing beginner concepts with collision-safe inflections "
    "and concrete local semantic links; no game boards or promotions."
)
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
GAME_ITEM_IDS: tuple[str, ...] = ()
BEGINNER_BENCHMARK = V24_BEGINNER_BENCHMARK


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
        "n_v28_food_vegetable_conopida",
        "Conopidă",
        "gastronomie",
        0.88,
        "Legumă cu o parte albă și compactă, folosită în mâncare.",
        ("conopide", "conopidele", "conopidei"),
    ),
    ConceptSpec(
        "n_v28_food_vegetable_spanac",
        "Spanac",
        "gastronomie",
        0.88,
        "Legumă cu frunze verzi, gătită sau mâncată în salate.",
        ("spanacul", "spanacului"),
    ),
    ConceptSpec(
        "n_v28_body_mouth_dinte",
        "Dinte",
        "stiinta",
        0.93,
        "Parte tare din gură, folosită pentru mușcare și mestecare.",
        ("dintele", "dinți", "dinții", "dintelui"),
    ),
    ConceptSpec(
        "n_v28_nature_weather_curcubeu",
        "Curcubeu",
        "stiinta",
        0.91,
        "Arc colorat care apare pe cer când lumina trece prin picături de apă.",
        ("curcubeul", "curcubeie", "curcubeiele", "curcubeului"),
    ),
    ConceptSpec(
        "n_v28_nature_material_piatra",
        "Piatră",
        "stiinta",
        0.93,
        "Bucată tare de rocă, întâlnită în natură și folosită la construcții.",
        ("pietre", "pietrele", "pietrei"),
    ),
    ConceptSpec(
        "n_v28_transport_water_vapor",
        "Vapor",
        "societate",
        0.88,
        "Navă care transportă oameni sau mărfuri pe apă.",
        ("vaporul", "vapoare", "vapoarele", "vaporului"),
    ),
    ConceptSpec(
        "n_v28_work_occupation_meserie",
        "Meserie",
        "societate",
        0.91,
        "Ocupație învățată și practicată pentru a munci și a câștiga bani.",
        ("meseria", "meserii", "meseriile", "meseriei"),
    ),
    ConceptSpec(
        "n_v28_time_calendar_saptamana",
        "Săptămână",
        "societate",
        0.94,
        "Perioadă de șapte zile consecutive.",
        ("săptămâni", "săptămânile", "săptămânii"),
    ),
    ConceptSpec(
        "n_v28_time_calendar_luna_calendaristica",
        "Lună calendaristică",
        "societate",
        0.94,
        "Una dintre cele douăsprezece perioade ale anului calendaristic.",
        (
            "luni calendaristice",
            "lunile calendaristice",
            "lunii calendaristice",
            "lună de calendar",
            "luni de calendar",
        ),
    ),
    ConceptSpec(
        "n_v28_feeling_social_surpriza",
        "Surpriză",
        "societate",
        0.91,
        "Emoție apărută când se întâmplă ceva neașteptat.",
        ("surprizei",),
    ),
    ConceptSpec(
        "n_v28_feeling_social_rusine",
        "Rușine",
        "societate",
        0.88,
        "Emoție neplăcută simțită când credem că am făcut ceva greșit.",
        ("rușinea", "rușinii"),
    ),
    ConceptSpec(
        "n_v28_feeling_social_mandrie",
        "Mândrie",
        "societate",
        0.88,
        "Mulțumire pentru o reușită proprie sau a cuiva apropiat.",
        ("mândria", "mândriei"),
    ),
    ConceptSpec(
        "n_v28_feeling_positive_speranta",
        "Speranță",
        "societate",
        0.91,
        "Încrederea că un lucru bun se poate întâmpla.",
        ("speranțe", "speranțele", "speranței"),
    ),
    ConceptSpec(
        "n_v28_feeling_positive_iubire",
        "Iubire",
        "societate",
        0.93,
        "Sentiment puternic de afecțiune și apropiere.",
        ("iubirea", "iubirii"),
    ),
    ConceptSpec(
        "n_v28_feeling_positive_liniste",
        "Liniște",
        "societate",
        0.91,
        "Stare fără zgomot sau agitație, în care te poți odihni.",
        ("liniștea", "liniștii"),
    ),
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)


# Keep sense boundaries explicit. The Moon owns bare month-shaped forms; Vapor means a
# ship, not steam; broad emotional plurals can shift from the authored feeling sense.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "lună",
    "luna",
    "lunii",
    "luni",
    "lunile",
    "vapori",
    "abur",
    "surprize",
    "rușini",
    "mândrii",
    "iubirile",
    "liniști",
)


SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    # Everyday vegetables.
    EdgeSpec("n_v28_food_vegetable_conopida", "n_v4gas_legume", "is_a", "este o legumă", 0.99),
    EdgeSpec(
        "n_v4gas_mancare",
        "n_v28_food_vegetable_conopida",
        "includes_food",
        "poate include conopidă",
        0.96,
    ),
    EdgeSpec(
        "n_v28_food_vegetable_conopida", "n_v3gas_salata", "used_in", "se folosește în salată", 0.94
    ),
    EdgeSpec(
        "n_v28_food_vegetable_conopida", "n_v28_food_vegetable_spanac", "same_kind", "legume", 0.96
    ),
    EdgeSpec("n_v28_food_vegetable_spanac", "n_v4gas_legume", "is_a", "este o legumă", 0.99),
    EdgeSpec(
        "n_v4gas_mancare",
        "n_v28_food_vegetable_spanac",
        "includes_food",
        "poate include spanac",
        0.96,
    ),
    EdgeSpec(
        "n_v28_food_vegetable_spanac", "n_v3gas_salata", "used_in", "se folosește în salată", 0.96
    ),
    EdgeSpec(
        "n_v24_food_garden_veg_mazare",
        "n_v28_food_vegetable_spanac",
        "same_kind",
        "legume verzi",
        0.94,
    ),
    # Body, weather, and natural material.
    EdgeSpec("n_v24_body_face_gura", "n_v28_body_mouth_dinte", "has_part", "gura are dinți", 0.99),
    EdgeSpec("n_v28_body_mouth_dinte", "n_v4sti_corp", "part_of_body", "parte a corpului", 0.98),
    EdgeSpec(
        "n_v28_body_mouth_dinte",
        "n_v24_action_food_a_manca",
        "enables_action",
        "ajută la mestecat",
        0.99,
    ),
    EdgeSpec("n_v28_body_mouth_dinte", "n_v3per_medic", "cared_by", "este îngrijit de medic", 0.90),
    EdgeSpec(
        "n_v24_weather_precipitation_ploaie",
        "n_v28_nature_weather_curcubeu",
        "enables_weather",
        "cu soarele poate forma un curcubeu",
        0.98,
    ),
    EdgeSpec(
        "n_v24_nature_sky_soare",
        "n_v28_nature_weather_curcubeu",
        "enables_weather",
        "cu ploaia poate forma un curcubeu",
        0.98,
    ),
    EdgeSpec(
        "n_v28_nature_weather_curcubeu",
        "n_v24_nature_world_cer",
        "seen_in_sky",
        "apare pe cer",
        0.99,
    ),
    EdgeSpec(
        "n_v28_nature_weather_curcubeu", "n_v4art_culoare", "has_part", "are mai multe culori", 0.97
    ),
    EdgeSpec(
        "n_v2geo_munte",
        "n_v28_nature_material_piatra",
        "has_part",
        "muntele este alcătuit din piatră",
        0.97,
    ),
    EdgeSpec(
        "n_v28_nature_material_piatra",
        "n_v24_nature_world_pamant",
        "found_in",
        "se găsește în pământ",
        0.96,
    ),
    EdgeSpec(
        "n_v28_nature_material_piatra",
        "n_v24_nature_world_natura",
        "part_of_nature",
        "parte din natură",
        0.96,
    ),
    EdgeSpec("n_v28_nature_material_piatra", "n_v4sti_solid", "is_a", "este un corp solid", 0.98),
    # Transport, work, and calendar time.
    EdgeSpec(
        "n_v28_transport_water_vapor", "n_v2soc_port", "uses_terminal", "oprește în port", 0.99
    ),
    EdgeSpec("n_v28_transport_water_vapor", "n_v3geo_mare", "travels_on", "circulă pe mare", 0.99),
    EdgeSpec(
        "n_v24_transport_rail_tren",
        "n_v28_transport_water_vapor",
        "same_transport_kind",
        "mijloace de transport",
        0.94,
    ),
    EdgeSpec(
        "n_v24_transport_personal_masina",
        "n_v28_transport_water_vapor",
        "same_transport_kind",
        "mijloace de transport",
        0.94,
    ),
    EdgeSpec(
        "n_v4per_profesor",
        "n_v28_work_occupation_meserie",
        "occupation_example",
        "meseria de profesor",
        0.97,
    ),
    EdgeSpec(
        "n_v28_work_occupation_meserie",
        "n_v4soc_serviciu",
        "practiced_at",
        "se practică la serviciu",
        0.98,
    ),
    EdgeSpec(
        "n_v28_work_occupation_meserie",
        "n_v4soc_salariu",
        "may_provide",
        "poate aduce salariu",
        0.96,
    ),
    EdgeSpec(
        "n_v28_work_occupation_meserie",
        "n_v24_action_routine_a_lucra",
        "involves_action",
        "înseamnă a lucra",
        0.98,
    ),
    EdgeSpec(
        "n_v24_time_day_zi",
        "n_v28_time_calendar_saptamana",
        "builds_time_unit",
        "șapte zile formează o săptămână",
        0.99,
    ),
    EdgeSpec(
        "n_v28_time_calendar_saptamana",
        "n_v28_time_calendar_luna_calendaristica",
        "part_of_time",
        "săptămânile intră într-o lună",
        0.97,
    ),
    EdgeSpec(
        "n_v28_time_calendar_saptamana",
        "n_v4ist_an",
        "part_of_time",
        "săptămânile intră într-un an",
        0.97,
    ),
    EdgeSpec(
        "n_v24_time_day_ora", "n_v28_time_calendar_saptamana", "time_unit", "unități de timp", 0.94
    ),
    EdgeSpec(
        "n_v4ist_an",
        "n_v28_time_calendar_luna_calendaristica",
        "has_part",
        "anul are douăsprezece luni",
        0.99,
    ),
    EdgeSpec(
        "n_v28_time_calendar_luna_calendaristica",
        "n_v24_time_day_zi",
        "has_part",
        "luna are mai multe zile",
        0.98,
    ),
    EdgeSpec(
        "n_v28_time_calendar_luna_calendaristica",
        "n_v24_time_day_ora",
        "has_part",
        "cuprinde multe ore",
        0.94,
    ),
    # Six missing everyday feelings, with explicit qualified relations.
    EdgeSpec(
        "n_v24_feeling_joy_bucurie",
        "n_v28_feeling_social_surpriza",
        "can_follow",
        "poate urma unei surprize",
        0.93,
    ),
    EdgeSpec(
        "n_v24_feeling_difficult_frica",
        "n_v28_feeling_social_surpriza",
        "can_follow",
        "poate urma unei surprize",
        0.93,
    ),
    EdgeSpec(
        "n_v28_feeling_social_surpriza",
        "n_v24_feeling_difficult_tristete",
        "may_cause",
        "poate aduce tristețe",
        0.88,
    ),
    EdgeSpec(
        "n_v28_feeling_social_surpriza",
        "n_v28_feeling_positive_liniste",
        "contrasts_with",
        "întrerupe liniștea",
        0.97,
    ),
    EdgeSpec(
        "n_v24_feeling_difficult_tristete",
        "n_v28_feeling_social_rusine",
        "can_follow",
        "poate urma rușinii",
        0.91,
    ),
    EdgeSpec(
        "n_v28_feeling_social_rusine",
        "n_v24_feeling_difficult_frica",
        "can_accompany",
        "poate veni cu frică",
        0.91,
    ),
    EdgeSpec(
        "n_v28_feeling_social_rusine",
        "n_v28_feeling_social_mandrie",
        "contrasts_with",
        "se opune mândriei",
        0.98,
    ),
    EdgeSpec(
        "n_v28_feeling_positive_iubire",
        "n_v28_feeling_social_rusine",
        "eases_feeling",
        "poate alina rușinea",
        0.91,
    ),
    EdgeSpec(
        "n_v28_feeling_social_mandrie",
        "n_v24_feeling_joy_bucurie",
        "can_accompany",
        "poate veni cu bucurie",
        0.94,
    ),
    EdgeSpec(
        "n_v4soc_familie",
        "n_v28_feeling_social_mandrie",
        "may_inspire",
        "poate inspira mândrie",
        0.94,
    ),
    EdgeSpec(
        "n_v28_feeling_social_mandrie",
        "n_v28_feeling_positive_iubire",
        "can_grow_from",
        "poate crește din iubire",
        0.91,
    ),
    EdgeSpec(
        "n_v24_feeling_joy_a_iubi",
        "n_v28_feeling_positive_iubire",
        "expressed_as",
        "exprimă iubire",
        0.99,
    ),
    EdgeSpec(
        "n_v28_feeling_positive_iubire",
        "n_v28_feeling_positive_speranta",
        "supports_feeling",
        "poate hrăni speranța",
        0.96,
    ),
    EdgeSpec(
        "n_v24_feeling_joy_bucurie",
        "n_v28_feeling_positive_speranta",
        "supports_feeling",
        "poate întări speranța",
        0.91,
    ),
    EdgeSpec(
        "n_v28_feeling_positive_speranta",
        "n_v24_feeling_difficult_frica",
        "contrasts_with",
        "se opune fricii",
        0.96,
    ),
    EdgeSpec(
        "n_v28_feeling_positive_speranta",
        "n_v28_feeling_positive_liniste",
        "supports_feeling",
        "poate aduce liniște",
        0.96,
    ),
    EdgeSpec(
        "n_v28_feeling_positive_liniste",
        "n_v24_feeling_needs_oboseala",
        "relieves",
        "poate alina oboseala",
        0.94,
    ),
    EdgeSpec(
        "n_v28_feeling_positive_liniste",
        "n_v24_feeling_difficult_furie",
        "contrasts_with",
        "se opune furiei",
        0.97,
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
    blocked = {_norm(alias) for alias in BLOCKED_ALIAS_FORMS}
    deferred = {_norm(term) for term in DEFERRED_AMBIGUOUS_TERMS}
    node_ids = set(NEW_NODE_IDS)
    incident: Counter[str] = Counter()
    outgoing: Counter[str] = Counter()
    edge_keys: set[tuple[str, str, str]] = set()
    for edge in SEMANTIC_EDGES:
        incident.update((edge.source, edge.target))
        outgoing.update((edge.source,))
        key = (*sorted((edge.source, edge.target)), edge.relation)
        edge_keys.add(key)

    assert len(CONCEPTS) == len(node_ids) == len(labels) == len(set(labels)) == 15
    assert len(aliases) == len(normalized_aliases) == len(set(normalized_aliases)) == 44
    assert not (set(labels) & set(normalized_aliases))
    assert not ((set(labels) | set(normalized_aliases)) & blocked)
    assert not ((set(labels) | set(normalized_aliases)) & deferred)
    assert len(SEMANTIC_EDGES) == len(edge_keys) == 53
    assert all(incident[node_id] >= 4 for node_id in node_ids)
    assert all(outgoing[node_id] >= 2 for node_id in node_ids)
    assert all(
        edge.source != edge.target
        and (edge.source in node_ids or edge.target in node_ids)
        and edge.relation != "related_to"
        and edge.label_ro.strip()
        and 0.85 <= edge.strength <= 1.0
        and edge.bidirectional in (0, 1)
        for edge in SEMANTIC_EDGES
    )
    assert len(REVIEW_ITEM_IDS) == 33


_validate_source()
