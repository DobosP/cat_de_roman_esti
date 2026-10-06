"""Reverse reviewed deltas when checking earlier content-wave history."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

_V1_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-testing-release/artifact-delta.json"
)
_V1_RECEIPT_SHA256 = "e0d40083ff1e3ba2316ff723cc5e0661e42e2247c78b64676e6c34d956570776"
_V1_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "4162c8db2205ac4f250e29e6e94ec1e0212036d6c38de5660991a8bd010204de",
    "board_rankings_v37.json": "23421501b0e4bc391a62d25a577ed9d08c935a9eb48a550ab0e5b2f0e8367acb",
    "derived_catalog_v38.json": "fe88e7265c68a79884eabb257912630722980dccd7238f3a834c6796aa65b400",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V1_AFTER = {
    "kg_sample.json": "1c74e5fe387b20ed196f76588d1ef96658743776817532c09a17ab9dd0a39b64",
    "games_pack.json": "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
    "board_rankings_v37.json": "bf7a88448ce7cb8d21d95defc745517d97c8542f582d66eadbfb92ef54bd4adc",
    "derived_catalog_v38.json": "bea0732aefeb0af59e99c926f893bc9f6bb54bae3bb371eace238872470ac2a4",
    "cat_mobile_app_pack_contract.json": (
        "82304733284ca62245e0d2ac0abb7b81c991ed1857ca904c990116c5bce280b4"
    ),
}


_V1_2_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-2-content-growth/artifact-delta.json"
)
_V1_2_RECEIPT_SHA256 = "1a5dc1eb4c8b60742a0981baea93a628c819bda790e235e0288e5a297f37adee"
# Independently checked against git 6deab61 and the supported V1.2 writes.
# These pins stay separate from both the receipt and mutable current-content pins.
_V1_2_BASELINE = {
    "kg_sample.json": "1c74e5fe387b20ed196f76588d1ef96658743776817532c09a17ab9dd0a39b64",
    "games_pack.json": "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
    "board_rankings_v37.json": "bf7a88448ce7cb8d21d95defc745517d97c8542f582d66eadbfb92ef54bd4adc",
    "derived_catalog_v38.json": "bea0732aefeb0af59e99c926f893bc9f6bb54bae3bb371eace238872470ac2a4",
    "cat_mobile_app_pack_contract.json": (
        "82304733284ca62245e0d2ac0abb7b81c991ed1857ca904c990116c5bce280b4"
    ),
}
_V1_2_AFTER = {
    "kg_sample.json": "c9f23c4a9dab1281ad91baaf0e2c836a5b7ab9a6d5f2776799908d76e10f4b85",
    "games_pack.json": "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
    "board_rankings_v37.json": "96409c88927a60e9d6d379237af88a57aef6b40279520bf54f64214017b45806",
    "derived_catalog_v38.json": "1340147300b3d9d174e09d899ac8eaf91756ca0470d0550121af66751ea92d71",
    "cat_mobile_app_pack_contract.json": (
        "8735d304a7d9734a53c03307c034093c910c1a931e73c40df346ed25700f1438"
    ),
}
_V1_2_REVIEW_BINDINGS = {
    "graph_proposal_sha256": "2aabb5e017fda46910f354a6bbce0c39dfdda8a5de215dce18bbeabc67683111",
    "graph_factual_sha256": "96ced04cb238ed93d8f2ee1140d41c530125723a957d3b7ecabdb3c74a43cf94",
    "graph_quality_sha256": "508f457f2dd6b6b95e503044dc4499cd664c99590585d4dd5f838cf467a1acc7",
}
_V1_2_TABLES = {
    "kg_sample.json": {"kg_nodes", "kg_edges", "kg_puzzles"},
    "games_pack.json": {"conexiuni", "contexto", "lant", "alchimie"},
    "board_rankings_v37.json": {"boards"},
    "derived_catalog_v38.json": {"boards"},
    "cat_mobile_app_pack_contract.json": {"kg_nodes", "kg_edges", "kg_puzzles"},
}
_V1_2_ALIASES = {
    "n_v4via_lift": (
        "ascensor", "ascensorul", "ascensoare", "ascensoarele", "ascensorului", "ascensoarelor",
    ),
    "n_v4gas_rosie": ("tomată", "tomate", "tomatele", "tomatei", "tomatelor"),
    "n_vioara": ("scripcă", "scripci", "scripcile", "scripcii", "scripcilor"),
    "n_v4soc_magazin": (
        "prăvălie", "prăvălia", "prăvălii", "prăvăliile", "prăvăliei", "prăvăliilor",
    ),
}
_V1_2_PATH_IDS = {"n_v4geo_carare", "n_v4geo_poteca"}
_V1_2_NEW_EDGE = {
    "id": "de8800", "src_id": "n_v4geo_carare", "dst_id": "n_v4geo_poteca",
    "relation": "synonym_of", "label_ro": "sinonime pentru un drum îngust de mers pe jos",
    "strength": 0.95, "is_distractor": 0, "bidirectional": 1,
}
# Native rendering sorted dictionary keys without changing any ranked/derived row.
# Restore only the finite baseline orders independently inventoried from git 6deab61.
_V1_2_KEY_ORDERS = {
    "board_rankings_v37.json": {
        "": (("meta", "boards"),),
        "/boards/*": ((
            "id", "game", "status", "romanian_familiarity", "play_quality",
            "pilot_score", "rank", "pilot_eligible", "selection_weight",
        ),),
    },
    "derived_catalog_v38.json": {
        "": (("meta", "boards"),),
        "/boards/*": ((
            "id", "game", "source_id", "category", "difficulty", "romanian_familiarity",
            "play_quality", "standard_score", "starter_score", "starter_eligible",
            "standard_rank", "starter_rank", "payload",
        ),),
        "/boards/*/payload": (("members", "intruder", "group_label"), ("pairs",)),
        "/boards/*/payload/pairs/*": (("members", "group_label"),),
    },
}


# Independently fixed from git 18832d4 and supported V1.3 graph writes.
# Existing V1/V1.2 receipt and artifact pins remain unchanged.
_V1_3_GRAPH_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-3-everyday-concepts/graph-installation.json"
)
_V1_3_GRAPH_RECEIPT_SHA256 = "92ba14415cad62aaf1fb0b8578852e8efeaea090d085ae64448862bb32763e3e"
_V1_3_BASELINE = dict(_V1_2_AFTER)
_V1_3_AFTER = {
    "kg_sample.json": "d035f616b4aef5077d77d9cbbdefbd74c1ce2b360a1874a0533a0bd43bb04f63",
    "board_rankings_v37.json": "e24954508573a06c885be3163b3e25c011a14809a7b358cb0aad004dad9a8f2b",
    "derived_catalog_v38.json": "b4ae19266627b738ebe29928acc5952da9be98415fb8632870243e8634a32ad9",
    "games_pack.json": _V1_2_AFTER["games_pack.json"],
    "cat_mobile_app_pack_contract.json": (
        "f5ebc91f3cefb2fdc9755ea015d1eae9e58a2edf722621f273e73ef937d82e94"
    ),
}
_V1_3_REVIEW_BINDINGS = {
    "source_module_sha256": "df08b82ecb038f191bb158c520987d76705a453c8cf6b736913c644863d825c7",
    "proposal_sha256": "cd8bf5927d7dcc33e5207c99a06bb10a043c2b0220636265d3d6aecba6b938b3",
    "raw_factual_review_sha256": "333d1f5adc09fd13acecc2d52e799e18898b02b650a7b91d95471d0a69615248",
    "raw_quality_review_sha256": "052714f6a8d2433779998211bfc57f8152f8af8dc38b0cdc65367def9f372b0a",
}
_V1_3_NODE_IDS = (
    "n_v1_3_home_balama", "n_v1_3_material_lemn", "n_v1_3_clothing_fermoar",
)
_V1_3_DEGREES = {
    "n_v4sti_copac": (9, 10), "n_v4via_usa": (42, 43),
    "n_v23via_ghiozdan": (13, 14), "n_v24_home_surfaces_fereastra": (4, 5),
    "n_v24_home_storage_dulap": (7, 8), "n_v24_home_seating_scaun": (5, 6),
    "n_v30_clothing_everyday_pantaloni": (5, 6),
    "n_v30_clothing_everyday_fusta": (5, 6), "n_v30_clothing_outer_geaca": (5, 6),
    "n_v32_workshop_fastener_surub": (5, 7), "n_v32_workshop_cut_fierastrau": (4, 5),
}
_V1_3_RANK_FIELDS = {
    "ct_viata_de_roman_364": {"play_quality": (89, 91)},
    "ct_muzica_168": {"rank": (122, 123)},
    "ct_societate_290": {"rank": (123, 124)},
    "ct_stiinta_189": {"rank": (124, 125)},
    "ct_viata_de_roman_377": {
        "pilot_score": (77, 78), "play_quality": (88, 91), "rank": (125, 122),
    },
}
_V1_3_CATALOG_BASELINE = {
    "quick_games_v92.json": "cc242a902fd4c040f0e52da94ec95683a9bbcdab41f4b9fb72de5a9c5ff5659c",
    "alchimie_discovery_world_v92.json": (
        "4a6056f3138d0231752056fb588554ee8b4aaa9364511103329ea30120bec1c3"
    ),
    "alchimie_recipe_extensions_v92.json": (
        "9b7da100fb59f416667c0f23c04947f61d3d0e07d5712d57176293538302f1e3"
    ),
}


_V1_3_CATALOG_AFTER = {
    "alchimie_recipe_extensions_v92.json": (
        "b1caa2a46f0d9a2e72b25404fd991f62a20b65cf8604c292170d0efa941757a5"
    ),
    "quick_games_v92.json": "99db98d64b5b7c103ee70eab2b2b79b04d4ff62072942a159caa65518375ed9f",
    "alchimie_discovery_world_v92.json": (
        "28d73ca0c51883f24f370becd6c1fde1eb1c7d034c4be60cd64e8e7c94fbf8d6"
    ),
}
_V1_3_CATALOG_DELTA = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-3-everyday-concepts/reference/catalog-history-quick-world.json"
)
_V1_3_CATALOG_DELTA_SHA256 = "29aa6786173370f6ce31348acc41ab07f500db2d2c80f7bf95d9a431e9dabba0"


_V1_3_EXTENSION_DELTA = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-3-everyday-concepts/reference/catalog-history-extensions.json"
)
_V1_3_EXTENSION_DELTA_SHA256 = "bbf13df29b4437eef2293aedc329527c5a0708ecae9ebff94e7ef6a908ad92fd"


_V1_2_EXTENSION_HISTORY = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-3-everyday-concepts/reference/catalog-history-v1-2-extensions.json"
)
_V1_2_EXTENSION_HISTORY_SHA256 = "6d24f62277eae019bdb813a52050ab232bb7d64ccb8a038bed2855af07c468ca"


# V1.4 pins are actual supported writes independently compared with git46641d6.
# All previous wave literals and signed receipts remain unchanged.
_V1_4_GRAPH_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-4-time-links-and-predicates/graph-installation.json"
)
_V1_4_GRAPH_RECEIPT_SHA256 = "13f792c55e1cb5662b9fa4a8d4e86f54a987443ccc6a089abb177be9734cc5eb"
_V1_4_BASELINE = dict(_V1_3_AFTER)
_V1_4_AFTER = {
    "kg_sample.json": "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6",
    "board_rankings_v37.json": "58fa3d6b02b983cdfed05c9383057acfaccbd200612d3eb97e8279318b1f55ef",
    "derived_catalog_v38.json": "25059439b5c46a04263c229a8a3b9b4fc285240af60e15b7f1fdffa1a98f0c01",
    "games_pack.json": _V1_3_AFTER["games_pack.json"],
    "cat_mobile_app_pack_contract.json": (
        "2f756c7d71f65a1367648d477c67d6d1af0bd19411149667b77f3cf77a6153b8"
    ),
}
_V1_4_DEGREES = {
    "n_v24_time_day_ora": (8, 10), "n_v24_time_day_zi": (9, 10),
    "n_v29_time_units_minut": (4, 5),
}
_V1_4_ALIASES = {
    "before": ["ceasul", "ceasuri", "ceasurile"],
    "after": ["ceasul", "ceasuri", "ceasurile", "ceasornic", "ceasornice"],
}
_V1_4_NEW_EDGES = [
    {"id": "de8813", "src_id": "n_v24_time_day_ora", "dst_id": "n_v29_time_units_minut",
     "relation": "has_part_time", "label_ro": "ca unitate de durată, are șaizeci de minute",
     "strength": 0.99, "is_distractor": 0, "bidirectional": 0},
    {"id": "de8814", "src_id": "n_v24_time_day_zi", "dst_id": "n_v24_time_day_ora",
     "relation": "has_part_time", "label_ro": "ca unitate de durată, are douăzeci și patru de ore",
     "strength": 0.99, "is_distractor": 0, "bidirectional": 0},
]
_V1_4_CATALOG_BASELINE = dict(_V1_3_CATALOG_AFTER)
_V1_4_CATALOG_AFTER = {
    "quick_games_v92.json": "a21b3c6e50be6947ea8b9ac181f337566db9e4809dd5165a203338fff20d8609",
    "alchimie_discovery_world_v92.json": (
        "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"
    ),
    "alchimie_recipe_extensions_v92.json": (
        "1dd346c1786ea39d241f534e6a411c1297160771d3fbfa7f89a47fd22f586fb7"
    ),
}
_V1_4_CATALOG_DELTA = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v1-4-time-links-and-predicates/reference/catalog-history.json"
)
_V1_4_CATALOG_DELTA_SHA256 = "dc598d4ac54a16d0a92e2e7e2d5226c4f2e97f8ac750e55e326cb8c45b9e87e7"


_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v80-clatite-target/artifact-delta.json"
)
_V81_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v81-nuca-feedback/artifact-delta.json"
)
_V82_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v82-playable-content-batch/artifact-delta.json"
)
_V83_REVIEW = Path(__file__).resolve().parents[1] / "docs/reviews/v83-food-input-and-feedback"
_V84_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v84-six-game-graph-quality/artifact-delta.json"
)
_V85_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v85-ingredient-feedback-and-board-clarity/artifact-delta.json"
)
_V86_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v86-preparation-and-route-quality/artifact-delta.json"
)
_V87_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v87-snack-and-action-quality/artifact-delta.json"
)
_V88_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v88-cross-game-quality/artifact-delta.json"
)

_V89_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v89-feedback-and-conexiuni-recovery/artifact-delta.json"
)

_V90_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v90-household-discovery-and-critique-gates/artifact-delta.json"
)

_V91_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v91-recovery-and-mobile-clarity/artifact-delta.json"
)

_V92_ENTRY_SESSION_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v92-entry-creation-and-gui/artifact-delta.json"
)
# Pin the generated receipt as well as complete artifacts on both sides of its delta.
_V92_ENTRY_SESSION_RECEIPT_SHA256 = (
    "9133bcdef3ad91679208a9b60ef690aaa6df58b0333242ac65a70b8af16f732b"
)
_V92_ENTRY_SESSION_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_368"},
    "contexto": {"ct_geografie_365", "ct_muzica_366", "ct_personalitati_367"},
    "lant": {"lt_literatura_236"},
    "alchimie": set(),
}

_V92_SESSION03_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v92-session03-vocabulary-and-interface/artifact-delta.json"
)
# Pin the complete final receipt independently of every before/after artifact hash.
_V92_SESSION03_RECEIPT_SHA256 = (
    "8c990bc5645400e83b18bda92157dddeef45a18f9d66f1648c1ece7a9b29fd6c"
)
_V92_SESSION03_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "9c0a8fde33742ad5230d1697fe7617eabfc8a257a6409562e3b0357c0b8fc77b",
    "board_rankings_v37.json": "cdc148bfc95c9791b8b941b7c537a04b72d8d21398e1b258cf8e743ac9bdbde5",
    "derived_catalog_v38.json": "931278ac590aa1d4904e15d4a30990a349fe82af09cbbb1b9c1a3e3c1461671a",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V92_SESSION03_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_369"},
    "contexto": {"ct_istorie_368", "ct_literatura_369"},
    "lant": {"lt_arta_cultura_237", "lt_istorie_238"},
    "alchimie": set(),
}



_V93_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v93-words-and-game-quality/artifact-delta.json"
)
_V93_RECEIPT_SHA256 = "4fad0ef7db0131ed1e74bd881506dc2b9d86e6b09bc5c6832ba19f29292518f5"
_V93_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "02b966eacaa851a9b20c4f36e0ee50c217e49670553da462313b16830b2c13e6",
    "board_rankings_v37.json": "e467823999d6b20bd0abeb6a41ceb239faaf7c600afe7d9df3adfc65daad3b12",
    "derived_catalog_v38.json": "de2f46a72c23e5ecbd496d3a4314a48f0d4f636b71aa5ba4662bccc837298449",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V93_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_370"},
    "contexto": {"ct_gastronomie_370", "ct_gastronomie_371"},
    "lant": {"lt_geografie_239", "lt_literatura_240"},
    "alchimie": set(),
}

_V94_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v94-words-and-clearer-connections/artifact-delta.json"
)
_V94_RECEIPT_SHA256 = "803fd0860796c54159df54fd486c80c16d4e78f5133ee151162745c8569202a1"
_V94_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "573e921cbe54cb482535584a22e55183c4b7add9b0a9a92a1400f9dae4fd01d8",
    "board_rankings_v37.json": "5e29e48a7d684d23d5532f38d80fb996c92d3474744b20a0159111ac7b41bc76",
    "derived_catalog_v38.json": "46360ac6a77fff6cdab2f86500dcadc348243f71bab71eea01111e76bf80f2c4",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V94_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_371"},
    "contexto": {"ct_gastronomie_372", "ct_viata_de_roman_373"},
    "lant": {"lt_gastronomie_241"},
    "alchimie": set(),
}
_V94_LEDGER_SHA256 = "01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_V94_REJECTED_LANT = {
    "record_sha256": "a23970fe742c5674a07bc3b5c3eda183f9f3e61355974d3a231daa31168af5b5",
    "pair_sha256": "2b3185659e407d75fd4940708cf77460138141b9a67c952caf3e6ba6bf067401",
    "review_binding": "sha256:31c5fd57edeb74888ae689ebcfc430d8dc4150d6bdb975dc7e9ec5719007adb3",
    "source_gate_sha256": "bf30221d7d4f87c090d1f7c60c2d2e34dff2cabc3dde747e83c014c95f65047a",
    "start": "n_v17geo_sfinxul_bucegi",
    "target": "n_v20geo_crucea_caraiman",
}

_V95_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v95-discovery-and-game-quality/artifact-delta.json"
)
_V95_RECEIPT_SHA256 = "7672de9ef287a7808a12d77d11183b0b3741f6d969998ec026de9367f7fe47e1"
_V95_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "7d28b9df887fe561150bc582f390df0dde4f8c292e5550055bbe84e9e8d90990",
    "board_rankings_v37.json": "82f128edb3ccdd8208d41c43b7eb77df1e8d528d2aaea1fed5972712047255ed",
    "derived_catalog_v38.json": "4088402b80b78946e6f9cb7ee5379c9c3f32438801611008f266101625bb428d",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V95_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_372"},
    "contexto": {"ct_viata_de_roman_374", "ct_viata_de_roman_375"},
    "lant": {"lt_gastronomie_243", "lt_gastronomie_244"},
    "alchimie": set(),
}


_V96_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v96-words-and-input-clarity/artifact-delta.json"
)
_V96_RECEIPT_SHA256 = "703f7da7adb78213c2958eb45f4769122a8bb3020312bf45d5f89708b6305666"
_V96_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "27b1dba81a2e02d1e2616a1ad4e6eceefe12d189a86a0913c3655adee99bb3cf",
    "board_rankings_v37.json": "b4c32d0ff65e024e4bd2e292c03e5382f0927c7c388367bf1f80bd7a3c09a831",
    "derived_catalog_v38.json": "5e27495fcc34980ced41a7bbd5c0b61d703c459489d08d6b7322dac197fd7e96",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V96_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_373"},
    "contexto": {"ct_viata_de_roman_376"},
    "lant": {"lt_gastronomie_245"},
    "alchimie": set(),
}


_V97_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v97-discovery-continuity-and-new-words/artifact-delta.json"
)
_V97_RECEIPT_SHA256 = "b7e6a500524eb31c78b0b8a9fd05ed60bcb990657d7fd2af73e91b3ef64683ec"
_V97_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "f2538a91726da87a519f8efac5d3a9993a8a23445879af817f08bdabd478e307",
    "board_rankings_v37.json": "bee608938a113922842ec987bf44269ae086f45aaeb9c54f68e39c8f160bd9d3",
    "derived_catalog_v38.json": "9c46598b19acd30e82cf7bf542c82b8fcfe5039f607bc689ef27a98e78e3d76c",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V97_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_374"},
    "contexto": {"ct_viata_de_roman_377"},
    "lant": {"lt_gastronomie_246"},
    "alchimie": set(),
}


# The V92 expansion adds exactly 4 Conexiuni, 8 Contexto and 13 Lanț records.
# Pin complete current bytes before peeling it; never replace historical wave hashes.
_V92_ARTIFACT_HASHES = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "62c1eaaa7bb72674cf59a66f9b543d911749d52973155f6b201d796d97d6ea4a",
    "board_rankings_v37.json": "6f2662615b686a492b41f2d689a7ba6b380b62d7b8cecc5e7a3c9788d1dce641",
    "derived_catalog_v38.json": "09e6b1caa3ed586264a85d3d9807f0173384c02c80102dae072d14665432f2aa",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V92_ADDED_IDS = {
    "conexiuni": (
        "cx_limba_364",
        "cx_viata_de_roman_365",
        "cx_viata_de_roman_366",
        "cx_viata_de_roman_367",
    ),
    "contexto": (
        "ct_film_tv_357",
        "ct_film_tv_358",
        "ct_film_tv_359",
        "ct_gastronomie_360",
        "ct_gastronomie_361",
        "ct_sport_362",
        "ct_viata_de_roman_363",
        "ct_viata_de_roman_364",
    ),
    "lant": (
        "lt_film_tv_223",
        "lt_gastronomie_224",
        "lt_geografie_225",
        "lt_geografie_226",
        "lt_geografie_227",
        "lt_geografie_228",
        "lt_istorie_229",
        "lt_literatura_230",
        "lt_literatura_231",
        "lt_sport_232",
        "lt_sport_233",
        "lt_sport_234",
        "lt_stiinta_235",
    ),
    "alchimie": (),
}
# Exact (V91 weight, V92 weight) transitions caused by the larger ranked shelves.
_V92_WEIGHT_CHANGES = {
    "ct_gastronomie_131": (3, 2),
    "ct_gastronomie_132": (3, 2),
    "ct_geografie_028": (3, 2),
    "ct_limba_046": (2, 1),
    "ct_limba_223": (5, 4),
    "ct_literatura_230": (2, 1),
    "ct_muzica_241": (4, 3),
    "ct_muzica_244": (4, 3),
    "ct_personalitati_075": (4, 3),
    "cx_gastronomie_173": (5, 4),
    "cx_gastronomie_297": (5, 4),
    "cx_gastronomie_301": (5, 4),
    "cx_istorie_034": (3, 2),
    "cx_istorie_117": (2, 1),
    "cx_istorie_118": (4, 3),
    "cx_literatura_128": (3, 2),
    "cx_meme_net_045": (4, 3),
    "cx_meme_net_267": (4, 3),
    "cx_viata_de_roman_313": (5, 4),
    "lt_arta_cultura_003": (2, 1),
    "lt_arta_cultura_092": (3, 2),
    "lt_film_tv_011": (3, 2),
    "lt_film_tv_098": (4, 3),
    "lt_gastronomie_221": (5, 4),
    "lt_istorie_171": (4, 3),
    "lt_muzica_055": (3, 2),
    "lt_muzica_137": (5, 4),
    "lt_muzica_141": (4, 3),
    "lt_personalitati_067": (3, 2),
    "lt_personalitati_143": (5, 4),
    "lt_personalitati_149": (2, 1),
    "lt_societate_150": (4, 3),
    "lt_sport_080": (3, 2),
    "lt_stiinta_203": (2, 1),
    "lt_viata_de_roman_089": (4, 3),
}


def before_v92_artifact(current: dict, filename: str) -> dict:
    """Peel the exact reviewed V92 delta and reproduce complete 75584bf artifact bytes."""
    current = before_v92_entry_session_artifact(current, filename)
    indent = 2 if filename == "kg_sample.json" else 1

    def digest(value):
        blob = (json.dumps(value, ensure_ascii=False, indent=indent) + "\n").encode()
        return hashlib.sha256(blob).hexdigest()

    assert filename in _V92_ARTIFACT_HASHES
    assert digest(current) == _V92_ARTIFACT_HASHES[filename]
    restored = deepcopy(current)
    previous = json.loads(_V91_RECEIPT.read_bytes())["files"][filename]
    if filename == "games_pack.json":
        assert sum(len(ids) for ids in _V92_ADDED_IDS.values()) == 25
        for game, added in _V92_ADDED_IDS.items():
            rows = restored[game]
            assert {row["id"] for row in rows if row["id"] in added} == set(added)
            assert all(row["status"] == "approved" for row in rows if row["id"] in added)
            restored[game] = [row for row in rows if row["id"] not in added]
    elif filename == "board_rankings_v37.json":
        added = {item_id for ids in _V92_ADDED_IDS.values() for item_id in ids}
        rows = restored["boards"]
        assert {row["id"] for row in rows if row["id"] in added} == added
        restored["boards"] = [row for row in rows if row["id"] not in added]
        ranks: Counter[str] = Counter()
        changed = set()
        for row in restored["boards"]:
            ranks[row["game"]] += 1
            row["rank"] = ranks[row["game"]]
            if row["id"] in _V92_WEIGHT_CHANGES:
                before, after = _V92_WEIGHT_CHANGES[row["id"]]
                assert row["selection_weight"] == after
                row["selection_weight"] = before
                changed.add(row["id"])
        assert changed == set(_V92_WEIGHT_CHANGES)
    # The core derived board payloads, shared KG and mobile rows are not rewritten.
    # Their only potential inverse is the exact historical non-table metadata.
    head = {key for key, value in restored.items() if not isinstance(value, list)}
    assert head == set(previous["head_after"])
    restored.update(deepcopy(previous["head_after"]))
    assert digest(restored) == previous["after_sha256"]
    return restored


def _reverse_reviewed_delta(current: dict, filename: str, receipt_path: Path) -> dict:
    """Peel only exact reviewed additions/corrections before checking old wave pins."""
    receipt = json.loads(receipt_path.read_bytes())["files"][filename]
    restored = deepcopy(current)
    head = {key: value for key, value in restored.items() if not isinstance(value, list)}
    assert head == receipt["head_after"]
    for table, changes in receipt["tables"].items():
        rows = restored[table]
        assert isinstance(rows, list)
        for added in changes["added"]:
            assert rows.count(added) == 1
            rows.remove(added)
        by_id = {row["id"]: row for row in rows}
        assert len(by_id) == len(rows)
        for row_id, change in changes["changed"].items():
            assert by_id[row_id] == change["after"]
            by_id[row_id] = change["before"]
        rows = [by_id[row["id"]] for row in rows]
        for removal in sorted(changes["removed"], key=lambda record: record["index"]):
            row = removal["row"]
            assert row["id"] not in by_id
            assert 0 <= removal["index"] <= len(rows)
            rows.insert(removal["index"], row)
            by_id[row["id"]] = row
        if (order := changes["baseline_order"]) is not None:
            assert len(order) == len(set(order)) == len(rows)
            assert set(order) == set(by_id)
            rows = [by_id[row_id] for row_id in order]
        restored[table] = rows
    for key in head:
        if key not in receipt["head_before"]:
            del restored[key]
    restored.update(receipt["head_before"])
    return restored


def _reverse_bound_delta(
    current: dict, filename: str, receipt_path: Path, *,
    baseline_key_orders: dict[str, tuple[tuple[str, ...], ...]] | None = None,
) -> dict:
    """Check full bytes; optionally restore independently fixed dictionary orders."""
    receipt = json.loads(receipt_path.read_bytes())["files"][filename]
    indent = 2 if filename == "kg_sample.json" else 1

    def digest(value):
        blob = (json.dumps(value, ensure_ascii=False, indent=indent) + "\n").encode()
        return hashlib.sha256(blob).hexdigest()

    assert digest(current) == receipt["after_sha256"]
    restored = _reverse_reviewed_delta(current, filename, receipt_path)
    if baseline_key_orders is not None:
        for orders in baseline_key_orders.values():
            assert orders and all(len(order) == len(set(order)) for order in orders)
            assert len({frozenset(order) for order in orders}) == len(orders)
        visited: set[str] = set()

        def reorder(value, path: str):
            if isinstance(value, dict):
                keys = tuple(value)
                if path in baseline_key_orders:
                    matching = [order for order in baseline_key_orders[path]
                                if set(order) == set(value)]
                    assert len(matching) == 1
                    keys = matching[0]
                    visited.add(path)
                return {key: reorder(value[key], path + "/" + key) for key in keys}
            if isinstance(value, list):
                return [reorder(row, path + "/*") for row in value]
            return value

        restored = reorder(restored, "")
        assert visited == set(baseline_key_orders)
    assert digest(restored) == receipt["baseline_sha256"]
    return restored


def before_v92_entry_session_artifact(current: dict, filename: str) -> dict:
    """Restore complete c0ead5e bytes, rejecting drift before removing new records."""
    current = before_v92_session03_artifact(current, filename)
    receipt_blob = _V92_ENTRY_SESSION_RECEIPT.read_bytes()
    assert hashlib.sha256(receipt_blob).hexdigest() == _V92_ENTRY_SESSION_RECEIPT_SHA256
    files = json.loads(receipt_blob)["files"]
    assert set(files) == set(_V92_ARTIFACT_HASHES)
    assert filename in _V92_ARTIFACT_HASHES
    receipt = files[filename]
    assert receipt["baseline_sha256"] == _V92_ARTIFACT_HASHES[filename]
    expected_ids = {item_id for ids in _V92_ENTRY_SESSION_ADDED_IDS.values()
                    for item_id in ids}
    assert len(expected_ids) == 5
    for table, changes in receipt["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V92_ENTRY_SESSION_ADDED_IDS
            added = changes["added"]
            assert {row["id"] for row in added} == _V92_ENTRY_SESSION_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in added)
            assert not changes["changed"]
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V92_ENTRY_SESSION_RECEIPT)


def before_v92_session03_artifact(current: dict, filename: str) -> dict:
    """Restore exact 0b51e03 bytes before any older content inverse runs."""
    current = before_v93_artifact(current, filename)
    receipt_blob = _V92_SESSION03_RECEIPT.read_bytes()
    assert hashlib.sha256(receipt_blob).hexdigest() == _V92_SESSION03_RECEIPT_SHA256
    receipt = json.loads(receipt_blob)
    assert receipt["baseline_commit"] == "0b51e03c983bcbfc042807b4eb97e59a8a9e7781"
    files = receipt["files"]
    assert set(files) == set(_V92_SESSION03_BASELINE)
    assert filename in _V92_SESSION03_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V92_SESSION03_BASELINE[filename]
    expected_ids = set().union(*_V92_SESSION03_ADDED_IDS.values())
    assert len(expected_ids) == 5
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V92_SESSION03_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V92_SESSION03_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V92_SESSION03_RECEIPT)


def before_v93_artifact(current: dict, filename: str) -> dict:
    """Restore exact bf9d814 bytes before any historical content inverse runs."""
    receipt_blob = _V93_RECEIPT.read_bytes()
    assert hashlib.sha256(receipt_blob).hexdigest() == _V93_RECEIPT_SHA256
    current = before_v94_artifact(current, filename)
    receipt = json.loads(receipt_blob)
    assert receipt["baseline_commit"] == "bf9d8145f2797b7e1ea125531f81a98d2ff6098c"
    files = receipt["files"]
    assert set(files) == set(_V93_BASELINE)
    assert filename in _V93_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V93_BASELINE[filename]
    expected_ids = set().union(*_V93_ADDED_IDS.values())
    assert len(expected_ids) == 5
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V93_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V93_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V93_RECEIPT)


def before_v94_artifact(current: dict, filename: str) -> dict:
    """Restore exact c971846 content before evaluating any earlier wave."""
    current = before_v95_artifact(current, filename)
    blob = _V94_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V94_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "c971846feac31e73c3a2a2593c66265f29603e58"
    files = receipt["files"]
    assert set(files) == set(_V94_BASELINE) and filename in _V94_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V94_BASELINE[filename]
    expected_ids = set().union(*_V94_ADDED_IDS.values())
    assert len(expected_ids) == 4
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V94_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V94_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 242
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V94_RECEIPT)


def before_v95_artifact(current: dict, filename: str) -> dict:
    """Restore complete cf6b28b bytes before evaluating the original V94 transition."""
    current = before_v96_artifact(current, filename)
    blob = _V95_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V95_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "cf6b28bc0d247be33e494be1395ca7d676a9f4b4"
    files = receipt["files"]
    assert set(files) == set(_V95_BASELINE) and filename in _V95_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V95_BASELINE[filename]
    expected_ids = set().union(*_V95_ADDED_IDS.values())
    assert len(expected_ids) == 5
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V95_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V95_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 244
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V95_RECEIPT)


def before_v96_artifact(current: dict, filename: str) -> dict:
    """Restore complete 1457786 bytes before evaluating the original V95 transition."""
    current = before_v97_artifact(current, filename)
    blob = _V96_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V96_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "14577863038378c734c7b2e0e8b33ea8158f318b"
    files = receipt["files"]
    assert set(files) == set(_V96_BASELINE) and filename in _V96_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V96_BASELINE[filename]
    expected_ids = set().union(*_V96_ADDED_IDS.values())
    assert len(expected_ids) == 3
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V96_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V96_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 245
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V96_RECEIPT)



def _v1_4_graph_receipt() -> dict:
    blob = _V1_4_GRAPH_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_4_GRAPH_RECEIPT_SHA256
    receipt = json.loads(blob)
    expected = {
        "schema": "v1-4-exact-supported-graph-installation-v1",
        "baseline_commit": "46641d6f9963f92941d12f5955e5eb40a2d8fb56",
        "proposal_sha256": "6cae1819c10164f5181501eb86de75b32592af035f4198e642a43f63f798085d",
        "module_sha256": "b7c5af54445617975796759ecf22e1c814b749c8bd64dbeb0cd69d3a2dc4326a",
        "raw_factual_review_sha256": (
            "47d0f89b9ddbe6630f63764239365b78e14db40d12eaf04dc18c281e280e37ce"
        ),
        "raw_quality_review_sha256": (
            "3c2f8d9b1b66411741a254d26d028cd6b6dfb4972537163ab37a24784ff6e3e3"
        ),
        "kg_before_sha256": _V1_4_BASELINE["kg_sample.json"],
        "kg_after_sha256": _V1_4_AFTER["kg_sample.json"],
        "current_rank_sha256": _V1_4_AFTER["board_rankings_v37.json"],
        "current_derived_sha256": _V1_4_AFTER["derived_catalog_v38.json"],
        "current_mobile_sha256": _V1_4_AFTER["cat_mobile_app_pack_contract.json"],
        "prototype_bytes_exact": True,
        "new_concepts": 0,
        "new_qualified_synonym_families": 1,
        "new_exact_forms": 2,
        "new_directed_links": 2,
        "new_conversion_facts": 0,
        "new_curated_rounds_or_target_approvals": 0,
        "all9471_old_edges_exact": True,
        "all180_terminal_puzzles_exact": True,
        "all716_pack_records_exact": True,
        "all716_rank_rows_exact": True,
        "all336_derived_payloads_exact": True,
    }
    assert {key: receipt[key] for key in expected} == expected
    changes = receipt["node_field_changes"]
    assert len(changes) == 4 and all(set(row) == {"id", "changes"} for row in changes)
    assert {row["id"]: row["changes"] for row in changes} == {
        "n_v24_time_day_ceas": {"aliases": _V1_4_ALIASES},
        **{
            node_id: {"degree": {"before": first, "after": last}}
            for node_id, (first, last) in _V1_4_DEGREES.items()
        },
    }
    assert receipt["new_edges"] == _V1_4_NEW_EDGES
    return receipt


def before_v1_4_artifact(current: dict, filename: str) -> dict:
    """Peel only actual V1.4 graph/header/public-mobile writes back to git46641d6."""
    assert filename in _V1_4_BASELINE
    receipt = _v1_4_graph_receipt()
    current_hash = _v1_3_artifact_digest(current, filename)
    if current_hash in {_V1_4_BASELINE[filename], _V1_3_BASELINE[filename]}:
        return deepcopy(current)
    assert current_hash == _V1_4_AFTER[filename]
    restored = deepcopy(current)
    if filename == "kg_sample.json":
        assert len(current["kg_nodes"]) == 2419 and len(current["kg_edges"]) == 9473
        assert len(current["kg_puzzles"]) == 180
        assert current["kg_edges"][-2:] == receipt["new_edges"]
        restored["kg_edges"] = restored["kg_edges"][:-2]
        nodes = {row["id"]: row for row in restored["kg_nodes"]}
        assert len(nodes) == 2419
        assert nodes["n_v24_time_day_ceas"]["aliases"] == _V1_4_ALIASES["after"]
        nodes["n_v24_time_day_ceas"]["aliases"] = list(_V1_4_ALIASES["before"])
        for node_id, (first, last) in _V1_4_DEGREES.items():
            assert nodes[node_id]["degree"] == last
            nodes[node_id]["degree"] = first
        meta = restored["meta"]
        assert meta["build_version"] == "fixture-v1-4-time-links"
        assert meta["note"] == (
            "V1.4: one qualified clock synonym family (two forms) "
            "and two directed duration-unit links."
        )
        assert meta["counts"]["edges"] == 9473
        meta["build_version"] = "fixture-v1-3-everyday-concepts"
        meta["note"] = (
            "V1.3: three reviewed everyday concepts, twelve grammatical forms "
            "and twelve one-way links."
        )
        meta["counts"]["edges"] = 9471
        assert restored["kg_puzzles"] == current["kg_puzzles"]
    elif filename in {"board_rankings_v37.json", "derived_catalog_v38.json"}:
        assert len(current["boards"]) == (716 if filename.startswith("board_rankings") else 336)
        meta = restored["meta"]
        assert meta["kg_sha256"] == _V1_4_AFTER["kg_sample.json"]
        meta["kg_sha256"] = _V1_4_BASELINE["kg_sample.json"]
        if filename == "derived_catalog_v38.json":
            assert meta["v37_rankings_sha256"] == _V1_4_AFTER["board_rankings_v37.json"]
            meta["v37_rankings_sha256"] = _V1_4_BASELINE["board_rankings_v37.json"]
        assert restored["boards"] == current["boards"]
    elif filename == "cat_mobile_app_pack_contract.json":
        assert current["contract"] == "cat_de_roman_esti.mobile_app_pack.v1"
        assert len(current["kg_nodes"]) == 2419 and len(current["kg_edges"]) == 9473
        assert len(current["kg_puzzles"]) == 180
        for edge in receipt["new_edges"]:
            public_edge = {key: edge[key] for key in ("id", "src_id", "dst_id")}
            assert restored["kg_edges"].count(public_edge) == 1
            restored["kg_edges"].remove(public_edge)
        assert restored["kg_nodes"] == current["kg_nodes"]
        assert restored["kg_puzzles"] == current["kg_puzzles"]
        manifest = restored["manifest"]
        assert manifest["build_version"] == "fixture-v1-4-time-links"
        assert manifest["content_hash"] == (
            "sha256:9b8e304038ae5750d15eb804145dae4428f8fb8289d15873660669865234a0b3"
        )
        assert manifest["counts"] == {"nodes": 2419, "edges": 9473, "puzzles": 180}
        manifest["build_version"] = "fixture-v1-3-everyday-concepts"
        manifest["content_hash"] = (
            "sha256:a00fb1308f215ea8e554df5fb3f60e7d12a2031c075280099454fb7299d48db9"
        )
        manifest["counts"]["edges"] = 9471
    else:
        raise AssertionError("Unreviewed V1.4 artifact delta")
    assert _v1_3_artifact_digest(restored, filename) == _V1_4_BASELINE[filename]
    return restored


def before_v1_4_catalog(current: dict, filename: str) -> dict:
    """Restore only exact signed V1.4 metadata and four quick snapshot changes."""
    assert filename in _V1_4_CATALOG_BASELINE
    current_hash = _v1_3_catalog_digest(current)
    if current_hash in {_V1_4_CATALOG_BASELINE[filename], _V1_3_CATALOG_BASELINE[filename]}:
        return deepcopy(current)
    assert current_hash == _V1_4_CATALOG_AFTER[filename]
    blob = _V1_4_CATALOG_DELTA.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_4_CATALOG_DELTA_SHA256
    receipt = json.loads(blob)
    assert receipt["schema"] == "v1-4-signed-three-catalog-history-delta-v1"
    assert receipt["baseline_commit"] == "46641d6f9963f92941d12f5955e5eb40a2d8fb56"
    assert receipt["graph_installation_sha256"] == _V1_4_GRAPH_RECEIPT_SHA256
    assert receipt["parent_source3_sha256"] == (
        "56ef795c811a3f97c8c3fe96cf1b658e836babbf9fd88fe841c986ba7e65d4cc"
    )
    assert receipt["source4_sha256"] == (
        "444e4bc1dc9a55fbfccd5840e33975b3b672d9ea2f51ece88044d873653d79b1"
    )
    assert receipt["scope"] == (
        "Exact signed V1.4 catalog metadata plus four quick snapshot fields; "
        "all authored payloads, world mechanics/histories and extension books remain V1.3 exact."
    )
    assert {
        key: receipt[key]
        for key in (
            "authored_quick_boards",
            "world_concepts",
            "world_recipes",
            "world_named_goals",
            "compatible_histories",
            "extension_books",
            "extension_additions",
        )
    } == {
        "authored_quick_boards": 85,
        "world_concepts": 251,
        "world_recipes": 351,
        "world_named_goals": 32,
        "compatible_histories": 9,
        "extension_books": 27,
        "extension_additions": 49,
    }
    assert set(receipt["files"]) == set(_V1_4_CATALOG_AFTER)
    for name, delta in receipt["files"].items():
        assert set(delta) == {
            "baseline_sha256",
            "after_sha256",
            "metadata_before",
            "metadata_after",
            "quick_node_field_changes",
        }
        assert delta["baseline_sha256"] == _V1_4_CATALOG_BASELINE[name]
        assert delta["after_sha256"] == _V1_4_CATALOG_AFTER[name]
        fields = {"bindings", "candidate_sha256"}
        fields.add("semantic_reviews" if name.startswith("alchimie_recipe") else "reviews")
        if name == "alchimie_discovery_world_v92.json":
            fields.add("native_source_version")
            assert delta["metadata_before"]["native_source_version"] == 3
            assert delta["metadata_after"]["native_source_version"] == 4
        assert set(delta["metadata_before"]) == set(delta["metadata_after"]) == fields
        for phase, expected_kg in (
            ("before", _V1_4_BASELINE["kg_sample.json"]),
            ("after", _V1_4_AFTER["kg_sample.json"]),
        ):
            bind = delta["metadata_" + phase]["bindings"]
            if name == "alchimie_recipe_extensions_v92.json":
                assert bind == {
                    "kg": {
                        "path": "cat_de_roman_esti/fixtures/kg_sample.json",
                        "sha256": expected_kg,
                    },
                    "pack": {
                        "path": "cat_de_roman_esti/fixtures/games_pack.json",
                        "sha256": (
                            "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"
                        ),
                    },
                    "rubric": {
                        "path": "docs/CRITIQUE_RUBRIC.md",
                        "sha256": (
                            "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"
                        ),
                    },
                }
            else:
                assert set(bind) == (
                    {
                        "kg_sha256",
                        "pack_sha256",
                        "core_catalog_sha256",
                        "core_payload_sha256",
                        "rubric_sha256",
                    }
                    if name == "quick_games_v92.json"
                    else {
                        "kg_sha256",
                        "editorial_source_sha256",
                        "previous_world_sha256",
                        "rubric_sha256",
                    }
                )
                assert bind["kg_sha256"] == expected_kg
        if name == "quick_games_v92.json":
            assert delta["quick_node_field_changes"] == {
                "n_v24_time_day_ceas": {"aliases": _V1_4_ALIASES},
                **{
                    node_id: {"degree": {"before": first, "after": last}}
                    for node_id, (first, last) in _V1_4_DEGREES.items()
                },
            }
        else:
            assert not delta["quick_node_field_changes"]
    documents = receipt["staging_documents_sha256"]
    assert set(documents) == {
        f"docs/reviews/v1-4-time-links-and-predicates/native/{rail}/{leaf}"
        for rail in ("quick", "world", "extensions")
        for leaf in (
            "candidate.json",
            "factual-review.json",
            "quality-review.json",
            "proposal.json",
            "preinstall-audit.json",
            "final-factual-review.json",
            "final-quality-review.json",
        )
    }
    root = Path(__file__).resolve().parents[1]
    assert all(
        hashlib.sha256((root / path).read_bytes()).hexdigest() == expected
        for path, expected in documents.items()
    )
    assert (
        hashlib.sha256(
            (root / "go-backend/internal/contentrails/sources/authored-v4.json").read_bytes()
        ).hexdigest()
        == receipt["source4_sha256"]
    )
    delta = receipt["files"][filename]
    assert all(current[key] == value for key, value in delta["metadata_after"].items())
    restored = deepcopy(current)
    for key, value in delta["metadata_before"].items():
        restored[key] = deepcopy(value)
    if filename == "quick_games_v92.json":
        assert len(current["boards"]) == len(current["authored"]) == 85
        assert len(current["nodes"]) == 322
        for node_id, changes in delta["quick_node_field_changes"].items():
            for field, values in changes.items():
                assert restored["nodes"][node_id][field] == values["after"]
                restored["nodes"][node_id][field] = deepcopy(values["before"])
    elif filename == "alchimie_discovery_world_v92.json":
        assert len(current["concepts"]) == 251 and len(current["recipes"]) == 351
        assert len(current["goals"]) == 32 and len(current["compatible_versions"]) == 9
    else:
        assert len(current["boards"]) == 27
        assert sum(len(board["additions"]) for board in current["boards"]) == 49
    assert _v1_3_catalog_digest(restored) == _V1_4_CATALOG_BASELINE[filename]
    return restored



def _v1_3_artifact_digest(value: dict, filename: str) -> str:
    """Exact source encoding, without sorting or general normalization."""
    blob = (json.dumps(value, ensure_ascii=False,
                       indent=2 if filename == "kg_sample.json" else 1) + "\n").encode()
    return hashlib.sha256(blob).hexdigest()


def _v1_3_graph_receipt() -> dict:
    blob = _V1_3_GRAPH_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_3_GRAPH_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["schema"] == "v1-3-supported-graph-installation-v1"
    assert receipt["baseline_commit"] == "18832d41bedfe5f63ee98fcffa709d29d9f86361"
    assert {key: receipt[key] for key in _V1_3_REVIEW_BINDINGS} == _V1_3_REVIEW_BINDINGS
    assert receipt["before_kg_sha256"] == _V1_3_BASELINE["kg_sample.json"]
    assert receipt["after_kg_sha256"] == _V1_3_AFTER["kg_sample.json"]
    assert receipt["native_rank_sha256"] == _V1_3_AFTER["board_rankings_v37.json"]
    assert receipt["native_derived_sha256"] == _V1_3_AFTER["derived_catalog_v38.json"]
    assert receipt["matches_independent_prospective_fixture"] is True
    assert receipt["package_test_mirrors_exact"] is True
    assert receipt["counts"] == {
        "nodes_before": 2416, "nodes_after": 2419,
        "stored_aliases_before": 8663, "stored_aliases_after": 8675,
        "links_before": 9459, "links_after": 9471,
        "terminal_puzzles_before": 180, "terminal_puzzles_after": 180,
        "new_shared_concepts": 3, "new_grammatical_forms": 12, "new_links": 12,
        "genuine_synonym_families": 0, "new_curated_rounds": 0,
        "new_hidden_target_approvals": 0,
    }
    assert receipt["preservation"] == {
        "old_edge_records_exact": True, "old_node_fields_exact_except_11_degrees": True,
        "all_180_terminal_records_exact": True,
        "pack_bytes_exact_no_status_or_payload_edits": True, "old_alias_lists_exact": True,
    }
    changes = receipt["old_node_metadata_changes"]
    assert len(changes) == len(_V1_3_DEGREES)
    assert {row["id"]: row["changes"] for row in changes} == {
        node_id: {"degree": {"before": before, "after": after}}
        for node_id, (before, after) in _V1_3_DEGREES.items()
    }
    assert all(set(row) == {"id", "changes"} for row in changes)
    edges = receipt["new_edge_records"]
    assert [row["id"] for row in edges] == [f"de{n}" for n in range(8801, 8813)]
    assert all(row["src_id"] in _V1_3_NODE_IDS and row["dst_id"] not in _V1_3_NODE_IDS
               and row["bidirectional"] == 0 and row["is_distractor"] == 0 for row in edges)
    first, last = receipt["before_meta"], receipt["after_meta"]
    assert set(first) == set(last)
    assert {key for key in first if first[key] != last[key]} == {
        "build_version", "note", "counts",
    }
    assert first["build_version"] == "fixture-v1-2-reviewed-content"
    assert last["build_version"] == "fixture-v1-3-everyday-concepts"
    expected_counts = deepcopy(first["counts"])
    expected_counts.update(nodes=2419, edges=9471)
    expected_counts["by_category"]["viata_de_roman"] += 3
    assert last["counts"] == expected_counts
    return receipt


def before_v1_3_artifact(current: dict, filename: str) -> dict:
    """Peel exact installed V1.3 graph/rank/derived/mobile bytes back to 18832d4."""
    current = before_v1_4_artifact(current, filename)
    assert filename in _V1_3_BASELINE
    receipt = _v1_3_graph_receipt()
    current_hash = _v1_3_artifact_digest(current, filename)
    if current_hash == _V1_3_BASELINE[filename]:
        return deepcopy(current)
    assert filename in _V1_3_AFTER
    assert current_hash == _V1_3_AFTER[filename]
    restored = deepcopy(current)
    if filename == "kg_sample.json":
        assert current["meta"] == receipt["after_meta"]
        assert len(current["kg_puzzles"]) == 180
        assert tuple(row["id"] for row in current["kg_nodes"][-3:]) == _V1_3_NODE_IDS
        assert current["kg_edges"][-12:] == receipt["new_edge_records"]
        restored["kg_nodes"] = restored["kg_nodes"][:-3]
        restored["kg_edges"] = restored["kg_edges"][:-12]
        nodes = {row["id"]: row for row in restored["kg_nodes"]}
        assert len(nodes) == len(restored["kg_nodes"]) == 2416
        for node_id, (before, after) in _V1_3_DEGREES.items():
            assert nodes[node_id]["degree"] == after
            nodes[node_id]["degree"] = before
        restored["meta"] = deepcopy(receipt["before_meta"])
        assert restored["kg_puzzles"] == current["kg_puzzles"]
    elif filename == "board_rankings_v37.json":
        rows = restored["boards"]
        assert len(rows) == 716 and len({row["id"] for row in rows}) == 716
        by_id = {row["id"]: row for row in rows}
        for item_id, fields in _V1_3_RANK_FIELDS.items():
            for field, (before, after) in fields.items():
                assert by_id[item_id][field] == after
                by_id[item_id][field] = before
        position = next(i for i, row in enumerate(rows) if row["id"] == "ct_viata_de_roman_377")
        assert [row["id"] for row in rows[position:position + 4]] == [
            "ct_viata_de_roman_377", "ct_muzica_168", "ct_societate_290", "ct_stiinta_189",
        ]
        moved = rows.pop(position)
        rows.insert(position + 3, moved)
        assert restored["meta"]["kg_sha256"] == _V1_3_AFTER["kg_sample.json"]
        restored["meta"]["kg_sha256"] = _V1_3_BASELINE["kg_sample.json"]
    elif filename == "derived_catalog_v38.json":
        assert len(restored["boards"]) == 336
        assert restored["meta"]["kg_sha256"] == _V1_3_AFTER["kg_sample.json"]
        assert restored["meta"]["v37_rankings_sha256"] == _V1_3_AFTER["board_rankings_v37.json"]
        restored["meta"]["kg_sha256"] = _V1_3_BASELINE["kg_sample.json"]
        restored["meta"]["v37_rankings_sha256"] = _V1_3_BASELINE["board_rankings_v37.json"]
        assert restored["boards"] == current["boards"]
    elif filename == "cat_mobile_app_pack_contract.json":
        assert restored["contract"] == "cat_de_roman_esti.mobile_app_pack.v1"
        labels = {
            "n_v1_3_home_balama": "Balama", "n_v1_3_material_lemn": "Lemn",
            "n_v1_3_clothing_fermoar": "Fermoar",
        }
        for node_id, label in labels.items():
            expected = {"id": node_id, "label_ro": label}
            assert restored["kg_nodes"].count(expected) == 1
            restored["kg_nodes"].remove(expected)
        for edge in receipt["new_edge_records"]:
            expected = {key: edge[key] for key in ("id", "src_id", "dst_id")}
            assert restored["kg_edges"].count(expected) == 1
            restored["kg_edges"].remove(expected)
        assert len(restored["kg_nodes"]) == 2416
        assert len(restored["kg_edges"]) == 9459
        assert len(restored["kg_puzzles"]) == 180
        assert restored["kg_puzzles"] == current["kg_puzzles"]
        manifest = restored["manifest"]
        assert manifest["build_version"] == "fixture-v1-3-everyday-concepts"
        assert manifest["content_hash"] == (
            "sha256:a00fb1308f215ea8e554df5fb3f60e7d12a2031c075280099454fb7299d48db9"
        )
        assert manifest["counts"] == {"nodes": 2419, "edges": 9471, "puzzles": 180}
        manifest["build_version"] = "fixture-v1-2-reviewed-content"
        manifest["content_hash"] = (
            "sha256:16634bb35bfc4c629815792181dc26e917a02d75fe9fb5aa1e27f8c576f55e35"
        )
        manifest["counts"] = {"nodes": 2416, "edges": 9459, "puzzles": 180}
    else:
        raise AssertionError("Unreviewed V1.3 artifact delta")
    assert _v1_3_artifact_digest(restored, filename) == _V1_3_BASELINE[filename]
    return restored


def _v1_3_catalog_digest(value: dict) -> str:
    """Native Render uses exactly two spaces and a final newline for all three rails."""
    blob = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    return hashlib.sha256(blob).hexdigest()


def _before_v1_3_extensions(current: dict) -> dict:
    blob = _V1_3_EXTENSION_DELTA.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_3_EXTENSION_DELTA_SHA256
    delta = json.loads(blob)
    name = "alchimie_recipe_extensions_v92.json"
    assert delta["schema"] == "v1-3-extension-catalog-history-delta-v1"
    assert delta["baseline_commit"] == "18832d41bedfe5f63ee98fcffa709d29d9f86361"
    assert delta["baseline_sha256"] == _V1_3_CATALOG_BASELINE[name]
    assert delta["after_sha256"] == _V1_3_CATALOG_AFTER[name]
    assert set(delta["metadata_before"]) == set(delta["metadata_after"]) == {
        "bindings", "candidate_sha256", "semantic_reviews",
    }
    assert delta["board"] == {
        "id": "al_viata_de_roman_096", "node_id": "n_v4via_usa",
        "degree_before": 42, "degree_after": 43,
        "entry_before": "7e47eb8a0e11f498c2c1958c284e81a6b4c445ac1fe769dafd13108cc2d222b7",
        "entry_after": "fd4a511da803a07b8ad405b5d983e36e1408b9d3c88d7f4762b0b4fa6aa7403f",
    }
    documents = delta["staging_documents_sha256"]
    assert set(documents) == {
        "docs/reviews/v1-3-everyday-concepts/native/extensions/" + path
        for path in (
            "candidate.json", "factual-review.json", "quality-review.json", "proposal.json",
            "preinstall-audit.json", "final-factual-review.json", "final-quality-review.json",
        )
    }
    root = Path(__file__).resolve().parents[1]
    assert all(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected
               for path, expected in documents.items())
    restored = deepcopy(current)
    assert all(current[key] == value for key, value in delta["metadata_after"].items())
    for key, value in delta["metadata_before"].items():
        restored[key] = deepcopy(value)
    assert len(restored["boards"]) == 27
    assert sum(len(board["additions"]) for board in restored["boards"]) == 49
    boards = [board for board in restored["boards"] if board["id"] == "al_viata_de_roman_096"]
    assert len(boards) == 1
    board = boards[0]
    assert board["entry_sha256"] == delta["board"]["entry_after"]
    assert board["nodes"]["n_v4via_usa"]["degree"] == 43
    board["entry_sha256"] = delta["board"]["entry_before"]
    board["nodes"]["n_v4via_usa"]["degree"] = 42
    assert _v1_3_catalog_digest(restored) == _V1_3_CATALOG_BASELINE[name]
    return restored


def before_v1_3_catalog(current: dict, filename: str) -> dict:
    """Restore only exact signed catalog deltas; keep every legacy byte check."""
    current = before_v1_4_catalog(current, filename)
    assert filename in _V1_3_CATALOG_BASELINE
    current_hash = _v1_3_catalog_digest(current)
    if current_hash == _V1_3_CATALOG_BASELINE[filename]:
        return deepcopy(current)
    assert filename in _V1_3_CATALOG_AFTER, "Final reviewed V1.3 catalog inverse is not yet bound"
    assert current_hash == _V1_3_CATALOG_AFTER[filename]
    if filename == "alchimie_recipe_extensions_v92.json":
        return _before_v1_3_extensions(current)
    blob = _V1_3_CATALOG_DELTA.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_3_CATALOG_DELTA_SHA256
    receipt = json.loads(blob)
    assert receipt["schema"] == "v1-3-quick-world-catalog-history-delta-v1"
    assert receipt["baseline_commit"] == "18832d41bedfe5f63ee98fcffa709d29d9f86361"
    assert receipt["graph_installation_sha256"] == _V1_3_GRAPH_RECEIPT_SHA256
    assert receipt["source3_sha256"] == (
        "56ef795c811a3f97c8c3fe96cf1b658e836babbf9fd88fe841c986ba7e65d4cc"
    )
    assert receipt["scope"] == (
        "Only exact signed quick/world metadata and ten quick degree snapshots; "
        "preserve all old semantics and histories."
    )
    assert set(receipt["files"]) == set(_V1_3_CATALOG_AFTER) - {
        "alchimie_recipe_extensions_v92.json",
    }
    for name, delta in receipt["files"].items():
        assert set(delta) == {
            "baseline_sha256", "after_sha256", "metadata_before", "metadata_after", "node_degrees",
        }
        assert delta["baseline_sha256"] == _V1_3_CATALOG_BASELINE[name]
        assert delta["after_sha256"] == _V1_3_CATALOG_AFTER[name]
        fields = {"bindings", "candidate_sha256", "reviews"}
        if name == "alchimie_discovery_world_v92.json":
            fields.add("native_source_version")
            assert not delta["node_degrees"]
            assert delta["metadata_before"]["native_source_version"] == 2
            assert delta["metadata_after"]["native_source_version"] == 3
        else:
            assert delta["node_degrees"] == {
                node_id: {"before": before, "after": after}
                for node_id, (before, after) in _V1_3_DEGREES.items()
                if node_id != "n_v4via_usa"
            }
        assert set(delta["metadata_before"]) == set(delta["metadata_after"]) == fields
        assert delta["metadata_before"]["bindings"]["kg_sha256"] == (
            _V1_3_BASELINE["kg_sample.json"]
        )
        assert delta["metadata_after"]["bindings"]["kg_sha256"] == (
            _V1_3_AFTER["kg_sample.json"]
        )
    documents = receipt["staging_documents_sha256"]
    assert set(documents) == {
        f"docs/reviews/v1-3-everyday-concepts/native/{rail}/{name}"
        for rail in ("quick", "world")
        for name in (
            "candidate.json", "factual-review.json", "quality-review.json", "proposal.json",
            "preinstall-audit.json", "final-factual-review.json", "final-quality-review.json",
        )
    }
    root = Path(__file__).resolve().parents[1]
    assert all(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected
               for path, expected in documents.items())
    delta = receipt["files"][filename]
    restored = deepcopy(current)
    assert all(current[key] == value for key, value in delta["metadata_after"].items())
    for key, value in delta["metadata_before"].items():
        restored[key] = deepcopy(value)
    if filename == "quick_games_v92.json":
        assert len(restored["boards"]) == len(restored["authored"]) == 85
        assert len(restored["nodes"]) == 322
        for node_id, degree in delta["node_degrees"].items():
            assert restored["nodes"][node_id]["degree"] == degree["after"]
            restored["nodes"][node_id]["degree"] = degree["before"]
    else:
        assert len(restored["concepts"]) == 251 and len(restored["recipes"]) == 351
        assert len(restored["goals"]) == 32 and len(restored["compatible_versions"]) == 9
    assert _v1_3_catalog_digest(restored) == _V1_3_CATALOG_BASELINE[filename]
    return restored


def before_v1_2_extension_catalog(current: dict) -> dict:
    """Restore the complete original V1 extension book, with every old pin intact."""
    name = "alchimie_recipe_extensions_v92.json"
    current = before_v1_3_catalog(current, name)
    assert _v1_3_catalog_digest(current) == (
        "9b7da100fb59f416667c0f23c04947f61d3d0e07d5712d57176293538302f1e3"
    )
    blob = _V1_2_EXTENSION_HISTORY.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_2_EXTENSION_HISTORY_SHA256
    delta = json.loads(blob)
    assert delta["schema"] == "v1-2-extension-history-supplement-v1"
    assert delta["before_commit"] == "6deab61c20067c66f0b6120b2b09f44a580526d6"
    assert delta["after_commit"] == "18832d41bedfe5f63ee98fcffa709d29d9f86361"
    assert delta["scope"] == (
        "Exact three V1.2 alias/degree snapshot and entry changes plus source/review metadata; "
        "old V1 catalog bytes and assertions retained."
    )
    assert delta["baseline_sha256"] == (
        "c52035abbbf08f6a1d4c1b50d8048bc5efcf3c7a4f2c9daca0096cb3444c9661"
    )
    assert delta["after_sha256"] == _V1_3_CATALOG_BASELINE[name]
    assert set(delta["metadata_before"]) == set(delta["metadata_after"]) == {
        "bindings", "candidate_sha256", "semantic_reviews",
    }
    assert set(delta["boards"]) == {
        "al_gastronomie_029", "al_geografie_031", "al_personalitati_006",
    }
    assert all(current[key] == value for key, value in delta["metadata_after"].items())
    restored = deepcopy(current)
    for key, value in delta["metadata_before"].items():
        restored[key] = deepcopy(value)
    by_id = {board["id"]: board for board in restored["boards"]}
    expected_nodes = {
        "al_gastronomie_029": "n_v4gas_rosie", "al_geografie_031": "n_v4geo_carare",
        "al_personalitati_006": "n_vioara",
    }
    for board_id, change in delta["boards"].items():
        board = by_id[board_id]
        assert set(change) == {"entry_before", "entry_after", "nodes"}
        assert set(change["nodes"]) == {expected_nodes[board_id]}
        assert board["entry_sha256"] == change["entry_after"]
        for node_id, snapshot in change["nodes"].items():
            assert board["nodes"][node_id] == snapshot["after"]
            first, last = snapshot["before"], snapshot["after"]
            assert set(first) == set(last)
            fields = {key for key in first if first[key] != last[key]}
            if node_id in _V1_2_ALIASES:
                assert fields == {"aliases"}
                assert last["aliases"] == [*first["aliases"], *_V1_2_ALIASES[node_id]]
            else:
                assert node_id == "n_v4geo_carare" and fields == {"degree"}
                assert first["degree"] == 3 and last["degree"] == 4
            board["nodes"][node_id] = deepcopy(first)
        board["entry_sha256"] = change["entry_before"]
    assert _v1_3_catalog_digest(restored) == delta["baseline_sha256"]
    return restored


def before_v1_2_artifact(current: dict, filename: str) -> dict:
    """Peel only the exact reviewed V1.2 graph and serialization transition."""
    current = before_v1_3_artifact(current, filename)
    blob = _V1_2_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_2_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert set(receipt) == {
        "schema_version", "baseline_commit", "scope", "review_bindings", "generator", "files",
    }
    assert receipt["schema_version"] == 1
    assert receipt["scope"] == (
        "V1.2 exact graph/metadata inverse; no historic receipt or hash modified"
    )
    assert receipt["generator"] == (
        "Root exact before/after row delta from git baseline/current supported writes"
    )
    assert receipt["baseline_commit"] == "6deab61c20067c66f0b6120b2b09f44a580526d6"
    assert receipt["review_bindings"] == _V1_2_REVIEW_BINDINGS
    files = receipt["files"]
    assert set(files) == set(_V1_2_BASELINE) == set(_V1_2_AFTER)
    assert filename in files

    def changed_fields(before: dict, after: dict) -> set[str]:
        assert set(before) == set(after)
        return {key for key in before if before[key] != after[key]}

    for name, artifact in files.items():
        assert set(artifact) == {
            "baseline_sha256", "after_sha256", "head_before", "head_after", "tables",
        }
        assert artifact["baseline_sha256"] == _V1_2_BASELINE[name]
        assert artifact["after_sha256"] == _V1_2_AFTER[name]
        assert set(artifact["tables"]) == _V1_2_TABLES[name]
        before, after = artifact["head_before"], artifact["head_after"]
        assert set(before) == set(after) == (
            {"contract", "manifest"} if name.startswith("cat_mobile") else {"meta"}
        )
        if name == "games_pack.json":
            assert before == after
        elif name.startswith("cat_mobile"):
            assert before["contract"] == after["contract"]
            first, last = before["manifest"], after["manifest"]
            assert changed_fields(first, last) == {"build_version", "content_hash", "counts"}
            assert first["content_hash"] == (
                "sha256:b673caa14e7b6635fb8d7f283c2e0a4f8dbb9667450746ce9cdf0081dc8fd310"
            )
            assert last["content_hash"] == (
                "sha256:16634bb35bfc4c629815792181dc26e917a02d75fe9fb5aa1e27f8c576f55e35"
            )
        else:
            first, last = before["meta"], after["meta"]
            expected = {
                "kg_sample.json": {"build_version", "note", "counts"},
                "board_rankings_v37.json": {"kg_sha256"},
                "derived_catalog_v38.json": {"kg_sha256", "v37_rankings_sha256"},
            }[name]
            assert changed_fields(first, last) == expected
            if name != "kg_sample.json":
                assert first["kg_sha256"] == _V1_2_BASELINE["kg_sample.json"]
                assert last["kg_sha256"] == _V1_2_AFTER["kg_sample.json"]
            if name == "derived_catalog_v38.json":
                assert first["v37_rankings_sha256"] == _V1_2_BASELINE["board_rankings_v37.json"]
                assert last["v37_rankings_sha256"] == _V1_2_AFTER["board_rankings_v37.json"]
        if name in {"kg_sample.json", "cat_mobile_app_pack_contract.json"}:
            assert first["build_version"] == "fixture-v1-reviewed-content"
            assert last["build_version"] == "fixture-v1-2-reviewed-content"
            assert first["counts"]["edges"] == 9458
            assert last["counts"] == {**first["counts"], "edges": 9459}
        for table, changes in artifact["tables"].items():
            assert set(changes) == {"added", "removed", "changed", "baseline_order"}
            assert not changes["removed"] and changes["baseline_order"] is None
            if name == "kg_sample.json" and table == "kg_nodes":
                assert not changes["added"]
                assert set(changes["changed"]) == set(_V1_2_ALIASES) | _V1_2_PATH_IDS
                for node_id, change in changes["changed"].items():
                    assert set(change) == {"before", "after"}
                    first, last = change["before"], change["after"]
                    assert first["id"] == last["id"] == node_id
                    if node_id in _V1_2_ALIASES:
                        assert changed_fields(first, last) == {"aliases"}
                        assert last["aliases"] == [*first["aliases"], *_V1_2_ALIASES[node_id]]
                    else:
                        assert changed_fields(first, last) == {"degree"}
                        assert first["degree"] == 3 and last["degree"] == 4
            elif name in {"kg_sample.json", "cat_mobile_app_pack_contract.json"} and (
                table == "kg_edges"
            ):
                expected = _V1_2_NEW_EDGE if name == "kg_sample.json" else {
                    key: _V1_2_NEW_EDGE[key] for key in ("id", "src_id", "dst_id")
                }
                assert changes["added"] == [expected] and not changes["changed"]
            else:
                assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(
        current, filename, _V1_2_RECEIPT,
        baseline_key_orders=_V1_2_KEY_ORDERS.get(filename),
    )


def before_v1_artifact(current: dict, filename: str) -> dict:
    """Peel V1.2, then reconstruct cc0a6a4 through the original pinned V1 delta."""
    current = before_v1_2_artifact(current, filename)
    blob = _V1_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V1_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "cc0a6a490f4a37f6f94b59cf9a84eb760cb3a401"
    files = receipt["files"]
    assert set(files) == set(_V1_BASELINE) == set(_V1_AFTER)
    assert filename in files
    for name, artifact in files.items():
        assert artifact["baseline_sha256"] == _V1_BASELINE[name]
        assert artifact["after_sha256"] == _V1_AFTER[name]
        assert all(not change["added"] for change in artifact["tables"].values())
    return _reverse_bound_delta(current, filename, _V1_RECEIPT)


def before_v97_artifact(current: dict, filename: str) -> dict:
    """Restore complete fd3ca7c bytes before evaluating the original V96 transition."""
    current = before_v1_artifact(current, filename)
    blob = _V97_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V97_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "fd3ca7c78b6bee774c283d873d400abf4a8e7d65"
    files = receipt["files"]
    assert set(files) == set(_V97_BASELINE) and filename in _V97_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V97_BASELINE[filename]
    expected_ids = set().union(*_V97_ADDED_IDS.values())
    assert len(expected_ids) == 3
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V97_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V97_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 246
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V97_RECEIPT)


def before_v94_lant_ledger(current: dict) -> dict:
    """Remove only the exact V94 rejection and retain every original V49 byte."""
    def digest(value):
        blob = (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()
        return hashlib.sha256(blob).hexdigest()

    assert digest(current) == _V94_LEDGER_SHA256
    assert current["meta"]["count"] == len(current["items"]) == 105
    assert current["items"]["lt_geografie_242"] == _V94_REJECTED_LANT
    restored = deepcopy(current)
    del restored["items"]["lt_geografie_242"]
    restored["meta"]["count"] = 104
    assert digest(restored) == _V49_LEDGER_SHA256
    return restored


def v49_lant_ledger_bytes(path: Path) -> bytes:
    """Historical tests consume a strictly verified reconstruction of their ledger."""
    value = before_v94_lant_ledger(json.loads(path.read_bytes()))
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def before_v91_artifact(current: dict, filename: str) -> dict:
    """Restore exact V90 content before checking earlier historical receipts."""
    previous = before_v92_artifact(current, filename)
    return _reverse_bound_delta(previous, filename, _V91_RECEIPT)


def _before_v90(current: dict, filename: str) -> dict:
    previous = before_v91_artifact(current, filename)
    return _reverse_bound_delta(previous, filename, _V90_RECEIPT)


def before_v90_fixture(current: dict) -> dict:
    return _before_v90(current, "kg_sample.json")


def before_v90_pack(current: dict) -> dict:
    return _before_v90(current, "games_pack.json")


def before_v90_rankings(current: dict) -> dict:
    return _before_v90(current, "board_rankings_v37.json")


def before_v90_derived(current: dict) -> dict:
    return _before_v90(current, "derived_catalog_v38.json")


def before_v90_mobile(current: dict) -> dict:
    return _before_v90(current, "cat_mobile_app_pack_contract.json")


def _before_v89(current: dict, filename: str) -> dict:
    previous = _before_v90(current, filename)
    return _reverse_bound_delta(previous, filename, _V89_RECEIPT)


def before_v89_fixture(current: dict) -> dict:
    return _before_v89(current, "kg_sample.json")


def before_v89_pack(current: dict) -> dict:
    return _before_v89(current, "games_pack.json")


def before_v89_rankings(current: dict) -> dict:
    return _before_v89(current, "board_rankings_v37.json")


def before_v89_derived(current: dict) -> dict:
    return _before_v89(current, "derived_catalog_v38.json")


def _before_v88(current: dict, filename: str) -> dict:
    previous = _before_v89(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V88_RECEIPT)


def before_v88_fixture(current: dict) -> dict:
    return _before_v88(current, "kg_sample.json")


def before_v88_pack(current: dict) -> dict:
    return _before_v88(current, "games_pack.json")


def before_v88_rankings(current: dict) -> dict:
    return _before_v88(current, "board_rankings_v37.json")


def before_v88_derived(current: dict) -> dict:
    return _before_v88(current, "derived_catalog_v38.json")


def _before_v87(current: dict, filename: str) -> dict:
    previous = _before_v88(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V87_RECEIPT)


def before_v87_fixture(current: dict) -> dict:
    return _before_v87(current, "kg_sample.json")


def before_v87_pack(current: dict) -> dict:
    return _before_v87(current, "games_pack.json")


def before_v87_rankings(current: dict) -> dict:
    return _before_v87(current, "board_rankings_v37.json")


def before_v87_derived(current: dict) -> dict:
    return _before_v87(current, "derived_catalog_v38.json")


def _before_v86(current: dict, filename: str) -> dict:
    previous = _before_v87(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V86_RECEIPT)


def before_v86_fixture(current: dict) -> dict:
    return _before_v86(current, "kg_sample.json")


def before_v86_pack(current: dict) -> dict:
    return _before_v86(current, "games_pack.json")


def before_v86_rankings(current: dict) -> dict:
    return _before_v86(current, "board_rankings_v37.json")


def before_v86_derived(current: dict) -> dict:
    return _before_v86(current, "derived_catalog_v38.json")


def before_v85_fixture(current: dict) -> dict:
    return _before_v85(current, "kg_sample.json")


def before_v85_pack(current: dict) -> dict:
    return _before_v85(current, "games_pack.json")


def before_v85_rankings(current: dict) -> dict:
    return _before_v85(current, "board_rankings_v37.json")


def before_v85_derived(current: dict) -> dict:
    return _before_v85(current, "derived_catalog_v38.json")


def _before_v85(current: dict, filename: str) -> dict:
    previous = _before_v86(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V85_RECEIPT)


def _before_v84(current: dict, filename: str) -> dict:
    previous = _before_v85(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V84_RECEIPT)


def before_v84_fixture(current: dict) -> dict:
    return _before_v84(current, "kg_sample.json")


def before_v84_pack(current: dict) -> dict:
    return _before_v84(current, "games_pack.json")


def before_v84_rankings(current: dict) -> dict:
    return _before_v84(current, "board_rankings_v37.json")


def before_v84_derived(current: dict) -> dict:
    return _before_v84(current, "derived_catalog_v38.json")


def before_v84_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact retired Drojdie row from the committed V83 module."""
    restored = before_v85_projection_rows(current)
    assert not any(row[0] == "drojdie" for row in restored)
    index = next(i for i, row in enumerate(restored) if row[0] == "gem")
    restored.insert(index, (
        "drojdie", "n_v4gas_mancare", "ingrediente", 1, "domain_fallback",
        "ctxp_3218ea40b036e40101f5",
    ))
    return restored


