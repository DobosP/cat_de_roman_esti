"""Reviewed food input forms for V83; apply through the shared V24 transaction."""

from __future__ import annotations

from basic_words_v33_data import BEGINNER_BENCHMARK  # noqa: F401
from contexto_common_words_v72_data import DEFERRED_AMBIGUOUS_TERMS  # noqa: F401

BUILD_VERSION = "fixture-v83-food-input-and-feedback"
NOTE = "v83:24 reviewed grammatical and qualified food forms across8 existing concepts."
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()
INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    'n_gas_urda': ('urdei', 'urde', 'urdele', 'urdelor'),
    'n_gas_telemea': ('telemelei', 'telemele', 'telemelele', 'telemelelor'),
    'n_gas_mujdei': ('mujdeiului', 'mujdeie', 'mujdeiele', 'mujdeielor'),
    'n_v3gas_friptura': ('fripturii', 'fripturilor'),
    'n_v3gas_cartofi_prajiti': ('cartof prăjit', 'cartofului prăjit', 'cartofilor prăjiți'),
    'n_gas_bulz': ('bulzuri cu brânză', 'bulzurile cu brânză'),
    'n_v21gas_cornulete': (
        'cornuleț cu gem', 'cornulețul cu gem',
        'cornulețului cu gem', 'cornulețelor cu gem',
    ),
    'n_v17gas_gogosi': ('gogoașa prăjită',),
}

ALIAS_PROBES = tuple(
    (form, owner) for owner, forms in ALIAS_ADDITIONS.items() for form in forms
)


def build_nodes_and_edges() -> dict[str, object]:
    return {
        "nodes": [], "edges": [],
        "aliases": {owner: list(forms) for owner, forms in ALIAS_ADDITIONS.items()},
    }
