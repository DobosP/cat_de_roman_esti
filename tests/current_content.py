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
    build_version="fixture-v84-six-game-graph-quality",
    artifact_sha256=_frozen(
        {
            "cat_de_roman_esti/fixtures/kg_sample.json": (
                "3fb0f97c5b4c813eb72d8fd3589c4ce92f724d0565db840c1bc3909458a60ab0"
            ),
            "cat_de_roman_esti/fixtures/games_pack.json": (
                "c843705d565770d6916567be8b7c627c16bfdcf9dd8368e6a333f0f222484b57"
            ),
            "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
                "67a7a3274f24485d45ab75191a9701482c0959be4029e29e47c7c576360a6075"
            ),
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
                "579128d90d34a57a093202e54babe76b1ceb6840a36e332c9ecc540a8fb5251a"
            ),
            "tests/fixtures/cat_mobile_app_pack_contract.json": (
                "43e18a0b84b81196573bca0c5643c117def93535c38fa67b52adf5da63fd3166"
            ),
        }
    ),
    payload_sha256=_frozen(
        {
            "ranking_rows": (
                "bc8b055086548c7ed69712a3c8804c76175e44cb74e0562f3047b15d1fac5d23"
            ),
            "frozen_derived_boards": (
                "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
            ),
            "kg_nodes_without_aliases": (
                "ae230c3696da3f8823339cfd07b88fc6fe037a0c8377bb1ad0b4e7a77237a33a"
            ),
            "kg_edges": (
                "aac243f6d75566598f321f5622ba0b0d39662cacdc8e30c7df3d53b990ee12e8"
            ),
            "kg_puzzles": (
                "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
            ),
            "contexto_profile": (
                "9e56ca1f7e2e647b7695b4e1931fea644076f8e3a26aa0abf633b709cd38769c"
            ),
            "alchimie_closure_profile": (
                "94eccce7dd6c9555afcc64566c5e5b82368fbfe746c1298f53a3e62681b27b32"
            ),
            "mobile_content": (
                "10984193d18dd817029c5972fe84e39bb490c4ef819399408cd54c299c67ed00"
            ),
        }
    ),
    kg_counts=_frozen({"nodes": 2380, "edges": 9279, "aliases": 8517, "puzzles": 180}),
    mobile_counts=_frozen({"nodes": 2380, "edges": 9279, "puzzles": 180}),
    pack_counts=_frozen({"conexiuni": 232, "contexto": 226, "lant": 98, "alchimie": 82}),
    pack_id_high_water=_frozen(
        {"conexiuni": 361, "contexto": 336, "lant": 220, "alchimie": 106}
    ),
    status_counts=_frozen({"approved": 630, "pending": 8}),
    game_inventory=_frozen(
        {
            "conexiuni": (232, 232, 0),
            "contexto": (226, 224, 2),
            "lant": (98, 95, 3),
            "alchimie": (82, 79, 3),
        }
    ),
    ranking_counts=_frozen(
        {
            "total": 638,
            "approved": 630,
            "pilot_eligible": 468,
            "by_game": _frozen(
                {"conexiuni": 232, "contexto": 226, "lant": 98, "alchimie": 82}
            ),
            "eligible_by_game": _frozen(
                {"conexiuni": 74, "contexto": 220, "lant": 95, "alchimie": 79}
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
    contexto_approved=224,
    contexto_eligible=220,
    contexto_id_high_water=336,
    projection_terms=471,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
