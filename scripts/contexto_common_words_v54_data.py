"""Reviewed people-noun morphology for the V54 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing people and role
concepts enter the shared resolver. Forms of ``părinte`` remain blocked because
the ordinary surface denotes both a parent and a cleric.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v53_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v54-people-morphology"
NOTE = (
    "v54: forty-eight unanimously reviewed people genitive/dative forms; two "
    "parent/clergy polysemes rejected; no nodes, edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v4per_om": ("omului", "oamenilor"),
    "n_v4per_femeie": ("femeii", "femeilor"),
    "n_v4per_barbat": ("bărbatului", "bărbaților"),
    "n_v4soc_copil": ("copilului", "copiilor"),
    "n_v4soc_elev": ("elevului", "elevilor"),
    "n_v4soc_student": ("studentului", "studenților"),
    "n_cetatean": ("cetățenei", "cetățenelor"),
    "n_v4per_profesor": ("profesorului", "profesorilor"),
    "n_v3per_medic": ("medicului", "medicilor"),
    "n_v4soc_preot": ("preotului", "preoților"),
    "n_v3per_poet": ("poetului", "poeților"),
    "n_v3per_compozitor": ("compozitorului", "compozitorilor"),
    "n_v3per_pictor": ("pictorului", "pictorilor"),
    "n_v3per_sculptor": ("sculptorului", "sculptorilor"),
    "n_v3per_politician": ("politicianului", "politicienilor"),
    "n_v3per_muzician": ("muzicianului", "muzicienilor"),
    "n_v3per_cantaret": ("cântărețului", "cântăreților"),
    "n_v3per_fotbalist": ("fotbalistului", "fotbaliștilor"),
    "n_sportiv": ("sportivului", "sportivilor"),
    "n_inventator": ("inventatorului", "inventatorilor"),
    "n_v4per_savant": ("savantului", "savanților"),
    "n_v4per_cercetator": ("cercetătorului", "cercetătorilor"),
    "n_v4per_jucator": ("jucătorului", "jucătorilor"),
    "n_v4per_lider": ("liderului", "liderilor"),
}

# ``părinte`` is already polysemous between a parent and a cleric. Its case
# forms cannot acquire an exclusive family owner without a sense-aware resolver.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("părintelui", "părinților")
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
