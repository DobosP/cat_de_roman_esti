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
    build_version="fixture-v86-preparation-and-route-quality",
    artifact_sha256=_frozen(
        {
            "cat_de_roman_esti/fixtures/kg_sample.json": (
                "b612eda1fb8712fb57f1e16ca2a4fed3e5f6cec847c977ab45ee420c575ffa1a"
            ),
            "cat_de_roman_esti/fixtures/games_pack.json": (
                "b9c8771294abbb2242ca006f64b8bb8dd5e4ae175345383c608c53455015b25d"
            ),
            "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
                "7e46c05207ef102aa7ff877d019235dede5d5e78c0afb19bd005fa413bd384cf"
            ),
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
                "55cfcd131f91e5f712c4fcf6b6324a167d0aaca24b59301b86c79a1462d7f68e"
            ),
            "tests/fixtures/cat_mobile_app_pack_contract.json": (
                "2222e09de934f8428bd90c5857b49d514587bf5fa2c44ecd4c3c0cec0cf09e3c"
            ),
        }
    ),
    payload_sha256=_frozen(
        {
            "ranking_rows": (
                "a0e3dd4a7a2146fab253ea640c9f5e0f84074611f8681a6f06a7287621f1ef9d"
            ),
            "frozen_derived_boards": (
                "1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db"
            ),
            "kg_nodes_without_aliases": (
                "895441ecc3bff2196a96af2d3c9c780e62bf6e799f5fc9aa7fa84359a749ac22"
            ),
            "kg_edges": (
                "8a686cc80c40b95f03df33bbe74047b921a243f67fae20c3a55ba9896f47dd63"
            ),
            "kg_puzzles": (
                "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
            ),
            "contexto_profile": (
                "fc141f40dfb5d26ad9986b028ef27ab6b6a8fe4bbada0accdebefda49f2b3353"
            ),
            "alchimie_closure_profile": (
                "94eccce7dd6c9555afcc64566c5e5b82368fbfe746c1298f53a3e62681b27b32"
            ),
            "mobile_content": (
                "bd2ccd079148398fc7732f9ade2ca6e0259d1613d3a7e5a8f97c791f746e9c82"
            ),
        }
    ),
    kg_counts=_frozen({"nodes": 2397, "edges": 9360, "aliases": 8572, "puzzles": 180}),
    mobile_counts=_frozen({"nodes": 2397, "edges": 9360, "puzzles": 180}),
    pack_counts=_frozen({"conexiuni": 232, "contexto": 235, "lant": 100, "alchimie": 82}),
    pack_id_high_water=_frozen(
        {"conexiuni": 361, "contexto": 345, "lant": 222, "alchimie": 106}
    ),
    status_counts=_frozen({"approved": 641, "pending": 8}),
    game_inventory=_frozen(
        {
            "conexiuni": (232, 232, 0),
            "contexto": (235, 233, 2),
            "lant": (100, 97, 3),
            "alchimie": (82, 79, 3),
        }
    ),
    ranking_counts=_frozen(
        {
            "total": 649,
            "approved": 641,
            "pilot_eligible": 479,
            "by_game": _frozen(
                {"conexiuni": 232, "contexto": 235, "lant": 100, "alchimie": 82}
            ),
            "eligible_by_game": _frozen(
                {"conexiuni": 74, "contexto": 229, "lant": 97, "alchimie": 79}
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
            "food_responsive": 2292,
            "food_direct_projections": 17,
            "family_member_rank": 2112,
        }
    ),
    clatite_opener_ranks=_frozen(
        {"făină": 2, "ou": 7, "gem": 10, "dulceață": 9,
         "lapte": 57, "brânză": 39, "smântână": 28}
    ),
    contexto_approved=233,
    contexto_eligible=229,
    contexto_id_high_water=345,
    projection_terms=468,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
