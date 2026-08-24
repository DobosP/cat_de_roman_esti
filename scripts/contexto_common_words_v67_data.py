"""Reviewed online-content and social-media morphology for the V67 wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
online-content and social-media concepts enter the resolver. Bare forms of
``flux`` remain blocked because the ordinary surface spans tides, physical or
information flows, and the continuously updated social-media feed sense.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v66_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v67-online-content-and-social-media-morphology"
NOTE = (
    "v67: forty-eight unanimously reviewed online-content and social-media "
    "genitive/dative forms; two flux/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_net_comentarii_online": (
        "comentariului public de pe internet",
        "comentariilor publice de pe internet",
    ),
    "n_net_parodie_online": (
        "parodiei video de pe internet",
        "parodiilor video de pe internet",
    ),
    "n_net_sketch_online": ("scenetei online", "scenetelor online"),
    "n_v4mem_distribuire": (
        "distribuirii de conținut online",
        "distribuirilor de conținut online",
    ),
    "n_net_challenge_online": (
        "provocării virale online",
        "provocărilor virale online",
    ),
    "n_net_unboxing_ro": (
        "despachetării filmate online",
        "despachetărilor filmate online",
    ),
    "n_net_reactie_video": ("videoului de reacție", "videourilor de reacție"),
    "n_net_thumbnail_cu_sageata": (
        "miniaturii video cu săgeată",
        "miniaturilor video cu săgeată",
    ),
    "n_net_algoritm_social": (
        "algoritmului platformei sociale",
        "algoritmilor platformelor sociale",
    ),
    "n_v2mem_clip_scurt": ("clipului video scurt", "clipurilor video scurte"),
    "n_v4mem_urmaritor": (
        "urmăritorului paginii online",
        "urmăritorilor paginii online",
    ),
    "n_v2mem_canal_youtube": ("canalului YouTube", "canalelor YouTube"),
    "n_v2mem_sunet_viral": ("sunetului viral", "sunetelor virale"),
    "n_v2mem_clip_culinar": ("rețetei video", "rețetelor video"),
    "n_v2mem_documentar_online": (
        "documentarului online",
        "documentarelor online",
    ),
    "n_v2mem_comedie_online": (
        "comediei video online",
        "comediilor video online",
    ),
    "n_v2mem_personaj_memetic": (
        "personajului memetic",
        "personajelor memetice",
    ),
    "n_v2mem_replici_memorabile": (
        "replicii memorabile",
        "replicilor memorabile",
    ),
    "n_v2mem_public_online": (
        "audienței românești online",
        "audiențelor românești online",
    ),
    "n_v2mem_format_video": ("formatului video", "formatelor video"),
    "n_v3mem_sablon_meme": ("șablonului de meme", "șabloanelor de meme"),
    "n_v3mem_screenshot": (
        "capturii de ecran salvate",
        "capturilor de ecran salvate",
    ),
    "n_v4mem_postare": ("postării publice online", "postărilor publice online"),
    "n_v3mem_scroll_infinit": ("derulării infinite", "derulărilor infinite"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("fluxului", "fluxurilor")
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