def before_v85_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore only V85's two native replacements to their exact V84 positions."""
    restored = before_v86_projection_rows(current)
    for index, successor, row in (
        (29, "piper", (
            "scorțișoară", "n_v4gas_mancare", "ingrediente", 1, "domain_fallback",
            "ctxp_ed454bb254e529d7508c",
        )),
        (38, "cappuccino", (
            "cacao", "n_v3gas_cafea", "băuturi", 1, "explicit",
            "ctxp_73226150ba2fe847d20e",
        )),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == successor
        restored.insert(index, row)
    return restored


def before_v86_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact Congelator projection retired by its V86 native concept."""
    restored = before_v87_projection_rows(current)
    assert not any(row[0] == "congelator" for row in restored)
    assert restored[86][0] == "hotă de bucătărie"
    restored.insert(86, (
        "congelator", "n_v24_home_appliances_frigider", "ustensile de bucătărie",
        0, "explicit", "ctxp_ab9722a1b626f7b1d9ca",
    ))
    return restored


def before_v87_projection_rows(current: list[tuple]) -> list[tuple]:
    """Remove the reviewed Tort cue and restore the two exact V86 pastry rows."""
    restored = before_v88_projection_rows(current)
    added = (
        "tort", "n_v4gas_prajitura", "mâncare gătită", 1, "explicit",
        "ctxp_7de7b40dd74b4b0f44bf",
    )
    assert restored.count(added) == 1
    restored.remove(added)
    for index, row in (
        (14, ("brioșă", "n_v4gas_paine", "mâncare gătită", 1, "explicit",
              "ctxp_48dbb31871219f323569")),
        (15, ("chec", "n_v4gas_paine", "mâncare gătită", 1, "explicit",
              "ctxp_2e50eafd1e160b7bc25a")),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == "chiflă"
        restored.insert(index, row)
    return restored


def before_v90_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact retired dust row and the complete 465-row V89 fingerprint."""
    restored = list(current)
    assert not any(row[0] == "praf" for row in restored)
    assert restored[314][0] == "scoică"
    restored.insert(314, (
        "praf", "n_v24_nature_world_pamant", "peisaj", 1, "explicit",
        "ctxp_81703160cad7893fa1c9",
    ))
    assert len(restored) == 465
    assert hashlib.sha256(json.dumps(
        restored, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest() == (
        "2c47be5276ba580036413db1308075a5ec44db27e8af8146c5c37aca4f597320"
    )
    return restored


def before_v88_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the two exact V87 household cues replaced by native V88 owners."""
    restored = before_v90_projection_rows(current)
    for index, successor, row in (
        (59, "birou de acasă", (
            "taburet", "n_v4soc_casa", "mobilier și casă", 1, "domain_fallback",
            "ctxp_cd04babfc1ac9193f9cf",
        )),
        (106, "cârpă de praf", (
            "mătură", "n_v31_cleaning_floor_aspirator", "curățenie", 1, "explicit",
            "ctxp_14422411a52f6dbbfe68",
        )),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == successor
        restored.insert(index, row)
    return restored


def before_v89_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only the reviewed Diplomat-to-whipped-cream native cue."""
    added = frozenset({("n_v87_food_tort_diplomat", "n_v86_food_frisca")})
    assert added <= current
    return current - added


def before_v88_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only V88's independently reviewed native bread-family cue."""
    current = before_v89_feedback_pairs(current)
    added = frozenset({("n_v87_food_briosa", "n_v4gas_paine")})
    assert added <= current
    return current - added


def before_v87_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only the three reviewed V87 native exact-target additions."""
    current = before_v88_feedback_pairs(current)
    added = frozenset({
        ("n_v87_food_pandispan", "n_v87_food_chec"),
        ("n_v24_food_snack_biscuit", "n_v87_food_piscot"),
        ("n_v4gas_prajitura", "n_v87_food_cremsnit"),
    })
    assert added <= current
    return current - added


def before_v90_projection_neighborhoods(current: dict) -> dict:
    """Restore V89's retired dust policy before older exact-scope checks."""
    from cat_de_roman_esti.wordgames.contexto_projection import ProjectionNeighborhood

    assert set(current) == {"gem", "burta", "tort", "ciocolata calda"}
    return {
        "praf": ProjectionNeighborhood(
            "n_v24_nature_world_pamant", 0.60, include_direct_neighbors=False,
            exact_target_ids=frozenset({
                "n_v31_cleaning_floor_faras", "n_v31_cleaning_floor_mop",
                "n_v31_cleaning_floor_aspirator",
            }),
        ),
        **current,
    }


def before_v89_projection_neighborhoods(current: dict) -> dict:
    """Restore the exact V88 policies after validating the three closed dust scopes."""
    restored = before_v90_projection_neighborhoods(current)
    policy = restored.pop("praf")
    assert (policy.anchor_id, policy.min_strength, policy.include_direct_neighbors,
            policy.exact_target_ids) == (
        "n_v24_nature_world_pamant", 0.60, False, frozenset({
            "n_v31_cleaning_floor_faras", "n_v31_cleaning_floor_mop",
            "n_v31_cleaning_floor_aspirator",
        }),
    )
    return restored


def before_v87_projection_neighborhoods(current: dict) -> dict:
    """Retain exact older policies while checking the two closed V87 cue policies."""
    restored = before_v89_projection_neighborhoods(current)
    for key, anchor, target in (
        ("tort", "n_v4gas_prajitura", "n_v87_food_tort_diplomat"),
        ("ciocolata calda", "n_v24_food_snack_ceai", "n_v85_food_ciocolata"),
    ):
        policy = restored.pop(key)
        assert (policy.anchor_id, policy.min_strength, policy.include_direct_neighbors,
                policy.exact_target_ids) == (anchor, 0.60, False, frozenset({target}))
    return restored


def v83_added_forms() -> set[str]:
    receipt = json.loads((_V83_REVIEW / "morphology-delta.json").read_bytes())
    return {
        form for change in receipt["alias_changes"].values()
        for form in change["after"] if form not in change["before"]
    }


def before_v83_fixture(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "morphology-delta.json").read_bytes())
    restored = before_v84_fixture(current)
    assert restored["meta"] == receipt["after_kg_meta"]
    for row in restored["kg_nodes"]:
        change = receipt["alias_changes"].get(row["id"])
        if change is not None:
            assert row["aliases"] == change["after"]
            row["aliases"] = change["before"]
    restored["meta"] = receipt["baseline_kg_meta"]
    return restored


def before_v83_pack(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_pack(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v83_rankings(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    added = {row["id"] for row in receipt["new_records"]}
    assert added <= {row["id"] for row in restored["boards"]}
    restored["boards"] = [row for row in restored["boards"] if row["id"] not in added]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v83_derived(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v82_pack(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_pack(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v82_rankings(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    new_ids = {row["id"] for row in receipt["new_records"]}
    assert new_ids <= {row["id"] for row in restored["boards"]}
    restored["boards"] = [row for row in restored["boards"] if row["id"] not in new_ids]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v82_derived(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_fixture(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v83_fixture(current)
    assert restored["meta"] == receipt["after_kg_meta"]
    new_node = receipt["new_node"]
    assert new_node in restored["kg_nodes"]
    nodes = []
    for row in restored["kg_nodes"]:
        if row["id"] == new_node["id"]:
            continue
        change = receipt["changed_nodes"].get(row["id"])
        if change:
            assert row == change["after"]
            row = change["before"]
        nodes.append(row)
    restored["kg_nodes"] = nodes
    for edge in receipt["new_edges"]:
        assert edge in restored["kg_edges"]
        restored["kg_edges"].remove(edge)
    for idx, row in enumerate(restored["kg_puzzles"]):
        change = receipt["changed_puzzles"].get(row["id"])
        if change:
            assert row == change["after"]
            restored["kg_puzzles"][idx] = change["before"]
    restored["meta"] = receipt["baseline_kg_meta"]
    return restored


def before_v81_rankings(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v82_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    rows = {row["id"]: row for row in restored["boards"]}
    assert len(rows) == len(restored["boards"])
    assert set(rows) == set(receipt["baseline_ranking_order"])
    for item_id, change in receipt["changed_ranking_rows"].items():
        assert rows[item_id] == change["after"]
        rows[item_id] = change["before"]
    restored["boards"] = [rows[item_id] for item_id in receipt["baseline_ranking_order"]]
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v81_derived(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v82_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the one retired synthetic row for the V79 history fingerprint."""

    restored = before_v84_projection_rows(current)
    assert not any(row[0] == "nucă" for row in restored)
    index = next(i for i, row in enumerate(restored) if row[0] == "alună")
    restored.insert(index, (
        "nucă", "n_v24_food_breakfast_miere", "ingrediente", 1, "explicit",
        "ctxp_92113401f76976ac37f7",
    ))
    return restored


def before_v80_pack(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = before_v82_pack(current)
    restored["contexto"] = [
        row for row in restored["contexto"] if row["id"] not in receipt["new_ids"]
    ]
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v80_rankings(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = before_v81_rankings(current)
    restored["boards"] = [
        row for row in restored["boards"] if row["id"] not in receipt["new_ids"]
    ]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_ranking_meta"]
    return restored


def before_v80_derived(current: dict) -> dict:
    restored = before_v81_derived(current)
    restored["meta"] = json.loads(_RECEIPT.read_bytes())["baseline_derived_meta"]
    return restored
