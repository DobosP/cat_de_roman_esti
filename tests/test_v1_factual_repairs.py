"""Pinned factual migration rejects unreviewed changes and preserves exact history."""

from __future__ import annotations

import copy
import gzip
import json
import shutil
from collections import Counter

import pytest

from scripts import apply_v1_factual_repairs as repair


def _write(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _read(path):
    return json.loads(path.read_bytes())


@pytest.fixture
def isolated(tmp_path):
    archive = repair.ROOT / repair.REVIEW_DIR / "kg-before-v1.json.gz"
    baseline = (gzip.decompress(archive.read_bytes()) if archive.exists()
                else (repair.ROOT / repair.FIXTURE_PATHS[0]).read_bytes())
    assert repair.sha256(baseline) == repair.BASELINE_KG_SHA256
    for relative in repair.FIXTURE_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(baseline)
    for relative in (repair.PROPOSAL_PATH, *repair.REVIEW_PATHS.values(), repair.RUBRIC_PATH):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repair.ROOT / relative, path)
    return tmp_path


def _snapshot(root):
    return {path: (root / path).read_bytes() for path in repair.FIXTURE_PATHS}


def _reject(root, match):
    before = _snapshot(root)
    with pytest.raises(ValueError, match=match):
        repair.apply_repairs(root=root, write=True)
    assert _snapshot(root) == before


def test_dry_run_validates_without_mutating_any_input(isolated):
    originals = {path: path.read_bytes() for path in isolated.rglob("*.json")}
    plan = repair.apply_repairs(root=isolated)
    assert not plan.report["written"]
    assert plan.report["fixture_validation"] == "GREEN"
    assert not plan.report["puzzles_regenerated"]
    assert originals == {path: path.read_bytes() for path in originals}
    assert repair.sha256(plan.candidate) != repair.BASELINE_KG_SHA256


def test_exact_write_preserves_puzzles_order_and_every_unreviewed_field(isolated):
    original = _read(isolated / repair.FIXTURE_PATHS[0])
    proposal = _read(isolated / repair.PROPOSAL_PATH)
    plan = repair.apply_repairs(root=isolated, write=True)
    assert plan.report["written"]
    assert set(_snapshot(isolated).values()) == {plan.candidate}
    assert b"\r\n" not in plan.candidate and plan.candidate.endswith(b"\n")
    after = json.loads(plan.candidate)
    expected = copy.deepcopy(original)
    for change in proposal["changes"]:
        key = "kg_nodes" if change["kind"] == "node" else "kg_edges"
        if change["operation"] == "remove_exact_record":
            expected[key] = [row for row in expected[key] if row["id"] != change["id"]]
        else:
            row = next(row for row in expected[key] if row["id"] == change["id"])
            row[change["field"]] = change["after"][change["field"]]
    for row in expected["kg_nodes"]:
        if row["id"] in {"n_ftv_operatiunea_monstrul", "n_ftv_dem_radulescu"}:
            row["degree"] -= 1
    assert after["kg_nodes"] == expected["kg_nodes"]
    assert after["kg_edges"] == expected["kg_edges"]
    assert after["kg_puzzles"] == original["kg_puzzles"]
    assert len(after["kg_puzzles"]) == 180
    assert len(after["kg_edges"]) == 9458
    assert after["meta"]["counts"]["edges"] == 9458
    assert after["meta"]["build_version"] == "fixture-v1-reviewed-content"
    assert after["meta"]["generated_at"] == original["meta"]["generated_at"]
    counts = Counter(endpoint for edge in after["kg_edges"]
                     for endpoint in (edge["src_id"], edge["dst_id"]))
    for item in plan.report["degree_changes"]:
        assert item["after"] == counts[item["id"]] == item["before"] - 1
    _reject(isolated, "stale baseline")  # A second apply must not edit a different baseline.


@pytest.mark.parametrize("tamper", ["one_mirror", "both_mirrors", "proposal", "rubric"])
def test_stale_bytes_fail_closed(isolated, tamper):
    if tamper == "one_mirror":
        path = isolated / repair.FIXTURE_PATHS[1]
        path.write_bytes(path.read_bytes() + b"\n")
        match = "baseline mirrors differ"
    elif tamper == "both_mirrors":
        for relative in repair.FIXTURE_PATHS:
            path = isolated / relative
            path.write_bytes(path.read_bytes() + b"\n")
        match = "stale baseline"
    else:
        path = isolated / (repair.PROPOSAL_PATH if tamper == "proposal" else repair.RUBRIC_PATH)
        path.write_bytes(path.read_bytes() + b"\n")
        match = "proposal SHA256" if tamper == "proposal" else "rubric binding"
    _reject(isolated, match)


