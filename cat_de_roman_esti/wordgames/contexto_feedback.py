"""Reviewed Contexto-only scoring proxies for inbound-only everyday nodes.

The V30--V33 beginner meshes deliberately accept edges from the mature graph without
providing a path back.  That topology is useful to Lanț and Alchimie, but it makes every
one of those familiar concepts an unreachable Cald sau Rece guess.  These explicit
proxies affect feedback only: the submitted node keeps its public identity, and an exact
target match bypasses the proxy in :mod:`contexto`.

Each proxy is a mature, recognizable concept connected to the mapped node by an authored
semantic path of at most three hops.  The inventory is closed and validated in V44 tests.
"""

from __future__ import annotations

# (mature feedback anchor, everyday node ids).  Grouping keeps the intended semantic
# context visible while still producing an exact, collision-checked node map.
COMMON_FEEDBACK_PROXY_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "n_v4sti_animal",
        (
            "n_v30_animal_farm_cal",
            "n_v30_animal_farm_capra",
            "n_v30_animal_farm_oaie",
            "n_v30_animal_farm_vaca",
            "n_v30_animal_field_iepure",
        ),
    ),
    (
        "n_v29_clothing_everyday_haina",
        (
            "n_v30_clothing_everyday_fusta",
            "n_v30_clothing_everyday_pantaloni",
            "n_v30_clothing_everyday_rochie",
            "n_v30_clothing_footwear_pantof",
            "n_v30_clothing_footwear_soseta",
            "n_v30_clothing_outer_geaca",
        ),
    ),
    (
        "n_v4gas_bucatarie",
        (
            "n_v30_kitchen_cookware_oala",
            "n_v30_kitchen_utensil_lingura",
        ),
    ),
    ("n_v24_home_appliances_aragaz", ("n_v30_kitchen_cookware_tigaie",)),
    ("n_v24_food_snack_ceai", ("n_v30_kitchen_drink_cana",)),
    ("n_v2gas_ciorba", ("n_v30_kitchen_table_castron",)),
    ("n_v4gas_masa", ("n_v30_kitchen_table_farfurie",)),
    ("n_v4gas_mancare", ("n_v30_kitchen_utensil_furculita",)),
    (
        "n_v24_body_limbs_picior",
        (
            "n_v31_body_lower_calcai",
            "n_v31_body_lower_coapsa",
            "n_v31_body_lower_gamba",
            "n_v31_body_lower_genunchi",
            "n_v31_body_lower_glezna",
        ),
    ),
    (
        "n_v24_action_home_a_spala",
        (
            "n_v31_cleaning_dishes_burete_vase",
            "n_v31_cleaning_supply_detergent",
        ),
    ),
    (
        "n_v24_home_surfaces_podea",
        (
            "n_v31_cleaning_floor_aspirator",
            "n_v31_cleaning_floor_faras",
            "n_v31_cleaning_floor_mop",
        ),
    ),
    ("n_v4gas_apa", ("n_v31_cleaning_water_galeata",)),
    (
        "n_v4via_baie",
        (
            "n_v31_hygiene_bath_prosop",
            "n_v31_hygiene_bath_sapun",
            "n_v31_hygiene_hair_sampon",
        ),
    ),
    ("n_v24_body_face_cap", ("n_v31_hygiene_hair_pieptene",)),
    (
        "n_v28_body_mouth_dinte",
        (
            "n_v31_hygiene_oral_pasta_dinti",
            "n_v31_hygiene_oral_periuta_dinti",
        ),
    ),
    ("n_v24_body_face_gura", ("n_v32_body_face_buza",)),
    (
        "n_v24_body_face_cap",
        (
            "n_v32_body_face_frunte",
            "n_v32_body_face_nara",
            "n_v32_body_face_obraz",
        ),
    ),
    (
        "n_v4sti_ochi",
        (
            "n_v32_body_face_pleoapa",
            "n_v32_body_face_spranceana",
        ),
    ),
    ("n_v4sti_floare", ("n_v32_garden_container_ghiveci_flori",)),
    (
        "n_v24_home_outdoor_gradina",
        (
            "n_v32_garden_soil_grebla",
            "n_v32_garden_transport_roaba",
        ),
    ),
    ("n_v24_nature_world_pamant", ("n_v32_garden_soil_lopata",)),
    (
        "n_v4gas_apa",
        (
            "n_v32_garden_water_furtun",
            "n_v32_garden_water_stropitoare",
        ),
    ),
    ("n_v4sti_copac", ("n_v32_workshop_cut_fierastrau",)),
    (
        "n_v4sti_metal",
        (
            "n_v32_workshop_fastener_cui",
            "n_v32_workshop_fastener_surub",
        ),
    ),
    (
        "n_v24_action_routine_a_lucra",
        (
            "n_v32_workshop_hand_ciocan",
            "n_v32_workshop_hand_cleste",
            "n_v32_workshop_hand_surubelnita",
        ),
    ),
    (
        "n_v4via_baie",
        (
            "n_v33_bathroom_clothing_halat_baie",
            "n_v33_bathroom_fixture_cada_baie",
            "n_v33_bathroom_fixture_chiuveta",
            "n_v33_bathroom_fixture_vas_toaleta",
            "n_v33_bathroom_supply_hartie_igienica",
        ),
    ),
    ("n_v4gas_apa", ("n_v33_bathroom_fixture_robinet",)),
    (
        "n_v3sti_electricitate",
        (
            "n_v33_electric_control_intrerupator",
            "n_v33_electric_extension_prelungitor",
            "n_v33_electric_outlet_priza",
            "n_v33_electric_plug_stecher",
            "n_v33_electric_wire_cablu",
        ),
    ),
    ("n_v24_home_appliances_lampa", ("n_v33_electric_light_bec",)),
    (
        "n_v4geo_padure",
        (
            "n_v33_forest_animal_caprioara",
            "n_v33_forest_animal_cerb",
            "n_v33_forest_animal_lup",
            "n_v33_forest_animal_urs",
            "n_v33_forest_animal_vulpe",
        ),
    ),
    ("n_v4sti_copac", ("n_v33_forest_animal_veverita",)),
)


def _build_proxy_index() -> dict[str, str]:
    result: dict[str, str] = {}
    for anchor_id, node_ids in COMMON_FEEDBACK_PROXY_GROUPS:
        for node_id in node_ids:
            previous = result.setdefault(node_id, anchor_id)
            if previous != anchor_id:
                raise RuntimeError(f"conflicting Contexto feedback proxy for {node_id!r}")
    if len(result) != 71:
        raise RuntimeError("Contexto common-word proxy inventory must contain 71 nodes")
    if set(result) & set(result.values()):
        raise RuntimeError("Contexto feedback proxies must terminate at mature anchors")
    return result


COMMON_FEEDBACK_PROXIES = _build_proxy_index()


def feedback_proxy_id(node_id: str) -> str:
    """Return the reviewed mature scoring proxy, or the original node id."""

    return COMMON_FEEDBACK_PROXIES.get(node_id, node_id)
