"""Unanimously reviewed typed vocabulary for the V50 word-game wave.

Only exact same-referent forms enter the shared resolver, where they benefit
Contexto and Lanț.  Related basic words are authored separately in the
Contexto-only projection and never enter this alias batch.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import (
    BEGINNER_BENCHMARK,
)
from basic_words_v33_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v50-typed-vocabulary"
NOTE = (
    "v50: eight independently unanimous Romanian alias surfaces plus twelve "
    "non-winning Contexto basic-word projections; no nodes, edges, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v24_home_rooms_camera": ("odaie",),
    "n_v24_people_parents_mama": ("mămică",),
    "n_v24_people_parents_tata": ("tătic",),
    "n_lbax_regionalism_barabula": (
        "barabule",
        "barabulei",
        "barabulelor",
    ),
    "n_lbax_regionalism_papusoi": ("păpușoii",),
    "n_v4gas_paine": ("pită",),
}

# Every form below failed one or both independent exact-alias reviews.  Some are
# useful non-winning guesses, but none may silently enter the shared resolver.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "ogradă",
    "leafă",
    "muică",
    "baraboi",
    "cucuruzi",
    "cucuruzii",
    "blid",
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
    assert len(aliases) == len(normalized) == len(set(normalized)) == 8
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
