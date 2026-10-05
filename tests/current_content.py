"""One manually reviewed snapshot of the currently served content artifacts.

These values are expected test data.  They are intentionally written here rather than
computed from the fixtures being checked.  Historical wave, review, pre-apply, dossier,
ledger, and reconstruction hashes remain local to the tests that own that evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


def _frozen(values: dict[K, V]) -> Mapping[K, V]:
    return MappingProxyType(values)


@dataclass(frozen=True, slots=True)
class CurrentContentSnapshot:
    build_version: str
    artifact_sha256: Mapping[str, str]
    payload_sha256: Mapping[str, str]
    kg_counts: Mapping[str, int]
    mobile_counts: Mapping[str, int]
    pack_counts: Mapping[str, int]
    pack_id_high_water: Mapping[str, int]
    status_counts: Mapping[str, int]
    game_inventory: Mapping[str, tuple[int, int, int]]
    ranking_counts: Mapping[str, int | Mapping[str, int]]
    derived_counts: Mapping[str, int | Mapping[str, int]]
    quick_counts: Mapping[str, int | Mapping[str, int]]
    quick_selectable_counts: Mapping[str, int | Mapping[str, int]]
    feedback_observations: Mapping[str, int]
    clatite_opener_ranks: Mapping[str, int]
    contexto_approved: int
    contexto_eligible: int
    contexto_id_high_water: int
    projection_terms: int
    projection_domains: int
    legacy_feedback_proxies: int

    @property
    def kg_sha256(self) -> str:
        return self.artifact_sha256["cat_de_roman_esti/fixtures/kg_sample.json"]

    @property
    def pack_sha256(self) -> str:
        return self.artifact_sha256["cat_de_roman_esti/fixtures/games_pack.json"]

    @property
    def rankings_sha256(self) -> str:
        return self.artifact_sha256[
            "cat_de_roman_esti/fixtures/board_rankings_v37.json"
        ]

    @property
    def derived_sha256(self) -> str:
        return self.artifact_sha256[
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
        ]

    @property
    def quick_sha256(self) -> str:
        return self.artifact_sha256["cat_de_roman_esti/fixtures/quick_games_v92.json"]

    @property
    def mobile_sha256(self) -> str:
        return self.artifact_sha256[
            "tests/fixtures/cat_mobile_app_pack_contract.json"
        ]

    @property
    def ranking_rows_sha256(self) -> str:
        return self.payload_sha256["ranking_rows"]

    @property
    def frozen_boards_sha256(self) -> str:
        return self.payload_sha256["frozen_derived_boards"]

    @property
    def nodes_without_aliases_sha256(self) -> str:
        return self.payload_sha256["kg_nodes_without_aliases"]

    @property
    def edges_sha256(self) -> str:
        return self.payload_sha256["kg_edges"]

    @property
    def puzzles_sha256(self) -> str:
        return self.payload_sha256["kg_puzzles"]

    @property
    def contexto_profile_sha256(self) -> str:
        return self.payload_sha256["contexto_profile"]


CURRENT_CONTENT = CurrentContentSnapshot(
    build_version='fixture-v1-2-reviewed-content',
    artifact_sha256=_frozen({
        'cat_de_roman_esti/fixtures/kg_sample.json': (
            'c9f23c4a9dab1281ad91baaf0e2c836a5b7ab9a6d5f2776799908d76e10f4b85'
        ),
        'cat_de_roman_esti/fixtures/games_pack.json': (
            'e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8'
        ),
        'cat_de_roman_esti/fixtures/board_rankings_v37.json': (
            '96409c88927a60e9d6d379237af88a57aef6b40279520bf54f64214017b45806'
        ),
        'cat_de_roman_esti/fixtures/derived_catalog_v38.json': (
            '1340147300b3d9d174e09d899ac8eaf91756ca0470d0550121af66751ea92d71'
        ),
        'cat_de_roman_esti/fixtures/quick_games_v92.json': (
            'cc242a902fd4c040f0e52da94ec95683a9bbcdab41f4b9fb72de5a9c5ff5659c'
        ),
        'tests/fixtures/cat_mobile_app_pack_contract.json': (
            '8735d304a7d9734a53c03307c034093c910c1a931e73c40df346ed25700f1438'
        ),
    }),
    payload_sha256=_frozen({
        'ranking_rows': '5848733fa5d59d3ddf7b84c968c1647fcbcc78664b018039b920f2d348d2ac41',
        'frozen_derived_boards': '993e4e04834d2ab446ec28dd593177e071b11b881e49f941f677e0eaf66d01d4',
        'kg_nodes_without_aliases': (
            'a8c082b2c8bfc5ab8085831ffaf002d879363fe514918da9b7bb1d88017cff36'
        ),
        'kg_edges': 'a2c5cb088b941f929785b23c0778fe6b3910f68c8af05431d0f643505c8dd6ac',
        'kg_puzzles': '3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc',
        'contexto_profile': '9a9f3a940e3ffeaf938308a58a2786822327f3e0fdcd26188fc921041b13a3a3',
        'alchimie_closure_profile': (
            'e3b695dcd41ce465cfb46274217441bc0dfd10f19dde0bf9d64d94d603c5289e'
        ),
        'mobile_content': 'c8f9c6fc4f9d2ff7e1221f10ef17f2cbcc7194206d773fae8cebc583e6c74c51',
    }),
    kg_counts=_frozen({
        'nodes': 2416,
        'edges': 9459,
        'aliases': 8663,
        'puzzles': 180,
    }),
    mobile_counts=_frozen({
        'nodes': 2416,
        'edges': 9459,
        'puzzles': 180,
    }),
    pack_counts=_frozen({
        'conexiuni': 245,
        'contexto': 265,
        'lant': 123,
        'alchimie': 83,
    }),
    pack_id_high_water=_frozen({
        'conexiuni': 374,
        'contexto': 377,
        'lant': 246,
        'alchimie': 107,
    }),
    status_counts=_frozen({
        'approved': 709,
        'pending': 7,
    }),
    game_inventory=_frozen({
        'conexiuni': (245, 245, 0),
        'contexto': (265, 263, 2),
        'lant': (123, 121, 2),
        'alchimie': (83, 80, 3),
    }),
    ranking_counts=_frozen({
        'total': 716,
        'approved': 709,
        'pilot_eligible': 527,
        'by_game': _frozen({
            'conexiuni': 245,
            'contexto': 265,
            'lant': 123,
            'alchimie': 83,
        }),
        'eligible_by_game': _frozen({
            'conexiuni': 83,
            'contexto': 255,
            'lant': 121,
            'alchimie': 68,
        }),
    }),
    derived_counts=_frozen(
        {
            "total": 336,
            "by_game": _frozen({"intrusul": 183, "perechi": 153}),
            "sources_by_game": _frozen({"intrusul": 66, "perechi": 51}),
            "starter_by_game": _frozen({"intrusul": 24, "perechi": 26}),
        }
    ),
    quick_counts=_frozen({
        "total": 421,
        "by_game": _frozen({"intrusul": 228, "perechi": 193}),
        "authored_by_game": _frozen({"intrusul": 45, "perechi": 40}),
        "starter_by_game": _frozen({"intrusul": 62, "perechi": 61}),
    }),
    quick_selectable_counts=_frozen({
        "total": 418,
        "by_game": _frozen({"intrusul": 226, "perechi": 192}),
        "preferred_by_game": _frozen({"intrusul": 188, "perechi": 153}),
    }),
    feedback_observations=_frozen({
        'food_responsive': 2306,
        'food_direct_projections': 17,
        'family_member_rank': 2127,
    }),
    clatite_opener_ranks=_frozen(
        {"făină": 2, "ou": 7, "gem": 10, "dulceață": 9,
         "lapte": 34, "brânză": 41, "smântână": 28}
    ),
    contexto_approved=263,
    contexto_eligible=255,
    contexto_id_high_water=377,
    projection_terms=464,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
