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
    build_version="fixture-v83-food-input-and-feedback",
    artifact_sha256=_frozen(
        {
            "cat_de_roman_esti/fixtures/kg_sample.json": (
                "4ce12d15ec247ebcaba3e119caed91f8d2624b09fa5568a8d7ece728f76a8a5e"
            ),
            "cat_de_roman_esti/fixtures/games_pack.json": (
                "78e680f3849f9a9de2a2675cbe7349ba23c8165f415cfc89a7533121bc34399c"
            ),
            "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
                "f80397b3fc1dbfb58c9b4daf1e74fcebc43b698a5e290660333dad71a5d8dfb2"
            ),
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
                "e406f182bbc8629b05dac9f2d58b51de45113f2917b8beeb078f8ddccf2a66af"
            ),
            "tests/fixtures/cat_mobile_app_pack_contract.json": (
                "ea2fe6b05df3104f674905c971f506fdf41168c6c9760bab7b2a780fcaae93a0"
            ),
        }
    ),
    payload_sha256=_frozen(
        {
            "ranking_rows": (
                "8bfffd8c9b15294140e5af6bc91070e59a6e0d744b808062834b799b46c90048"
            ),
            "frozen_derived_boards": (
                "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
            ),
            "kg_nodes_without_aliases": (
                "b1e54aa885302131fb26b9a8740d63399196235f4c0786eb7382dfa77c05d178"
            ),
            "kg_edges": (
                "913b938c4d6206a11e07e9a13878a6ec117b1586868f44394c9626607979dc3d"
            ),
            "kg_puzzles": (
                "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
            ),
            "contexto_profile": (
                "c373e44b5e34768b73ce1772138ea5ec0a76c801a37aea1cdccbdc99425c831b"
            ),
        }
    ),
    kg_counts=_frozen({"nodes": 2365, "edges": 9223, "aliases": 8475, "puzzles": 180}),
    mobile_counts=_frozen({"nodes": 2365, "edges": 9223, "puzzles": 180}),
    pack_counts=_frozen({"conexiuni": 232, "contexto": 223, "lant": 97, "alchimie": 82}),
    status_counts=_frozen({"approved": 626, "pending": 8}),
    game_inventory=_frozen(
        {
            "conexiuni": (232, 232, 0),
            "contexto": (223, 221, 2),
            "lant": (97, 94, 3),
            "alchimie": (82, 79, 3),
        }
    ),
    ranking_counts=_frozen(
        {
            "total": 634,
            "approved": 626,
            "pilot_eligible": 464,
            "by_game": _frozen(
                {"conexiuni": 232, "contexto": 223, "lant": 97, "alchimie": 82}
            ),
            "eligible_by_game": _frozen(
                {"conexiuni": 74, "contexto": 217, "lant": 94, "alchimie": 79}
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
    contexto_approved=221,
    contexto_eligible=217,
    contexto_id_high_water=333,
    projection_terms=472,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
