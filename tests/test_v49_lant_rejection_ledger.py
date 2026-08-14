"""Regression contract for the V49 durable Lanț rejection ledger."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from cat_de_roman_esti.wordgames.service import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
)

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import critique_pack  # noqa: E402
import import_candidates  # noqa: E402

_V45_REVIEW = _ROOT / "docs/reviews/v45-lant-pending-gate"
_V45_DOSSIERS = _V45_REVIEW / "dossiers"
_V45_VERDICTS = _V45_REVIEW / "lant_verdicts.json"
_V49_REVIEW = _ROOT / "docs/reviews/v49-lant-rejection-ledger"
_V49_SEED_AUDIT = _V49_REVIEW / "seed-audit.json"
_V49_ADR = _ROOT / "docs/adr/0073-durable-lant-rejection-debt.md"
_LEDGER = _ROOT / "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"

_V45_GATE_SHA256 = "4e976a185b27ccee2737542ed8321c6664b7b8c974ae8e793076571964af4458"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_V49_SEED_AUDIT_SHA256 = (
    "10fda097f8c91986db9ad14d3784be01977fbc90ff7cf889ae3f86d3b4726fb3"
)
_V45_REJECT_ID_SET_SHA256 = (
    "eadd0fc249c8bcdd601e2ffd9a03b0c2aa472e9115d853fdf165aa884bd597e6"
)
_V45_PRE_APPLY_PACK_SHA256 = (
    "742478415995b67379ba6fe58f939132abbff141aef7af392eff05b70e7845b6"
)
_V45_PRE_APPLY_COMMIT = "246e8577412831405c67bfd6e8843121d8309cd0"
_V48_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_CURRENT_RANKINGS_SHA256 = (
    "ec747eb5ee4842e6b6635569fb360e2ea13edbe0b30cffaf61d89758876cf720"
)
_CURRENT_DERIVED_SHA256 = (
    "a97c3b124ddbf5f1c018e9fe50a33bc6d1dd44cc7e0b6c9331ee0a6df05b3dc0"
)
_FROZEN_DERIVED_BOARDS_SHA256 = (
    "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
)
_V45_KEEPS = {
    "lt_literatura_210",
    "lt_stiinta_216",
    "lt_viata_de_roman_211",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v49_real_ledger_exactly_binds_the_104_v45_rejections() -> None:
    artifact = _json(_V45_VERDICTS)
    dossiers = {
        path.stem: _json(path) for path in sorted(_V45_DOSSIERS.glob("*.json"))
    }
    artifact_rows = {row["id"]: row for row in artifact["perItem"]}
    rejected = {
        item_id for item_id, verdict in artifact["verdicts"].items() if verdict == "reject"
    }
    kept = {
        item_id for item_id, verdict in artifact["verdicts"].items() if verdict == "keep"
    }
    data = _json(_LEDGER)
    loaded = {
        row["id"]: row for row in critique_pack.load_lant_rejection_tombstones()
    }
    runtime_ids = {row["id"] for row in _json(_PACKAGE_PACK)["lant"]}

    assert Counter(artifact["verdicts"].values()) == {"reject": 104, "keep": 3}
    assert kept == _V45_KEEPS
    assert set(data["items"]) == set(loaded) == rejected
    assert len({(row["start"], row["target"]) for row in loaded.values()}) == 104
    assert rejected.isdisjoint(kept | runtime_ids)
    assert kept.isdisjoint(data["items"])

    for item_id in sorted(rejected):
        entry = data["items"][item_id]
        dossier = dossiers[item_id]
        pair = {
            "start": dossier["start"]["id"],
            "target": dossier["target"]["id"],
        }
        assert loaded[item_id] == {"id": item_id, **pair}
        assert entry["record_sha256"] == dossier["record_sha256"]
        assert entry["pair_sha256"] == critique_pack.canonical_json_sha256(pair)
        assert entry["review_binding"] == dossier["review_binding"]
        assert entry["review_binding"] == artifact_rows[item_id]["review_binding"]
        assert entry["source_gate_sha256"] == _V45_GATE_SHA256


def test_v49_real_ledger_pins_the_exact_v45_seed_provenance() -> None:
    data = _json(_LEDGER)
    rejected_ids = sorted(data["items"])
    id_blob = ("\n".join(rejected_ids) + "\n").encode()

    assert data["schema_version"] == 1
    assert data["meta"] == {
        "note": (
            "Exact rejected Lanț records retained only for future exact start-target "
            "novelty checks; they are never runtime boards."
        ),
        "count": 104,
        "initial_seed_gate_sha256": _V45_GATE_SHA256,
        "initial_seed_id_set_sha256": _V45_REJECT_ID_SET_SHA256,
        "initial_seed_pack_sha256": _V45_PRE_APPLY_PACK_SHA256,
        "initial_seed_pack_commit": _V45_PRE_APPLY_COMMIT,
    }
    assert _sha256(_V45_VERDICTS) == _V45_GATE_SHA256
    assert _sha256(_LEDGER) == _V49_LEDGER_SHA256
    assert hashlib.sha256(id_blob).hexdigest() == _V45_REJECT_ID_SET_SHA256
    assert critique_pack.validate_lant_rejection_tombstones(data) == (
        critique_pack.load_lant_rejection_tombstones(_LEDGER)
    )


def test_v49_seed_audit_and_adr_bind_the_executable_contract() -> None:
    audit = _json(_V49_SEED_AUDIT)

    assert _sha256(_V49_SEED_AUDIT) == _V49_SEED_AUDIT_SHA256
    assert audit == {
        "schema_version": 1,
        "version": "V49",
        "audited_at": "2026-08-11",
        "scope": "lant_rejection_ledger_initial_seed",
        "source": {
            "pre_apply_pack_commit": _V45_PRE_APPLY_COMMIT,
            "pre_apply_pack_sha256": _V45_PRE_APPLY_PACK_SHA256,
            "gate_path": "docs/reviews/v45-lant-pending-gate/lant_verdicts.json",
            "gate_sha256": _V45_GATE_SHA256,
            "dossiers_path": "docs/reviews/v45-lant-pending-gate/dossiers",
            "rejected_id_set_sha256": _V45_REJECT_ID_SET_SHA256,
        },
        "output": {
            "path": "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json",
            "sha256": _V49_LEDGER_SHA256,
            "record_count": 104,
            "directed_pair_count": 104,
        },
        "excluded_pending_ids": sorted(_V45_KEEPS),
        "checks": {
            "source_rows_were_pending": 104,
            "record_digests_match_dossiers": 104,
            "pairs_match_dossiers": 104,
            "verdicts_are_reject": 104,
            "review_bindings_match_gate": 104,
            "source_gate_digests_match": 104,
            "excluded_holds_absent": 3,
            "runtime_pair_overlap": 0,
        },
    }

    adr = _V49_ADR.read_text(encoding="utf-8")
    readme = (_V49_REVIEW / "README.md").read_text(encoding="utf-8")
    assert "exact directed `start` → `target` pair" in adr
    assert "same pack/ledger transaction" in adr
    assert "104 IDs and 104 unique directed pairs" in readme
    assert "reverse direction is not inferred" in readme
    assert _V49_SEED_AUDIT_SHA256 in readme


@pytest.mark.parametrize(
    ("path", "replacement", "error"),
    [
        (("meta", "count"), 103, "stale meta count"),
        (("meta", "initial_seed_gate_sha256"), "bad", "initial_seed_gate_sha256"),
        (("meta", "initial_seed_id_set_sha256"), "bad", "initial_seed_id_set_sha256"),
        (("meta", "initial_seed_pack_sha256"), "bad", "initial_seed_pack_sha256"),
        (("meta", "initial_seed_pack_commit"), "bad", "initial seed commit"),
        (
            ("items", "lt_arta_cultura_156", "record_sha256"),
            "bad",
            "invalid binding",
        ),
        (
            ("items", "lt_arta_cultura_156", "source_gate_sha256"),
            "bad",
            "invalid binding",
        ),
        (
            ("items", "lt_arta_cultura_156", "pair_sha256"),
            "0" * 64,
            "pair digest drift",
        ),
    ],
)
def test_v49_ledger_integrity_mutations_fail_closed(
    path: tuple[str, ...], replacement: object, error: str
) -> None:
    data = copy.deepcopy(_json(_LEDGER))
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement

    with pytest.raises(ValueError, match=error):
        critique_pack.validate_lant_rejection_tombstones(data)


def test_v49_seed_row_deletion_fails_even_with_a_matching_smaller_count() -> None:
    data = copy.deepcopy(_json(_LEDGER))
    data["items"].pop(next(iter(data["items"])))
    data["meta"]["count"] -= 1

    with pytest.raises(ValueError, match="initial seed ID set drift"):
        critique_pack.validate_lant_rejection_tombstones(data)


def test_v49_rejection_debt_is_an_exact_directed_pair_failure() -> None:
    rejected = critique_pack.load_lant_rejection_tombstones()[0]
    marker = f"rejected:{rejected['id']}"
    pairs = {(rejected["start"], rejected["target"]): [marker]}

    assert critique_pack.check_lant_rejection_debt(rejected, pairs) == [
        {
            "check": "lant_rejection_debt",
            "level": "FAIL",
            "detail": (
                "directed start/target pair was already rejected "
                f"(see: {marker})"
            ),
        }
    ]
    assert critique_pack.check_lant_rejection_debt(
        {"start": rejected["target"], "target": rejected["start"]}, pairs
    ) == []


def test_v49_pending_gate_preflight_reads_the_real_rejection_ledger() -> None:
    rejected = critique_pack.load_lant_rejection_tombstones()[0]
    dossier = _json(_V45_DOSSIERS / f"{rejected['id']}.json")
    candidate = {
        "id": "lt_test_reintroduced_pair_220",
        "category": dossier["category"],
        "difficulty": dossier["difficulty"],
        "source": "test",
        "status": "pending",
        "start": rejected["start"],
        "target": rejected["target"],
        "optimal": dossier["optimal"],
    }
    pack, service, strong, regions = critique_pack.load_all(
        _PACKAGE_PACK, _PACKAGE_KG
    )
    pack["lant"].append(candidate)

    _, _, selected = critique_pack.run(
        pack,
        service,
        strong,
        regions,
        ["lant"],
        {"pending"},
        {candidate["id"]},
    )
    findings = selected[0][2]

    assert any(
        finding["check"] == "lant_rejection_debt"
        and finding["level"] == "FAIL"
        and f"rejected:{rejected['id']}" in finding["detail"]
        for finding in findings
    )

    _, _, pending_sweep = critique_pack.run(
        pack,
        service,
        strong,
        regions,
        ["lant"],
        {"pending"},
        None,
    )
    sweep_findings = next(
        row_findings
        for _, row, row_findings in pending_sweep
        if row["id"] == candidate["id"]
    )
    assert any(
        finding["check"] == "lant_rejection_debt"
        and finding["level"] == "FAIL"
        for finding in sweep_findings
    )


def test_v49_prospective_gate_censuses_same_batch_lant_pair_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pack, service, strong, regions = critique_pack.load_all(
        _PACKAGE_PACK,
        _PACKAGE_KG,
    )
    source = next(row for row in pack["lant"] if row["status"] == "pending")
    promoted = {**source, "id": "lt_test_promote_same_pair"}
    rejected = {**source, "id": "lt_test_reject_same_pair"}
    mini_pack = {
        **pack,
        "lant": [
            row for row in pack["lant"] if row["id"] != source["id"]
        ] + [promoted, rejected],
    }
    monkeypatch.setattr(
        apply_rereview.critique_pack,
        "load_all",
        lambda *_args: (copy.deepcopy(mini_pack), service, strong, regions),
    )

    assert apply_rereview.critique_promotions(
        {promoted["id"]},
        {rejected["id"]},
    ) == 1
    assert apply_rereview.critique_promotions({promoted["id"]}, set()) == 1

    unique_pack = {
        **mini_pack,
        "lant": [row for row in mini_pack["lant"] if row["id"] != rejected["id"]],
    }
    monkeypatch.setattr(
        apply_rereview.critique_pack,
        "load_all",
        lambda *_args: (copy.deepcopy(unique_pack), service, strong, regions),
    )
    assert apply_rereview.critique_promotions({promoted["id"]}, set()) == 0


def test_v49_import_preflight_blocks_only_kept_exact_directed_pairs() -> None:
    rejected = critique_pack.load_lant_rejection_tombstones()[0]
    marker = f"rejected:{rejected['id']}"
    candidate = {
        "lant": [
            {"start": rejected["start"], "target": rejected["target"]},
            {"start": rejected["target"], "target": rejected["start"]},
            {"start": rejected["start"], "target": rejected["target"]},
        ]
    }
    quality = {
        "instances": [
            {"ref": "lant[0]", "verdict": "keep"},
            {"ref": "lant[1]", "verdict": "keep"},
            {"ref": "lant[2]", "verdict": "drop"},
        ]
    }
    pairs = {(rejected["start"], rejected["target"]): [marker]}

    assert import_candidates.lant_rejection_errors(candidate, quality, pairs) == [
        "lant[0] reuses rejected directed start/target pair " f"(see: {marker})"
    ]


def test_v49_import_preflight_checks_the_post_alias_directed_pair() -> None:
    raw_start, canonical_start = next(iter(import_candidates.DUPLICATE_ALIASES.items()))
    marker = "rejected:lt_prior_alias_pair"
    candidate = {"lant": [{"start": raw_start, "target": "n_target"}]}
    quality = {
        "instances": [{"ref": "lant[0]", "verdict": "keep"}],
    }
    pairs = {(canonical_start, "n_target"): [marker]}

    assert import_candidates.lant_rejection_errors(candidate, quality, pairs) == [
        "lant[0] reuses rejected directed start/target pair " f"(see: {marker})"
    ]


def test_v49_verified_candidate_preflight_aborts_before_rejected_pair_import(
    tmp_path: Path,
) -> None:
    rejected = critique_pack.load_lant_rejection_tombstones()[0]
    category = "test"
    directory = tmp_path / category
    directory.mkdir()
    candidate = {
        "nodes": [],
        "edges": [],
        "conexiuni": [],
        "contexto": [],
        "lant": [{"start": rejected["start"], "target": rejected["target"]}],
        "alchimie": [],
    }
    candidate_blob = (json.dumps(candidate) + "\n").encode()
    binding = "sha256:" + hashlib.sha256(candidate_blob).hexdigest()
    (directory / "candidates.json").write_bytes(candidate_blob)
    (directory / "verify_factual.json").write_text(
        json.dumps({
            "category": category,
            "candidate_sha256": binding,
            "reviewed_refs": ["lant[0]"],
            "issues": [],
            "coverage_note": "complete",
        }),
        encoding="utf-8",
    )
    (directory / "verify_quality.json").write_text(
        json.dumps({
            "category": category,
            "candidate_sha256": binding,
            "instances": [{
                "ref": "lant[0]",
                "verdict": "keep",
                "note": "would otherwise stage pending",
            }],
            "coverage_note": "complete",
        }),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="reuses rejected directed start/target pair"):
        import_candidates.preflight_candidates(tmp_path)


def test_v49_append_helper_binds_a_new_reject_without_rewriting_seed_meta() -> None:
    original = _LEDGER.read_bytes()
    original_meta = _json(_LEDGER)["meta"]
    record = {
        "id": "lt_test_rejected_pair_220",
        "category": "test",
        "difficulty": "normal",
        "source": "test",
        "status": "pending",
        "start": "n_test_start",
        "target": "n_test_target",
        "optimal": 3,
    }
    review_binding = "sha256:" + "a" * 64
    gate_digest = "b" * 64
    updated = apply_rereview.updated_lant_rejection_tombstones(
        original,
        [record],
        {record["id"]: review_binding},
        {record["id"]: gate_digest},
    )
    data = json.loads(updated.decode("utf-8"))
    entry = data["items"][record["id"]]
    pair = {"start": record["start"], "target": record["target"]}

    assert data["meta"] == {**original_meta, "count": 105}
    assert entry == {
        "record_sha256": critique_pack.canonical_json_sha256(record),
        "pair_sha256": critique_pack.canonical_json_sha256(pair),
        "review_binding": review_binding,
        "source_gate_sha256": gate_digest,
        **pair,
    }
    assert {row["id"] for row in critique_pack.validate_lant_rejection_tombstones(data)} == (
        {*_json(_LEDGER)["items"], record["id"]}
    )


@pytest.mark.parametrize("validator_result", [0, 1])
def test_v49_future_lant_rejection_appends_and_rolls_back_transactionally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    validator_result: int,
) -> None:
    record = {
        "id": "lt_test_future_reject_220",
        "category": "test",
        "difficulty": "normal",
        "source": "test",
        "status": "pending",
        "start": "n_test_start",
        "target": "n_test_target",
        "optimal": 3,
    }
    pack = {
        "meta": {
            "counts": {"conexiuni": 0, "contexto": 0, "lant": 1, "alchimie": 0},
            "id_high_water": {"conexiuni": 0, "contexto": 0, "lant": 220, "alchimie": 0},
        },
        "conexiuni": [],
        "contexto": [],
        "lant": [record],
        "alchimie": [],
    }
    original_pack = (json.dumps(pack) + "\n").encode()
    copies = (tmp_path / "package-pack.json", tmp_path / "tests-pack.json")
    for copy_path in copies:
        copy_path.write_bytes(original_pack)
    empty_ledger = {
        "schema_version": 1,
        "meta": {
            "note": "test",
            "count": 0,
            "initial_seed_gate_sha256": "0" * 64,
            "initial_seed_id_set_sha256": hashlib.sha256(b"").hexdigest(),
            "initial_seed_pack_sha256": "0" * 64,
            "initial_seed_pack_commit": "0" * 40,
        },
        "items": {},
    }
    ledger_path = tmp_path / "lant-rejections.json"
    original_ledger = (json.dumps(empty_ledger) + "\n").encode()
    ledger_path.write_bytes(original_ledger)
    binding = "sha256:" + "a" * 64
    artifact = {
        "game": "lant",
        "mode": "gate",
        "batch": {"version": 2, "mode": "gate", "input_ids": [record["id"]]},
        "verdicts": {record["id"]: "reject"},
        "perItem": [{
            "id": record["id"],
            "game": "lant",
            "proposed": "reject",
            "final": "reject",
            "analyst": "reject",
            "verifier": "reject",
            "verified": True,
            "verifier_lost": False,
            "review_binding": binding,
        }],
        "coverage": {
            "total": 1,
            "verified": 1,
            "unverifiedClean": 0,
            "verifiersLost": 0,
            "lost": 0,
        },
    }
    artifact_path = tmp_path / "lant_verdicts.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    monkeypatch.setattr(apply_rereview, "PACK_COPIES", copies)
    monkeypatch.setattr(
        apply_rereview.critique_pack,
        "LANT_REJECTION_TOMBSTONES",
        ledger_path,
    )
    monkeypatch.setattr(
        apply_rereview,
        "current_review_bindings",
        lambda _ids: {record["id"]: binding},
    )
    monkeypatch.setattr(apply_rereview, "critique_promotions", lambda *_args: 0)
    monkeypatch.setattr(
        apply_rereview.validate_games_pack,
        "main",
        lambda _argv: validator_result,
    )

    if validator_result:
        with pytest.raises(SystemExit, match="pack validation failed"):
            apply_rereview.main(["apply_rereview.py", "--dir", str(tmp_path)])
        assert [path.read_bytes() for path in copies] == [original_pack, original_pack]
        assert ledger_path.read_bytes() == original_ledger
        return

    assert apply_rereview.main(["apply_rereview.py", "--dir", str(tmp_path)]) == 0
    assert all(_json(path)["lant"] == [] for path in copies)
    ledger = _json(ledger_path)
    assert ledger["meta"]["count"] == 1
    assert ledger["items"][record["id"]]["source_gate_sha256"] == hashlib.sha256(
        artifact_path.read_bytes()
    ).hexdigest()


def test_v49_ledger_is_non_runtime_and_preserves_pack_boards_and_sessions() -> None:
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
    assert _PACKAGE_DERIVED.read_bytes() == _TEST_DERIVED.read_bytes()
    assert _sha256(_PACKAGE_PACK) == _V48_PACK_SHA256
    assert _sha256(_PACKAGE_RANKINGS) == _CURRENT_RANKINGS_SHA256
    assert _sha256(_PACKAGE_DERIVED) == _CURRENT_DERIVED_SHA256

    pack = _json(_PACKAGE_PACK)
    rankings = _json(_PACKAGE_RANKINGS)
    derived = _json(_PACKAGE_DERIVED)
    rejected_ids = set(_json(_LEDGER)["items"])
    rejected_pairs = {
        (row["start"], row["target"])
        for row in _json(_LEDGER)["items"].values()
    }
    pack_ids = {
        row["id"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for row in pack[game]
    }
    boards_blob = (json.dumps(derived["boards"], ensure_ascii=False, indent=1) + "\n").encode()

    assert pack["meta"]["counts"] == {
        "conexiuni": 232,
        "contexto": 207,
        "lant": 97,
        "alchimie": 82,
    }
    assert Counter(
        row["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for row in pack[game]
    ) == {"approved": 610, "pending": 8}
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
    assert derived["meta"]["counts"]["by_game"] == {
        "intrusul": 183,
        "perechi": 153,
    }
    assert hashlib.sha256(boards_blob).hexdigest() == _FROZEN_DERIVED_BOARDS_SHA256
    assert rejected_ids.isdisjoint(pack_ids)
    assert rejected_pairs.isdisjoint(
        (row["start"], row["target"]) for row in pack["lant"]
    )
    assert rejected_ids.isdisjoint(row["id"] for row in rankings["boards"])
    assert rejected_ids.isdisjoint(row["source_id"] for row in derived["boards"])
    assert DEFAULT_SESSION_TTL_SECONDS == 2 * 60 * 60
    assert DEFAULT_MAX_SESSIONS == 1_000
