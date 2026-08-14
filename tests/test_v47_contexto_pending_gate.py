"""Regression contract for the strict V47 Cald sau Rece pending-target gate."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from cat_de_roman_esti.wordgames.contexto import (
    _build_session,
    _responsive_count,
    _score_feedback,
    store,
    temperature_for,
)
from cat_de_roman_esti.wordgames.contexto_projection import PROJECTION_TERMS
from cat_de_roman_esti.wordgames.derived_catalog import (
    DEFAULT_DERIVED_CATALOG_SHA256,
)
from cat_de_roman_esti.wordgames.service import get_service

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import critique_pack  # noqa: E402

_REVIEW = _ROOT / "docs/reviews/v47-contexto-pending-gate"
_DOSSIERS = _REVIEW / "dossiers"
_VERDICTS = _REVIEW / "contexto_verdicts.json"
_CRITIQUE = _REVIEW / "critique.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"

_PENDING_ID_SET_SHA256 = "508ac4014f6c519fc0891b92474e683e9a26078e86091cee8ee77a1aa10e97c1"
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_RANKINGS_SHA256 = "ec747eb5ee4842e6b6635569fb360e2ea13edbe0b30cffaf61d89758876cf720"
_DERIVED_SHA256 = "a97c3b124ddbf5f1c018e9fe50a33bc6d1dd44cc7e0b6c9331ee0a6df05b3dc0"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"

_PROMOTED = {"ct_gastronomie_300"}
_KEPT = {"ct_meme_net_238", "ct_societate_257"}
_REJECTED = {
    "ct_gastronomie_301",
    "ct_limba_307",
    "ct_societate_179",
    "ct_societate_256",
    "ct_societate_303",
    "ct_societate_305",
    "ct_stiinta_104",
    "ct_stiinta_306",
    "ct_viata_de_roman_302",
    "ct_viata_de_roman_304",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v47_gate_covers_and_binds_all_13_fresh_dossiers() -> None:
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    ids = sorted(dossiers)
    id_blob = ("\n".join(ids) + "\n").encode()
    artifact = _json(_VERDICTS)

    assert len(ids) == len(set(ids)) == 13
    assert hashlib.sha256(id_blob).hexdigest() == _PENDING_ID_SET_SHA256
    verdicts, batch, bindings = apply_rereview.validated_artifact(
        artifact,
        "contexto",
        _VERDICTS,
    )
    assert batch["input_ids"] == ids
    assert set(verdicts) == set(dossiers) == _PROMOTED | _KEPT | _REJECTED
    assert Counter(verdicts.values()) == {"reject": 10, "keep": 2, "promote": 1}
    assert Counter(row["analyst"] for row in artifact["perItem"]) == {
        "reject": 10,
        "keep": 2,
        "promote": 1,
    }
    assert Counter(row["verifier"] for row in artifact["perItem"]) == {
        "reject": 9,
        "keep": 2,
        "promote": 2,
    }
    assert artifact["evidence"] == {
        "reviewed_at": "2026-08-01",
        "pending_id_set_sha256": _PENDING_ID_SET_SHA256,
        "fresh_dossiers": 13,
        "deterministic_fail_records": 0,
        "deterministic_warn_records": 1,
        "analyst_counts": {"promote": 1, "reject": 10, "keep": 2},
        "verifier_counts": {"promote": 2, "reject": 9, "keep": 2},
        "final_counts": {"promote": 1, "reject": 10, "keep": 2},
        "independent_review_disagreements": 1,
        "new_aliases_or_projections": 0,
        "stale_v42_judgments_reused": False,
    }

    for row in artifact["perItem"]:
        item_id = row["id"]
        assert bindings[item_id] == dossiers[item_id]["review_binding"]
        assert critique_pack.dossier_review_binding(dossiers[item_id]) == bindings[item_id]
        assert row["final"] == apply_rereview.synthesized_gate_verdict(
            row["analyst"],
            row["verifier"],
        )


def test_v47_deterministic_floor_is_green_but_human_c1_c3_gate_is_stricter() -> None:
    report = _json(_CRITIQUE)
    artifact = _json(_VERDICTS)
    rows = {row["id"]: row for row in artifact["perItem"]}
    findings = [
        finding
        for item in report["items"].values()
        for finding in item["findings"]
    ]

    assert not [finding for finding in findings if finding["level"] == "FAIL"]
    assert findings == [
        {
            "check": "salience_floor",
            "level": "WARN",
            "detail": "Sonicitate salience 0.15 < 0.20 (greu floor)",
        }
    ]
    assert rows["ct_stiinta_104"]["failure_modes"] == ["C1", "C2", "C3", "C6"]
    assert rows["ct_gastronomie_300"]["metrics"] == {
        "direct_incoming": 15,
        "responsive": 2259,
        "direct_projections": 19,
        "direct_feedback_proxies": 1,
    }
    assert rows["ct_societate_303"]["analyst"] == "reject"
    assert rows["ct_societate_303"]["verifier"] == "promote"
    assert rows["ct_societate_303"]["final"] == "reject"


def test_v47_live_feedback_proves_mancare_and_rejects_the_misleading_family_field() -> None:
    svc = get_service()
    food_target = "n_v4gas_mancare"
    family_target = "n_v4soc_familie"

    assert len(svc.predecessor_ids(food_target)) == 15
    assert _responsive_count(svc.distances_to(food_target)) == 2259
    assert all(
        svc.resolve(surface) == food_target
        for surface in ("mâncare", "mâncarea", "mâncăruri", "mâncărurile")
    )
    assert sum(term.anchor_id == food_target for term in PROJECTION_TERMS) == 19

    family = _build_session(family_target, "usor", None)
    for surface in ("mamă", "tată", "bunică", "bunic", "frate", "soră"):
        node_id = svc.resolve(surface)
        assert node_id is not None
        score = _score_feedback(svc, family, node_id)
        assert score.rank == 2079
        assert temperature_for(
            family,
            score.feedback_distance,
            score.weighted_distance,
            rank_override=score.rank,
        ) == "Inghetat"

    # The natural definite weather form belongs to the served Cargo-song concept.
    assert svc.resolve("ploaia") == "n_muz_ploaia_cargo"


def test_v47_pack_applies_only_the_bound_outcomes_and_keeps_unique_live_targets() -> None:
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    pack = _json(_PACKAGE_PACK)
    contexto = {record["id"]: record for record in pack["contexto"]}
    statuses = Counter(
        record["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for record in pack[game]
    )

    assert pack["meta"]["counts"] == {
        "conexiuni": 232,
        "contexto": 207,
        "lant": 97,
        "alchimie": 82,
    }
    assert pack["meta"]["id_high_water"]["contexto"] == 317
    assert Counter(record["status"] for record in contexto.values()) == {
        "approved": 205,
        "pending": 2,
    }
    assert statuses == {"approved": 610, "pending": 8}
    assert contexto["ct_gastronomie_300"]["status"] == "approved"
    assert {item_id for item_id, row in contexto.items() if row["status"] == "pending"} == _KEPT
    assert _REJECTED.isdisjoint(contexto)

    rankings = _json(_PACKAGE_RANKINGS)
    eligible_ids = {
        row["id"]
        for row in rankings["boards"]
        if row["game"] == "contexto" and row["pilot_eligible"]
    }
    eligible_targets = [contexto[item_id]["target"] for item_id in eligible_ids]
    assert len(eligible_ids) == len(eligible_targets) == len(set(eligible_targets)) == 202


def test_v47_archive_preserves_every_removed_record_binding_without_a_ledger() -> None:
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    artifact = _json(_VERDICTS)
    rows = {row["id"]: row for row in artifact["perItem"]}
    pack = _json(_PACKAGE_PACK)
    live_ids = {record["id"] for record in pack["contexto"]}

    assert _REJECTED.isdisjoint(live_ids)
    assert _REJECTED <= set(dossiers) == set(rows)
    for item_id in _REJECTED:
        dossier = dossiers[item_id]
        assert rows[item_id]["final"] == "reject"
        assert rows[item_id]["review_binding"] == dossier["review_binding"]
        assert dossier["record_sha256"]
        assert dossier["kg_sha256"]
        assert dossier["rubric_sha256"]


def test_v47_rankings_and_frozen_derived_catalog_track_the_clean_pack() -> None:
    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
    assert hashlib.sha256(_PACKAGE_PACK.read_bytes()).hexdigest() == _PACK_SHA256
    assert hashlib.sha256(_PACKAGE_RANKINGS.read_bytes()).hexdigest() == _RANKINGS_SHA256
    rankings = _json(_PACKAGE_RANKINGS)
    assert rankings["meta"]["counts"] == {
        "total": 618,
        "approved": 610,
        "pilot_eligible": 449,
        "by_game": {
            "conexiuni": 232,
            "contexto": 207,
            "lant": 97,
            "alchimie": 82,
        },
        "eligible_by_game": {
            "conexiuni": 74,
            "contexto": 202,
            "lant": 94,
            "alchimie": 79,
        },
    }
    ranked = {row["id"]: row for row in rankings["boards"]}
    assert ranked["ct_gastronomie_300"]["pilot_eligible"] is True
    assert ranked["ct_gastronomie_300"]["pilot_score"] == 94
    assert all(ranked[item_id]["pilot_eligible"] is False for item_id in _KEPT)
    assert _REJECTED.isdisjoint(ranked)

    assert _PACKAGE_DERIVED.read_bytes() == _TEST_DERIVED.read_bytes()
    assert hashlib.sha256(_PACKAGE_DERIVED.read_bytes()).hexdigest() == _DERIVED_SHA256
    assert DEFAULT_DERIVED_CATALOG_SHA256 == _DERIVED_SHA256
    derived = _json(_PACKAGE_DERIVED)
    boards_blob = (json.dumps(derived["boards"], ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(boards_blob).hexdigest() == _FROZEN_BOARDS_SHA256
    assert derived["meta"]["counts"]["by_game"] == {
        "intrusul": 183,
        "perechi": 153,
    }
    assert _REJECTED.isdisjoint(board["source_id"] for board in derived["boards"])

    assert store._ttl == 7200
    assert store._max == 1000
