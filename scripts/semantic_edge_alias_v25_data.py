"""Audited aliases and semantic links for the v25 everyday-language wave.

The module is side-effect free. ``apply_common_words_v24.py --data-module
semantic_edge_alias_v25_data`` consumes these plain records through the same
rollback-safe transaction used by v24.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from common_words_v24_data import (
    BEGINNER_BENCHMARK as V24_BEGINNER_BENCHMARK,
)
from common_words_v24_data import (
    DEFERRED_AMBIGUOUS_TERMS,
)
from common_words_v24_data import (
    GAME_ITEM_IDS as V24_GAME_ITEM_IDS,
)

BUILD_VERSION = "fixture-v25-semantic-aliases"
NOTE = (
    "v25: collision-screened everyday Romanian inflections and explicit semantic "
    "links replacing generic graph proximity with concrete player-facing relations."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()
BEGINNER_BENCHMARK = V24_BEGINNER_BENCHMARK
BASELINE_PACK_SHA256 = "2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023"
REVIEW_ITEM_IDS: tuple[str, ...] = (
    *V24_GAME_ITEM_IDS,
    "cx_viata_de_roman_291",
    "ct_literatura_298",
    "ct_viata_de_roman_299",
    "lt_literatura_210",
    "lt_viata_de_roman_211",
    "al_literatura_097",
    "al_viata_de_roman_098",
)


@dataclass(frozen=True, slots=True)
class EdgeSpec:
    source: str
    target: str
    relation: str
    label_ro: str
    strength: float = 0.97
    bidirectional: int = 0


def _norm(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .casefold()
        .split()
    )


# Every form was screened against the committed v24 resolver. Definite plurals are
# valuable here because accent folding already makes many feminine definite singulars
# equivalent to their base label, while plural morphology remains a distinct lookup.
ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v24_food_pantry_zahar": ("zaharuri", "zaharurile"),
    "n_v24_food_pantry_faina": ("făinuri", "făinurile"),
    "n_v24_food_pantry_ulei": ("uleiurile",),
    "n_v24_food_breakfast_iaurt": ("iaurturile",),
    "n_v24_food_orchard_mar": ("merele",),
    "n_v24_food_orchard_para": ("perele",),
    "n_v24_food_orchard_pruna": ("prunele",),
    "n_v24_food_small_fruit_cireasa": ("cireșele",),
    "n_v24_food_small_fruit_capsuna": ("căpșunile",),
    "n_v24_food_small_fruit_strugure": ("strugurii",),
    "n_v24_food_summer_fruit_pepene": ("pepenii",),
    "n_v24_food_summer_fruit_caisa": ("caisele",),
    "n_v24_food_summer_fruit_piersica": ("piersicile",),
    "n_v24_food_imported_fruit_banana": ("bananele",),
    "n_v24_food_imported_fruit_portocala": ("portocalele",),
    "n_v24_food_imported_fruit_lamaie": ("lămâile",),
    "n_v24_food_salad_veg_morcov": ("morcovii",),
    "n_v24_food_salad_veg_ardei": ("ardeii",),
    "n_v24_food_salad_veg_castravete": ("castraveții",),
    "n_v24_food_garden_veg_dovleac": ("dovlecii",),
    "n_v24_food_garden_veg_ridiche": ("ridichile",),
    "n_v24_food_snack_ceai": ("ceaiurile",),
    "n_v24_food_snack_biscuit": ("biscuiții",),
    "n_v24_food_snack_sandvis": (
        "sandvici",
        "sandviciul",
        "sandviciuri",
        "sendviș",
        "sendvișul",
        "sendvișuri",
        "sandvișurile",
    ),
    "n_v24_home_rooms_camera": ("camerele",),
    "n_v24_home_rooms_sufragerie": ("sufrageriile",),
    "n_v24_home_rooms_dormitor": ("dormitoarele",),
    "n_v24_home_outdoor_balcon": ("balcoanele",),
    "n_v24_home_outdoor_curte": ("curțile",),
    "n_v24_home_outdoor_gradina": ("grădinile",),
    "n_v24_home_structure_acoperis": ("acoperișurile",),
    "n_v24_home_structure_perete": ("pereții",),
    "n_v24_home_structure_tavan": ("tavanele",),
    "n_v24_home_surfaces_podea": ("podelele",),
    "n_v24_home_surfaces_fereastra": ("ferestrele",),
    "n_v24_home_surfaces_oglinda": ("oglinzile",),
    "n_v24_home_storage_dulap": ("dulapurile",),
    "n_v24_home_storage_raft": ("rafturile",),
    "n_v24_home_storage_comoda_sertare": ("comodele cu sertare",),
    "n_v24_home_bed_saltea": ("saltelele",),
    "n_v24_home_bed_perna": ("pernele",),
    "n_v24_home_textiles_cearsaf": ("cearșafurile",),
    "n_v24_home_textiles_covor": ("covoarele",),
    "n_v24_home_seating_scaun": ("scaunele",),
    "n_v24_home_seating_canapea": ("canapelele",),
    "n_v24_home_seating_fotoliu": ("fotoliile",),
    "n_v24_home_appliances_lampa": ("lămpile",),
    "n_v24_home_appliances_frigider": ("frigiderele",),
    "n_v24_home_appliances_aragaz": ("aragazurile",),
    "n_v24_people_parents_mama": ("mamele",),
    "n_v24_people_parents_tata": ("tații",),
    "n_v24_people_parents_bebelus": ("bebelușii",),
    "n_v24_people_descendants_fiu": ("fiii",),
    "n_v24_people_descendants_fiica": ("fiicele",),
    "n_v24_people_descendants_nepot": ("nepoții",),
    "n_v24_people_relatives_frate": ("frații",),
    "n_v24_people_relatives_sora": ("surorile",),
    "n_v24_people_relatives_unchi": ("unchii",),
    "n_v24_people_grandparents_matusa": ("mătușile",),
    "n_v24_people_relationships_prieten": ("prietenii",),
    "n_v24_body_face_cap": ("capetele",),
    "n_v24_body_face_nas": ("nasurile",),
    "n_v24_body_face_gura": ("gurile",),
    "n_v24_body_limbs_mana": ("mâinile",),
    "n_v24_body_limbs_deget": ("degetele",),
    "n_v24_body_limbs_picior": ("picioarele",),
    "n_v24_nature_plant_parts_iarba": ("ierburile",),
    "n_v24_nature_plant_parts_ramura": ("ramurile",),
    "n_v24_nature_plant_parts_radacina": ("rădăcinile",),
    "n_v24_nature_world_cer": ("cerurile",),
    "n_v24_nature_sky_stea": ("stelele",),
    "n_v24_weather_precipitation_zapada": ("zăpezile",),
    "n_v24_weather_air_vant": ("vânturile",),
    "n_v24_weather_air_nor": ("norii",),
    "n_v24_weather_air_ceata": ("cețurile",),
    "n_v24_weather_storm_furtuna": ("furtunile",),
    "n_v24_weather_storm_fulger": ("fulgerele",),
    "n_v24_weather_storm_tunet": ("tunetele",),
    "n_v24_transport_rail_tren": ("trenurile",),
    "n_v24_transport_rail_tramvai": ("tramvaiele",),
    "n_v24_transport_rail_metrou": ("metrourile",),
    "n_v24_transport_personal_masina": ("mașinile",),
    "n_v24_transport_personal_bicicleta": ("bicicletele",),
    "n_v24_transport_personal_motocicleta": ("motocicletele",),
    "n_v24_transport_road_camion": ("camioanele",),
    "n_v24_transport_road_microbuz": ("microbuzele",),
    "n_v24_transport_terminals_gara": ("gările",),
    "n_v24_transport_terminals_aeroport": ("aeroporturile",),
    "n_v24_transport_terminals_statie": ("stațiile",),
    "n_v24_places_public_parc": ("parcurile",),
    "n_v24_places_public_farmacie": ("farmaciile",),
    "n_v24_places_public_restaurant": ("restaurantele",),
    "n_v24_school_writing_caiet": ("caietele",),
    "n_v24_school_writing_creion": ("creioanele",),
    "n_v24_school_writing_pix": ("pixurile",),
    "n_v24_school_supplies_stilou": ("stilourile",),
    "n_v24_school_supplies_rigla": ("riglele",),
    "n_v24_school_classroom_clasa_scolara": ("clasele școlare",),
    "n_v24_school_classroom_banca_scolara": ("băncile școlare",),
    "n_v24_school_classroom_lectie": ("lecțiile",),
    "n_v24_school_assessment_tema_acasa": ("temele pentru acasă",),
    "n_v24_school_assessment_examen": ("examenele",),
    "n_v24_school_assessment_catalog_scolar": ("cataloagele școlare",),
    "n_v24_time_day_ceas": ("ceasurile",),
    "n_v24_time_day_ora": ("orele",),
    "n_v24_time_day_zi": ("zilele",),
    "n_v24_action_food_a_manca": ("mânca", "mănânci", "mâncați"),
    "n_v24_action_food_a_bea": ("bei", "beți"),
    "n_v24_action_food_a_gati": ("găti", "gătești", "gătiți"),
    "n_v24_action_movement_a_merge": ("mergi", "mergeți"),
    "n_v24_action_movement_a_veni": ("veni",),
    "n_v24_action_movement_a_se_juca": ("se juca", "te joci", "vă jucați"),
    "n_v24_action_senses_a_vedea": ("vedea", "vezi", "vedeți"),
    "n_v24_action_senses_a_auzi": ("auzi", "auziți"),
    "n_v24_action_senses_a_vorbi": ("vorbi", "vorbești", "vorbiți"),
    "n_v24_action_language_a_spune": ("spui", "spuneți"),
    "n_v24_action_language_a_citi": ("citi", "citești", "citiți"),
    "n_v24_action_language_a_scrie": ("scrii", "scrieți"),
    "n_v24_action_routine_a_dormi": ("dormi", "dormiți"),
    "n_v24_action_routine_a_lucra": ("lucra", "lucrezi", "lucrați"),
    "n_v24_action_routine_a_invata": ("înveți", "învățați"),
    "n_v24_action_home_a_spala": ("speli", "spălați"),
    "n_v24_action_home_a_deschide": ("deschizi", "deschideți"),
    "n_v24_action_home_a_inchide": ("închizi", "închideți"),
    "n_v24_feeling_joy_a_iubi": ("iubi", "iubești", "iubiți"),
    "n_v24_feeling_joy_bucurie": ("bucuriile",),
    "n_v24_feeling_difficult_tristete": ("tristețile",),
    "n_v24_feeling_difficult_frica": ("fricile",),
    "n_v24_feeling_difficult_furie": ("furiile",),
    "n_v24_feeling_needs_foame": ("mi-e foame", "îmi e foame"),
    "n_v24_feeling_needs_sete": ("mi-e sete", "îmi e sete"),
    "n_v2via_vecini": ("vecin",),
}


# Bare forms that would collapse two senses after accent folding or morphology. They
# stay explicit so later edits cannot quietly reintroduce known resolver mistakes.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "metroul",
    "vin",
    "vii",
    "paturi",
    "paturile",
    "râzi",
    "râdeți",
    "lunile",
    "bunici",
    "bunicii",
    "soții",
    "radierele",
    "joc",
)


# Exact, reviewable catalog. It stays deliberately small so familiar one-hop repairs do
# not turn category roots into shortcuts or inflate Alchimie through generic shared hubs.
SEMANTIC_EDGES: tuple[EdgeSpec, ...] = (
    EdgeSpec(
        "n_v24_home_appliances_frigider",
        "n_v4gas_bucatarie",
        "located_in",
        "se află în bucătărie",
        0.98,
        1,
    ),
    EdgeSpec(
        "n_v24_home_appliances_aragaz",
        "n_v4gas_bucatarie",
        "located_in",
        "se află în bucătărie",
        0.99,
        1,
    ),
    EdgeSpec(
        "n_v4gas_mancare",
        "n_v24_action_food_a_manca",
        "used_for_action",
        "se mănâncă",
        0.99,
    ),
    EdgeSpec(
        "n_v4gas_apa",
        "n_v24_action_food_a_bea",
        "used_for_action",
        "se bea",
        0.99,
    ),
    EdgeSpec(
        "n_v4gas_bucatarie",
        "n_v24_action_food_a_gati",
        "enables_action",
        "loc de gătit",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_ochi",
        "n_v24_action_senses_a_vedea",
        "enables_action",
        "vede cu ochii",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_ureche",
        "n_v24_action_senses_a_auzi",
        "enables_action",
        "aude cu urechile",
        0.99,
    ),
    EdgeSpec(
        "n_v24_body_face_gura",
        "n_v24_action_senses_a_vorbi",
        "enables_action",
        "vorbește cu gura",
        0.99,
    ),
    EdgeSpec(
        "n_v3lit_carte",
        "n_v24_action_language_a_citi",
        "enables_action",
        "se citește",
        0.99,
    ),
    EdgeSpec(
        "n_v24_school_writing_caiet",
        "n_v24_action_language_a_scrie",
        "enables_action",
        "scrie în caiet",
        0.99,
    ),
    EdgeSpec(
        "n_v4via_usa",
        "n_v24_action_home_a_deschide",
        "used_for_action",
        "se deschide",
        0.99,
    ),
    EdgeSpec(
        "n_v4via_usa",
        "n_v24_action_home_a_inchide",
        "used_for_action",
        "se închide",
        0.99,
    ),
    EdgeSpec(
        "n_v24_home_bed_pat",
        "n_v24_action_routine_a_dormi",
        "enables_action",
        "doarme în pat",
        0.99,
    ),
    EdgeSpec(
        "n_v4soc_serviciu",
        "n_v24_action_routine_a_lucra",
        "enables_action",
        "lucrează la serviciu",
        0.99,
    ),
    EdgeSpec(
        "n_v3soc_scoala",
        "n_v24_action_routine_a_invata",
        "enables_action",
        "învață la școală",
        0.99,
    ),
    EdgeSpec(
        "n_v24_transport_terminals_gara",
        "n_v24_transport_rail_tren",
        "serves_transport",
        "tren și gară",
        0.99,
        1,
    ),
    EdgeSpec(
        "n_v24_transport_terminals_aeroport",
        "n_v2sti_avion",
        "serves_transport",
        "avion și aeroport",
        0.99,
        1,
    ),
    EdgeSpec(
        "n_v24_feeling_needs_oboseala",
        "n_v24_action_routine_a_dormi",
        "satisfied_by",
        "se alină prin somn",
        0.99,
    ),
    EdgeSpec(
        "n_v24_school_supplies_radiera",
        "n_v24_school_writing_creion",
        "used_with",
        "șterge urmele de creion",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_copac",
        "n_v24_nature_plant_parts_ramura",
        "has_part",
        "are ramuri",
        0.99,
    ),
    EdgeSpec(
        "n_v4sti_copac",
        "n_v24_nature_plant_parts_radacina",
        "has_part",
        "are rădăcini",
        0.99,
    ),
    EdgeSpec(
        "n_v24_nature_plant_parts_ramura",
        "n_v4sti_frunza",
        "has_part",
        "are frunze",
        0.99,
    ),
    EdgeSpec(
        "n_v24_weather_air_nor",
        "n_v24_weather_precipitation_ploaie",
        "causes_weather",
        "poate aduce ploaie",
        0.98,
    ),
    EdgeSpec(
        "n_v24_feeling_needs_foame",
        "n_v4gas_mancare",
        "satisfied_by",
        "se potolește cu mâncare",
        0.99,
    ),
    EdgeSpec(
        "n_v24_feeling_needs_sete",
        "n_v4gas_apa",
        "satisfied_by",
        "se potolește cu apă",
        0.99,
    ),
)

INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = tuple(
    (edge.source, edge.target) for edge in SEMANTIC_EDGES
)
ALIAS_PROBES: tuple[tuple[str, str], ...] = tuple(
    (alias, node_id)
    for node_id, aliases in ALIAS_ADDITIONS.items()
    for alias in aliases
)


def build_nodes_and_edges() -> dict[str, object]:
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
    return {
        "nodes": [],
        "edges": edges,
        "aliases": {node_id: list(values) for node_id, values in ALIAS_ADDITIONS.items()},
    }


def _validate_source() -> None:
    aliases = [alias for values in ALIAS_ADDITIONS.values() for alias in values]
    normalized = [_norm(alias) for alias in aliases]
    assert len(ALIAS_ADDITIONS) == 132
    assert len(aliases) == len(normalized) == len(set(normalized)) == 168
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert not ({_norm(value) for value in DEFERRED_AMBIGUOUS_TERMS} & set(normalized))
    assert len(REVIEW_ITEM_IDS) == len(set(REVIEW_ITEM_IDS)) == 33
    assert len(SEMANTIC_EDGES) == len(
        {(edge.source, edge.target, edge.relation) for edge in SEMANTIC_EDGES}
    )
    assert len(SEMANTIC_EDGES) == 25
    assert all(
        edge.source != edge.target
        and edge.relation != "related_to"
        and edge.label_ro.strip()
        and 0.8 <= edge.strength <= 1.0
        and edge.bidirectional in (0, 1)
        for edge in SEMANTIC_EDGES
    )


_validate_source()
