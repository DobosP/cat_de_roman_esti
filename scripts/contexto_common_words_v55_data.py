"""Reviewed place-noun morphology for the V55 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing place concepts enter
the resolver. Forms of ``golf`` remain blocked because the ordinary surface
denotes both a geographic inlet and the sport.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v54_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v55-place-morphology"
NOTE = (
    "v55: forty-eight unanimously reviewed place genitive/dative forms; two "
    "geography/sport polysemes rejected; no nodes, edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v3geo_tara": ("țării", "țărilor"),
    "n_v3geo_insula": ("insulei", "insulelor"),
    "n_v3geo_deal": ("dealului", "dealurilor"),
    "n_v3geo_vale": ("văii", "văilor"),
    "n_v3geo_harta": ("hărții", "hărților"),
    "n_v3geo_granita": ("graniței", "granițelor"),
    "n_v3geo_capitala": ("capitalei", "capitalelor"),
    "n_v4geo_padure": ("pădurii", "pădurilor"),
    "n_v4geo_sat": ("satului", "satelor"),
    "n_v4geo_drum": ("drumului", "drumurilor"),
    "n_v4geo_camp": ("câmpului", "câmpurilor"),
    "n_v4geo_plaja": ("plajei", "plajelor"),
    "n_v4geo_izvor": ("izvorului", "izvoarelor"),
    "n_v4geo_parau": ("pârâului", "pâraielor"),
    "n_v4geo_cascada": ("cascadei", "cascadelor"),
    "n_v4geo_tarm": ("țărmului", "țărmurilor"),
    "n_v4geo_vulcan": ("vulcanului", "vulcanilor"),
    "n_v4geo_hotar": ("hotarului", "hotarelor"),
    "n_v4geo_mal": ("malului", "malurilor"),
    "n_v4geo_stanca": ("stâncii", "stâncilor"),
    "n_v4geo_nisip": ("nisipului", "nisipurilor"),
    "n_v4geo_peisaj": ("peisajului", "peisajelor"),
    "n_v4geo_catun": ("cătunului", "cătunelor"),
    "n_v4geo_peninsula": ("peninsulei", "peninsulelor"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("golfului", "golfurilor")
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
