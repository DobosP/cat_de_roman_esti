"""Reviewed sports-ecosystem morphology for the V60 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
sports concepts enter the resolver. Bare forms of ``fileu`` remain blocked
because the ordinary surface spans sports nets, general netting, and hair nets.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v59_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v60-sports-ecosystem-morphology"
NOTE = (
    "v60: forty-eight unanimously reviewed sports-ecosystem genitive/dative "
    "forms; two net/polyseme surfaces rejected; no nodes, edges, projections, "
    "or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v3spo_minge": ("mingii sportive", "mingilor sportive"),
    "n_v3spo_meci": ("meciului sportiv", "meciurilor sportive"),
    "n_v3spo_gol": ("golului marcat", "golurilor marcate"),
    "n_v3spo_arbitru": ("arbitrului sportiv", "arbitrilor sportivi"),
    "n_v3spo_medalie": ("medaliei sportive", "medaliilor sportive"),
    "n_v3spo_campionat": (
        "campionatului sportiv",
        "campionatelor sportive",
    ),
    "n_v4spo_echipa": ("echipei sportive", "echipelor sportive"),
    "n_v4spo_sala": ("sălii de sport", "sălilor de sport"),
    "n_v4spo_antrenament": (
        "antrenamentului sportiv",
        "antrenamentelor sportive",
    ),
    "n_v4spo_alergare": ("alergării sportive", "alergărilor sportive"),
    "n_v4spo_concurs": ("concursului sportiv", "concursurilor sportive"),
    "n_v4spo_competitie": (
        "competiției sportive",
        "competițiilor sportive",
    ),
    "n_v4spo_pauza": ("pauzei de meci", "pauzelor de meci"),
    "n_v4spo_suporter": ("suporterului echipei", "suporterilor echipei"),
    "n_v4spo_tribuna": ("tribunei de stadion", "tribunelor de stadion"),
    "n_v4spo_vestiar": ("vestiarului sportiv", "vestiarelor sportive"),
    "n_v4spo_tricou": ("tricoului sportiv", "tricourilor sportive"),
    "n_v4spo_stadion": ("stadionului sportiv", "stadioanelor sportive"),
    "n_v4spo_scor": ("scorului de meci", "scorurilor de meci"),
    "n_v4spo_fluier": ("fluierului de arbitru", "fluierelor de arbitru"),
    "n_v4spo_poarta": ("porții de joc", "porților de joc"),
    "n_v4spo_pista": ("pistei sportive", "pistelor sportive"),
    "n_v2spo_club_sportiv": ("clubului sportiv", "cluburilor sportive"),
    "n_v2spo_finala_sportiva": ("finalei sportive", "finalelor sportive"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("fileului", "fileurilor")
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
