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
    build_version='fixture-v1-3-everyday-concepts',
    artifact_sha256=_frozen({
        'cat_de_roman_esti/fixtures/kg_sample.json': (
            'd035f616b4aef5077d77d9cbbdefbd74c1ce2b360a1874a0533a0bd43bb04f63'
        ),
        'cat_de_roman_esti/fixtures/games_pack.json': (
            'e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8'
        ),
        'cat_de_roman_esti/fixtures/board_rankings_v37.json': (
            'e24954508573a06c885be3163b3e25c011a14809a7b358cb0aad004dad9a8f2b'
        ),
        'cat_de_roman_esti/fixtures/derived_catalog_v38.json': (
            'b4ae19266627b738ebe29928acc5952da9be98415fb8632870243e8634a32ad9'
        ),
        'cat_de_roman_esti/fixtures/quick_games_v92.json': (
            '99db98d64b5b7c103ee70eab2b2b79b04d4ff62072942a159caa65518375ed9f'
        ),
        'tests/fixtures/cat_mobile_app_pack_contract.json': (
            'f5ebc91f3cefb2fdc9755ea015d1eae9e58a2edf722621f273e73ef937d82e94'
        ),
    }),
    payload_sha256=_frozen({
        'ranking_rows': '4c86e3531b6199b87d2672db01d44123cd6d11fe56e0a33e78eaec8f3f3201e0',
        'frozen_derived_boards': '993e4e04834d2ab446ec28dd593177e071b11b881e49f941f677e0eaf66d01d4',
        'kg_nodes_without_aliases': (
            'a81a780ffba72bb77400d52f83d3de80115364c3708d465513e2efe103b59c4e'
        ),
        'kg_edges': '38e78e4dea242d7b319d31b55158d90fb827570c66023ba5f24eaba09aa492a7',
        'kg_puzzles': '3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc',
        'contexto_profile': 'b34856651cdc5205cba1a57407a13dc0e95a0bd844ef82b3eca81ec703e37313',
        'alchimie_closure_profile': (
            'e3b695dcd41ce465cfb46274217441bc0dfd10f19dde0bf9d64d94d603c5289e'
        ),
        # Public projection and full fixture/API hashes bind distinct contracts.
        'mobile_content': 'a00fb1308f215ea8e554df5fb3f60e7d12a2031c075280099454fb7299d48db9',
        'fixture_content': 'c48dc37f32c8a08495e24a4b0b6ac773c7027dc102f4be236881c8425e7b1b42',
    }),
    kg_counts=_frozen({
        'nodes': 2419,
        'edges': 9471,
        'aliases': 8675,
        'puzzles': 180,
    }),
    mobile_counts=_frozen({
        'nodes': 2419,
        'edges': 9471,
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
        'food_responsive': 2309,
        'food_direct_projections': 17,
        'family_member_rank': 2130,
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
