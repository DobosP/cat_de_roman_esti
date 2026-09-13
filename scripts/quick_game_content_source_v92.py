"""V92 authored additions for Intrusul and Perechi.

This is editorial source, not a served fixture. The root build rail emits a bound
candidate file and requires two complete independent reviews before any package
catalog write. Original V38 boards and shared KG records remain unedited.

Perechi mixes practical associations and familiar Romanian culture in the broad
``viata_de_roman`` shelf. No pair is reused across these twenty authored boards.
"""

from __future__ import annotations

from copy import deepcopy

BOARDS = (
    {
        "id": "iq92_rail",
        "game": "intrusul",
        "source_id": "aq92_intrusul_rail",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_transport_rail_tren",
                "n_v24_transport_rail_tramvai",
                "n_v24_transport_rail_metrou",
            ],
            "intruder": "n_v24_transport_personal_bicicleta",
            "group_label": "Mijloace de transport care circulă pe șine",
        },
        "sources": [
            "https://dexonline.ro/definitie/tren",
            "https://dexonline.ro/definitie/tramvai",
            "https://dexonline.ro/definitie/metrou",
            "https://dexonline.ro/definitie/biciclet%C4%83",
        ],
        "rationale": "Predicat explicit: Mijloace de transport care circulă pe șine. "
        "Trio: Tren, Tramvai, Metrou. Bicicletă nu satisface "
        "predicatul. Vocabular familiar, fără informații de "
        "actualitate.",
    },
    {
        "id": "iq92_precipitation",
        "game": "intrusul",
        "source_id": "aq92_intrusul_precipitation",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_weather_precipitation_ploaie",
                "n_v24_weather_precipitation_zapada",
                "n_v24_weather_precipitation_grindina",
            ],
            "intruder": "n_v33_forest_animal_lup",
            "group_label": "Forme de precipitații",
        },
        "sources": [
            "https://dexonline.ro/definitie/ploaie",
            "https://dexonline.ro/definitie/z%C4%83pad%C4%83",
            "https://dexonline.ro/definitie/grindin%C4%83",
            "https://dexonline.ro/definitie/lup",
        ],
        "rationale": "Predicat explicit: Forme de precipitații. Trio: Ploaie, "
        "Zăpadă, Grindină. Lup nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_face",
        "game": "intrusul",
        "source_id": "aq92_intrusul_face",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v32_body_face_obraz",
                "n_v32_body_face_pleoapa",
                "n_v32_body_face_spranceana",
            ],
            "intruder": "n_v31_body_lower_genunchi",
            "group_label": "Părți ale feței",
        },
        "sources": [
            "https://dexonline.ro/definitie/obraz",
            "https://dexonline.ro/definitie/pleoap%C4%83",
            "https://dexonline.ro/definitie/spr%C3%A2ncean%C4%83",
            "https://dexonline.ro/definitie/genunchi",
        ],
        "rationale": "Predicat explicit: Părți ale feței. Trio: Obraz, Pleoapă, "
        "Sprânceană. Genunchi nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_leg",
        "game": "intrusul",
        "source_id": "aq92_intrusul_leg",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v31_body_lower_coapsa",
                "n_v31_body_lower_gamba",
                "n_v31_body_lower_glezna",
            ],
            "intruder": "n_v24_body_face_nas",
            "group_label": "Părți ale membrului inferior",
        },
        "sources": [
            "https://dexonline.ro/definitie/coaps%C4%83",
            "https://dexonline.ro/definitie/gamb%C4%83",
            "https://dexonline.ro/definitie/glezn%C4%83",
            "https://dexonline.ro/definitie/nas",
        ],
        "rationale": "Predicat explicit: Părți ale membrului inferior. Trio: Coapsă, "
        "Gambă, Gleznă. Nas nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_plant",
        "game": "intrusul",
        "source_id": "aq92_intrusul_plant",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_nature_plant_parts_radacina",
                "n_v24_nature_plant_parts_ramura",
                "n_v4sti_frunza",
            ],
            "intruder": "n_v28_nature_material_piatra",
            "group_label": "Părți ale unei plante",
        },
        "sources": [
            "https://dexonline.ro/definitie/r%C4%83d%C4%83cin%C4%83",
            "https://dexonline.ro/definitie/ramur%C4%83",
            "https://dexonline.ro/definitie/frunz%C4%83",
            "https://dexonline.ro/definitie/piatr%C4%83",
        ],
        "rationale": "Predicat explicit: Părți ale unei plante. Trio: Rădăcină, "
        "Ramură, frunză. Piatră nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_seating",
        "game": "intrusul",
        "source_id": "aq92_intrusul_seating",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_home_seating_canapea",
                "n_v24_home_seating_fotoliu",
                "n_v88_home_taburet",
            ],
            "intruder": "n_v33_bathroom_fixture_robinet",
            "group_label": "Mobilier pe care te așezi",
        },
        "sources": [
            "https://dexonline.ro/definitie/canapea",
            "https://dexonline.ro/definitie/fotoliu",
            "https://dexonline.ro/definitie/taburet",
            "https://dexonline.ro/definitie/robinet",
        ],
        "rationale": "Predicat explicit: Mobilier pe care te așezi. Trio: Canapea, "
        "Fotoliu, Taburet. Robinet nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_workshop",
        "game": "intrusul",
        "source_id": "aq92_intrusul_workshop",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v32_workshop_hand_ciocan",
                "n_v32_workshop_hand_cleste",
                "n_v32_workshop_cut_fierastrau",
            ],
            "intruder": "n_v31_hygiene_oral_periuta_dinti",
            "group_label": "Unelte manuale de atelier",
        },
        "sources": [
            "https://dexonline.ro/definitie/ciocan",
            "https://dexonline.ro/definitie/cle%C8%99te",
            "https://dexonline.ro/definitie/fier%C4%83str%C4%83u",
            "https://dexonline.ro/definitie/periu%C8%9B%C4%83",
        ],
        "rationale": "Predicat explicit: Unelte manuale de atelier. Trio: Ciocan, "
        "Clește, Fierăstrău. Periuță de dinți nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_cheese",
        "game": "intrusul",
        "source_id": "aq92_intrusul_cheese",
        "category": "gastronomie",
        "difficulty": "usor",
        "payload": {
            "members": ["n_gas_telemea", "n_gas_urda", "n_v42gas_branza_burduf"],
            "intruder": "n_v24_food_summer_fruit_caisa",
            "group_label": "Sortimente de brânză",
        },
        "sources": [
            "https://dexonline.ro/definitie/telemea",
            "https://dexonline.ro/definitie/urd%C4%83",
            "https://dexonline.ro/definitie/br%C3%A2nz%C4%83",
            "https://dexonline.ro/definitie/cais%C4%83",
        ],
        "rationale": "Predicat explicit: Sortimente de brânză. Trio: Telemea, Urdă, "
        "Brânză de burduf. Caisă nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_pastries",
        "game": "intrusul",
        "source_id": "aq92_intrusul_pastries",
        "category": "gastronomie",
        "difficulty": "usor",
        "payload": {
            "members": ["n_v18gas_amandina", "n_v21gas_ecler", "n_v21gas_savarina"],
            "intruder": "n_gas_mustar",
            "group_label": "Prăjituri din cofetărie",
        },
        "sources": [
            "https://dexonline.ro/definitie/amandin%C4%83",
            "https://dexonline.ro/definitie/ecler",
            "https://dexonline.ro/definitie/savarin%C4%83",
            "https://dexonline.ro/definitie/mu%C8%99tar",
        ],
        "rationale": "Predicat explicit: Prăjituri din cofetărie. Trio: Amandină, "
        "Ecler, Savarină. Muștar nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_geometry",
        "game": "intrusul",
        "source_id": "aq92_intrusul_geometry",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": ["n_v88_school_compas", "n_v88_school_echer", "n_v88_school_raportor"],
            "intruder": "n_v31_cleaning_floor_mop",
            "group_label": "Instrumente din trusa de geometrie",
        },
        "sources": [
            "https://dexonline.ro/definitie/compas",
            "https://dexonline.ro/definitie/echer",
            "https://dexonline.ro/definitie/raportor",
            "https://dexonline.ro/definitie/mop",
        ],
        "rationale": "Predicat explicit: Instrumente din trusa de geometrie. Trio: "
        "Compas, Echer, Raportor. Mop nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_bathroom",
        "game": "intrusul",
        "source_id": "aq92_intrusul_bathroom",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v33_bathroom_fixture_chiuveta",
                "n_v33_bathroom_fixture_cada_baie",
                "n_v33_bathroom_fixture_robinet",
            ],
            "intruder": "n_v24_time_day_ceas",
            "group_label": "Obiecte sanitare racordate la apă",
        },
        "sources": [
            "https://dexonline.ro/definitie/chiuvet%C4%83",
            "https://dexonline.ro/definitie/cad%C4%83",
            "https://dexonline.ro/definitie/robinet",
            "https://dexonline.ro/definitie/ceas",
        ],
        "rationale": "Predicat explicit: Obiecte sanitare racordate la apă. Trio: "
        "Chiuvetă, Cadă de baie, Robinet. Ceas nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_floor_cleaning",
        "game": "intrusul",
        "source_id": "aq92_intrusul_floor_cleaning",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v31_cleaning_floor_mop",
                "n_v88_cleaning_matura",
                "n_v31_cleaning_floor_aspirator",
            ],
            "intruder": "n_v24_school_supplies_stilou",
            "group_label": "Obiecte folosite la curățarea podelei",
        },
        "sources": [
            "https://dexonline.ro/definitie/mop",
            "https://dexonline.ro/definitie/m%C4%83tur%C4%83",
            "https://dexonline.ro/definitie/aspirator",
            "https://dexonline.ro/definitie/stilou",
        ],
        "rationale": "Predicat explicit: Obiecte folosite la curățarea podelei. "
        "Trio: Mop, Mătură, Aspirator. Stilou nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_gardening",
        "game": "intrusul",
        "source_id": "aq92_intrusul_gardening",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v32_garden_soil_lopata",
                "n_v32_garden_soil_grebla",
                "n_v32_garden_water_stropitoare",
            ],
            "intruder": "n_v31_hygiene_oral_pasta_dinti",
            "group_label": "Unelte folosite în grădină",
        },
        "sources": [
            "https://dexonline.ro/definitie/lopat%C4%83",
            "https://dexonline.ro/definitie/grebl%C4%83",
            "https://dexonline.ro/definitie/stropitoare",
            "https://dexonline.ro/definitie/past%C4%83",
        ],
        "rationale": "Predicat explicit: Unelte folosite în grădină. Trio: Lopată, "
        "Greblă, Stropitoare. Pastă de dinți nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_forest_animals",
        "game": "intrusul",
        "source_id": "aq92_intrusul_forest_animals",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v33_forest_animal_urs",
                "n_v33_forest_animal_vulpe",
                "n_v33_forest_animal_veverita",
            ],
            "intruder": "n_v30_animal_farm_oaie",
            "group_label": "Animale sălbatice din pădurile României",
        },
        "sources": [
            "https://dexonline.ro/definitie/urs",
            "https://dexonline.ro/definitie/vulpe",
            "https://dexonline.ro/definitie/veveri%C8%9B%C4%83",
            "https://dexonline.ro/definitie/oaie",
        ],
        "rationale": "Predicat explicit: Animale sălbatice din pădurile României. "
        "Trio: Urs, Vulpe, Veveriță. Oaie nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_farm_animals",
        "game": "intrusul",
        "source_id": "aq92_intrusul_farm_animals",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v30_animal_farm_vaca",
                "n_v30_animal_farm_cal",
                "n_v30_animal_farm_capra",
            ],
            "intruder": "n_v33_forest_animal_lup",
            "group_label": "Animale domestice crescute în gospodărie",
        },
        "sources": [
            "https://dexonline.ro/definitie/vac%C4%83",
            "https://dexonline.ro/definitie/cal",
            "https://dexonline.ro/definitie/capr%C4%83",
            "https://dexonline.ro/definitie/lup",
        ],
        "rationale": "Predicat explicit: Animale domestice crescute în gospodărie. "
        "Trio: Vacă, Cal, Capră. Lup nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_orchard",
        "game": "intrusul",
        "source_id": "aq92_intrusul_orchard",
        "category": "gastronomie",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_food_orchard_mar",
                "n_v24_food_orchard_para",
                "n_v24_food_orchard_pruna",
            ],
            "intruder": "n_v24_food_salad_veg_morcov",
            "group_label": "Fructe care cresc în livadă",
        },
        "sources": [
            "https://dexonline.ro/definitie/m%C4%83r",
            "https://dexonline.ro/definitie/par%C4%83",
            "https://dexonline.ro/definitie/prun%C4%83",
            "https://dexonline.ro/definitie/morcov",
        ],
        "rationale": "Predicat explicit: Fructe care cresc în livadă. Trio: Măr, "
        "Pară, Prună. Morcov nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_duration",
        "game": "intrusul",
        "source_id": "aq92_intrusul_duration",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": ["n_v29_time_units_secunda", "n_v29_time_units_minut", "n_v24_time_day_ora"],
            "intruder": "n_v24_school_supplies_rigla",
            "group_label": "Unități pentru măsurarea duratei",
        },
        "sources": [
            "https://dexonline.ro/definitie/secund%C4%83",
            "https://dexonline.ro/definitie/minut",
            "https://dexonline.ro/definitie/or%C4%83",
            "https://dexonline.ro/definitie/rigl%C4%83",
        ],
        "rationale": "Predicat explicit: Unități pentru măsurarea duratei. Trio: "
        "Secundă, Minut, Oră. Riglă nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_storage",
        "game": "intrusul",
        "source_id": "aq92_intrusul_storage",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_home_storage_dulap",
                "n_v24_home_storage_raft",
                "n_v24_home_storage_comoda_sertare",
            ],
            "intruder": "n_v31_hygiene_hair_sampon",
            "group_label": "Obiecte pentru depozitarea lucrurilor",
        },
        "sources": [
            "https://dexonline.ro/definitie/dulap",
            "https://dexonline.ro/definitie/raft",
            "https://dexonline.ro/definitie/comod%C4%83",
            "https://dexonline.ro/definitie/%C8%99ampon",
        ],
        "rationale": "Predicat explicit: Obiecte pentru depozitarea lucrurilor. "
        "Trio: Dulap, Raft, Comodă cu sertare. Șampon nu satisface "
        "predicatul. Vocabular familiar, fără informații de "
        "actualitate.",
    },
    {
        "id": "iq92_cereals",
        "game": "intrusul",
        "source_id": "aq92_intrusul_cereals",
        "category": "gastronomie",
        "difficulty": "usor",
        "payload": {
            "members": ["n_v84_food_grau", "n_v84_food_orz", "n_v84_food_ovaz"],
            "intruder": "n_v85_food_vanilie",
            "group_label": "Cereale",
        },
        "sources": [
            "https://dexonline.ro/definitie/gr%C3%A2u",
            "https://dexonline.ro/definitie/orz",
            "https://dexonline.ro/definitie/ov%C4%83z",
            "https://dexonline.ro/definitie/vanilie",
        ],
        "rationale": "Predicat explicit: Cereale. Trio: Grâu, Orz, Ovăz. Vanilie nu "
        "satisface predicatul. Vocabular familiar, fără informații de "
        "actualitate.",
    },
    {
        "id": "iq92_nuts",
        "game": "intrusul",
        "source_id": "aq92_intrusul_nuts",
        "category": "gastronomie",
        "difficulty": "usor",
        "payload": {
            "members": ["n_v81_food_pantry_nuca", "n_v85_food_alune_padure", "n_v85_food_migdale"],
            "intruder": "n_v85_food_cacao",
            "group_label": "Miezuri comestibile în coajă tare",
        },
        "sources": [
            "https://dexonline.ro/definitie/nuc%C4%83",
            "https://dexonline.ro/definitie/alun%C4%83",
            "https://dexonline.ro/definitie/migdale",
            "https://dexonline.ro/definitie/cacao",
        ],
        "rationale": "Predicat explicit: Miezuri comestibile în coajă tare. Trio: "
        "Nucă, Alune de pădure, Migdale. Cacao nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_clothing",
        "game": "intrusul",
        "source_id": "aq92_intrusul_clothing",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v30_clothing_everyday_pantaloni",
                "n_v30_clothing_everyday_rochie",
                "n_v30_clothing_everyday_fusta",
            ],
            "intruder": "n_v31_hygiene_hair_pieptene",
            "group_label": "Articole de îmbrăcăminte",
        },
        "sources": [
            "https://dexonline.ro/definitie/pantaloni",
            "https://dexonline.ro/definitie/rochie",
            "https://dexonline.ro/definitie/fust%C4%83",
            "https://dexonline.ro/definitie/pieptene",
        ],
        "rationale": "Predicat explicit: Articole de îmbrăcăminte. Trio: Pantaloni, "
        "Rochie, Fustă. Pieptene nu satisface predicatul. Vocabular "
        "familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_textiles",
        "game": "intrusul",
        "source_id": "aq92_intrusul_textiles",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_home_textiles_patura",
                "n_v24_home_textiles_cearsaf",
                "n_v24_home_textiles_covor",
            ],
            "intruder": "n_v32_workshop_hand_ciocan",
            "group_label": "Textile pentru casă",
        },
        "sources": [
            "https://dexonline.ro/definitie/p%C4%83tur%C4%83",
            "https://dexonline.ro/definitie/cear%C8%99af",
            "https://dexonline.ro/definitie/covor",
            "https://dexonline.ro/definitie/ciocan",
        ],
        "rationale": "Predicat explicit: Textile pentru casă. Trio: Pătură, Cearșaf, "
        "Covor. Ciocan nu satisface predicatul. Vocabular familiar, "
        "fără informații de actualitate.",
    },
    {
        "id": "iq92_building",
        "game": "intrusul",
        "source_id": "aq92_intrusul_building",
        "category": "viata_de_roman",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_home_structure_acoperis",
                "n_v24_home_structure_perete",
                "n_v24_home_structure_tavan",
            ],
            "intruder": "n_v24_transport_personal_motocicleta",
            "group_label": "Părți ale construcției unei case",
        },
        "sources": [
            "https://dexonline.ro/definitie/acoperi%C8%99",
            "https://dexonline.ro/definitie/perete",
            "https://dexonline.ro/definitie/tavan",
            "https://dexonline.ro/definitie/motociclet%C4%83",
        ],
        "rationale": "Predicat explicit: Părți ale construcției unei case. Trio: "
        "Acoperiș, Perete, Tavan. Motocicletă nu satisface predicatul. "
        "Vocabular familiar, fără informații de actualitate.",
    },
    {
        "id": "iq92_emotions",
        "game": "intrusul",
        "source_id": "aq92_intrusul_emotions",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": [
                "n_v24_feeling_difficult_tristete",
                "n_v24_feeling_difficult_frica",
                "n_v24_feeling_difficult_furie",
            ],
            "intruder": "n_v24_feeling_needs_foame",
            "group_label": "Emoții",
        },
        "sources": [
            "https://dexonline.ro/definitie/triste%C8%9Be",
            "https://dexonline.ro/definitie/fric%C4%83",
            "https://dexonline.ro/definitie/furie",
            "https://dexonline.ro/definitie/foame",
        ],
        "rationale": "Predicat explicit: Emoții. Trio: Tristețe, Frică, Furie. Foame "
        "nu satisface predicatul. Vocabular familiar, fără informații "
        "de actualitate.",
    },
    {
        "id": "iq92_sky",
        "game": "intrusul",
        "source_id": "aq92_intrusul_sky",
        "category": "stiinta",
        "difficulty": "usor",
        "payload": {
            "members": ["n_v24_nature_sky_soare", "n_v24_nature_sky_luna", "n_v24_nature_sky_stea"],
            "intruder": "n_v24_food_salad_veg_morcov",
            "group_label": "Corpuri cerești",
        },
        "sources": [
            "https://dexonline.ro/definitie/soare",
            "https://dexonline.ro/definitie/lun%C4%83",
            "https://dexonline.ro/definitie/stea",
            "https://dexonline.ro/definitie/morcov",
        ],
        "rationale": "Predicat explicit: Corpuri cerești. Trio: Soare, Lună, Stea. "
        "Morcov nu satisface predicatul. Vocabular familiar, fără "
        "informații de actualitate.",
    },
    {
        "id": "pq92_associations_01",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_01",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v86_food_frisca", "n_v88_food_smantana_dulce"],
                    "group_label": "Spuma și ingredientul din care o bați",
                },
                {
                    "members": ["n_v31_hygiene_bath_sapun", "n_v31_hygiene_bath_prosop"],
                    "group_label": "Te speli, apoi te usuci",
                },
                {
                    "members": ["n_v24_home_bed_pat", "n_v24_home_bed_saltea"],
                    "group_label": "Mobilier pentru dormit și suportul pe care te întinzi",
                },
                {
                    "members": ["n_v84_food_drojdie", "n_v4gas_paine"],
                    "group_label": "Agent de dospire și produs de panificație",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/fri%C8%99c%C4%83",
            "https://dexonline.ro/definitie/s%C4%83pun",
            "https://dexonline.ro/definitie/prosop",
            "https://dexonline.ro/definitie/pat",
            "https://dexonline.ro/definitie/saltea",
            "https://dexonline.ro/definitie/drojdie",
            "https://dexonline.ro/definitie/p%C3%A2ine",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Frișcă ↔ Smântână dulce pentru frișcă; Săpun "
        "↔ Prosop; Pat ↔ Saltea; Drojdie ↔ Pâine. Fiecare pereche "
        "păstrează o explicație proprie; nicio pereche intenționată nu "
        "este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_02",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_02",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v17fil_garcea", "n_ftv_mugur_mihaescu"],
                    "group_label": "Personaj și actorul care îl interpretează",
                },
                {
                    "members": ["n_v24_time_day_ceas", "n_v24_time_day_ora"],
                    "group_label": "Instrument și unitatea pe care o indică",
                },
                {
                    "members": [
                        "n_v32_garden_container_ghiveci_flori",
                        "n_v32_garden_water_stropitoare",
                    ],
                    "group_label": "Vasul plantei și unealta cu care o uzi",
                },
                {
                    "members": ["n_v33_forest_animal_caprioara", "n_v33_forest_animal_cerb"],
                    "group_label": "Animale sălbatice din familia cervidelor",
                },
            ]
        },
        "sources": [
            "https://www.kanald.ro/avere-mugur-mihaescu-ce-venituri-are-actorul-care-i-a-dat-viata-personajului-garcea-20173461",
            "https://dexonline.ro/definitie/ceas",
            "https://dexonline.ro/definitie/or%C4%83",
            "https://dexonline.ro/definitie/ghiveci",
            "https://dexonline.ro/definitie/stropitoare",
            "https://dexonline.ro/definitie/c%C4%83prioar%C4%83",
            "https://dexonline.ro/definitie/cerb",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Garcea ↔ Mugur Mihăescu; Ceas ↔ Oră; Ghiveci "
        "de flori ↔ Stropitoare; Căprioară ↔ Cerb. Fiecare pereche "
        "păstrează o explicație proprie; nicio pereche intenționată nu "
        "este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_03",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_03",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_spt_david_popovici", "n_v2spo_inot_sportiv"],
                    "group_label": "Sportiv și disciplina sa",
                },
                {
                    "members": ["n_v33_electric_light_bec", "n_v33_electric_control_intrerupator"],
                    "group_label": "Sursa de lumină și comanda ei",
                },
                {
                    "members": ["n_v24_transport_rail_tren", "n_v24_transport_terminals_gara"],
                    "group_label": "Mijloc de transport și locul de îmbarcare",
                },
                {
                    "members": ["n_ion_luca_caragiale", "n_o_scrisoare_pierduta"],
                    "group_label": "Dramaturg și comedie",
                },
            ]
        },
        "sources": [
            "https://www.cosr.ro/public/sportive/popovici-david",
            "https://dexonline.ro/definitie/bec",
            "https://dexonline.ro/definitie/%C3%AEntrerup%C4%83tor",
            "https://dexonline.ro/definitie/tren",
            "https://dexonline.ro/definitie/gar%C4%83",
            "https://ro.wikisource.org/wiki/O_scrisoare_pierdut%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: David Popovici ↔ Înot sportiv; Bec ↔ "
        "Întrerupător de lumină; Tren ↔ Gară; I.L. Caragiale ↔ O "
        "scrisoare pierdută. Fiecare pereche păstrează o explicație "
        "proprie; nicio pereche intenționată nu este refolosită în "
        "această extensie.",
    },
    {
        "id": "pq92_associations_04",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_04",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v4gas_sare", "n_v84_food_saramura"],
                    "group_label": "Substanță și soluția ei în apă",
                },
                {
                    "members": [
                        "n_v24_people_grandparents_bunica",
                        "n_v24_people_grandparents_bunic",
                    ],
                    "group_label": "Părinții părinților",
                },
                {
                    "members": ["n_v30_kitchen_utensil_furculita", "n_v30_kitchen_utensil_lingura"],
                    "group_label": "Tacâmuri",
                },
                {
                    "members": ["n_constantin_brancusi", "n_v20art_domnisoara_pogany"],
                    "group_label": "Sculptor și sculptură",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/sare",
            "https://dexonline.ro/definitie/saramur%C4%83",
            "https://dexonline.ro/definitie/bunic%C4%83",
            "https://dexonline.ro/definitie/bunic",
            "https://dexonline.ro/definitie/furculi%C8%9B%C4%83",
            "https://dexonline.ro/definitie/lingur%C4%83",
            "https://cimec.ro/patrimoniu-mobil/portalul-brancusi/",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Sare ↔ Saramură; Bunică ↔ Bunic; Furculiță ↔ "
        "Lingură; Constantin Brâncuși ↔ Domnișoara Pogany. Fiecare "
        "pereche păstrează o explicație proprie; nicio pereche "
        "intenționată nu este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_05",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_05",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_mihai_eminescu", "n_v21lit_floare_albastra"],
                    "group_label": "Poet și poezie",
                },
                {"members": ["n_gas_telemea", "n_gas_urda"], "group_label": "Sortimente de brânză"},
                {
                    "members": ["n_v32_body_face_pleoapa", "n_v32_body_face_spranceana"],
                    "group_label": "Părți ale feței din jurul ochiului",
                },
                {
                    "members": ["n_v24_food_pantry_faina", "n_v84_food_aluat"],
                    "group_label": "Ingredient de bază și amestecul obținut",
                },
            ]
        },
        "sources": [
            "https://ro.wikisource.org/wiki/Floare_albastr%C4%83",
            "https://dexonline.ro/definitie/telemea",
            "https://dexonline.ro/definitie/urd%C4%83",
            "https://dexonline.ro/definitie/pleoap%C4%83",
            "https://dexonline.ro/definitie/spr%C3%A2ncean%C4%83",
            "https://dexonline.ro/definitie/f%C4%83in%C4%83",
            "https://dexonline.ro/definitie/aluat",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Mihai Eminescu ↔ Floare albastră; Telemea ↔ "
        "Urdă; Pleoapă ↔ Sprânceană; Făină ↔ Aluat. Fiecare pereche "
        "păstrează o explicație proprie; nicio pereche intenționată nu "
        "este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_06",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_06",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_people_relatives_frate", "n_v24_people_relatives_sora"],
                    "group_label": "Copii care au părinți comuni",
                },
                {
                    "members": [
                        "n_v24_transport_personal_bicicleta",
                        "n_v24_transport_personal_motocicleta",
                    ],
                    "group_label": "Vehicule cu două roți",
                },
                {
                    "members": ["n_v32_workshop_hand_ciocan", "n_v32_workshop_fastener_cui"],
                    "group_label": "Unealta cu care bați elementul de fixare",
                },
                {
                    "members": ["n_v24_weather_air_nor", "n_v24_weather_precipitation_ploaie"],
                    "group_label": "Precipitația cade din nori",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/frate",
            "https://dexonline.ro/definitie/sor%C4%83",
            "https://dexonline.ro/definitie/biciclet%C4%83",
            "https://dexonline.ro/definitie/motociclet%C4%83",
            "https://dexonline.ro/definitie/ciocan",
            "https://dexonline.ro/definitie/cui",
            "https://dexonline.ro/definitie/nor",
            "https://dexonline.ro/definitie/ploaie",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Frate ↔ Soră; Bicicletă ↔ Motocicletă; "
        "Ciocan ↔ Cui; Nor ↔ Ploaie. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_07",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_07",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v31_body_lower_calcai", "n_v31_body_lower_glezna"],
                    "group_label": "Părți învecinate ale piciorului",
                },
                {
                    "members": ["n_v24_home_seating_canapea", "n_v24_home_seating_fotoliu"],
                    "group_label": "Mobilier tapițat pentru șezut",
                },
                {
                    "members": ["n_ftv_bobita", "n_v19fil_mihai_bobonete"],
                    "group_label": "Personaj și actorul care îl interpretează",
                },
                {
                    "members": ["n_v24_food_orchard_mar", "n_v24_food_orchard_para"],
                    "group_label": "Fructe de livadă",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/c%C4%83lc%C3%A2i",
            "https://dexonline.ro/definitie/glezn%C4%83",
            "https://dexonline.ro/definitie/canapea",
            "https://dexonline.ro/definitie/fotoliu",
            "https://femeiaalege.protv.ro/stiri/bobita-din-las-fierbinti-te-face-sa-mori-de-ras-si-in-viata-reala-vezi-un-interviu-exclusiv-cu-mihai-bobonete.html",
            "https://dexonline.ro/definitie/m%C4%83r",
            "https://dexonline.ro/definitie/par%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Călcâi ↔ Gleznă; Canapea ↔ Fotoliu; Bobiță ↔ "
        "Mihai Bobonete; Măr ↔ Pară. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_08",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_08",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v29_time_calendar", "n_v4ist_an"],
                    "group_label": "Instrument de organizare și intervalul pe care îl cuprinde",
                },
                {
                    "members": [
                        "n_v24_people_relationships_sot",
                        "n_v24_people_relationships_sotie",
                    ],
                    "group_label": "Parteneri de căsătorie",
                },
                {
                    "members": ["n_simona_halep", "n_spt_simona_wimbledon_2019"],
                    "group_label": "Sportivă și turneu câștigat",
                },
                {"members": ["n_v84_food_orz", "n_v84_food_ovaz"], "group_label": "Cereale"},
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/calendar",
            "https://dexonline.ro/definitie/an",
            "https://dexonline.ro/definitie/so%C8%9B",
            "https://dexonline.ro/definitie/so%C8%9Bie",
            "https://www.wtatennis.com/news/1446826/i-wanted-this-badly-simona-halep-stuns-serena-williams-for-wimbledon-2019-title",
            "https://dexonline.ro/definitie/orz",
            "https://dexonline.ro/definitie/ov%C4%83z",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Calendar ↔ An; Soț ↔ Soție; Simona Halep ↔ "
        "Wimbledon 2019; Orz ↔ Ovăz. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_09",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_09",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": [
                        "n_v33_bathroom_fixture_chiuveta",
                        "n_v33_bathroom_fixture_robinet",
                    ],
                    "group_label": "Vas sanitar și sursa lui de apă",
                },
                {
                    "members": ["n_v3lit_carte", "n_v24_action_language_a_citi"],
                    "group_label": "Obiectul și acțiunea obișnuită",
                },
                {
                    "members": ["n_v24_weather_storm_fulger", "n_v24_weather_storm_tunet"],
                    "group_label": "Lumina și sunetul descărcării electrice",
                },
                {
                    "members": [
                        "n_v31_hygiene_oral_periuta_dinti",
                        "n_v31_hygiene_oral_pasta_dinti",
                    ],
                    "group_label": "Se folosesc împreună pentru curățarea dinților",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/chiuvet%C4%83",
            "https://dexonline.ro/definitie/robinet",
            "https://dexonline.ro/definitie/carte",
            "https://dexonline.ro/definitie/citi",
            "https://dexonline.ro/definitie/fulger",
            "https://dexonline.ro/definitie/tunet",
            "https://dexonline.ro/definitie/periu%C8%9B%C4%83",
            "https://dexonline.ro/definitie/past%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Chiuvetă ↔ Robinet; Carte ↔ a citi; Fulger ↔ "
        "Tunet; Periuță de dinți ↔ Pastă de dinți. Fiecare pereche "
        "păstrează o explicație proprie; nicio pereche intenționată nu "
        "este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_10",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_10",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": [
                        "n_v24_weather_precipitation_ploaie",
                        "n_v24_weather_precipitation_zapada",
                    ],
                    "group_label": "Forme de precipitații",
                },
                {
                    "members": ["n_v84_food_grau", "n_v84_food_gris"],
                    "group_label": "Cereală și produs obținut prin măcinare",
                },
                {
                    "members": ["n_v30_clothing_everyday_fusta", "n_v30_clothing_everyday_rochie"],
                    "group_label": "Articole de îmbrăcăminte",
                },
                {
                    "members": ["n_v81_food_pantry_nuca", "n_v85_food_migdale"],
                    "group_label": "Miezuri comestibile în coajă tare",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/ploaie",
            "https://dexonline.ro/definitie/z%C4%83pad%C4%83",
            "https://dexonline.ro/definitie/gr%C3%A2u",
            "https://dexonline.ro/definitie/gri%C8%99",
            "https://dexonline.ro/definitie/fust%C4%83",
            "https://dexonline.ro/definitie/rochie",
            "https://dexonline.ro/definitie/nuc%C4%83",
            "https://dexonline.ro/definitie/migdale",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Ploaie ↔ Zăpadă; Grâu ↔ Griș; Fustă ↔ "
        "Rochie; Nucă ↔ Migdale. Fiecare pereche păstrează o explicație "
        "proprie; nicio pereche intenționată nu este refolosită în "
        "această extensie.",
    },
    {
        "id": "pq92_associations_11",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_11",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_school_supplies_rigla", "n_v88_school_echer"],
                    "group_label": "Instrumente pentru trasarea liniilor",
                },
                {
                    "members": ["n_v30_clothing_footwear_pantof", "n_v30_clothing_footwear_soseta"],
                    "group_label": "Se poartă împreună în picioare",
                },
                {
                    "members": ["n_v24_home_bed_pat", "n_v24_home_bed_perna"],
                    "group_label": "Mobilier și sprijin pentru cap în timpul somnului",
                },
                {
                    "members": ["n_ion_creanga", "n_v23lit_capra_cu_trei_iezi"],
                    "group_label": "Scriitor și poveste",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/rigl%C4%83",
            "https://dexonline.ro/definitie/echer",
            "https://dexonline.ro/definitie/pantof",
            "https://dexonline.ro/definitie/%C8%99oset%C4%83",
            "https://dexonline.ro/definitie/pat",
            "https://dexonline.ro/definitie/pern%C4%83",
            "https://ro.wikisource.org/wiki/Capra_cu_trei_iezi",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Riglă ↔ Echer; Pantof ↔ Șosetă; Pat ↔ Pernă; "
        "Ion Creangă ↔ Capra cu trei iezi. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_12",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_12",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_people_parents_mama", "n_v24_people_parents_tata"],
                    "group_label": "Părinții",
                },
                {
                    "members": ["n_v33_electric_outlet_priza", "n_v33_electric_plug_stecher"],
                    "group_label": "Piese care se conectează pentru alimentare electrică",
                },
                {
                    "members": ["n_ciprian_porumbescu", "n_v20art_balada_porumbescu"],
                    "group_label": "Compozitor și lucrare muzicală",
                },
                {
                    "members": ["n_v29_time_units_minut", "n_v29_time_units_secunda"],
                    "group_label": "Un minut are șaizeci de secunde",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/mam%C4%83",
            "https://dexonline.ro/definitie/tat%C4%83",
            "https://dexonline.ro/definitie/priz%C4%83",
            "https://dexonline.ro/definitie/%C8%99techer",
            "https://muzeulbucovinei.ro/mnb/obiective-culturale/muzeul-memorial-ciprian-porumbescu",
            "https://dexonline.ro/definitie/minut",
            "https://dexonline.ro/definitie/secund%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Mamă ↔ Tată; Priză electrică ↔ Ștecher; "
        "Ciprian Porumbescu ↔ Balada pentru vioară; Minut ↔ Secundă. "
        "Fiecare pereche păstrează o explicație proprie; nicio pereche "
        "intenționată nu este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_13",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_13",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_home_storage_dulap", "n_v24_home_storage_raft"],
                    "group_label": "Spații pentru depozitare",
                },
                {
                    "members": ["n_v31_hygiene_hair_pieptene", "n_v31_hygiene_hair_sampon"],
                    "group_label": "Obiecte folosite pentru îngrijirea părului",
                },
                {
                    "members": ["n_v32_garden_water_stropitoare", "n_v4gas_apa"],
                    "group_label": "Unealtă și lichidul pentru udarea plantelor",
                },
                {
                    "members": ["n_v3gas_clatite", "n_v17gas_dulceata"],
                    "group_label": "Desert și umplutură dulce",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/dulap",
            "https://dexonline.ro/definitie/raft",
            "https://dexonline.ro/definitie/pieptene",
            "https://dexonline.ro/definitie/%C8%99ampon",
            "https://dexonline.ro/definitie/stropitoare",
            "https://dexonline.ro/definitie/ap%C4%83",
            "https://dexonline.ro/definitie/cl%C4%83tite",
            "https://dexonline.ro/definitie/dulcea%C8%9B%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Dulap ↔ Raft; Pieptene ↔ Șampon; Stropitoare "
        "↔ Apă; Clătite ↔ Dulceață. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_14",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_14",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v29_kitchen_table_cutit", "n_v4gas_paine"],
                    "group_label": "Unealtă și alimentul pe care îl taie",
                },
                {
                    "members": ["n_ioan_slavici", "n_moara_cu_noroc"],
                    "group_label": "Scriitor și nuvelă",
                },
                {
                    "members": ["n_spt_cristina_neagu", "n_v3spo_handbal"],
                    "group_label": "Sportivă și disciplina sa",
                },
                {
                    "members": ["n_v85_food_cacao", "n_v85_food_ciocolata"],
                    "group_label": "Ingredient de bază și produsul făcut din el",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/cu%C8%9Bit",
            "https://dexonline.ro/definitie/p%C3%A2ine",
            "https://ro.wikisource.org/wiki/Moara_cu_noroc",
            "https://www.ihf.info/media-center/news/unstoppable-8-says-farewell-was-my-calling",
            "https://dexonline.ro/definitie/cacao",
            "https://dexonline.ro/definitie/ciocolat%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Cuțit ↔ Pâine; Ioan Slavici ↔ Moara cu "
        "noroc; Cristina Neagu ↔ Handbal; Cacao ↔ Ciocolată. Fiecare "
        "pereche păstrează o explicație proprie; nicio pereche "
        "intenționată nu este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_15",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_15",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_home_appliances_aragaz", "n_v30_kitchen_cookware_tigaie"],
                    "group_label": "Sursa de căldură și vasul pentru prăjit",
                },
                {
                    "members": ["n_gas_sarmale", "n_v2lim_varza"],
                    "group_label": "Preparat și frunzele folosite la învelire",
                },
                {
                    "members": ["n_henri_coanda", "n_efectul_coanda"],
                    "group_label": "Inventator și fenomenul care îi poartă numele",
                },
                {
                    "members": ["n_v31_cleaning_floor_aspirator", "n_v90_household_praf"],
                    "group_label": "Aparatul și murdăria pe care o îndepărtează",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/aragaz",
            "https://dexonline.ro/definitie/tigaie",
            "https://dexonline.ro/definitie/sarmale",
            "https://dexonline.ro/definitie/varz%C4%83",
            "https://acad.ro/acad_membri/membri/Coanda_Henri.html",
            "https://dexonline.ro/definitie/aspirator",
            "https://dexonline.ro/definitie/praf",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Aragaz ↔ Tigaie; Sarmale ↔ Varză; Henri "
        "Coandă ↔ Efectul Coandă; Aspirator ↔ Praf. Fiecare pereche "
        "păstrează o explicație proprie; nicio pereche intenționată nu "
        "este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_16",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_16",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_gas_mamaliga", "n_v84_food_malai"],
                    "group_label": "Preparat și ingredientul său de bază",
                },
                {
                    "members": ["n_v31_body_lower_gamba", "n_v31_body_lower_genunchi"],
                    "group_label": "Părți învecinate ale piciorului",
                },
                {
                    "members": ["n_gas_mujdei", "n_v4gas_usturoi"],
                    "group_label": "Sos și ingredientul care îi dă gustul",
                },
                {
                    "members": ["n_ftv_florin_piersic", "n_v17fil_margelatu"],
                    "group_label": "Actor și personaj",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/m%C4%83m%C4%83lig%C4%83",
            "https://dexonline.ro/definitie/m%C4%83lai",
            "https://dexonline.ro/definitie/gamb%C4%83",
            "https://dexonline.ro/definitie/genunchi",
            "https://dexonline.ro/definitie/mujdei",
            "https://dexonline.ro/definitie/usturoi",
            "https://tvr1.tvr.ro/florin-piersic--90-de-ani-de-poveste-alaturi-de-unul-dintre-cei-mai-iubi--i-actori-din-istoria-teatrului---i-filmului-romanesc_54062.html",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Mămăligă ↔ Mălai; Gambă ↔ Genunchi; Mujdei ↔ "
        "Usturoi; Florin Piersic ↔ Mărgelatu. Fiecare pereche păstrează "
        "o explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_17",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_17",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v4lit_biblioteca", "n_v3lit_carte"],
                    "group_label": "Locul de păstrare și împrumut al cărților",
                },
                {
                    "members": ["n_v30_kitchen_drink_cana", "n_v24_food_snack_ceai"],
                    "group_label": "Băutură și vasul din care o bei",
                },
                {
                    "members": ["n_v32_workshop_hand_surubelnita", "n_v32_workshop_fastener_surub"],
                    "group_label": "Unealta care rotește elementul de fixare",
                },
                {
                    "members": ["n_v84_food_cuptor", "n_v84_food_tava_copt"],
                    "group_label": "Sursa de căldură și vasul folosit la copt",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/bibliotec%C4%83",
            "https://dexonline.ro/definitie/carte",
            "https://dexonline.ro/definitie/can%C4%83",
            "https://dexonline.ro/definitie/ceai",
            "https://dexonline.ro/definitie/%C8%99urubelni%C8%9B%C4%83",
            "https://dexonline.ro/definitie/%C8%99urub",
            "https://dexonline.ro/definitie/cuptor",
            "https://dexonline.ro/definitie/tav%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Bibliotecă ↔ Carte; Cană ↔ Ceai; Șurubelniță "
        "↔ Șurub; Cuptor de bucătărie ↔ Tavă de copt. Fiecare pereche "
        "păstrează o explicație proprie; nicio pereche intenționată nu "
        "este refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_18",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_18",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_school_writing_caiet", "n_v24_school_writing_pix"],
                    "group_label": "Suport și instrument pentru scris",
                },
                {
                    "members": ["n_v88_cleaning_matura", "n_v31_cleaning_floor_faras"],
                    "group_label": "Se folosesc împreună la măturat",
                },
                {
                    "members": ["n_george_enescu", "n_rapsodia_romana"],
                    "group_label": "Compozitor și lucrare muzicală",
                },
                {
                    "members": ["n_v18gas_amandina", "n_v21gas_ecler"],
                    "group_label": "Prăjituri de cofetărie",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/caiet",
            "https://dexonline.ro/definitie/pix",
            "https://dexonline.ro/definitie/m%C4%83tur%C4%83",
            "https://dexonline.ro/definitie/f%C4%83ra%C8%99",
            "https://www.georgeenescu.ro/prime-auditii_doc_31_110-ani-de-la-prima-auditie-absoluta-a-celor-doua-rapsodii-romane-de-george-enescu-23-februarie-1903-ateneul-roman-sub-bagheta-compozitorului_pg_0.htm",
            "https://dexonline.ro/definitie/amandin%C4%83",
            "https://dexonline.ro/definitie/ecler",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Caiet ↔ Pix; Mătură ↔ Făraș; George Enescu ↔ "
        "Rapsodia Română; Amandină ↔ Ecler. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_19",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_19",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v24_school_writing_creion", "n_v24_school_supplies_radiera"],
                    "group_label": "Instrument de scris și obiectul care îi șterge urma",
                },
                {
                    "members": ["n_v31_cleaning_floor_mop", "n_v31_cleaning_water_galeata"],
                    "group_label": "Se folosesc împreună la spălarea podelei",
                },
                {
                    "members": ["n_gas_mustar", "n_gas_mici"],
                    "group_label": "Condiment și preparatul lângă care este servit",
                },
                {
                    "members": ["n_v24_home_surfaces_fereastra", "n_v24_home_surfaces_oglinda"],
                    "group_label": "Obiecte casnice care conțin sticlă",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/creion",
            "https://dexonline.ro/definitie/radier%C4%83",
            "https://dexonline.ro/definitie/mop",
            "https://dexonline.ro/definitie/g%C4%83leat%C4%83",
            "https://dexonline.ro/definitie/mu%C8%99tar",
            "https://dexonline.ro/definitie/mici",
            "https://dexonline.ro/definitie/fereastr%C4%83",
            "https://dexonline.ro/definitie/oglind%C4%83",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Creion ↔ Radieră; Mop ↔ Găleată; Muștar ↔ "
        "Mici; Fereastră ↔ Oglindă. Fiecare pereche păstrează o "
        "explicație proprie; nicio pereche intenționată nu este "
        "refolosită în această extensie.",
    },
    {
        "id": "pq92_associations_20",
        "game": "perechi",
        "source_id": "aq92_perechi_associations_20",
        "category": "viata_de_roman",
        "difficulty": "normal",
        "payload": {
            "pairs": [
                {
                    "members": ["n_v29_kitchen_table_pahar", "n_v4gas_apa"],
                    "group_label": "Băutură și vasul din care o bei",
                },
                {
                    "members": ["n_emil_racovita", "n_speologie"],
                    "group_label": "Cercetător și domeniul explorării peșterilor",
                },
                {
                    "members": [
                        "n_v24_nature_plant_parts_radacina",
                        "n_v24_nature_plant_parts_ramura",
                    ],
                    "group_label": "Părți ale unei plante",
                },
                {
                    "members": ["n_nadia_comaneci", "n_spt_nadia_zecele_perfect"],
                    "group_label": "Sportivă și performanță istorică",
                },
            ]
        },
        "sources": [
            "https://dexonline.ro/definitie/pahar",
            "https://dexonline.ro/definitie/ap%C4%83",
            "https://www.iser.ro/ro/index.html",
            "https://dexonline.ro/definitie/r%C4%83d%C4%83cin%C4%83",
            "https://dexonline.ro/definitie/ramur%C4%83",
            "https://www.cosr.ro/news/anul-nadia-2026-lansat-oficial",
        ],
        "rationale": "Patru asocieri independente din vocabularul cotidian și "
        "cultura generală: Pahar ↔ Apă; Emil Racoviță ↔ Speologie; "
        "Rădăcină ↔ Ramură; Nadia Comăneci ↔ Primul 10 perfect. Fiecare "
        "pereche păstrează o explicație proprie; nicio pereche "
        "intenționată nu este refolosită în această extensie.",
    },
)


def candidate_boards() -> list[dict]:
    """Return independent copies for candidate generation and integrity checks."""
    return deepcopy(list(BOARDS))
