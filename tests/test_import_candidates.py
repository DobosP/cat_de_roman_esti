"""Fail-close verification-contract tests for ``scripts/import_candidates.py``."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import import_candidates  # noqa: E402


def _artifacts() -> tuple[dict, dict, dict]:
    candidate = {
        "nodes": [
            {
                "id": "n_candidate",
                "label": "Candidat",
                "type": "concept",
                "description": "Concept verificat.",
            }
        ],
        "edges": [
            {
                "src": "n_candidate",
                "dst": "n_existing",
                "relation": "related_to",
                "weight": 0.8,
            }
        ],
        "conexiuni": [
            {
                "difficulty": "normal",
                "groups": [],
            }
        ],
        "contexto": [],
        "lant": [],
        "alchimie": [],
    }
    factual = {
        "category": "istorie",
        "reviewed_refs": [
            "n_candidate",
            "edge:n_candidate->n_existing",
            "conexiuni[0]",
        ],
        "issues": [],
        "coverage_note": "Toate referințele brute au fost verificate.",
    }
    quality = {
        "category": "istorie",
        "instances": [
            {
                "ref": "conexiuni[0]",
                "verdict": "keep",
                "note": "Partiție clară pentru publicul țintă.",
            }
        ],
        "coverage_note": "A fost evaluată singura instanță.",
    }
    return candidate, factual, quality


def _write_batch(
    tmp_path: Path,
    candidate: dict | None = None,
    factual: dict | None = None,
    quality: dict | None = None,
) -> Path:
    defaults = _artifacts()
    payloads = [
        defaults[0] if candidate is None else candidate,
        defaults[1] if factual is None else factual,
        defaults[2] if quality is None else quality,
    ]
    payloads = copy.deepcopy(payloads)
    batch = tmp_path / "batch"
    category = batch / "istorie"
    category.mkdir(parents=True, exist_ok=True)
    candidate_bytes = json.dumps(payloads[0], ensure_ascii=False).encode("utf-8")
    (category / "candidates.json").write_bytes(candidate_bytes)
    binding = f"sha256:{hashlib.sha256(candidate_bytes).hexdigest()}"
    for name, payload in zip(
        ("verify_factual.json", "verify_quality.json"), payloads[1:], strict=True
    ):
        payload["candidate_sha256"] = binding
        (category / name).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    return batch


def _assert_contract_error(batch: Path, expected: str) -> None:
    with pytest.raises(SystemExit) as exc:
        import_candidates.preflight_candidates(batch)
    message = str(exc.value)
    assert message.startswith("invalid candidate verification contract:")
    assert expected in message


def test_preflight_accepts_complete_artifacts_with_explicit_block_and_drop(tmp_path):
    candidate, factual, quality = _artifacts()
    candidate["edges"].append(
        {
            "src": "n_existing",
            "dst": "n_candidate",
            "relation": "related_to",
            "weight": 0.7,
        }
    )
    factual["reviewed_refs"].append("edge:n_existing->n_candidate")
    factual["issues"] = [
        {
            "ref": "edge:n_candidate->n_existing",
            "severity": "block",
            "issue": "Relația în această direcție nu este susținută.",
        }
    ]
    quality["instances"][0]["verdict"] = "drop"
    batch = _write_batch(tmp_path, candidate, factual, quality)

    bundles = import_candidates.preflight_candidates(batch)
    prepared, _ = import_candidates._prepare_candidate(
        bundles["istorie"]["cand"],
        bundles["istorie"]["factual"]["issues"],
        set(),
    )

    assert [
        (edge["src"], edge["dst"]) for edge in prepared["edges"]
    ] == [("n_existing", "n_candidate")]


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("category", "category must equal"),
        ("coverage", "coverage_note must be a nonblank string"),
        ("missing_ref", "reviewed_refs missing"),
        ("extra_ref", "reviewed_refs contains unknown refs"),
        ("duplicate_ref", "reviewed_refs contains duplicates"),
        ("blank_issue_ref", ".ref must be a canonical nonblank ref"),
        ("unknown_issue_ref", ".ref is unknown"),
        ("unknown_severity", ".severity is unknown"),
        ("blank_issue", ".issue must be a nonblank string"),
        ("unresolved_fix", "unresolved factual fix"),
    ],
)
def test_factual_contract_rejects_partial_or_unknown_verification(tmp_path, case, expected):
    candidate, factual, quality = _artifacts()
    if case == "category":
        factual["category"] = "sport"
    elif case == "coverage":
        factual["coverage_note"] = " "
    elif case == "missing_ref":
        factual["reviewed_refs"].pop()
    elif case == "extra_ref":
        factual["reviewed_refs"].append("n_unknown")
    elif case == "duplicate_ref":
        factual["reviewed_refs"].append(factual["reviewed_refs"][0])
    else:
        issue = {
            "ref": "n_candidate",
            "severity": "note",
            "issue": "Observație verificată.",
        }
        if case == "unknown_issue_ref":
            issue["ref"] = "n_unknown"
        elif case == "blank_issue_ref":
            issue["ref"] = " "
        elif case == "unknown_severity":
            issue["severity"] = "warn"
        elif case == "blank_issue":
            issue["issue"] = " "
        elif case == "unresolved_fix":
            issue["severity"] = "fix"
        factual["issues"] = [issue]

    batch = _write_batch(tmp_path, candidate, factual, quality)
    _assert_contract_error(batch, expected)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("category", "category must equal"),
        ("coverage", "coverage_note must be a nonblank string"),
        ("missing_row", "instances missing"),
        ("extra_row", ".ref is unknown"),
        ("duplicate_row", "duplicate instance refs"),
        ("blank_ref", ".ref must be a canonical nonblank ref"),
        ("unknown_verdict", ".verdict is unknown"),
        ("blank_note", ".note must be a nonblank string"),
        ("unresolved_fix", "unresolved quality fix"),
    ],
)
def test_quality_contract_requires_exactly_one_resolved_row_per_instance(
    tmp_path, case, expected
):
    candidate, factual, quality = _artifacts()
    if case == "category":
        quality["category"] = "sport"
    elif case == "coverage":
        quality["coverage_note"] = ""
    elif case == "missing_row":
        quality["instances"] = []
    elif case == "extra_row":
        quality["instances"].append(
            {"ref": "lant[0]", "verdict": "drop", "note": "În plus."}
        )
    elif case == "duplicate_row":
        quality["instances"].append(copy.deepcopy(quality["instances"][0]))
    elif case == "blank_ref":
        quality["instances"][0]["ref"] = " "
    elif case == "unknown_verdict":
        quality["instances"][0]["verdict"] = "maybe"
    elif case == "blank_note":
        quality["instances"][0]["note"] = " "
    elif case == "unresolved_fix":
        quality["instances"][0]["verdict"] = "fix"

    batch = _write_batch(tmp_path, candidate, factual, quality)
    _assert_contract_error(batch, expected)


@pytest.mark.parametrize("filename", ["verify_factual.json", "verify_quality.json"])
def test_preflight_rejects_missing_verification_artifact(tmp_path, filename):
    batch = _write_batch(tmp_path)
    (batch / "istorie" / filename).unlink()

    _assert_contract_error(batch, f"missing {filename}")


def test_preflight_rejects_artifacts_after_candidate_content_changes(tmp_path):
    batch = _write_batch(tmp_path)
    path = batch / "istorie" / "candidates.json"
    candidate = json.loads(path.read_text(encoding="utf-8"))
    candidate["conexiuni"][0]["difficulty"] = "greu"
    path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")

    _assert_contract_error(batch, "candidate_sha256 does not match candidates.json")


def test_factual_coverage_is_bound_to_raw_ids_before_alias_mapping(tmp_path):
    candidate, factual, quality = _artifacts()
    raw_id = "n_ftv_cristian_mungiu"
    candidate["nodes"][0]["id"] = raw_id
    candidate["edges"][0]["src"] = raw_id
    factual["reviewed_refs"] = [
        raw_id,
        f"edge:{raw_id}->n_existing",
        "conexiuni[0]",
    ]
    batch = _write_batch(tmp_path, candidate, factual, quality)

    bundles = import_candidates.preflight_candidates(batch)
    assert raw_id in bundles["istorie"]["node_refs"]

    factual["reviewed_refs"][0] = "n_cristian_mungiu"
    _write_batch(tmp_path, candidate, factual, quality)
    _assert_contract_error(batch, "reviewed_refs missing")


def test_duplicate_raw_refs_fail_instead_of_sharing_one_review_entry(tmp_path):
    candidate, factual, quality = _artifacts()
    candidate["edges"].append(copy.deepcopy(candidate["edges"][0]))
    batch = _write_batch(tmp_path, candidate, factual, quality)

    _assert_contract_error(batch, "raw references are not unique")


def test_raw_candidate_requires_every_declared_content_array(tmp_path):
    candidate, factual, quality = _artifacts()
    del candidate["contexto"]
    batch = _write_batch(tmp_path, candidate, factual, quality)

    _assert_contract_error(batch, "contexto must be an array")


def test_blocked_node_removes_edges_and_instances_that_touch_it():
    candidate, factual, _ = _artifacts()
    candidate["conexiuni"][0]["groups"] = [{"tiles": ["n_candidate"]}]
    factual["issues"] = [
        {
            "ref": "n_candidate",
            "severity": "block",
            "issue": "Nodul nu este importabil.",
        }
    ]

    prepared, factual_by_game = import_candidates._prepare_candidate(
        candidate,
        factual["issues"],
        {"n_candidate"},
    )

    assert prepared["nodes"] == []
    assert prepared["edges"] == []
    assert factual_by_game["conexiuni"][0] == "block"


def test_invalid_verification_aborts_before_graph_or_pack_mutation(tmp_path, monkeypatch):
    candidate, factual, quality = _artifacts()
    factual["reviewed_refs"].pop()
    batch = _write_batch(tmp_path, candidate, factual, quality)
    pack_copies = (tmp_path / "package-pack.json", tmp_path / "test-pack.json")
    for pack in pack_copies:
        pack.write_bytes(b"unchanged")

    densify_called = False

    def unexpected_densify(*_args, **_kwargs):
        nonlocal densify_called
        densify_called = True
        raise AssertionError("preflight must run before densify")

    monkeypatch.setattr(import_candidates.densify_content, "run", unexpected_densify)
    monkeypatch.setattr(import_candidates, "PACK_COPIES", pack_copies)

    with pytest.raises(SystemExit, match="invalid candidate verification contract"):
        import_candidates.main(["import_candidates.py", "--dir", str(batch)])

    assert densify_called is False
    assert [pack.read_bytes() for pack in pack_copies] == [b"unchanged", b"unchanged"]
    assert not (batch / "curation_report.txt").exists()
