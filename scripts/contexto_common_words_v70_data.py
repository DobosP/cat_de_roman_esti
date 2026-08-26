"""Reviewed social-and-civic-life morphology for the V70 wave.

Only normalized-unique genitive/dative forms unanimously bound to an existing
social-and-civic-life concept enter the resolver. Forms of ``lege`` remain
blocked across legal, scientific, customary, and religious senses; forms of
``bancă`` remain blocked across the financial-institution and bench senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v68_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v70-social-and-civic-life-morphology"
NOTE = (
    "v70: forty-six unanimously reviewed social-and-civic-life genitive/dative "
    "forms; four lege/bancă polyseme surfaces rejected; no nodes, edges, "
    "projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v4soc_apartament": ("apartamentului", "apartamentelor"),
    "n_v4soc_autobuz": ("autobuzului", "autobuzelor"),
    "n_v24_feeling_joy_bucurie": ("bucuriei", "bucuriilor"),
    "n_v4soc_casatorie": ("căsătoriei", "căsătoriilor"),
    "n_v4soc_divort": ("divorțului", "divorțurilor"),
    "n_v24_feeling_difficult_frica": ("fricii", "fricilor"),
    "n_v24_feeling_difficult_furie": ("furiei", "furiilor"),
    "n_v4soc_magazin": ("magazinului", "magazinelor"),
    "n_v4soc_nunta": ("nunții", "nunților"),
    "n_v4soc_pensie": ("pensiei", "pensiilor"),
    "n_v4soc_salariu": ("salariului", "salariilor"),
    "n_v3soc_spital": ("spitalului", "spitalelor"),
    "n_v2soc_universitate": ("universității", "universităților"),
    "n_v20soc_greva": ("grevei", "grevelor"),
    "n_v20soc_sindicat": ("sindicatului", "sindicatelor"),
    "n_v20soc_referendum": ("referendumului", "referendumurilor"),
    "n_v3soc_partid_politic": ("partidului politic", "partidelor politice"),
    "n_v3soc_protest": ("protestului", "protestelor"),
    "n_v4soc_pacient": ("pacientului", "pacienților"),
    "n_v20soc_prefect": ("prefectului", "prefecților"),
    "n_v3soc_impozit": ("impozitului", "impozitelor"),
    "n_v2soc_armata": ("armatei", "armatelor"),
    "n_v11soc_diaspora": ("diasporei", "diasporelor"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "legii",
    "legilor",
    "băncii",
    "băncilor",
)
DEFERRED_AMBIGUOUS_TERMS = (
    *BASE_DEFERRED_AMBIGUOUS_TERMS,
    *BLOCKED_ALIAS_FORMS,
)

ALIAS_PROBES: tuple[tuple[str, str], ...] = tuple(
    (alias, node_id) for node_id, aliases in ALIAS_ADDITIONS.items() for alias in aliases
)
INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = ()


def _norm(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char)).casefold().split()
    )


def build_nodes_and_edges() -> dict[str, object]:
    """Return the alias-only batch consumed by the rollback-safe applier."""

    return {
        "nodes": [],
        "edges": [],
        "aliases": {node_id: list(aliases) for node_id, aliases in ALIAS_ADDITIONS.items()},
    }


def _validate_source() -> None:
    aliases = [alias for values in ALIAS_ADDITIONS.values() for alias in values]
    normalized = [_norm(alias) for alias in aliases]
    blocked = {_norm(value) for value in BLOCKED_ALIAS_FORMS}
    assert len(ALIAS_ADDITIONS) == 23
    assert all(len(values) == 2 for values in ALIAS_ADDITIONS.values())
    assert len(aliases) == len(normalized) == len(set(normalized)) == 46
    assert not (blocked & set(normalized))
    assert len(blocked) == 4
    assert len(DEFERRED_AMBIGUOUS_TERMS) == len(set(DEFERRED_AMBIGUOUS_TERMS)) == 68
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
