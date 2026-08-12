"""Reviewed household-noun morphology for the V52 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing household concepts
enter the shared resolver.  Two blanket forms remain blocked because the
accent-insensitive key is also a valid inflection of ``pat`` (bed).
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v51_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v52-household-morphology"
NOTE = (
    "v52: forty-eight unanimously reviewed household genitive/dative forms; "
    "two accent-insensitive bed/blanket collisions rejected; no nodes, edges, "
    "projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v24_home_rooms_camera": ("camerei", "camerelor"),
    "n_v24_home_rooms_sufragerie": ("sufrageriei", "sufrageriilor"),
    "n_v24_home_rooms_dormitor": ("dormitorului", "dormitoarelor"),
    "n_v24_home_outdoor_balcon": ("balconului", "balcoanelor"),
    "n_v24_home_outdoor_curte": ("curții", "curților"),
    "n_v24_home_outdoor_gradina": ("grădinii", "grădinilor"),
    "n_v24_home_structure_acoperis": ("acoperișului", "acoperișurilor"),
    "n_v24_home_structure_perete": ("peretelui", "pereților"),
    "n_v24_home_structure_tavan": ("tavanului", "tavanelor"),
    "n_v24_home_surfaces_podea": ("podelei", "podelelor"),
    "n_v24_home_surfaces_fereastra": ("ferestrei", "ferestrelor"),
    "n_v24_home_surfaces_oglinda": ("oglinzii", "oglinzilor"),
    "n_v24_home_storage_dulap": ("dulapului", "dulapurilor"),
    "n_v24_home_storage_raft": ("raftului", "rafturilor"),
    "n_v24_home_bed_saltea": ("saltelei", "saltelelor"),
    "n_v24_home_bed_perna": ("pernei", "pernelor"),
    "n_v24_home_textiles_cearsaf": ("cearșafului", "cearșafurilor"),
    "n_v24_home_textiles_covor": ("covorului", "covoarelor"),
    "n_v24_home_seating_scaun": ("scaunului", "scaunelor"),
    "n_v24_home_seating_canapea": ("canapelei", "canapelelor"),
    "n_v24_home_seating_fotoliu": ("fotoliului", "fotoliilor"),
    "n_v24_home_appliances_lampa": ("lămpii", "lămpilor"),
    "n_v24_home_appliances_frigider": ("frigiderului", "frigiderelor"),
    "n_v24_home_appliances_aragaz": ("aragazului", "aragazurilor"),
}

# Diacritic folding maps both forms to legitimate inflections of ``pat``.
# Neither reviewer accepted assigning those keys exclusively to ``pătură``.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("păturile", "păturilor")
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
