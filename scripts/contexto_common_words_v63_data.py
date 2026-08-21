"""Reviewed film and television morphology for the V63 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
film and television concepts enter the resolver. Bare forms of ``rol`` remain
blocked because the ordinary surface spans performance, functional,
administrative, maritime, and clothing senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v62_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v63-film-and-television-morphology"
NOTE = (
    "v63: forty-eight unanimously reviewed film and television "
    "genitive/dative forms; two role/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v2fil_serial_tv": (
        "serialului dramatic de televiziune",
        "serialelor dramatice de televiziune",
    ),
    "n_v2fil_emisiune_tv": (
        "emisiunii de televiziune",
        "emisiunilor de televiziune",
    ),
    "n_v2fil_actor": ("actorului de film", "actorilor de film"),
    "n_v2fil_prezentator_tv": (
        "prezentatorului de televiziune",
        "prezentatorilor de televiziune",
    ),
    "n_v2fil_regizor": ("regizorului de film", "regizorilor de film"),
    "n_v2fil_personaj": ("personajului de film", "personajelor de film"),
    "n_v2fil_comedie": (
        "comediei cinematografice",
        "comediilor cinematografice",
    ),
    "n_v2fil_concurs_tv": (
        "concursului televizat",
        "concursurilor televizate",
    ),
    "n_v3fil_film": ("filmului de cinema", "filmelor de cinema"),
    "n_v3fil_cinematograf": (
        "cinematografului local",
        "cinematografelor locale",
    ),
    "n_v3fil_scenariu": ("scenariului de film", "scenariilor de film"),
    "n_v3fil_episod": ("episodului de serial", "episoadelor de serial"),
    "n_v3fil_sezon": ("sezonului de serial", "sezoanelor de serial"),
    "n_v3fil_trailer": ("trailerului de film", "trailerelor de film"),
    "n_v3fil_subtitrare": (
        "subtitrării de film",
        "subtitrărilor de film",
    ),
    "n_v3fil_dublaj": ("dublajului de film", "dublajelor de film"),
    "n_v3fil_documentar": (
        "documentarului cinematografic",
        "documentarelor cinematografice",
    ),
    "n_v3fil_coloana_sonora": (
        "coloanei sonore de film",
        "coloanelor sonore de film",
    ),
    "n_v4fil_ecran": (
        "ecranului cinematografic",
        "ecranelor cinematografice",
    ),
    "n_v4fil_camera_video": (
        "camerei video profesionale",
        "camerelor video profesionale",
    ),
    "n_v4fil_studio": ("studioului de film", "studiourilor de film"),
    "n_v4fil_montaj": ("montajului de film", "montajelor de film"),
    "n_v4fil_producator": (
        "producătorului de film",
        "producătorilor de film",
    ),
    "n_v4fil_operator_imagine": (
        "operatorului profesionist de imagine",
        "operatorilor profesioniști de imagine",
    ),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("rolului", "rolurilor")
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
