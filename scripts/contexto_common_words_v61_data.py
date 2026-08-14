"""Reviewed home-care and maintenance morphology for the V61 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
home-care concepts enter the resolver. Bare forms of ``cheie`` remain blocked
because the ordinary surface spans lock keys, solutions, tools, music, and places.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v60_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v61-home-care-and-maintenance-morphology"
NOTE = (
    "v61: forty-eight unanimously reviewed home-care and maintenance "
    "genitive/dative forms; two key/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v31_hygiene_bath_prosop": ("prosopului de baie", "prosoapelor de baie"),
    "n_v31_hygiene_bath_sapun": ("săpunului de baie", "săpunurilor de baie"),
    "n_v31_hygiene_hair_sampon": ("șamponului de păr", "șampoanelor de păr"),
    "n_v31_hygiene_hair_pieptene": ("pieptenului de păr", "pieptenilor de păr"),
    "n_v31_hygiene_oral_periuta_dinti": (
        "periuței pentru dinți",
        "periuțelor pentru dinți",
    ),
    "n_v31_hygiene_oral_pasta_dinti": (
        "pastei pentru dinți",
        "pastelor pentru dinți",
    ),
    "n_v31_cleaning_water_galeata": (
        "găleții de curățenie",
        "găleților de curățenie",
    ),
    "n_v31_cleaning_floor_mop": ("mopului de podea", "mopurilor de podea"),
    "n_v31_cleaning_supply_detergent": (
        "detergentului de curățenie",
        "detergenților de curățenie",
    ),
    "n_v31_cleaning_floor_aspirator": (
        "aspiratorului de podea",
        "aspiratoarelor de podea",
    ),
    "n_v31_cleaning_floor_faras": (
        "fărașului de curățenie",
        "fărașelor de curățenie",
    ),
    "n_v31_cleaning_dishes_burete_vase": (
        "buretelui pentru vase",
        "bureților pentru vase",
    ),
    "n_v32_workshop_hand_ciocan": ("ciocanului de atelier", "ciocanelor de atelier"),
    "n_v32_workshop_fastener_cui": ("cuiului de atelier", "cuielor de atelier"),
    "n_v32_workshop_hand_surubelnita": (
        "șurubelniței de atelier",
        "șurubelnițelor de atelier",
    ),
    "n_v32_workshop_fastener_surub": (
        "șurubului de atelier",
        "șuruburilor de atelier",
    ),
    "n_v32_workshop_hand_cleste": ("cleștelui de atelier", "cleștilor de atelier"),
    "n_v32_workshop_cut_fierastrau": (
        "fierăstrăului de atelier",
        "fierăstraielor de atelier",
    ),
    "n_v32_garden_soil_lopata": ("lopeții de grădină", "lopeților de grădină"),
    "n_v32_garden_soil_grebla": ("greblei de grădină", "greblelor de grădină"),
    "n_v32_garden_transport_roaba": ("roabei de grădină", "roabelor de grădină"),
    "n_v32_garden_water_furtun": (
        "furtunului pentru grădină",
        "furtunurilor pentru grădină",
    ),
    "n_v33_bathroom_fixture_chiuveta": ("chiuvetei de baie", "chiuvetelor de baie"),
    "n_v33_bathroom_fixture_robinet": ("robinetului de baie", "robinetelor de baie"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("cheii", "cheilor")
DEFERRED_AMBIGUOUS_TERMS = (
    *BASE_DEFERRED_AMBIGUOUS_TERMS,
    *BLOCKED_ALIAS_FORMS,
)

ALIAS_PROBES: tuple[tuple[str, str], ...] = tuple(
    (alias, node_id)
    for node_id, aliases in ALIAS_ADDITIONS.items()
    for alias in aliases
)
INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = ()


def _norm(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return " ".join(
        "".join(
            char for char in decomposed if not unicodedata.combining(char)
        ).casefold().split()
    )


def build_nodes_and_edges() -> dict[str, object]:
    """Return the alias-only batch consumed by the rollback-safe applier."""

    return {
        "nodes": [],
        "edges": [],
        "aliases": {
            node_id: list(aliases)
            for node_id, aliases in ALIAS_ADDITIONS.items()
        },
    }


def _validate_source() -> None:
    aliases = [alias for values in ALIAS_ADDITIONS.values() for alias in values]
    normalized = [_norm(alias) for alias in aliases]
    assert len(ALIAS_ADDITIONS) == 24
    assert len(aliases) == len(normalized) == len(set(normalized)) == 48
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert len({_norm(value) for value in BLOCKED_ALIAS_FORMS}) == 2
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
