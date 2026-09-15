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
    build_version='fixture-v90-household-discovery',
    artifact_sha256=_frozen({
        'cat_de_roman_esti/fixtures/kg_sample.json': (
            'd4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109'
        ),
        'cat_de_roman_esti/fixtures/games_pack.json': (
            '573e921cbe54cb482535584a22e55183c4b7add9b0a9a92a1400f9dae4fd01d8'
        ),
        'cat_de_roman_esti/fixtures/board_rankings_v37.json': (
            '5e29e48a7d684d23d5532f38d80fb996c92d3474744b20a0159111ac7b41bc76'
        ),
        'cat_de_roman_esti/fixtures/derived_catalog_v38.json': (
            '46360ac6a77fff6cdab2f86500dcadc348243f71bab71eea01111e76bf80f2c4'
        ),
        'cat_de_roman_esti/fixtures/quick_games_v92.json': (
            '04622c7dc0e7d38f68d949c03be349f716a99222d344eb60db6b96d560a6dc21'
        ),
        'tests/fixtures/cat_mobile_app_pack_contract.json': (
            '5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f'
        ),
    }),
    payload_sha256=_frozen({
        'ranking_rows': '148129a618c114cf265481173c165405f75aa031a2f22e239d933c5e5e80a4c2',
        'frozen_derived_boards': '1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db',
        'kg_nodes_without_aliases': (
            '413ef622714003dfb7c0b4ff90a84d7c3f943ede2d62aee934385ed12eadd8c0'
        ),
        'kg_edges': '30d453ff93590332de7a10fa84f4dd3b614e54245ddfbbc1b3002e2e0e6af795',
        'kg_puzzles': '3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc',
        'contexto_profile': 'b1abe04b91fcdf031368660c81d78cdde63bc5634bae82b5efe99bc2c984858e',
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
        'conexiuni': 241,
        'contexto': 259,
        'lant': 118,
        'alchimie': 83,
    }),
    pack_id_high_water=_frozen({
        'conexiuni': 370,
        'contexto': 371,
        'lant': 240,
        'alchimie': 107,
    }),
    status_counts=_frozen({
        'approved': 693,
        'pending': 8,
    }),
    game_inventory=_frozen({
        'conexiuni': (241, 241, 0),
        'contexto': (259, 257, 2),
        'lant': (118, 115, 3),
        'alchimie': (83, 80, 3),
    }),
    ranking_counts=_frozen({
        'total': 701,
        'approved': 693,
        'pilot_eligible': 531,
        'by_game': _frozen({
            'conexiuni': 241,
            'contexto': 259,
            'lant': 118,
            'alchimie': 83,
        }),
        'eligible_by_game': _frozen({
            'conexiuni': 83,
            'contexto': 253,
            'lant': 115,
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
    quick_counts=_frozen({
        "total": 401,
        "by_game": _frozen({"intrusul": 218, "perechi": 183}),
        "authored_by_game": _frozen({"intrusul": 35, "perechi": 30}),
        "starter_by_game": _frozen({"intrusul": 53, "perechi": 51}),
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
    contexto_approved=257,
    contexto_eligible=253,
    contexto_id_high_water=371,
    projection_terms=464,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
