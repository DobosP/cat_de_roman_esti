"""Reviewed nature-noun morphology for the V56 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing animal, plant,
weather, and basic-science concepts enter the resolver. Forms of ``corp``
remain blocked because the ordinary surface spans incompatible senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v55_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v56-nature-morphology"
NOTE = (
    "v56: forty-six unanimously reviewed nature genitive/dative forms; four "
    "sense-colliding surfaces rejected; no nodes, edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v4sti_animal": ("animalului", "animalelor"),
    "n_v4sti_insecta": ("insectei", "insectelor"),
    "n_v4sti_pasare": ("păsării", "păsărilor"),
    "n_v4sti_planta": ("plantei", "plantelor"),
    "n_v4sti_floare": ("florii", "florilor"),
    "n_v4sti_copac": ("copacului", "copacilor"),
    "n_v4sti_frunza": ("frunzei", "frunzelor"),
    "n_v24_weather_precipitation_ploaie": ("ploii", "ploilor"),
    "n_v24_weather_precipitation_zapada": ("zăpezii", "zăpezilor"),
    "n_v24_weather_air_vant": ("vântului", "vânturilor"),
    "n_v24_weather_air_nor": ("norului", "norilor"),
    "n_v24_weather_storm_furtuna": ("furtunii", "furtunilor"),
    "n_v24_weather_storm_fulger": ("fulgerului", "fulgerelor"),
    "n_v24_weather_storm_tunet": ("tunetului", "tunetelor"),
    "n_v24_weather_air_ceata": ("ceții", "cețurilor"),
    "n_v3sti_atom": ("atomului", "atomilor"),
    "n_v3sti_molecula": ("moleculei", "moleculelor"),
    "n_v3sti_planeta": ("planetei", "planetelor"),
    "n_v3sti_microscop": ("microscopului", "microscoapelor"),
    "n_v4sti_temperatura": ("temperaturii", "temperaturilor"),
    "n_v4sti_gaz": ("gazului", "gazelor"),
    "n_v4sti_lichid": ("lichidului", "lichidelor"),
    "n_v3sti_vaccin": ("vaccinului", "vaccinurilor"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "peștelui",
    "peștilor",
    "corpului",
    "corpurilor",
)
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
    assert len(ALIAS_ADDITIONS) == 23
    assert len(aliases) == len(normalized) == len(set(normalized)) == 46
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert len({_norm(value) for value in BLOCKED_ALIAS_FORMS}) == 4
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
