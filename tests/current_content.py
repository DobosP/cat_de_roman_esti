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
    build_version="fixture-v88-cross-game-quality",
    artifact_sha256=_frozen(
        {
            "cat_de_roman_esti/fixtures/kg_sample.json": (
                "2964951e3f68be7b49abb7f727b97d700a42d7e3527b117ef8b6c2830103f9fc"
            ),
            "cat_de_roman_esti/fixtures/games_pack.json": (
                "4c7030bd86e966162f4ac51ef00cf3bb649ff7a9d59c8c34e180cb7ff53e1636"
            ),
            "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
                "b19a53983a1b4555c700f717033bb61b66aea9ea2dce643a7df0cf1a31e2c764"
            ),
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
                "1c1613cd4f1e59c2b8d68ded9b071b1f812198f50aca528a3785fef34fad90b8"
            ),
            "tests/fixtures/cat_mobile_app_pack_contract.json": (
                "d2fbb9f550a05b6b128431ee55787b2b156846887f0bc8ce1908f09e6683b951"
            ),
        }
    ),
    payload_sha256=_frozen(
        {
            "ranking_rows": (
                "b80be93f072ab75158902092a6bd1e49afdaf1be2018e5d2b8632dde70ca29d6"
            ),
            "frozen_derived_boards": (
                "1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db"
            ),
            "kg_nodes_without_aliases": (
                "9d051fdfdb3598b6bac04cca2667affdc4ab597640a228a69da28c7f721984d0"
            ),
            "kg_edges": (
                "d79b787d2e2b3a7d9cb32de5f9b9fd77b48f6adc434d3d9e901e12d69459d9ba"
            ),
            "kg_puzzles": (
                "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
            ),
            "contexto_profile": (
                "82cb55b827cee27819c19a7dfd205c92ebf32717f0de5de4acfe32605948acdf"
            ),
            "alchimie_closure_profile": (
                "94eccce7dd6c9555afcc64566c5e5b82368fbfe746c1298f53a3e62681b27b32"
            ),
            "mobile_content": (
                "f8f5c13f2cb302338f35adf38e311906856d24cb04f58592c77783a519a61fd3"
            ),
        }
    ),
    kg_counts=_frozen({"nodes": 2413, "edges": 9442, "aliases": 8631, "puzzles": 180}),
    mobile_counts=_frozen({"nodes": 2413, "edges": 9442, "puzzles": 180}),
    pack_counts=_frozen({"conexiuni": 234, "contexto": 241, "lant": 100, "alchimie": 83}),
    pack_id_high_water=_frozen(
        {"conexiuni": 363, "contexto": 351, "lant": 222, "alchimie": 107}
    ),
    status_counts=_frozen({"approved": 650, "pending": 8}),
    game_inventory=_frozen(
        {
            "conexiuni": (234, 234, 0),
            "contexto": (241, 239, 2),
            "lant": (100, 97, 3),
            "alchimie": (83, 80, 3),
        }
    ),
    ranking_counts=_frozen(
        {
            "total": 658,
            "approved": 650,
            "pilot_eligible": 488,
            "by_game": _frozen(
                {"conexiuni": 234, "contexto": 241, "lant": 100, "alchimie": 83}
            ),
            "eligible_by_game": _frozen(
                {"conexiuni": 76, "contexto": 235, "lant": 97, "alchimie": 80}
            ),
        }
    ),
    derived_counts=_frozen(
        {
            "total": 336,
            "by_game": _frozen({"intrusul": 183, "perechi": 153}),
            "sources_by_game": _frozen({"intrusul": 66, "perechi": 51}),
            "starter_by_game": _frozen({"intrusul": 24, "perechi": 26}),
        }
    ),
    feedback_observations=_frozen(
        {
            "food_responsive": 2306,
            "food_direct_projections": 17,
            "family_member_rank": 2126,
        }
    ),
    clatite_opener_ranks=_frozen(
        {"făină": 2, "ou": 7, "gem": 10, "dulceață": 9,
         "lapte": 34, "brânză": 41, "smântână": 28}
    ),
    contexto_approved=239,
    contexto_eligible=235,
    contexto_id_high_water=351,
    projection_terms=465,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
