"""V37 deterministic Romanian-familiarity and pilot board-ranking contracts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_script():
    path = _REPO_ROOT / "scripts" / "rank_games_pack.py"
    spec = importlib.util.spec_from_file_location("rank_games_pack_v37", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RANK = _load_script()


@pytest.fixture(scope="module")
def generated() -> dict:
    return RANK.generate_rankings()


def _salience(node_id: str) -> float:
    return {
        "low": 0.10,
        "mid": 0.50,
        "high": 0.90,
        "route": 0.80,
        "result": 0.75,
    }.get(node_id, 0.0)


def _node(node_id: str, salience: float | None = None) -> dict:
    node = {"id": node_id}
    if salience is not None:
        node["salience"] = salience
    return node


def test_familiarity_is_bounded_and_rewards_familiar_required_concepts() -> None:
    low_contexto = {"target": _node("low"), "strong_neighbors": [_node("low")]}
    high_contexto = {"target": _node("high"), "strong_neighbors": [_node("high")]}
    assert RANK.romanian_familiarity("contexto", high_contexto, _salience) > (
        RANK.romanian_familiarity("contexto", low_contexto, _salience)
    )

    low_groups = [
        {"members": [_node("low") for _ in range(4)]} for _ in range(4)
    ]
    anchored_groups = [
        {"members": [_node("high") for _ in range(4)]},
        *({"members": [_node("mid") for _ in range(4)]} for _ in range(3)),
    ]
    assert RANK.romanian_familiarity(
        "conexiuni", {"groups": anchored_groups}, _salience
    ) > RANK.romanian_familiarity(
        "conexiuni", {"groups": low_groups}, _salience
    )

    low_lant = {
        "start": _node("low"),
        "target": _node("low"),
        "representative_shortest_paths": [
            {"nodes": [_node("low"), _node("low-route"), _node("low")]}
        ],
    }
    high_lant = {
        "start": _node("high"),
        "target": _node("high"),
        "representative_shortest_paths": [
            {"nodes": [_node("high"), _node("route"), _node("high")]}
        ],
    }
    assert RANK.romanian_familiarity("lant", high_lant, _salience) > (
        RANK.romanian_familiarity("lant", low_lant, _salience)
    )

    low_alchimie = {
        "target": _node("low"),
        "seeds": [_node("low") for _ in range(5)],
        "minimum_action_recipe": [],
    }
    high_alchimie = {
        "target": _node("high"),
        "seeds": [_node("high") for _ in range(5)],
        "minimum_action_recipe": [
            {"results": [_node("result")]},
        ],
    }
    assert RANK.romanian_familiarity("alchimie", high_alchimie, _salience) > (
        RANK.romanian_familiarity("alchimie", low_alchimie, _salience)
    )

    for score in (
        RANK.romanian_familiarity("contexto", low_contexto, _salience),
        RANK.romanian_familiarity("contexto", high_contexto, _salience),
    ):
        assert 0 <= score <= 100


def test_game_quality_proxies_reward_clear_bounded_semantic_play() -> None:
    def empty_edge(_source: str, _target: str) -> float:
        return 0.0

    clean_conex = {
        "lint_findings": [],
        "fairness": {
            "unfair_tiles": [],
            "contested_tiles": [],
            "engine_unfair_raw": 0,
        },
        "cross_group_strong_edges": [],
    }
    tangled_conex = {
        **clean_conex,
        "lint_findings": [
            {"check": "mirrored_groups", "level": "WARN"},
            {"check": "type_coherence", "level": "WARN"},
        ],
        "fairness": {
            "unfair_tiles": ["X"],
            "contested_tiles": ["A", "B", "C", "D"],
            "engine_unfair_raw": 8,
        },
    }
    assert RANK.play_quality("conexiuni", {}, clean_conex, empty_edge) > (
        RANK.play_quality("conexiuni", {}, tangled_conex, empty_edge)
    )

    rich_contexto = {
        "lint_findings": [],
        "target": {"incoming_degree": 10},
        "reachable": 200,
        "strong_neighbors": [_node(str(i), 0.90) for i in range(5)],
    }
    thin_contexto = {
        "lint_findings": [],
        "target": {"incoming_degree": 1},
        "reachable": 30,
        "strong_neighbors": [_node("only", 0.10)],
    }
    assert RANK.play_quality("contexto", {}, rich_contexto, empty_edge) > (
        RANK.play_quality("contexto", {}, thin_contexto, empty_edge)
    )

    wide_lant = {
        "branch_profile": {
            "valid_first_hops": 3,
            "narrowest_shortest_path_layer": 3,
            "total_intermediate_shortest_path_nodes": 6,
        },
        "representative_shortest_paths": [
            {"edges": [{"strength": 0.90}, {"strength": 0.85}]},
        ],
    }
    narrow_lant = {
        "branch_profile": {
            "valid_first_hops": 1,
            "narrowest_shortest_path_layer": 1,
            "total_intermediate_shortest_path_nodes": 1,
        },
        "representative_shortest_paths": [
            {"edges": [{"strength": 0.30}, {"strength": 0.25}]},
        ],
    }
    rec_lant = {"optimal": 3}
    assert RANK.play_quality("lant", rec_lant, wide_lant, empty_edge) > (
        RANK.play_quality("lant", rec_lant, narrow_lant, empty_edge)
    )

    seeds = [_node(f"s{i}") for i in range(5)]
    balanced_alchimie = {
        "seeds": seeds,
        "craft_profile": {"opening_pairs": 3},
        "productive_openings": [{"result_count": 3} for _ in range(3)],
        "minimum_action_recipe": [
            {
                "pair": [_node("s0"), _node("s1")],
                "results": [_node("result")],
            }
        ],
    }
    empty_alchimie = {
        "seeds": seeds,
        "craft_profile": {"opening_pairs": 0},
        "productive_openings": [],
        "minimum_action_recipe": [],
    }
    def strong_edge(_source: str, _target: str) -> float:
        return 0.90

    rec_alchimie = {"difficulty": "normal", "target_depth": 2}
    assert RANK.play_quality(
        "alchimie", rec_alchimie, balanced_alchimie, strong_edge
    ) > RANK.play_quality(
        "alchimie", rec_alchimie, empty_alchimie, empty_edge
    )


def test_formula_curves_are_clamped_and_goldilocks_shaped() -> None:
    assert RANK._bounded_score(-100) == 0
    assert RANK._bounded_score(1000) == 100
    assert RANK._bounded_score(72.5) == 73
    assert RANK._choice_score(3) > RANK._choice_score(1)
    assert RANK._choice_score(3) > RANK._choice_score(12)
    assert RANK._width_score(4) > RANK._width_score(1)
    assert RANK._width_score(4) > RANK._width_score(12)
    assert RANK._opening_ratio_score(0.25) > RANK._opening_ratio_score(0.01)
    assert RANK._opening_ratio_score(0.25) > RANK._opening_ratio_score(1.0)
    assert RANK._par_score("usor", 2) > RANK._par_score("usor", 6)


def test_artifact_is_complete_exactly_bound_and_byte_identical(generated: dict) -> None:
    package_bytes = RANK.PACKAGE_RANKINGS.read_bytes()
    tests_bytes = RANK.TESTS_RANKINGS.read_bytes()
    assert package_bytes == tests_bytes == RANK.render_rankings(generated)

    artifact = json.loads(package_bytes)
    assert artifact == generated
    assert tuple(artifact) == ("meta", "boards")
    assert tuple(artifact["meta"]) == RANK.META_FIELDS
    assert tuple(artifact["meta"]["counts"]) == RANK.COUNT_FIELDS
    assert all(tuple(row) == RANK.BOARD_FIELDS for row in artifact["boards"])

    meta = artifact["meta"]
    assert meta["schema_version"] == 1
    assert meta["pack_sha256"] == RANK.critique_pack.normalized_text_sha256(
        RANK.critique_pack.PACKAGE_PACK
    )
    assert meta["kg_sha256"] == RANK.critique_pack.normalized_text_sha256(
        RANK.critique_pack.PACKAGE_KG
    )
    assert meta["rubric_sha256"] == RANK.critique_pack.normalized_text_sha256(
        RANK.critique_pack.RUBRIC_PATH
    )
    assert meta["counts"] == {
        "total": 794,
        "approved": 572,
        "pilot_eligible": 486,
        "by_game": {
            "conexiuni": 288,
            "contexto": 207,
            "lant": 201,
            "alchimie": 98,
        },
        "eligible_by_game": {
            "conexiuni": 123,
            "contexto": 192,
            "lant": 94,
            "alchimie": 77,
        },
    }


def test_every_pack_record_has_one_matching_score_row(generated: dict) -> None:
    pack = json.loads(RANK.critique_pack.PACKAGE_PACK.read_text(encoding="utf-8"))
    expected = {
        str(rec["id"]): (game, str(rec["status"]))
        for game in RANK.GAME_KINDS
        for rec in pack[game]
    }
    rows = generated["boards"]
    assert len(rows) == len(expected) == len({row["id"] for row in rows})
    assert {
        row["id"]: (row["game"], row["status"]) for row in rows
    } == expected
    assert all(0 <= row["romanian_familiarity"] <= 100 for row in rows)
    assert all(0 <= row["play_quality"] <= 100 for row in rows)
    assert all(0 <= row["pilot_score"] <= 100 for row in rows)
    assert all(1 <= row["selection_weight"] <= 5 for row in rows)
    assert all(
        row["pilot_score"]
        == RANK._bounded_score(
            0.60 * row["romanian_familiarity"] + 0.40 * row["play_quality"]
        )
        for row in rows
    )
    assert all(not row["pilot_eligible"] for row in rows if row["status"] != "approved")


def test_ranks_and_selection_quintiles_recompute_exactly(generated: dict) -> None:
    for game in RANK.GAME_KINDS:
        rows = [row for row in generated["boards"] if row["game"] == game]
        ordered = sorted(rows, key=lambda row: (-row["pilot_score"], row["id"]))
        assert [row["id"] for row in rows] == [row["id"] for row in ordered]
        assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))

        eligible = [row for row in ordered if row["pilot_eligible"]]
        count = len(eligible)
        assert count > 0
        for index, row in enumerate(eligible):
            assert row["selection_weight"] == 5 - min(4, (5 * index) // count)
        assert all(
            row["selection_weight"] == 1
            for row in rows
            if not row["pilot_eligible"]
        )


def test_default_checker_is_green_and_prints_a_human_audit(capsys) -> None:
    assert RANK.main(["rank_games_pack.py"]) == 0
    output = capsys.readouterr().out
    assert "794 total / 486 pilot-eligible" in output
    assert "conexiuni" in output and "contexto" in output
    assert "lant" in output and "alchimie" in output
    assert "top:" in output
    assert output.rstrip().endswith("board rankings GREEN")
