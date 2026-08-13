"""Regression contract for the strict V48 Alchimie pending-target gate."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from cat_de_roman_esti.wordgames import alchimie
from cat_de_roman_esti.wordgames.derived_catalog import (
    DEFAULT_DERIVED_CATALOG_SHA256,
)

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import audit_alchimie_projections  # noqa: E402
import critique_pack  # noqa: E402

_REVIEW = _ROOT / "docs/reviews/v48-alchimie-pending-gate"
_DOSSIERS = _REVIEW / "dossiers"
_VERDICTS = _REVIEW / "alchimie_verdicts.json"
_CRITIQUE = _REVIEW / "critique.json"
_PROJECTION = _REVIEW / "projection-audit.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"

_PENDING_ID_SET_SHA256 = "d7cbc45ce53f4c70e2d3c3d8214e5f49964422f703f3004514ab08eccb822120"
_VERDICTS_SHA256 = "e14ceab934c7e19ce8a2f1a2cdcf9e03650654e5ae268fa6e04f51401368b8d7"
_PROJECTION_SHA256 = "486aa09129e6ad1e4b4477b4721782ee7e041c1e3329714d82897ccb9757571c"
_PRE_APPLY_PACK_SHA256 = "c4542d4201c45b04f58563eb08aa2ba0973389f453f5181f53066a88df550d05"
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_RANKINGS_SHA256 = "fc1ac0bbb89334fa069ed5c68eea592c44cd0ab4ca6115bbe7e5870ac9834b9a"
_DERIVED_SHA256 = "c0d8a00334c920ef512c633f05a990a434428c7b4b6c8916618de9eb11d8f6c0"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_KG_SHA256 = "f2a4229c05072028fef1d8e68e97a6fe2e7c74c535bcca0fca0a0708acf5ed12"
_RUBRIC_SHA256 = "29781ef5daa65b0637425ea258702f9f644486807ea61e49020be66d168e0ca3"

_PROMOTED = {"al_literatura_097"}
_KEPT = {
    "al_gastronomie_026",
    "al_gastronomie_030",
    "al_viata_de_roman_092",
}
_REJECTED = {
    "al_arta_cultura_015",
    "al_film_tv_022",
    "al_geografie_032",
    "al_limba_047",
    "al_literatura_051",
    "al_muzica_065",
    "al_personalitati_070",
    "al_societate_076",
    "al_viata_de_roman_094",
    "al_viata_de_roman_095",
    "al_viata_de_roman_098",
    "al_viata_de_roman_099",
    "al_viata_de_roman_100",
    "al_viata_de_roman_101",
    "al_viata_de_roman_102",
    "al_viata_de_roman_103",
    "al_viata_de_roman_104",
}
_E2_FAILURES = {
    "al_arta_cultura_015",
    "al_geografie_032",
    "al_limba_047",
    "al_personalitati_070",
    "al_viata_de_roman_092",
    "al_viata_de_roman_094",
    "al_viata_de_roman_095",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v48_gate_is_an_exact_archive_valid_21_dossier_contract() -> None:
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    ids = sorted(dossiers)
    id_blob = ("\n".join(ids) + "\n").encode()
    artifact = _json(_VERDICTS)

    assert len(ids) == len(set(ids)) == 21
    assert hashlib.sha256(id_blob).hexdigest() == _PENDING_ID_SET_SHA256
    assert _sha256(_VERDICTS) == _VERDICTS_SHA256
    assert _sha256(_PROJECTION) == _PROJECTION_SHA256

    # This remains valid after the live pack has applied its outcomes because the
    # projection artifact carries the exact reviewed source records.
    verdicts, batch, bindings = apply_rereview.validated_artifact(
        artifact,
        "alchimie",
        _VERDICTS,
    )
    assert batch == {
        "version": 2,
        "mode": "gate",
        "input_ids": ids,
        "projection_audit_sha256": _PROJECTION_SHA256,
    }
    assert set(verdicts) == set(dossiers) == _PROMOTED | _KEPT | _REJECTED
    assert Counter(verdicts.values()) == {
        "reject": 17,
        "keep": 3,
        "promote": 1,
    }
    assert Counter(row["analyst"] for row in artifact["perItem"]) == {
        "reject": 17,
        "keep": 3,
        "promote": 1,
    }
    assert Counter(row["verifier"] for row in artifact["perItem"]) == {
        "reject": 14,
        "promote": 4,
        "keep": 3,
    }
    assert Counter(row["final"] for row in artifact["perItem"]) == {
        "reject": 17,
        "keep": 3,
        "promote": 1,
    }
    assert artifact["coverage"] == {
        "total": 21,
        "verified": 21,
        "unverifiedClean": 0,
        "verifiersLost": 0,
        "lost": 0,
    }
    assert artifact["evidence"] == {
        "reviewed_at": "2026-08-01",
        "pending_id_set_sha256": _PENDING_ID_SET_SHA256,
        "projection_audit_sha256": _PROJECTION_SHA256,
        "fresh_dossiers": 21,
        "deterministic_fail_records": 0,
        "deterministic_warn_records": 3,
        "live_e2_opening_floor_failures": 7,
        "analyst_counts": {"promote": 1, "reject": 17, "keep": 3},
        "verifier_counts": {"promote": 4, "reject": 14, "keep": 3},
        "final_counts": {"promote": 1, "reject": 17, "keep": 3},
        "independent_review_disagreements": 3,
        "mandatory_a5_holds": 3,
        "stale_v42_judgments_reused": False,
        "new_nodes_edges_or_authored_records": 0,
    }

    rows = {row["id"]: row for row in artifact["perItem"]}
    assert {
        item_id for item_id, row in rows.items() if row["analyst"] != row["verifier"]
    } == {"al_film_tv_022", "al_literatura_051", "al_societate_076"}
    for item_id, row in rows.items():
        assert bindings[item_id] == dossiers[item_id]["review_binding"]
        assert critique_pack.dossier_review_binding(dossiers[item_id]) == bindings[item_id]
        assert row["final"] == apply_rereview.synthesized_gate_verdict(
            row["analyst"],
            row["verifier"],
        )


def test_v48_deterministic_gate_has_only_the_three_exact_salience_warnings() -> None:
    report = _json(_CRITIQUE)
    findings = [
        (item_id, finding)
        for item_id, info in report["items"].items()
        for finding in info["findings"]
    ]

    assert report["pack_findings"] == []
    assert not [finding for _, finding in findings if finding["level"] == "FAIL"]
    assert findings == [
        (
            "al_film_tv_022",
            {
                "check": "salience_floor",
                "level": "WARN",
                "detail": "Subtitrare salience 0.23 < 0.35 (normal floor)",
            },
        ),
        (
            "al_geografie_032",
            {
                "check": "salience_floor",
                "level": "WARN",
                "detail": "Subcarpații salience 0.22 < 0.35 (normal floor)",
            },
        ),
        (
            "al_societate_076",
            {
                "check": "salience_floor",
                "level": "WARN",
                "detail": "Uniunea Europeană salience 0.30 < 0.60 (usor floor)",
            },
        ),
    ]


def test_v48_projection_audit_binds_live_bounds_and_both_reviewers() -> None:
    audit = _json(_PROJECTION)
    artifact = _json(_VERDICTS)
    ids = artifact["batch"]["input_ids"]
    audit_rows = {row["id"]: row for row in audit["items"]}
    verdict_rows = {row["id"]: row for row in artifact["perItem"]}

    assert audit["schema"] == "alchimie-live-projection-audit-v1"
    assert audit["game"] == "alchimie"
    assert audit["mode"] == "gate"
    assert audit["status"] == "pending"
    assert audit["input_ids"] == ids
    assert audit["input_ids_sha256"] == _PENDING_ID_SET_SHA256
    assert audit["pack_sha256"] == _PRE_APPLY_PACK_SHA256
    assert audit["kg_sha256"] == _KG_SHA256
    assert audit["rubric_sha256"] == _RUBRIC_SHA256
    assert audit["dossier_manifest_sha256"] == (
        "2a3250f1701ba54ee586670979d4105a5d6b093e7b2227cb0230bbd721d723db"
    )
    assert audit["generator"] == {
        "path": "scripts/audit_alchimie_projections.py",
        "sha256": "9dcae3ce7e5d4643fced7edcf6d962cc55568163fa5d77c93a325b69aeb405c2",
    }
    assert audit["summary"] == {
        "records": 21,
        "live_opening_floor_failures": 7,
    }
    assert len(audit["items"]) == len(audit_rows) == 21
    assert set(audit_rows) == set(ids)
    assert {
        item_id
        for item_id, row in audit_rows.items()
        if not row["bounds"]["e2_live_opening_floor"]
    } == _E2_FAILURES

    invariant_bounds = {
        "declared_par_matches_exact",
        "projection_par_matches_exact",
        "route_limit",
        "recipe_pair_limit",
        "projected_concept_limit",
        "result_per_pair_limit",
    }
    for item_id, row in audit_rows.items():
        assert set(row["bounds"]) == invariant_bounds | {"e2_live_opening_floor"}
        assert all(row["bounds"][name] for name in invariant_bounds)
        assert row["bounds"]["e2_live_opening_floor"] == (
            row["projected_opening_pair_count"] >= alchimie.MIN_OPENING_PAIRS
        )
        assert row["route_count"] <= alchimie.MAX_TARGET_ROUTES
        assert row["recipe_pair_count"] <= alchimie.MAX_RECIPE_PAIRS
        assert row["projected_concept_count"] <= alchimie.MAX_PROJECTED_CONCEPTS
        assert row["max_results_per_pair"] <= alchimie.MAX_RESULTS_PER_RECIPE
        assert verdict_rows[item_id]["analyst_projection_audit_sha256"] == (
            _PROJECTION_SHA256
        )
        assert verdict_rows[item_id]["verifier_projection_audit_sha256"] == (
            _PROJECTION_SHA256
        )

    hold_rows = {item_id: verdict_rows[item_id] for item_id in _KEPT}
    assert all(
        row["analyst"] == row["verifier"] == row["final"] == "keep"
        for row in hold_rows.values()
    )
    assert all("A5" in row["failure_modes"] for row in hold_rows.values())
    assert not {
        item_id
        for item_id, row in verdict_rows.items()
        if "A5" in row["failure_modes"]
    } - _KEPT


def test_v48_archived_projection_rebuild_is_cache_independent_and_byte_exact() -> None:
    audit = _json(_PROJECTION)

    alchimie._build_recipe_projection_cached.cache_clear()
    first = audit_alchimie_projections.rebuild_archived_artifact(audit, _DOSSIERS)
    alchimie._build_recipe_projection_cached.cache_clear()
    second = audit_alchimie_projections.rebuild_archived_artifact(audit, _DOSSIERS)
    alchimie._build_recipe_projection_cached.cache_clear()

    assert first == second == audit
    rebuilt_bytes = (json.dumps(first, ensure_ascii=False, indent=1) + "\n").encode()
    assert rebuilt_bytes == _PROJECTION.read_bytes()


def test_v48_archive_preserves_sources_after_bound_outcomes_are_applied() -> None:
    dossiers = {path.stem: _json(path) for path in sorted(_DOSSIERS.glob("*.json"))}
    artifact = _json(_VERDICTS)
    _, batch, _ = apply_rereview.validated_artifact(
        artifact,
        "alchimie",
        _VERDICTS,
    )
    audit_rows = {row["id"]: row for row in _json(_PROJECTION)["items"]}
    live = {row["id"]: row for row in _json(_PACKAGE_PACK)["alchimie"]}

    assert set(audit_rows) == set(dossiers) == _PROMOTED | _KEPT | _REJECTED
    for item_id, row in audit_rows.items():
        source = row["source_record"]
        assert source["id"] == item_id
        assert source["status"] == "pending"
        assert row["record_sha256"] == dossiers[item_id]["record_sha256"]
        assert row["record_sha256"] == critique_pack.canonical_json_sha256(source)
        assert row["review_binding"] == dossiers[item_id]["review_binding"]

    for item_id in _KEPT:
        assert live[item_id] == audit_rows[item_id]["source_record"]
    for item_id in _PROMOTED:
        source = dict(audit_rows[item_id]["source_record"])
        source["status"] = "approved"
        assert live[item_id] == source
    assert _REJECTED.isdisjoint(live)

    with pytest.raises(SystemExit, match="stale Alchimie live-projection source"):
        apply_rereview.validate_live_alchimie_projection_source(batch, _VERDICTS)


def test_v48_pack_rankings_and_frozen_derived_mirrors_track_the_gate() -> None:
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    assert _sha256(_PACKAGE_PACK) == _PACK_SHA256
    pack = _json(_PACKAGE_PACK)
    live = {row["id"]: row for row in pack["alchimie"]}
    statuses = Counter(
        row["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for row in pack[game]
    )

    assert pack["meta"]["counts"] == {
        "conexiuni": 232,
        "contexto": 207,
        "lant": 97,
        "alchimie": 82,
    }
    assert pack["meta"]["id_high_water"]["alchimie"] == 106
    assert statuses == {"approved": 610, "pending": 8}
    assert Counter(row["status"] for row in live.values()) == {
        "approved": 79,
        "pending": 3,
    }
    assert live["al_literatura_097"]["status"] == "approved"
    assert {item_id for item_id, row in live.items() if row["status"] == "pending"} == _KEPT
    assert _REJECTED.isdisjoint(live)

    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
    assert _sha256(_PACKAGE_RANKINGS) == _RANKINGS_SHA256
    rankings = _json(_PACKAGE_RANKINGS)
    assert rankings["meta"]["pack_sha256"] == _PACK_SHA256
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
    assert ranked["al_literatura_097"]["status"] == "approved"
    assert ranked["al_literatura_097"]["pilot_eligible"] is True
    assert ranked["al_literatura_097"]["pilot_score"] == 80
    assert all(ranked[item_id]["status"] == "pending" for item_id in _KEPT)
    assert all(ranked[item_id]["pilot_eligible"] is False for item_id in _KEPT)
    assert _REJECTED.isdisjoint(ranked)

    assert _PACKAGE_DERIVED.read_bytes() == _TEST_DERIVED.read_bytes()
    assert _sha256(_PACKAGE_DERIVED) == _DERIVED_SHA256
    assert DEFAULT_DERIVED_CATALOG_SHA256 == _DERIVED_SHA256
    derived = _json(_PACKAGE_DERIVED)
    assert derived["meta"]["pack_sha256"] == _PACK_SHA256
    assert derived["meta"]["v37_rankings_sha256"] == _RANKINGS_SHA256
    assert derived["meta"]["counts"] == {
        "total": 336,
        "by_game": {"intrusul": 183, "perechi": 153},
        "sources_by_game": {"intrusul": 66, "perechi": 51},
        "starter_by_game": {"intrusul": 24, "perechi": 26},
    }
    boards_blob = (json.dumps(derived["boards"], ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(boards_blob).hexdigest() == _FROZEN_BOARDS_SHA256
    assert _REJECTED.isdisjoint(board["source_id"] for board in derived["boards"])

    assert alchimie.store._ttl == 7200
    assert alchimie.store._max == 1000
