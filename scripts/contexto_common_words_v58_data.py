"""Reviewed school/literacy morphology for the V58 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing school, language,
and literacy concepts enter the resolver. Forms of ``carte`` remain blocked
because the ordinary surface spans books, playing cards, and documents.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v57_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v58-school-literacy-morphology"
NOTE = (
    "v58: forty-eight unanimously reviewed school/literacy genitive/dative forms; "
    "two book/card/document polysemes rejected; no nodes, edges, projections, or "
    "game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v3soc_scoala": ("școlii", "școlilor"),
    "n_v2lim_cuvant": ("cuvântului", "cuvintelor"),
    "n_v4lim_text": ("textului", "textelor"),
    "n_v3lim_dictionar": ("dicționarului", "dicționarelor"),
    "n_v3lim_litera": ("literei", "literelor"),
    "n_v3lim_propozitie": ("propoziției", "propozițiilor"),
    "n_v4lim_intrebare": ("întrebării", "întrebărilor"),
    "n_v4lim_raspuns": ("răspunsului", "răspunsurilor"),
    "n_v3lit_lectura": ("lecturii", "lecturilor"),
    "n_v4lit_biblioteca": (
        "bibliotecii școlare",
        "bibliotecilor școlare",
    ),
    "n_v4lit_pagina": ("paginii", "paginilor"),
    "n_v3lit_capitol": ("capitolului de carte", "capitolelor de carte"),
    "n_v4lit_coperta": ("copertei de carte", "copertelor de carte"),
    "n_v4lit_manuscris": (
        "manuscrisului literar",
        "manuscriselor literare",
    ),
    "n_v4lit_jurnal": ("jurnalului personal", "jurnalelor personale"),
    "n_v4lit_ziar": ("ziarului", "ziarelor"),
    "n_v4lit_revista": ("revistei literare", "revistelor literare"),
    "n_v3lit_cititor": ("cititorului", "cititorilor"),
    "n_v3lit_autor": ("autorului literar", "autorilor literari"),
    "n_v3lit_scriitor": ("scriitorului", "scriitorilor"),
    "n_v17soc_liceu": ("liceului", "liceelor"),
    "n_v3lim_silaba": ("silabei", "silabelor"),
    "n_substantiv": ("substantivului", "substantivelor"),
    "n_verb": ("verbului", "verbelor"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("cărții", "cărților")
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
