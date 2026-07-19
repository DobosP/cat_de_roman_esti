"""V38 offline derivation, ranking, and artifact contracts."""

from __future__ import annotations

import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent


def _load_generator():
    path = _ROOT / "scripts" / "build_derived_catalog_v38.py"
    spec = importlib.util.spec_from_file_location("build_derived_catalog_v38", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = _load_generator()


@pytest.fixture(scope="module")
def generated() -> dict:
    return BUILD.generate_catalog()


def _competition_ranks(rows: list[dict], score_field: str) -> tuple[list[dict], list[int]]:
    ordered = sorted(rows, key=lambda row: (-row[score_field], row["id"]))
    ranks: list[int] = []
    previous_score: int | None = None
    current_rank = 0
    for position, row in enumerate(ordered, 1):
        if position == 1 or row[score_field] != previous_score:
            current_rank = position
            previous_score = row[score_field]
        ranks.append(current_rank)
    return ordered, ranks


def test_generated_catalog_is_exact_complete_and_byte_identical(generated: dict) -> None:
    expected = BUILD.render_catalog(generated)
    assert BUILD.PACKAGE_CATALOG.read_bytes() == expected
    assert BUILD.TEST_CATALOG.read_bytes() == expected
    assert generated["meta"]["counts"] == {
        "total": 336,
        "by_game": {"intrusul": 183, "perechi": 153},
        "sources_by_game": {"intrusul": 66, "perechi": 51},
        "starter_by_game": {"intrusul": 24, "perechi": 26},
    }
    assert tuple(generated["meta"]) == BUILD.META_FIELDS
    assert tuple(generated["meta"]["counts"]) == BUILD.COUNT_FIELDS
    assert all(tuple(row) == BUILD.BOARD_FIELDS for row in generated["boards"])


def test_catalog_is_bound_to_every_reviewed_input(generated: dict) -> None:
    meta = generated["meta"]
    assert meta["schema_version"] == BUILD.SCHEMA_VERSION
    assert meta["formula_version"] == BUILD.FORMULA_VERSION
    assert meta["pack_sha256"] == BUILD.normalized_text_sha256(BUILD.DEFAULT_PACK)
    assert meta["kg_sha256"] == BUILD.normalized_text_sha256(
        BUILD.critique_pack.PACKAGE_KG
    )
    assert meta["rubric_sha256"] == BUILD.normalized_text_sha256(
        BUILD.critique_pack.RUBRIC_PATH
    )
    assert meta["v37_rankings_sha256"] == BUILD.normalized_text_sha256(
        BUILD.DEFAULT_RANKINGS
    )


def test_scores_ranks_and_source_caps_recompute_exactly(generated: dict) -> None:
    rows = generated["boards"]
    assert len({row["id"] for row in rows}) == len(rows)
    per_source = Counter((row["game"], row["source_id"]) for row in rows)
    assert max(per_source.values()) == BUILD.MAX_VARIANTS_PER_SOURCE
    assert all(count <= BUILD.MAX_VARIANTS_PER_SOURCE for count in per_source.values())
    for row in rows:
        familiarity = row["romanian_familiarity"]
        quality = row["play_quality"]
        assert row["standard_score"] == BUILD._bounded_score(
            0.60 * familiarity + 0.40 * quality
        )
        assert row["starter_score"] == BUILD._bounded_score(
            0.75 * familiarity + 0.25 * quality
        )
        assert row["id"] == BUILD._candidate_id(
            row["game"], row["source_id"], row["payload"]
        )
    for game in BUILD.DERIVED_GAMES:
        game_rows = [row for row in rows if row["game"] == game]
        standard, standard_ranks = _competition_ranks(game_rows, "standard_score")
        assert [row["standard_rank"] for row in standard] == standard_ranks
        starter, starter_ranks = _competition_ranks(
            [row for row in game_rows if row["starter_eligible"]], "starter_score"
        )
        assert [row["starter_rank"] for row in starter] == starter_ranks
        assert all(
            row["starter_rank"] is None
            for row in game_rows
            if not row["starter_eligible"]
        )


def test_equal_scores_share_semantic_competition_rank(generated: dict) -> None:
    rows = generated["boards"]
    for game in BUILD.DERIVED_GAMES:
        game_rows = [row for row in rows if row["game"] == game]
        for score_field, rank_field, eligible_only in (
            ("standard_score", "standard_rank", False),
            ("starter_score", "starter_rank", True),
        ):
            ranked = [
                row
                for row in game_rows
                if not eligible_only or row["starter_eligible"]
            ]
            score_groups = {
                score: [row for row in ranked if row[score_field] == score]
                for score in {row[score_field] for row in ranked}
            }
            tied_groups = [group for group in score_groups.values() if len(group) > 1]
            assert tied_groups
            for group in tied_groups:
                assert len({row[rank_field] for row in group}) == 1
                score = group[0][score_field]
                expected = 1 + sum(row[score_field] > score for row in ranked)
                assert group[0][rank_field] == expected


def test_selected_intrusul_rows_recompute_strict_semantic_gate(generated: dict) -> None:
    pack, svc, _, _ = BUILD.critique_pack.load_all(
        BUILD.critique_pack.PACKAGE_PACK,
        BUILD.critique_pack.PACKAGE_KG,
    )
    kg = json.loads(BUILD.critique_pack.PACKAGE_KG.read_text(encoding="utf-8"))
    strengths, linked = BUILD._edge_maps(kg)
    sources = {rec["id"]: rec for rec in pack["conexiuni"]}
    for row in (row for row in generated["boards"] if row["game"] == "intrusul"):
        source = sources[row["source_id"]]
        members = row["payload"]["members"]
        intruder = row["payload"]["intruder"]
        assert len({svc.node(node_id).node_type for node_id in [*members, intruder]}) == 1
        intended = [
            BUILD._strength(strengths, left, right)
            for left, right in itertools.combinations(members, 2)
        ]
        assert sum(value >= BUILD.STRONG_EDGE for value in intended) >= 2
        assert all(intruder not in linked.get(member, set()) for member in members)
        matching = [
            key for key, nodes in source["groups"].items() if set(members) <= set(nodes)
        ]
        assert len(matching) == 1
        assert intruder not in source["groups"][matching[0]]
        saliences = [float(svc.node(node_id).salience) for node_id in [*members, intruder]]
        assert row["starter_eligible"] is (
            min(saliences) >= BUILD.STARTER_SALIENCE
            and min(intended) >= BUILD.STARTER_EDGE
        )


def test_selected_perechi_rows_recompute_unique_matching_gate(generated: dict) -> None:
    pack, svc, _, _ = BUILD.critique_pack.load_all(
        BUILD.critique_pack.PACKAGE_PACK,
        BUILD.critique_pack.PACKAGE_KG,
    )
    kg = json.loads(BUILD.critique_pack.PACKAGE_KG.read_text(encoding="utf-8"))
    strengths, _ = BUILD._edge_maps(kg)
    sources = {rec["id"]: rec for rec in pack["conexiuni"]}
    for row in (row for row in generated["boards"] if row["game"] == "perechi"):
        source = sources[row["source_id"]]
        pairs = [pair["members"] for pair in row["payload"]["pairs"]]
        visible = [node_id for pair in pairs for node_id in pair]
        assert len(visible) == len(set(visible)) == 8
        intended_sets = {frozenset(pair) for pair in pairs}
        intended = [BUILD._strength(strengths, *pair) for pair in pairs]
        cross = [
            BUILD._strength(strengths, left, right)
            for left, right in itertools.combinations(visible, 2)
            if frozenset((left, right)) not in intended_sets
        ]
        assert min(intended) >= BUILD.STRONG_EDGE
        assert max(cross, default=0.0) < BUILD.STRONG_EDGE
        matched_groups = [
            next(
                key
                for key, nodes in source["groups"].items()
                if set(pair) <= set(nodes)
            )
            for pair in pairs
        ]
        assert len(set(matched_groups)) == 4
        saliences = [float(svc.node(node_id).salience) for node_id in visible]
        assert row["starter_eligible"] is (
            min(saliences) >= BUILD.STARTER_SALIENCE
            and min(intended) >= BUILD.STARTER_EDGE
            and max(cross, default=0.0) == 0.0
        )


def test_read_only_checker_is_green(capsys) -> None:
    assert BUILD.main(["build_derived_catalog_v38.py"]) == 0
    output = capsys.readouterr().out
    assert "336 boards (183 intrusul / 153 perechi)" in output
    assert output.rstrip().endswith("derived catalog GREEN")
