"""Unanimously reviewed typed-vocabulary morphology for the V51 wave.

Only normalized-unique grammatical forms of already accepted exact aliases enter
the shared resolver. Related common words are authored separately in the
Contexto-only projection and never enter this alias batch.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v50_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v51-typed-vocabulary"
NOTE = (
    "v51: thirty-two unanimously reviewed inflections of accepted Romanian aliases "
    "plus eight non-winning Contexto common-word projections; no nodes, edges, or "
    "game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v24_home_rooms_camera": (
        "odaia",
        "odăi",
        "odăile",
        "odăii",
        "odăilor",
    ),
    "n_v24_people_parents_mama": (
        "mămici",
        "mămicile",
        "mămicii",
        "mămicilor",
    ),
    "n_v24_people_parents_tata": (
        "tăticul",
        "tătici",
        "tăticii",
        "tăticului",
        "tăticilor",
    ),
    "n_v4gas_paine": (
        "pite",
        "pitele",
        "pitei",
        "pitelor",
    ),
    "n_v24_transport_personal_masina": (
        "automobilul",
        "automobile",
        "automobilele",
        "automobilului",
        "automobilelor",
        "autoturismul",
        "autoturisme",
        "autoturismele",
        "autoturismului",
        "autoturismelor",
    ),
    "n_v24_people_relationships_prieten": (
        "amicul",
        "amici",
        "amicului",
        "amicilor",
    ),
}

# Disagreement, competing ownership, and hard homonyms stay unresolved.  The
# shared applier verifies that none can silently acquire a resolver owner.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "amicii",
    "arborele",
    "arbori",
    "arborii",
    "arborelui",
    "arborilor",
    "cuptor",
    "fișă",
    "elan",
    "priză multiplă",
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
    assert len(ALIAS_ADDITIONS) == 6
    assert len(aliases) == len(normalized) == len(set(normalized)) == 32
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
