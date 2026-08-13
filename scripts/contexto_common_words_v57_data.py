"""Reviewed creative-arts morphology for the V57 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing creative-arts
concepts enter the resolver. Forms of ``tablou`` remain blocked because the
ordinary surface spans both an artwork and structured displays or panels.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v56_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v57-creative-arts-morphology"
NOTE = (
    "v57: forty-eight unanimously reviewed creative-arts genitive/dative forms; two "
    "artwork/display polysemes rejected; no nodes, edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v3art_arta": ("artei", "artelor"),
    "n_v4art_spectacol": ("spectacolului", "spectacolelor"),
    "n_v4art_dans": ("dansului", "dansurilor"),
    "n_v4art_festival": ("festivalului", "festivalurilor"),
    "n_v4art_basm": ("basmului", "basmelor"),
    "n_v4art_orchestra": ("orchestrei", "orchestrelor"),
    "n_v2art_muzeu": ("muzeului", "muzeelor"),
    "n_v2art_balada_populara": ("baladei populare", "baladelor populare"),
    "n_v4art_traditie": ("tradiției", "tradițiilor"),
    "n_v2art_ceramica_populara": ("ceramicii populare", "ceramicilor populare"),
    "n_v4art_fotografie": ("fotografiei", "fotografiilor"),
    "n_v4art_colind": ("colindului", "colindelor"),
    "n_v4art_mestesug": ("meșteșugului", "meșteșugurilor"),
    "n_v4art_vopsea": ("vopselei", "vopselelor"),
    "n_v4art_pensula": ("pensulei", "pensulelor"),
    "n_v3art_expozitie": ("expoziției", "expozițiilor"),
    "n_v2art_fresca": ("frescei", "frescelor"),
    "n_v3art_desen": ("desenului", "desenelor"),
    "n_v3art_statuie": ("statuii", "statuilor"),
    "n_v3art_galerie_arta": ("galeriei de artă", "galeriilor de artă"),
    "n_arta_plastica": ("artei plastice", "artelor plastice"),
    "n_v2art_pictura_romaneasca": (
        "picturii românești",
        "picturilor românești",
    ),
    "n_v2art_sculptura_romaneasca": (
        "sculpturii românești",
        "sculpturilor românești",
    ),
    "n_v2art_dans_popular": ("dansului popular", "dansurilor populare"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("tabloului", "tablourilor")
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
