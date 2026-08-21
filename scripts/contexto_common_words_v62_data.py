"""Reviewed transport and mobility morphology for the V62 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
transport and mobility concepts enter the resolver. Bare forms of ``port``
remain blocked because the ordinary surface spans harbors, carrying, clothing,
conduct, and computer interfaces.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v61_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v62-transport-and-mobility-morphology"
NOTE = (
    "v62: forty-eight unanimously reviewed transport and mobility "
    "genitive/dative forms; two port/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v24_transport_rail_tren": (
        "trenului de călători",
        "trenurilor de călători",
    ),
    "n_v24_transport_rail_tramvai": (
        "tramvaiului urban",
        "tramvaielor urbane",
    ),
    "n_v24_transport_rail_metrou": ("metroului urban", "metrourilor urbane"),
    "n_v4soc_autobuz": ("autobuzului urban", "autobuzelor urbane"),
    "n_v24_transport_personal_masina": (
        "autoturismului personal",
        "autoturismelor personale",
    ),
    "n_v24_transport_personal_bicicleta": (
        "bicicletei personale",
        "bicicletelor personale",
    ),
    "n_v24_transport_personal_motocicleta": (
        "motocicletei personale",
        "motocicletelor personale",
    ),
    "n_v24_transport_road_camion": ("camionului rutier", "camioanelor rutiere"),
    "n_v24_transport_road_microbuz": (
        "microbuzului rutier",
        "microbuzelor rutiere",
    ),
    "n_v24_transport_road_duba": ("dubei rutiere", "dubelor rutiere"),
    "n_v24_transport_terminals_gara": ("gării feroviare", "gărilor feroviare"),
    "n_v24_transport_terminals_aeroport": (
        "aeroportului civil",
        "aeroporturilor civile",
    ),
    "n_v24_transport_terminals_statie": (
        "stației de transport",
        "stațiilor de transport",
    ),
    "n_v2sti_avion": ("avionului de pasageri", "avioanelor de pasageri"),
    "n_v28_transport_water_vapor": (
        "vaporului de transport",
        "vapoarelor de transport",
    ),
    "n_v2via_parcare": ("parcării auto", "parcărilor auto"),
    "n_v4geo_strada": ("străzii urbane", "străzilor urbane"),
    "n_v4geo_canal": ("canalului navigabil", "canalelor navigabile"),
    "n_v4geo_carare": ("cărării pietonale", "cărărilor pietonale"),
    "n_v3via_naveta": (
        "navetei între casă și serviciu",
        "navetelor între casă și serviciu",
    ),
    "n_v20soc_ambulanta": ("ambulanței medicale", "ambulanțelor medicale"),
    "n_v20soc_pasaport": (
        "pașaportului de călătorie",
        "pașapoartelor de călătorie",
    ),
    "n_v18via_trotineta_electrica": (
        "trotinetei electrice urbane",
        "trotinetelor electrice urbane",
    ),
    "n_v18via_rovinieta": ("rovinietei rutiere", "rovinietelor rutiere"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("portului", "porturilor")
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
