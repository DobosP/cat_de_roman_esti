"""Reviewed Romanian-language and grammar morphology for the V68 wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
Romanian-language and grammar concepts enter the resolver. Bare forms of
``punct`` remain blocked because the ordinary surface spans punctuation,
spatial or geometric locations, measurements, and scoring senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v67_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v68-romanian-language-and-grammar-morphology"
NOTE = (
    "v68: forty-eight unanimously reviewed Romanian-language and grammar "
    "genitive/dative forms; two punct/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v4lim_sunet": ("sunetului limbii române", "sunetelor limbii române"),
    "n_v2lim_scriere": (
        "scrierii alfabetice a limbii române",
        "scrierilor alfabetice ale limbilor romanice",
    ),
    "n_v3lim_limba": ("limbii naturale", "limbilor naturale"),
    "n_v2lim_vocabular": (
        "vocabularului limbii române",
        "vocabularelor limbilor romanice",
    ),
    "n_v2lim_parte_de_vorbire": (
        "părții de vorbire în română",
        "părților de vorbire în română",
    ),
    "n_v20lim_proverb": ("proverbului românesc", "proverbelor românești"),
    "n_v20lim_neologism": ("neologismului lexical", "neologismelor lexicale"),
    "n_v20lim_omonim": ("omonimului lexical", "omonimelor lexicale"),
    "n_v2lim_vorbire_populara": (
        "vorbirii populare românești",
        "vorbirilor populare românești",
    ),
    "n_v20lim_argou": ("argoului urban românesc", "argourilor urbane românești"),
    "n_sintaxa": ("sintaxei limbii române", "sintaxelor limbilor romanice"),
    "n_v20lim_paronim": ("paronimului lexical", "paronimelor lexicale"),
    "n_gramatica": ("gramaticii limbii române", "gramaticilor limbilor romanice"),
    "n_v4lim_virgula": ("virgulei ortografice", "virgulelor ortografice"),
    "n_v2lim_flexiune": ("flexiunii gramaticale", "flexiunilor gramaticale"),
    "n_v17lim_diminutive": ("diminutivului lexical", "diminutivelor lexicale"),
    "n_v2lim_expresie_idiomatica": (
        "expresiei idiomatice românești",
        "expresiilor idiomatice românești",
    ),
    "n_v4lim_persoana_gramaticala": (
        "persoanei gramaticale a verbului",
        "persoanelor gramaticale ale verbului",
    ),
    "n_v4lim_plural": ("pluralului gramatical", "pluralelor gramaticale"),
    "n_v4lim_greseala": ("greșelii de exprimare", "greșelilor de exprimare"),
    "n_v2lim_grai": ("graiului regional românesc", "graiurilor regionale românești"),
    "n_v3lim_fraza": ("frazei gramaticale", "frazelor gramaticale"),
    "n_v2lim_dialect": ("dialectului limbii române", "dialectelor limbii române"),
    "n_ortografie": (
        "ortografiei limbii române",
        "ortografiilor limbilor romanice",
    ),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("punctului", "punctelor")
DEFERRED_AMBIGUOUS_TERMS = (
    *BASE_DEFERRED_AMBIGUOUS_TERMS,
    *BLOCKED_ALIAS_FORMS,
)

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
    assert len(ALIAS_ADDITIONS) == 24
    assert len(aliases) == len(normalized) == len(set(normalized)) == 48
    assert not ({_norm(value) for value in BLOCKED_ALIAS_FORMS} & set(normalized))
    assert len({_norm(value) for value in BLOCKED_ALIAS_FORMS}) == 2
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
