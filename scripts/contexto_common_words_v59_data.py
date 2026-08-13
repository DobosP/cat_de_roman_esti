"""Reviewed human-anatomy morphology for the V59 typed-vocabulary wave.

Only normalized-unique, human-qualified genitive/dative forms of existing
anatomy concepts enter the resolver. Forms of ``creier`` remain blocked
because the ordinary surface spans the organ, intelligence, and a leader.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v58_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v59-human-anatomy-morphology"
NOTE = (
    "v59: forty-eight unanimously reviewed human-anatomy genitive/dative forms; "
    "two organ/intelligence/leader polysemes rejected; no nodes, edges, "
    "projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v4sti_inima": ("inimii umane", "inimilor umane"),
    "n_v4sti_os": ("osului uman", "oaselor umane"),
    "n_v4sti_piele": ("pielii umane", "pieilor umane"),
    "n_v4sti_ochi": ("ochiului uman", "ochilor umani"),
    "n_v4sti_ureche": ("urechii umane", "urechilor umane"),
    "n_v24_body_face_cap": ("capului uman", "capetelor umane"),
    "n_v24_body_face_nas": ("nasului uman", "nasurilor umane"),
    "n_v24_body_face_gura": ("gurii umane", "gurilor umane"),
    "n_v24_body_limbs_mana": ("mâinii umane", "mâinilor umane"),
    "n_v24_body_limbs_deget": ("degetului uman", "degetelor umane"),
    "n_v24_body_limbs_picior": ("piciorului uman", "picioarelor umane"),
    "n_v28_body_mouth_dinte": ("dintelui uman", "dinților umani"),
    "n_v29_body_upper_gat": ("gâtului uman", "gâturilor umane"),
    "n_v31_body_lower_genunchi": (
        "genunchiului uman",
        "genunchilor umani",
    ),
    "n_v31_body_lower_coapsa": ("coapsei umane", "coapselor umane"),
    "n_v31_body_lower_gamba": ("gambei umane", "gambelor umane"),
    "n_v31_body_lower_glezna": ("gleznei umane", "gleznelor umane"),
    "n_v31_body_lower_calcai": (
        "călcâiului uman",
        "călcâielor umane",
    ),
    "n_v32_body_face_buza": ("buzei umane", "buzelor umane"),
    "n_v32_body_face_obraz": ("obrazului uman", "obrajilor umani"),
    "n_v32_body_face_frunte": ("frunții umane", "frunților umane"),
    "n_v32_body_face_nara": ("nării umane", "nărilor umane"),
    "n_v32_body_face_spranceana": (
        "sprâncenei umane",
        "sprâncenelor umane",
    ),
    "n_v32_body_face_pleoapa": ("pleoapei umane", "pleoapelor umane"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("creierului", "creierelor")
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
