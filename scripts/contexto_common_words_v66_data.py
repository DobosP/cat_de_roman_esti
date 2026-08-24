"""Reviewed science and discovery morphology for the V66 typed-vocabulary wave.

Only normalized-unique, sense-qualified genitive/dative forms of existing
science and discovery concepts enter the resolver. Bare forms of ``curent``
remain blocked because the ordinary surface spans air, water, and electrical
current senses.
"""

from __future__ import annotations

import unicodedata

from basic_words_v33_data import BEGINNER_BENCHMARK
from contexto_common_words_v65_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v66-science-and-discovery-morphology"
NOTE = (
    "v66: forty-eight unanimously reviewed science and discovery "
    "genitive/dative forms; two current/polyseme surfaces rejected; no nodes, "
    "edges, projections, or game records."
)
NEW_NODE_IDS: tuple[str, ...] = ()
GAME_ITEM_IDS: tuple[str, ...] = ()

ALIAS_ADDITIONS: dict[str, tuple[str, ...]] = {
    "n_v2sti_stiinta": ("științei moderne", "științelor moderne"),
    "n_v2sti_laborator": (
        "laboratorului de cercetare",
        "laboratoarelor de cercetare",
    ),
    "n_v2sti_celula": ("celulei biologice", "celulelor biologice"),
    "n_v2sti_hormon": ("hormonului uman", "hormonilor umani"),
    "n_v2sti_bacterie": ("bacteriei patogene", "bacteriilor patogene"),
    "n_v2sti_calculator": (
        "calculatorului electronic",
        "calculatoarelor electronice",
    ),
    "n_v3sti_experiment": (
        "experimentului controlat",
        "experimentelor controlate",
    ),
    "n_v3sti_microscop": ("microscopului optic", "microscoapelor optice"),
    "n_v3sti_atom": ("atomului neutru", "atomilor neutri"),
    "n_v3sti_molecula": ("moleculei organice", "moleculelor organice"),
    "n_v3sti_energie": ("energiei cinetice", "energiilor cinetice"),
    "n_v3sti_planeta": ("planetei extrasolare", "planetelor extrasolare"),
    "n_v3sti_vaccin": ("vaccinului antiviral", "vaccinurilor antivirale"),
    "n_v4sti_virus": ("virusului biologic", "virusurilor biologice"),
    "n_v4sti_microb": ("microbului patogen", "microbilor patogeni"),
    "n_v4sti_lumina": ("luminii vizibile", "luminilor vizibile"),
    "n_v4sti_metal": ("metalului conductor", "metalelor conductoare"),
    "n_v4sti_forta": ("forței mecanice", "forțelor mecanice"),
    "n_v4sti_temperatura": (
        "temperaturii absolute",
        "temperaturilor absolute",
    ),
    "n_v4sti_gaz": ("gazului ideal", "gazelor ideale"),
    "n_v4sti_lichid": (
        "lichidului newtonian",
        "lichidelor newtoniene",
    ),
    "n_v4sti_solid": ("solidului cristalin", "solidelor cristaline"),
    "n_ribozom": ("ribozomului celular", "ribozomilor celulari"),
    "n_rachete": ("rachetei spațiale", "rachetelor spațiale"),
}

BLOCKED_ALIAS_FORMS: tuple[str, ...] = ("curentului", "curenților")
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
