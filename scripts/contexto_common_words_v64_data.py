"""Reviewed history and heritage morphology for the V64 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
history and heritage concepts enter the resolver. Bare forms of ``front``
remain blocked because the ordinary surface spans military, organizational,
mining, architectural, meteorological, and physical-wave senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v63_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v64-history-and-heritage-morphology"
NOTE = (
    "v64: forty-eight unanimously reviewed history and heritage "
    "genitive/dative forms; two front/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v2ist_batalie": ("bătăliei istorice", "bătăliilor istorice"),
    "n_v2ist_domnitor": ("domnitorului medieval", "domnitorilor medievali"),
    "n_v2ist_rege": ("regelui medieval", "regilor medievali"),
    "n_v2ist_unire": ("unirii istorice", "unirilor istorice"),
    "n_v2ist_imperiu": ("imperiului istoric", "imperiilor istorice"),
    "n_v2ist_razboi": ("războiului istoric", "războaielor istorice"),
    "n_v2ist_dinastie": ("dinastiei regale", "dinastiilor regale"),
    "n_v2ist_capitala_istorica": ("capitalei istorice", "capitalelor istorice"),
    "n_v2ist_monument_istoric": (
        "monumentului istoric",
        "monumentelor istorice",
    ),
    "n_v2ist_principat": ("principatului medieval", "principatelor medievale"),
    "n_v2ist_revolutie": ("revoluției istorice", "revoluțiilor istorice"),
    "n_v2ist_tratat": ("tratatului diplomatic", "tratatelor diplomatice"),
    "n_v3ist_domnie": ("domniei istorice", "domniilor istorice"),
    "n_v3ist_soldat": ("soldatului medieval", "soldaților medievali"),
    "n_v3ist_regat": ("regatului medieval", "regatelor medievale"),
    "n_v3ist_colonizare": ("colonizării istorice", "colonizărilor istorice"),
    "n_v3ist_cucerire": ("cuceririi istorice", "cuceririlor istorice"),
    "n_v3ist_independenta": (
        "independenței naționale",
        "independențelor naționale",
    ),
    "n_v3ist_dictatura": ("dictaturii istorice", "dictaturilor istorice"),
    "n_v3ist_monarhie": ("monarhiei istorice", "monarhiilor istorice"),
    "n_v3ist_cetate": ("cetății medievale", "cetăților medievale"),
    "n_v3ist_epoca": ("epocii istorice", "epocilor istorice"),
    "n_v4ist_data": ("datei calendaristice", "datelor calendaristice"),
    "n_v4ist_armura": ("armurii medievale", "armurilor medievale"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("frontului", "fronturilor")
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
