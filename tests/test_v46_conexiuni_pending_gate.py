"""Regression contract for the strict V46 Conexiuni pending-pool cleanup."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import critique_pack  # noqa: E402

_REVIEW = _ROOT / "docs/reviews/v46-conexiuni-pending-gate"
_DOSSIERS = _REVIEW / "dossiers"
_VERDICTS = _REVIEW / "conexiuni_verdicts.json"
_CRITIQUE = _REVIEW / "critique.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"
_TOMBSTONES = (
    _ROOT / "cat_de_roman_esti/fixtures/conexiuni_rejection_tombstones.json"
)

_PENDING_ID_SET_SHA256 = "0bd5fd1667b33897aa0954c7155552ccfa84d0cfb0f2111d4fc1195dfa221593"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_HUMAN_ONLY_REJECTS = {
    "cx_societate_294",
    "cx_societate_295",
    "cx_viata_de_roman_293",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v46_gate_covers_and_binds_all_79_fresh_dossiers() -> None:
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    ids = sorted(dossiers)
    id_blob = ("\n".join(ids) + "\n").encode()
    artifact = _json(_VERDICTS)

    assert len(ids) == len(set(ids)) == 79
    assert hashlib.sha256(id_blob).hexdigest() == _PENDING_ID_SET_SHA256
    verdicts, batch, bindings = apply_rereview.validated_artifact(
        artifact,
        "conexiuni",
        _VERDICTS,
    )
    assert batch["input_ids"] == ids
    assert set(verdicts) == set(dossiers)
    assert Counter(verdicts.values()) == {"reject": 79}
    assert Counter(row["analyst"] for row in artifact["perItem"]) == {"reject": 79}
    assert Counter(row["verifier"] for row in artifact["perItem"]) == {
        "reject": 38,
        "keep": 41,
    }
    assert artifact["evidence"] == {
        "reviewed_at": "2026-07-31",
        "pending_id_set_sha256": _PENDING_ID_SET_SHA256,
        "fresh_dossiers": 79,
        "deterministic_fail_records": 76,
        "deterministic_fail_findings": 438,
        "lint_clean_human_rejects": 3,
        "analyst_counts": {"reject": 79},
        "verifier_counts": {"reject": 38, "keep": 41},
        "independent_review_disagreements": 41,
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


def test_v46_deterministic_and_human_gates_close_the_full_batch() -> None:
    report = _json(_CRITIQUE)
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    failures = [
        finding
        for info in report["items"].values()
        for finding in info["findings"]
        if finding["level"] == "FAIL"
    ]
    failed_records = {
        item_id
        for item_id, info in report["items"].items()
        if any(finding["level"] == "FAIL" for finding in info["findings"])
    }

    assert len(failures) == 438
    assert len(failed_records) == 76
    assert Counter(finding["check"] for finding in failures) == {
        "duplicate_groups": 214,
        "member_overuse": 67,
        "board_reskin": 42,
        "tile_fairness": 41,
        "mirrored_groups": 38,
        "label_self_leak": 25,
        "red_herring_budget": 7,
        "board_type_shortcut": 3,
        "vague_predicate_wording": 1,
    }
    assert set(dossiers) - failed_records == _HUMAN_ONLY_REJECTS
    assert all(not dossiers[item_id]["lint_findings"] for item_id in _HUMAN_ONLY_REJECTS)


def test_v46_pack_removes_only_the_rejected_pending_conexiuni_records() -> None:
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    pack = _json(_PACKAGE_PACK)
    rejected = set(_json(_VERDICTS)["verdicts"])
    conexiuni = {record["id"]: record for record in pack["conexiuni"]}
    statuses = Counter(
        record["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for record in pack[game]
    )

    assert pack["meta"]["counts"] == {
        "conexiuni": 232,
        "contexto": 207,
        "lant": 97,
        "alchimie": 99,
    }
    assert pack["meta"]["id_high_water"]["conexiuni"] == 361
    assert Counter(record["status"] for record in conexiuni.values()) == {
        "approved": 232
    }
    assert statuses == {"approved": 609, "pending": 26}
    assert rejected.isdisjoint(conexiuni)


def test_v46_rejection_ledger_cross_binds_every_removed_record() -> None:
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    artifact_digest = hashlib.sha256(_VERDICTS.read_bytes()).hexdigest()
    tombstones = _json(_TOMBSTONES)

    assert tombstones["meta"]["count"] == len(tombstones["items"]) == 122
    assert tombstones["meta"]["group_count"] == 488
    critique_pack.validate_rejection_tombstones(tombstones)
    for item_id, dossier in dossiers.items():
        entry = tombstones["items"][item_id]
        dossier_groups = {
            frozenset(member["id"] for member in group["members"])
            for group in dossier["groups"]
        }
        tombstone_groups = {
            frozenset(members) for members in entry["groups"].values()
        }
        assert entry["record_sha256"] == dossier["record_sha256"]
        assert entry["review_binding"] == dossier["review_binding"]
        assert entry["source_gate_sha256"] == artifact_digest
        assert entry["groups_sha256"] == critique_pack.canonical_json_sha256(
            entry["groups"]
        )
        assert tombstone_groups == dossier_groups


def test_v46_rankings_and_frozen_derived_catalog_track_the_clean_pack() -> None:
    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
    rankings = _json(_PACKAGE_RANKINGS)
    assert rankings["meta"]["counts"] == {
        "total": 635,
        "approved": 609,
        "pilot_eligible": 448,
        "by_game": {
            "conexiuni": 232,
            "contexto": 207,
            "lant": 97,
            "alchimie": 99,
        },
        "eligible_by_game": {
            "conexiuni": 74,
            "contexto": 202,
            "lant": 94,
            "alchimie": 78,
        },
    }
    rejected = set(_json(_VERDICTS)["verdicts"])
    assert rejected.isdisjoint(row["id"] for row in rankings["boards"])

    assert _PACKAGE_DERIVED.read_bytes() == _TEST_DERIVED.read_bytes()
    derived = _json(_PACKAGE_DERIVED)
    boards_blob = (json.dumps(derived["boards"], ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(boards_blob).hexdigest() == _FROZEN_BOARDS_SHA256
    assert derived["meta"]["counts"]["by_game"] == {
        "intrusul": 183,
        "perechi": 153,
    }
    assert rejected.isdisjoint(board["source_id"] for board in derived["boards"])
