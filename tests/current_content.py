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
            '02b966eacaa851a9b20c4f36e0ee50c217e49670553da462313b16830b2c13e6'
        ),
        'cat_de_roman_esti/fixtures/board_rankings_v37.json': (
            'e467823999d6b20bd0abeb6a41ceb239faaf7c600afe7d9df3adfc65daad3b12'
        ),
        'cat_de_roman_esti/fixtures/derived_catalog_v38.json': (
            'de2f46a72c23e5ecbd496d3a4314a48f0d4f636b71aa5ba4662bccc837298449'
        ),
        'cat_de_roman_esti/fixtures/quick_games_v92.json': (
            '9fdcd45bca05d94077465c300851d18bcc487a7b82af3b69863e3d57534766ad'
        ),
        'tests/fixtures/cat_mobile_app_pack_contract.json': (
            '5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f'
        ),
    }),
    payload_sha256=_frozen({
        'ranking_rows': 'f09de1c28aa39bf2488d79c789edd5e5d9a25faf953ac3084015ce74488876e3',
        'frozen_derived_boards': '1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db',
        'kg_nodes_without_aliases': (
            '413ef622714003dfb7c0b4ff90a84d7c3f943ede2d62aee934385ed12eadd8c0'
        ),
        'kg_edges': '30d453ff93590332de7a10fa84f4dd3b614e54245ddfbbc1b3002e2e0e6af795',
        'kg_puzzles': '3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc',
        'contexto_profile': '0a6f6a585ffc635e66982b74873cb64157c28d2a9d10baa006d15e6457dae881',
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
        'conexiuni': 240,
        'contexto': 257,
        'lant': 116,
        'alchimie': 83,
    }),
    pack_id_high_water=_frozen({
        'conexiuni': 369,
        'contexto': 369,
        'lant': 238,
        'alchimie': 107,
    }),
    status_counts=_frozen({
        'approved': 688,
        'pending': 8,
    }),
    game_inventory=_frozen({
        'conexiuni': (240, 240, 0),
        'contexto': (257, 255, 2),
        'lant': (116, 113, 3),
        'alchimie': (83, 80, 3),
    }),
    ranking_counts=_frozen({
        'total': 696,
        'approved': 688,
        'pilot_eligible': 526,
        'by_game': _frozen({
            'conexiuni': 240,
            'contexto': 257,
            'lant': 116,
            'alchimie': 83,
        }),
        'eligible_by_game': _frozen({
            'conexiuni': 82,
            'contexto': 251,
            'lant': 113,
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
        "total": 393,
        "by_game": _frozen({"intrusul": 214, "perechi": 179}),
        "authored_by_game": _frozen({"intrusul": 31, "perechi": 26}),
        "starter_by_game": _frozen({"intrusul": 49, "perechi": 47}),
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
    contexto_approved=255,
    contexto_eligible=251,
    contexto_id_high_water=369,
    projection_terms=464,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