@pytest.mark.parametrize("tamper,match", [
    ("missing", "incomplete or extra"), ("extra", "incomplete or extra"),
    ("duplicate", "duplicate.*ID"), ("verdict", "unapproved factual verdict"),
    ("overall_verdict", "unapproved overall"), ("role", "wrong review role"),
    ("author", "independent"), ("same_reviewer", "independent"),
    ("empty_reviewer", "reviewer missing"), ("candidate", "stale candidate"),
    ("kg", "stale candidate"), ("before", "before_record_sha256 mismatch"),
    ("after", "after_record_sha256 mismatch"), ("missing_null", "after_record_sha256 mismatch"),
    ("sources", "evidence missing"),
])
def test_reviews_must_be_complete_current_independent_and_unanimous(isolated, tamper, match):
    path = isolated / repair.REVIEW_PATHS["factual"]
    review = _read(path)
    if tamper == "missing":
        review["items"].pop()
    elif tamper == "extra":
        review["items"].append({**review["items"][0], "id": "unreviewed-extra"})
    elif tamper == "duplicate":
        review["items"].append(copy.deepcopy(review["items"][0]))
    elif tamper == "verdict":
        review["items"][0]["verdict"] = "revise"
    elif tamper == "overall_verdict":
        review["verdict"] = "reject"
    elif tamper == "role":
        review["role"] = "quality"
    elif tamper == "author":
        review["reviewer"] = _read(isolated / repair.PROPOSAL_PATH)["author"]
    elif tamper == "same_reviewer":
        review["reviewer"] = _read(isolated / repair.REVIEW_PATHS["quality"])["reviewer"]
    elif tamper == "empty_reviewer":
        review["reviewer"] = " "
    elif tamper in {"candidate", "kg"}:
        review[f"{tamper}_sha256"] = "0" * 64
    elif tamper in {"before", "after"}:
        review["items"][0][f"{tamper}_record_sha256"] = "0" * 64
    elif tamper == "missing_null":
        next(row for row in review["items"] if row["id"] == "de427").pop("after_record_sha256")
    else:
        review["items"][0]["sources"] = []
    _write(path, review)
    _reject(isolated, match)


@pytest.mark.parametrize("tamper,match", [
    ("partial_before", "complete before record mismatch"),
    ("stale_before", "complete before record mismatch"),
    ("extra_field", "exceeds approved field"),
    ("wrong_field", "unapproved operation or field"),
    ("wrong_id", "exact seven IDs"),
])
def test_record_and_scope_guards_even_if_proposal_pin_is_advanced(isolated, monkeypatch,
                                                                tamper, match):
    path = isolated / repair.PROPOSAL_PATH
    proposal = _read(path)
    row = proposal["changes"][0]
    if tamper == "partial_before":
        row["before"].pop("aliases")
    elif tamper == "stale_before":
        row["before"]["salience"] += 0.01
    elif tamper == "extra_field":
        row["after"]["aliases"].append("unreviewed alias")
    elif tamper == "wrong_field":
        row["field"] = "aliases"
    else:
        row["id"] = "unreviewed-node"
    _write(path, proposal)
    monkeypatch.setattr(repair, "PROPOSAL_SHA256", repair.sha256(path.read_bytes()))
    _reject(isolated, match)


def test_real_validator_rejects_a_broken_puzzle_without_regeneration(isolated):
    before = _snapshot(isolated)
    plan = repair.prepare_repairs(root=isolated)
    corrupt = json.loads(plan.candidate)
    corrupt["kg_puzzles"][0]["optimal_hops"] += 1
    with pytest.raises(ValueError, match="fixture validation failed.*puzzle"):
        repair.validate_candidate(json.dumps(corrupt).encode("utf-8"))
    assert _snapshot(isolated) == before
    assert corrupt["kg_puzzles"][0]["optimal_hops"] != json.loads(plan.candidate)[
        "kg_puzzles"][0]["optimal_hops"]


def test_second_write_failure_rolls_back_both_exact_originals(isolated, monkeypatch):
    before = _snapshot(isolated)
    write = repair.atomic_write
    calls = 0

    def fail_second(path, blob):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected second mirror write failure")
        write(path, blob)

    monkeypatch.setattr(repair, "atomic_write", fail_second)
    with pytest.raises(OSError, match="injected second mirror"):
        repair.apply_repairs(root=isolated, write=True)
    assert _snapshot(isolated) == before


def test_post_write_validation_failure_rolls_back_every_byte(isolated, monkeypatch):
    validate = repair._validate_pair

    def fail_installed(paths):
        validate(paths)
        if paths[0] == isolated / repair.FIXTURE_PATHS[0]:
            raise ValueError("injected installed fixture validation failure")

    monkeypatch.setattr(repair, "_validate_pair", fail_installed)
    _reject(isolated, "injected installed fixture")


def test_concurrent_review_edit_is_not_overwritten_and_prevents_install(isolated, monkeypatch):
    validate = repair.validate_candidate
    path = isolated / repair.REVIEW_PATHS["factual"]
    concurrent = path.read_bytes() + b"\n"

    def change_review(blob):
        validate(blob)
        path.write_bytes(concurrent)

    monkeypatch.setattr(repair, "validate_candidate", change_review)
    _reject(isolated, "input changed during verification")
    assert path.read_bytes() == concurrent


def test_json_duplicate_verdict_key_is_rejected(isolated):
    path = isolated / repair.REVIEW_PATHS["factual"]
    raw = path.read_text(encoding="utf-8").replace(
        '\"verdict\": \"accept\"', '\"verdict\": \"reject\", \"verdict\": \"accept\"', 1,
    )
    path.write_bytes(raw.encode("utf-8"))
    _reject(isolated, "duplicate JSON key")


def test_cli_default_exports_candidate_but_never_edits_served_mirrors(isolated, tmp_path,
                                                                   monkeypatch, capsys):
    before = _snapshot(isolated)
    monkeypatch.setattr(repair, "ROOT", isolated)
    output = tmp_path.parent / (tmp_path.name + "-candidate.json")
    assert repair.main(["--candidate-output", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["written"] is False
    assert repair.sha256(output.read_bytes()) != repair.BASELINE_KG_SHA256
    assert _snapshot(isolated) == before
    with pytest.raises(SystemExit):
        repair.main(["--candidate-output", str(isolated / repair.FIXTURE_PATHS[0])])
    assert _snapshot(isolated) == before
