"""Reviewed food-noun morphology for the V53 typed-vocabulary wave.

Only normalized-unique genitive/dative forms of existing food concepts enter
the shared resolver.  Forms of ``masă`` remain blocked because the ordinary
surface denotes both a meal and a piece of furniture.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v52_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v53-food-morphology"
NOTE = (
    "v53: forty-eight unanimously reviewed food genitive/dative forms; two "
    "meal/table polysemes rejected; no nodes, edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v4gas_mancare": ("mâncării", "mâncărurilor"),
    "n_v4gas_apa": ("apei", "apelor"),
    "n_v4gas_paine": ("pâinii", "pâinilor"),
    "n_v4gas_carne": ("cărnii", "cărnurilor"),
    "n_v4gas_fruct": ("fructului", "fructelor"),
    "n_v4gas_supa": ("supei", "supelor"),
    "n_v4gas_prajitura": ("prăjiturii", "prăjiturilor"),
    "n_v4gas_ou": ("oului", "ouălor"),
    "n_v4gas_ceapa": ("cepei", "cepelor"),
    "n_v4gas_rosie": ("roșiei", "roșiilor"),
    "n_v4gas_vin": ("vinului", "vinurilor"),
    "n_v4gas_bucatarie": ("bucătăriei", "bucătăriilor"),
    "n_v24_food_pantry_ulei": ("uleiului", "uleiurilor"),
    "n_v24_food_breakfast_iaurt": ("iaurtului", "iaurturilor"),
    "n_v24_food_orchard_mar": ("mărului", "merelor"),
    "n_v24_food_orchard_para": ("perei", "perelor"),
    "n_v24_food_orchard_pruna": ("prunei", "prunelor"),
    "n_v24_food_small_fruit_cireasa": ("cireșei", "cireșelor"),
    "n_v24_food_small_fruit_capsuna": ("căpșunii", "căpșunilor"),
    "n_v24_food_small_fruit_strugure": ("strugurelui", "strugurilor"),
    "n_v24_food_summer_fruit_pepene": ("pepenelui", "pepenilor"),
    "n_v24_food_summer_fruit_caisa": ("caisei", "caiselor"),
    "n_v24_food_summer_fruit_piersica": ("piersicii", "piersicilor"),
    "n_v24_food_imported_fruit_banana": ("bananei", "bananelor"),
}

# ``masă`` is already polysemous between meal and furniture. Its case forms
# cannot acquire an exclusive food owner without a sense-aware resolver.
BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("mesei", "meselor")
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
