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
    build_version='fixture-v90-household-discovery',
    artifact_sha256=_frozen({
        'cat_de_roman_esti/fixtures/kg_sample.json': (
            'd4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109'
        ),
        'cat_de_roman_esti/fixtures/games_pack.json': (
            'e32139529aacc88e2f453ac1cee1d8cd9a2cd1b16f3ee0551a5a76779192391e'
        ),
        'cat_de_roman_esti/fixtures/board_rankings_v37.json': (
            'b5beb978b911c952ef2632cb2d93bc695be19f226b4a4661d77e26b335413fab'
        ),
        'cat_de_roman_esti/fixtures/derived_catalog_v38.json': (
            '6ac090bc2186bf00209913d1123ba3f54de9f7b02f9fa2a781f2dfcccbbf58a9'
        ),
        'tests/fixtures/cat_mobile_app_pack_contract.json': (
            '5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f'
        ),
    }),
    payload_sha256=_frozen({
        'ranking_rows': 'bf321fe40377f02f0ed5cb107c303eb87fac9428f7296549a55c8659acc3ba08',
        'frozen_derived_boards': '1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db',
        'kg_nodes_without_aliases': (
            '413ef622714003dfb7c0b4ff90a84d7c3f943ede2d62aee934385ed12eadd8c0'
        ),
        'kg_edges': '30d453ff93590332de7a10fa84f4dd3b614e54245ddfbbc1b3002e2e0e6af795',
        'kg_puzzles': '3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc',
        'contexto_profile': '656db0f943a12bd9440e8f9bef7a788c9318bd07933e5d18c0b87198f64e5b65',
        'alchimie_closure_profile': (
            '94eccce7dd6c9555afcc64566c5e5b82368fbfe746c1298f53a3e62681b27b32'
        ),
        'mobile_content': '83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3',
    }),
    kg_counts=_frozen({
        'nodes': 2416,
        'edges': 9459,
        'aliases': 8641,
        'puzzles': 180,
    }),
    mobile_counts=_frozen({
        'nodes': 2416,
        'edges': 9459,
        'puzzles': 180,
    }),
    pack_counts=_frozen({
        'conexiuni': 234,
        'contexto': 244,
        'lant': 100,
        'alchimie': 83,
    }),
    pack_id_high_water=_frozen({
        'conexiuni': 363,
        'contexto': 356,
        'lant': 222,
        'alchimie': 107,
    }),
    status_counts=_frozen({
        'approved': 653,
        'pending': 8,
    }),
    game_inventory=_frozen({
        'conexiuni': (234, 234, 0),
        'contexto': (244, 242, 2),
        'lant': (100, 97, 3),
        'alchimie': (83, 80, 3),
    }),
    ranking_counts=_frozen({
        'total': 661,
        'approved': 653,
        'pilot_eligible': 491,
        'by_game': _frozen({
            'conexiuni': 234,
            'contexto': 244,
            'lant': 100,
            'alchimie': 83,
        }),
        'eligible_by_game': _frozen({
            'conexiuni': 76,
            'contexto': 238,
            'lant': 97,
            'alchimie': 80,
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
    feedback_observations=_frozen({
        'food_responsive': 2306,
        'food_direct_projections': 17,
        'family_member_rank': 2127,
    }),
    clatite_opener_ranks=_frozen(
        {"făină": 2, "ou": 7, "gem": 10, "dulceață": 9,
         "lapte": 34, "brânză": 41, "smântână": 28}
    ),
    contexto_approved=242,
    contexto_eligible=238,
    contexto_id_high_water=356,
    projection_terms=464,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
