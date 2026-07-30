"""Unanimously reviewed true aliases for the V44 Cald sau Rece vocabulary wave.

The wave deliberately adds no nodes or graph edges. Related words stay in the
Contexto-only projection; only exact same-sense Romanian forms enter the shared
resolver and may solve a target.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK

BUILD_VERSION = "fixture-v44-contexto-common-words"
NOTE = (
    "v44: twelve independently reviewed Romanian synonym surfaces plus a bounded "
    "Contexto-only feedback repair; no new graph nodes, edges, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v24_home_rooms_dormitor": ("cameră de dormit",),
    "n_v24_transport_personal_masina": ("automobil", "autoturism"),
    "n_v24_people_relationships_prieten": ("amic",),
    "n_v24_people_relationships_sotie": ("nevastă",),
    "n_v24_feeling_difficult_frica": ("teamă",),
    "n_v24_school_supplies_radiera": ("gumă de șters",),
    "n_v29_time_weekly_weekend": ("week-end",),
    "n_v24_action_language_a_spune": ("a zice",),
    "n_v4sti_copac": ("arbore",),
    "n_v28_feeling_positive_iubire": ("dragoste",),
    "n_v24_weather_precipitation_zapada": ("omăt",),
}

# Tempting forms rejected by at least one independent reviewer. Accent folding makes
# the first three actively unsafe; the rest are related or narrower rather than exact.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "sofa",
    "mâță",
    "mânie",
    "cameră de zi",
    "living",
    "a sosi",
    "a munci",
    "slujbă",
    "spaimă",
)
NORMALIZATION_COLLISION_REJECTIONS: tuple[tuple[str, str], ...] = (
    ("sofa", "șofa"),
    ("mâță", "mata"),
    ("mânie", "manie"),
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
    """Return an alias-only batch for the shared rollback-safe applier."""

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
    assert len(ALIAS_ADDITIONS) == 11
    assert len(aliases) == len(normalized) == len(set(normalized)) == 12
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert all(
        _norm(left) == _norm(right)
        for left, right in NORMALIZATION_COLLISION_REJECTIONS
    )
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
