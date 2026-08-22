"""Reviewed music and performance morphology for the V65 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
music and performance concepts enter the resolver. Bare forms of ``notă``
remain blocked because the ordinary surface spans musical, educational,
written, accounting, diplomatic, and descriptive senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v64_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v65-music-and-performance-morphology"
NOTE = (
    "v65: forty-eight unanimously reviewed music and performance "
    "genitive/dative forms; two note/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v2muz_cantaret_pop": ("cântărețului pop", "cântăreților pop"),
    "n_v2muz_trupa_rock": (
        "formației muzicale rock",
        "formațiilor muzicale rock",
    ),
    "n_v2muz_hit_de_vara": ("hitului de vară", "hiturilor de vară"),
    "n_v2muz_balada_rock": ("baladei rock", "baladelor rock"),
    "n_v2muz_dj_producator": (
        "DJ-ului producător muzical",
        "DJ-lor producători muzicali",
    ),
    "n_v2muz_concert": ("concertului live", "concertelor live"),
    "n_v2muz_scena_festival": (
        "scenei principale de festival",
        "scenelor principale de festival",
    ),
    "n_v2muz_artist_mascat": ("artistului mascat", "artiștilor mascați"),
    "n_v2muz_refren_de_vara": ("refrenului de vară", "refrenelor de vară"),
    "n_v3muz_melodie": ("melodiei muzicale", "melodiilor muzicale"),
    "n_v3muz_album": ("albumului muzical", "albumelor muzicale"),
    "n_v3muz_chitara": ("chitarei electrice", "chitarelor electrice"),
    "n_v3muz_pian": ("pianului de concert", "pianelor de concert"),
    "n_v3muz_ritm": ("ritmului muzical", "ritmurilor muzicale"),
    "n_v3muz_microfon": ("microfonului de scenă", "microfoanelor de scenă"),
    "n_v3muz_videoclip": (
        "videoclipului muzical",
        "videoclipurilor muzicale",
    ),
    "n_v3muz_playlist": ("playlistului muzical", "playlisturilor muzicale"),
    "n_v3muz_instrument_muzical": (
        "instrumentului muzical de concert",
        "instrumentelor muzicale de concert",
    ),
    "n_v4muz_voce": ("vocii muzicale", "vocilor muzicale"),
    "n_v4muz_radio": ("radioului muzical", "radiourilor muzicale"),
    "n_v4muz_boxa": ("boxei audio", "boxelor audio"),
    "n_v4muz_casti": ("căștii audio", "căștilor audio"),
    "n_v4muz_partitura": ("partiturii muzicale", "partiturilor muzicale"),
    "n_v4muz_acord": ("acordului muzical", "acordurilor muzicale"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("notei", "notelor")
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
