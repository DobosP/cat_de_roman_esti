"""Regression contract for the strict V45 Lanț pending-pool cleanup (ADR-0069)."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from cat_de_roman_esti.data import load_fixture
from cat_de_roman_esti.wordgames.packs import validate_payload
from cat_de_roman_esti.wordgames.service import WordGameService

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import critique_pack  # noqa: E402

_REVIEW = _ROOT / "docs/reviews/v45-lant-pending-gate"
_DOSSIERS = _REVIEW / "dossiers"
_VERDICTS = _REVIEW / "lant_verdicts.json"
_CRITIQUE = _REVIEW / "critique.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"

_PENDING_ID_SET_SHA256 = "300d8e841ec55c68519de3f18fb4ab6cbed0912c6b0028fe1744afa7b78a373f"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_KEPT = {
    "lt_literatura_210",
    "lt_stiinta_216",
    "lt_viata_de_roman_211",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v45_gate_covers_and_binds_all_107_fresh_dossiers() -> None:
    dossier_paths = sorted(_DOSSIERS.glob("*.json"))
    dossiers = {path.stem: _json(path) for path in dossier_paths}
    ids = sorted(dossiers)
    id_blob = ("\n".join(ids) + "\n").encode()
    artifact = _json(_VERDICTS)

    assert len(ids) == len(set(ids)) == 107
    assert hashlib.sha256(id_blob).hexdigest() == _PENDING_ID_SET_SHA256
    verdicts, batch, bindings = apply_rereview.validated_artifact(
        artifact,
        "lant",
        _VERDICTS,
    )
    assert batch["input_ids"] == ids
    assert set(verdicts) == set(dossiers)
    assert Counter(verdicts.values()) == {"reject": 104, "keep": 3}
    assert {item_id for item_id, verdict in verdicts.items() if verdict == "keep"} == _KEPT
    assert artifact["evidence"] == {
        "reviewed_at": "2026-07-31",
        "pending_id_set_sha256": _PENDING_ID_SET_SHA256,
        "fresh_dossiers": 107,
        "deterministic_playability_fail_records": 91,
        "deterministic_playability_fail_findings": 177,
        "independent_review_disagreements": 13,
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


def test_v45_deterministic_gate_exposes_the_91_runtime_failures() -> None:
    report = _json(_CRITIQUE)
    failures = [
        finding
        for info in report["items"].values()
        for finding in info["findings"]
        if finding["check"] == "lant_playability" and finding["level"] == "FAIL"
    ]
    failed_records = {
        item_id
        for item_id, info in report["items"].items()
        if any(
            finding["check"] == "lant_playability" and finding["level"] == "FAIL"
            for finding in info["findings"]
        )
    }

    assert len(failures) == 177
    assert len(failed_records) == 91
    assert not (failed_records & _KEPT)


def test_v45_pack_keeps_only_the_three_unanimous_repair_holds() -> None:
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    pack = _json(_PACKAGE_PACK)
    verdicts = _json(_VERDICTS)["verdicts"]
    lant = {record["id"]: record for record in pack["lant"]}
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
    assert pack["meta"]["id_high_water"]["lant"] == 219
    assert Counter(record["status"] for record in lant.values()) == {
        "approved": 94,
        "pending": 3,
    }
    assert statuses == {"approved": 610, "pending": 8}
    assert {item_id for item_id, record in lant.items() if record["status"] == "pending"} == _KEPT
    assert not {
        item_id for item_id, verdict in verdicts.items() if verdict == "reject"
    } & set(lant)

    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    assert all(validate_payload(lant[item_id], "lant", svc) == [] for item_id in _KEPT)


def test_v45_rankings_and_frozen_derived_catalog_track_the_clean_pack() -> None:
    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
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
    assert all(ranked[item_id]["pilot_eligible"] is False for item_id in _KEPT)

    assert _PACKAGE_DERIVED.read_bytes() == _TEST_DERIVED.read_bytes()
    derived = _json(_PACKAGE_DERIVED)
    boards_blob = (json.dumps(derived["boards"], ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(boards_blob).hexdigest() == _FROZEN_BOARDS_SHA256
    assert derived["meta"]["counts"]["by_game"] == {"intrusul": 183, "perechi": 153}
