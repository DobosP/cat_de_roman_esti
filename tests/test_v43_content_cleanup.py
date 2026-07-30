"""Regression guards for the V43 strict content cleanup."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_KG = _ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
_TEST_KG = _ROOT / "tests" / "fixtures" / "kg_sample.json"
_FUNNEL = _ROOT / "docs" / "reviews" / "v43-release-funnel.json"
_FINAL_GATE = (
    _ROOT
    / "docs"
    / "reviews"
    / "v43-final-gate"
    / "conexiuni_verdicts.json"
)


def _fixture() -> dict:
    package_bytes = _PACKAGE_KG.read_bytes()
    assert package_bytes == _TEST_KG.read_bytes()
    return json.loads(package_bytes)


def test_verified_v43_current_fact_corrections_are_bound_in_both_kg_copies() -> None:
    fixture = _fixture()
    nodes = {node["id"]: node for node in fixture["kg_nodes"]}

    assert "8 iulie 2026" in nodes["n_v18spo_radu_dragusin"]["description"]
    assert "împrumutat la Fiorentina" in nodes["n_v18spo_radu_dragusin"]["description"]
    assert "17 martie 2012" in nodes["n_v20fil_te_cunosc_de_undeva"]["description"]
    assert "5 februarie 2024" in nodes["n_v21fil_power_couple"]["description"]
    assert "Din 2024" in nodes["n_v21fil_dani_otil"]["description"]
    assert (
        "Până la 30 iunie 2026"
        in nodes["n_v20via_carte_electronica_identitate"]["description"]
    )


def test_esigur_is_the_operational_police_system_not_fixed_rovinieta_cameras() -> None:
    fixture = _fixture()
    nodes = {node["id"]: node for node in fixture["kg_nodes"]}
    edges = {edge["id"]: edge for edge in fixture["kg_edges"]}
    esigur = nodes["n_v21via_esigur"]

    assert esigur["label_ro"] == "Sistemul e-SIGUR"
    assert esigur["degree"] == 0
    assert "Poliția Română" in esigur["description"]
    assert "trepiede mobile" in esigur["description"]
    assert not any("fix" in alias.casefold() for alias in esigur.get("aliases", ()))
    assert not any(
        "n_v21via_esigur" in (edge["src_id"], edge["dst_id"])
        for edge in edges.values()
    )
    assert {"de7495", "de7498"}.isdisjoint(edges)
    assert nodes["n_v18via_rovinieta"]["degree"] == 4
    assert nodes["n_v21via_autostrada_a7"]["degree"] == 2


def test_volatile_tiktok_superlative_is_not_stored_as_a_durable_fact() -> None:
    fixture = _fixture()
    nodes = {node["id"]: node for node in fixture["kg_nodes"]}
    edges = {edge["id"]: edge for edge in fixture["kg_edges"]}

    description = nodes["n_v19mem_aurelia_dobre"]["description"]
    assert "milioane de urmăritori" in description
    assert "cel mai urmărit" not in description
    assert edges["de6452"]["label_ro"] == "este activă pe"


def test_release_funnel_is_closed_without_quota_promotions() -> None:
    funnel = json.loads(_FUNNEL.read_text(encoding="utf-8"))
    final_gate = json.loads(_FINAL_GATE.read_text(encoding="utf-8"))

    assert funnel["initial_wave"]["proposals"] == 66
    assert funnel["initial_wave"]["early_survivors"] == 44
    assert funnel["replacement_wave"]["raw_review_totals"] == {
        "cultural": {
            "factual_clean": 2,
            "quality_keep": 0,
            "consensus": 0,
        },
        "everyday": {
            "factual_clean": 5,
            "factual_block": 4,
            "quality_keep": 3,
            "quality_drop": 6,
            "consensus": 2,
        },
    }
    assert funnel["final_real_id_gate"]["applied"] == {
        "new_rejections": 2,
        "new_promotions": 0,
        "rejection_tombstones": 43,
        "rejection_tombstone_groups": 172,
        "owner_demotions": 75,
    }
    assert final_gate["verdicts"] == {
        "cx_personalitati_360": "reject",
        "cx_sport_361": "reject",
    }
    assert final_gate["evidence"]["audited_approved_incumbents"] == {
        "cx_personalitati_339": "demote",
        "cx_sport_355": "demote",
        "cx_stiinta_356": "keep",
    }
