"""Reviewed Romanian dishes-and-pastries morphology for the V72 wave.

Only normalized-unique genitive/dative forms unanimously bound to an existing
gastronomy concept enter the resolver. Qualified forms keep the food senses of
``bulz`` and ``gogoașă`` distinct from their ordinary non-food senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v71_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v72-romanian-dishes-and-pastries-morphology"
NOTE = (
    "v72: fifty unanimously reviewed Romanian dishes-and-pastries "
    "genitive/dative forms; no nodes, edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v18gas_amandina": ("amandinei", "amandinelor"),
    "n_gas_ardei_umpluti": ("ardeiului umplut", "ardeilor umpluți"),
    "n_gas_baclava_dobrogeana": (
        "baclavalei dobrogene",
        "baclavalelor dobrogene",
    ),
    "n_gas_bulz": ("bulzului cu brânză", "bulzurilor cu brânză"),
    "n_gas_caltabos": ("caltaboșului", "caltaboșilor"),
    "n_gas_cascaval_pane": ("cașcavalului pane", "cașcavalurilor pane"),
    "n_gas_ciorba_burta": ("ciorbei de burtă", "ciorbelor de burtă"),
    "n_v11gas_ciorba_perisoare": (
        "ciorbei de perișoare",
        "ciorbelor de perișoare",
    ),
    "n_gas_ciorba_radauteana": (
        "ciorbei rădăuțene",
        "ciorbelor rădăuțene",
    ),
    "n_v3gas_clatite": ("clătitei", "clătitelor"),
    "n_v17gas_coliva": ("colivei", "colivelor"),
    "n_gas_covrigi_buzau": ("covrigului de Buzău", "covrigilor de Buzău"),
    "n_gas_cozonac": ("cozonacului", "cozonacilor"),
    "n_v17gas_carnati_plescoi": (
        "cârnatului de Pleșcoi",
        "cârnaților de Pleșcoi",
    ),
    "n_gas_drob_miel": ("drobului de miel", "droburilor de miel"),
    "n_v17gas_gogosi": ("gogoșii prăjite", "gogoșilor prăjite"),
    "n_gas_mamaliga": ("mămăligii", "mămăligilor"),
    "n_gas_papanasi": ("papanașului", "papanașilor"),
    "n_gas_piftie": ("piftiei", "piftiilor"),
    "n_v2gas_placinte": ("plăcintei", "plăcintelor"),
    "n_v18gas_salam_de_biscuiti": (
        "salamului de biscuiți",
        "salamurilor de biscuiți",
    ),
    "n_gas_salata_boeuf": ("salatei de boeuf", "salatelor de boeuf"),
    "n_gas_salata_vinete": ("salatei de vinete", "salatelor de vinete"),
    "n_gas_sarmale": ("sarmalei", "sarmalelor"),
    "n_v11gas_tochitura_moldoveneasca": (
        "tochiturii moldovenești",
        "tochiturilor moldovenești",
    ),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ()
DEFERRED_AMBIGUOUS_TERMS = BASE_DEFERRED_AMBIGUOUS_TERMS

ALIAS_PROBES: tuple[tuple[str, str], ...] = tuple(
    (alias, node_id) for node_id, aliases in ALIAS_ADDITIONS.items() for alias in aliases
)
INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = ()


def _norm(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char)).casefold().split()
    )


def build_nodes_and_edges() -> dict[str, object]:
    """Return the alias-only batch consumed by the rollback-safe applier."""

    return {
        "nodes": [],
        "edges": [],
        "aliases": {node_id: list(aliases) for node_id, aliases in ALIAS_ADDITIONS.items()},
    }


def _validate_source() -> None:
    aliases = [alias for values in ALIAS_ADDITIONS.values() for alias in values]
    normalized = [_norm(alias) for alias in aliases]
    assert len(ALIAS_ADDITIONS) == 25
    assert all(len(values) == 2 for values in ALIAS_ADDITIONS.values())
    assert len(aliases) == len(normalized) == len(set(normalized)) == 50
    assert BLOCKED_ALIAS_FORMS == ()
    assert len(DEFERRED_AMBIGUOUS_TERMS) == len(set(DEFERRED_AMBIGUOUS_TERMS)) == 70
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
