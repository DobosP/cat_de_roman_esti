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
    build_version="fixture-v85-ingredient-feedback-and-board-clarity",
    artifact_sha256=_frozen(
        {
            "cat_de_roman_esti/fixtures/kg_sample.json": (
                "b7d28b990d37164d8e41a93965a5824162ded56b2907ac03388fee717eb144b2"
            ),
            "cat_de_roman_esti/fixtures/games_pack.json": (
                "835937cc369918a0070a8d09a35f3982f21f74275476f061aa6c05242d270b4d"
            ),
            "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
                "21ff49faabb631e2a62cd07e15a6f1de69b7cb9ad04f900344771b7fefeeac0b"
            ),
            "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
                "66f4aebe9d64f638cfc8d48d51692b27a0f846d56e072a9a028a33b72d6e1ec7"
            ),
            "tests/fixtures/cat_mobile_app_pack_contract.json": (
                "d1f5808af8e0e5188b84ad4591891aa029e7f6e59fdb0c7cc14d7dd6775d2d09"
            ),
        }
    ),
    payload_sha256=_frozen(
        {
            "ranking_rows": (
                "f0673338b8fd00862f4e0eb933d53d0ea1e254d5d6560df1f01411629d074617"
            ),
            "frozen_derived_boards": (
                "1aa4138171644870f65ca1925f05c066f94e0dac087fd3682b5c374f225b86db"
            ),
            "kg_nodes_without_aliases": (
                "ed099e61d2369421e139a20566d387313a57f1367d65c5cb009e00765c696c6f"
            ),
            "kg_edges": (
                "e33a25235ccc2f5af771120fef9e91c59e8a082253b0e38929d7303bac118f4d"
            ),
            "kg_puzzles": (
                "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
            ),
            "contexto_profile": (
                "aaf2bb348db02403b3c278bf9640d4513d1fc54fc99fcb1663bcc3835eb92673"
            ),
            "alchimie_closure_profile": (
                "94eccce7dd6c9555afcc64566c5e5b82368fbfe746c1298f53a3e62681b27b32"
            ),
            "mobile_content": (
                "39da1d1b2ed32509d4ce6974251304454aa8d5b84976f9e475bd381626571c2c"
            ),
        }
    ),
    kg_counts=_frozen({"nodes": 2388, "edges": 9319, "aliases": 8542, "puzzles": 180}),
    mobile_counts=_frozen({"nodes": 2388, "edges": 9319, "puzzles": 180}),
    pack_counts=_frozen({"conexiuni": 232, "contexto": 230, "lant": 99, "alchimie": 82}),
    pack_id_high_water=_frozen(
        {"conexiuni": 361, "contexto": 340, "lant": 221, "alchimie": 106}
    ),
    status_counts=_frozen({"approved": 635, "pending": 8}),
    game_inventory=_frozen(
        {
            "conexiuni": (232, 232, 0),
            "contexto": (230, 228, 2),
            "lant": (99, 96, 3),
            "alchimie": (82, 79, 3),
        }
    ),
    ranking_counts=_frozen(
        {
            "total": 643,
            "approved": 635,
            "pilot_eligible": 473,
            "by_game": _frozen(
                {"conexiuni": 232, "contexto": 230, "lant": 99, "alchimie": 82}
            ),
            "eligible_by_game": _frozen(
                {"conexiuni": 74, "contexto": 224, "lant": 96, "alchimie": 79}
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
            "food_responsive": 2283,
            "food_direct_projections": 17,
            "family_member_rank": 2104,
        }
    ),
    clatite_opener_ranks=_frozen(
        {"făină": 2, "ou": 7, "gem": 10, "dulceață": 9,
         "lapte": 51, "brânză": 38, "smântână": 28}
    ),
    contexto_approved=228,
    contexto_eligible=224,
    contexto_id_high_water=340,
    projection_terms=469,
    projection_domains=26,
    legacy_feedback_proxies=71,
)
