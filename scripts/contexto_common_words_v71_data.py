"""Reviewed literature-and-storytelling morphology for the V71 wave.

Only normalized-unique genitive/dative forms unanimously bound to an existing
literature concept enter the resolver. Bare forms of ``intrigă`` remain blocked
across narrative-plot and scheming or machination senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v70_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v71-literature-and-storytelling-morphology"
NOTE = (
    "v71: forty-eight unanimously reviewed literature-and-storytelling "
    "genitive/dative forms; two intrigă polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v2lit_avangarda": ("avangardei literare", "avangardelor literare"),
    "n_v2lit_basm_cult": ("basmului cult", "basmelor culte"),
    "n_v2lit_cenaclu_literar": ("cenaclului literar", "cenaclurilor literare"),
    "n_v4lit_conflict": ("conflictului narativ", "conflictelor narative"),
    "n_v2lit_critic_literar": ("criticului literar", "criticilor literari"),
    "n_v2lit_dramaturgie": ("dramaturgiei", "dramaturgiilor"),
    "n_v4lit_librarie": ("librăriei", "librăriilor"),
    "n_v2lit_limbaj_poetic": ("limbajului poetic", "limbajelor poetice"),
    "n_v4lit_mesaj": (
        "mesajului din opera literară",
        "mesajelor din operele literare",
    ),
    "n_v4lit_narator": ("naratorului", "naratorilor"),
    "n_v2lit_nuvela": ("nuvelei literare", "nuvelelor literare"),
    "n_v2lit_personaj_literar": (
        "personajului literar",
        "personajelor literare",
    ),
    "n_v4lit_piesa": ("piesei dramatice", "pieselor dramatice"),
    "n_v3lit_poveste": ("poveștii literare", "poveștilor literare"),
    "n_v4lit_proza": ("prozei literare", "prozelor literare"),
    "n_v3lit_rima": ("rimei", "rimelor"),
    "n_v4lit_rand": ("rândului de text", "rândurilor de text"),
    "n_v2lit_sat_romanesc": (
        "satului din literatura română",
        "satelor din literatura română",
    ),
    "n_v4lit_stil": ("stilului literar", "stilurilor literare"),
    "n_v3lit_strofa": ("strofei", "strofelor"),
    "n_v4lit_tema": ("temei literare", "temelor literare"),
    "n_v4lit_titlu": (
        "titlului operei literare",
        "titlurilor operelor literare",
    ),
    "n_v3lit_vers": ("versului", "versurilor"),
    "n_v23lit_zmeul": ("zmeului din basme", "zmeilor din basme"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = (
    "intrigii",
    "intrigilor",
)
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
    blocked = {_norm(value) for value in BLOCKED_ALIAS_FORMS}
    assert len(ALIAS_ADDITIONS) == 24
    assert all(len(values) == 2 for values in ALIAS_ADDITIONS.values())
    assert len(aliases) == len(normalized) == len(set(normalized)) == 48
    assert not (blocked & set(normalized))
    assert len(blocked) == 2
    assert len(DEFERRED_AMBIGUOUS_TERMS) == len(set(DEFERRED_AMBIGUOUS_TERMS)) == 70
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK})


_validate_source()
