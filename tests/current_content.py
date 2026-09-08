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
    build_version="fixture-v87-snack-and-action-quality",
    artifact_sha256=_frozen(
        {
            "cat_de_roman_esti/fixtures/kg_sample.json": (
                "96d50f8b724b9d1d1ff5d02b5a9a206445d7d9edead778d6db173f00ac094bfa"
            ),
            "cat_de_roman_esti/fixtures/games_pack.json": (
                "536036f6d030be4e8750fb104325b67a9363535506d453ef8a0e0a824a3b63ab"
            ),
            "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
                "53defb36ab442aee1135ae3dd0522559abe27234048f9accdfbd5c9fe75eccc3"
            ),
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
                "f4e16944845311eeba231f866c5578a4f1de9ee40e08857cca575930a2bf1278"
            ),
            "tests/fixtures/cat_mobile_app_pack_contract.json": (
                "f0c346bff24fc821d56be1d41d15c7fca57c4473b637006679f712238a965ecf"
            ),
        }
    ),
    payload_sha256=_frozen(
        {
            "ranking_rows": (
                "fe9f0cea28159e428323bc15c33fdb6a1e9a05438aad53de7456022c10fba768"
            ),
            "frozen_derived_boards": (
                "1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db"
            ),
            "kg_nodes_without_aliases": (
                "b3a14076744a539fb870f6cf623c9736a5883cab70f0118827c37e363952a3ef"
            ),
            "kg_edges": (
                "15c1c2dcca5b4ac4cdfe3935cc0b45da63703cf54a32d3698aabc2366c6436e5"
            ),
            "kg_puzzles": (
                "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
            ),
            "contexto_profile": (
                "e9ee69b1cce346dcbe22feddeff7c01d99c8c1fc21cf881dc9b8f10cda2f94cc"
            ),
            "alchimie_closure_profile": (
                "94eccce7dd6c9555afcc64566c5e5b82368fbfe746c1298f53a3e62681b27b32"
            ),
            "mobile_content": (
                "7473bfe7d42189a28cf933032705b288ff2933fd8eeaf30c65a2dba3be4e79d4"
            ),
        }
    ),
    kg_counts=_frozen({"nodes": 2406, "edges": 9410, "aliases": 8603, "puzzles": 180}),
    mobile_counts=_frozen({"nodes": 2406, "edges": 9410, "puzzles": 180}),
    pack_counts=_frozen({"conexiuni": 232, "contexto": 241, "lant": 100, "alchimie": 82}),
    pack_id_high_water=_frozen(
        {"conexiuni": 361, "contexto": 351, "lant": 222, "alchimie": 106}
    ),
    status_counts=_frozen({"approved": 647, "pending": 8}),
    game_inventory=_frozen(
        {
            "conexiuni": (232, 232, 0),
            "contexto": (241, 239, 2),
            "lant": (100, 97, 3),
            "alchimie": (82, 79, 3),
        }
    ),
    ranking_counts=_frozen(
        {
            "total": 655,
            "approved": 647,
            "pilot_eligible": 485,
            "by_game": _frozen(
                {"conexiuni": 232, "contexto": 241, "lant": 100, "alchimie": 82}
            ),
            "eligible_by_game": _frozen(
                {"conexiuni": 74, "contexto": 235, "lant": 97, "alchimie": 79}
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
            "food_responsive": 2301,
            "food_direct_projections": 17,
            "family_member_rank": 2119,
        }
    ),
    clatite_opener_ranks=_frozen(
        {"făină": 2, "ou": 7, "gem": 10, "dulceață": 9,
         "lapte": 34, "brânză": 41, "smântână": 28}
    ),
    contexto_approved=239,
    contexto_eligible=235,
    contexto_id_high_water=351,
    projection_terms=467,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
