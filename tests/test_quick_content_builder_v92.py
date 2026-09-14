"""Editorial/reviewer custody and atomic publication of the quick-game supplement."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import build_quick_content_v92 as B
from scripts import content_file_transaction as T
from tests.current_content import CURRENT_CONTENT


def write(path: Path, value: dict) -> Path:
    path.write_bytes(B.Q.json_bytes(value))
    return path


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    artifact = B.candidate()
    candidate_path = write(tmp_path / "candidate.json", artifact)
    ids = [row["id"] for row in artifact["boards"]]
    paths = []
    for role in ("factual", "quality"):
        paths.append(
            write(
                tmp_path / f"{role}.json",
                {
                    "kind": B.REVIEW_KIND,
                    "role": role,
                    "reviewer": f"independent-{role}",
                    "candidate_sha256": B.file_sha(candidate_path),
                    "items": [
                        {
                            "id": item_id,
                            "verdict": "accept",
                            "rationale": "Exact visible board reviewed for its predicate.",
                            "sources": ["https://dexonline.ro/definitie/tren"],
                        }
                        for item_id in ids
                    ],
                },
            )
        )
    package = tmp_path / "package.json"
    package.write_bytes(b"original package bytes\n")
    monkeypatch.setattr(B.Q, "CATALOG_PATH", package)
    monkeypatch.setattr(B.Q, "CATALOG_SHA256", "")
    return SimpleNamespace(
        candidate=candidate_path,
        artifact=artifact,
        reviews=paths,
        proposal=tmp_path / "proposal.json",
        package=package,
        tmp=tmp_path,
        ids=ids,
    )


def build(e):
    return B.build_catalog(e.candidate, *e.reviews)


def args(e):
    return [
        "--candidate",
        str(e.candidate),
        "--factual-review",
        str(e.reviews[0]),
        "--quality-review",
        str(e.reviews[1]),
        "--proposal",
        str(e.proposal),
    ]


def change_review(e, role_index, mutate):
    value = json.loads(e.reviews[role_index].read_bytes())
    mutate(value)
    write(e.reviews[role_index], value)


def final_evidence(e, monkeypatch):
    catalog = build(e)
    write(e.proposal, catalog)
    catalog_sha = B.file_sha(e.proposal)
    monkeypatch.setattr(B.Q, "CATALOG_SHA256", catalog_sha)
    runtime_root = e.tmp / "runtime"
    for relative in B.RUNTIME_SOURCES:
        path = runtime_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"reviewed implementation: {relative}\n")
    monkeypatch.setattr(B, "ROOT", runtime_root)
    audit = write(
        e.tmp / "audit.json",
        {
            "kind": B.AUDIT_KIND,
            "passed": True,
            "catalog_sha256": catalog_sha,
            "candidate_sha256": catalog["candidate_sha256"],
            "bindings": B.Q.bindings(live=True),
            "runtime_sources": B.runtime_source_hashes(),
        },
    )
    finals = []
    for semantic in catalog["reviews"]:
        finals.append(
            write(
                e.tmp / f"final-{semantic['role']}.json",
                {
                    "kind": B.FINAL_KIND,
                    "role": semantic["role"],
                    "reviewer": semantic["reviewer"],
                    "catalog_sha256": catalog_sha,
                    "audit_sha256": B.file_sha(audit),
                    "verdict": "accept",
                    "rationale": "Exact live replay and frozen proposal accepted.",
                },
            )
        )
    return SimpleNamespace(catalog=catalog, audit=audit, reviews=finals, runtime=runtime_root)


def final_args(e, final):
    return [
        *args(e),
        "--write",
        "--live-audit",
        str(final.audit),
        "--final-factual-review",
        str(final.reviews[0]),
        "--final-quality-review",
        str(final.reviews[1]),
    ]


def test_candidate_reproducible_and_independent_copies():
    first = B.candidate()
    canonical = B.Q.json_bytes(first)
    first["boards"][0]["payload"]["members"][0] = "tampered"
    assert B.Q.json_bytes(B.candidate()) == canonical
    assert B.candidate()["bindings"]["editorial_source_sha256"] == B.file_sha(B.SOURCE_PATH)
    assert "pack_sha256" not in B.candidate()["bindings"]


def test_real_proposal_uses_reviewed_rows_ratings_and_provenance(evidence):
    catalog = build(evidence)
    expected = CURRENT_CONTENT.quick_counts["authored_by_game"]
    assert len(catalog["authored"]) == len(catalog["boards"]) == sum(expected.values())
    assert len([r for r in catalog["boards"] if r["game"] == "intrusul"]) == expected["intrusul"]
    assert catalog["authored"] == evidence.artifact["boards"]
    assert catalog["excluded"] == []
    assert {r["sha256"] for r in catalog["reviews"]} == {B.file_sha(p) for p in evidence.reviews}
    assert all(r["standard_score"] >= 55 for r in catalog["boards"])
    assert set(catalog["nodes"]) == {n for r in catalog["authored"] for n in B.Q.visible_ids(r)}
    assert evidence.package.read_bytes() == b"original package bytes\n"


def test_acceptance_is_intersection_and_exclusions_remain_visible(evidence):
    reject_id, hold_id = evidence.ids[:2]
    change_review(evidence, 0, lambda r: r["items"][0].update(verdict="reject"))
    change_review(evidence, 1, lambda r: r["items"][1].update(verdict="hold"))
    catalog = build(evidence)
    assert catalog["excluded"] == sorted([reject_id, hold_id])
    assert len(catalog["boards"]) == len(evidence.ids) - 2
    assert {r["id"] for r in catalog["authored"]} == set(evidence.ids) - {reject_id, hold_id}
    assert set(catalog["reviews"][0]) == {"role", "reviewer", "sha256"}


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(kind="wrong"),
        lambda r: r.update(role="quality"),
        lambda r: r.update(reviewer=""),
        lambda r: r.update(reviewer=" independent-factual "),
        lambda r: r.update(candidate_sha256="0" * 64),
        lambda r: r.pop("items"),
        lambda r: r["items"].pop(),
        lambda r: r["items"].append(copy.deepcopy(r["items"][0])),
        lambda r: r["items"][0].update(id="unknown"),
        lambda r: r["items"][0].update(id=[]),
        lambda r: r["items"][0].update(verdict="fix"),
        lambda r: r["items"][0].update(verdict=[]),
        lambda r: r["items"][0].update(rationale=" "),
        lambda r: r["items"][0].pop("sources"),
        lambda r: r["items"][0].update(sources=[]),
        lambda r: r["items"][0].update(sources=[42]),
        lambda r: r["items"][0].update(sources=["javascript:alert(1)"]),
        lambda r: r["items"][0].update(sources=["https://user:pass@example.org/"]),
        lambda r: r["items"][0].update(sources=["https://example.org/bad path"]),
    ],
)
def test_incomplete_stale_or_invalid_factual_review_fails_without_writes(evidence, mutate):
    change_review(evidence, 0, mutate)
    assert B.main(args(evidence)) == 2
    assert not evidence.proposal.exists()
    assert evidence.package.read_bytes() == b"original package bytes\n"


@pytest.mark.parametrize("role_index", [0, 1])
def test_missing_review_fails_closed(evidence, role_index):
    evidence.reviews[role_index].unlink()
    assert B.main(args(evidence)) == 2
    assert evidence.package.read_bytes() == b"original package bytes\n"


def test_same_reviewer_under_case_variant_is_not_independent(evidence):
    change_review(evidence, 1, lambda r: r.update(reviewer="INDEPENDENT-FACTUAL"))
    with pytest.raises(ValueError, match="independent"):
        build(evidence)


@pytest.mark.parametrize("change", ["source", "binding", "extra", "noncanonical"])
def test_candidate_tampering_cannot_be_restamped_by_reviewers(evidence, change):
    value = copy.deepcopy(evidence.artifact)
    if change == "source":
        value["boards"][0]["payload"]["group_label"] = "Changed predicate"
    elif change == "binding":
        value["bindings"]["kg_sha256"] = "0" * 64
    elif change == "extra":
        value["injected"] = True
    write(evidence.candidate, value)
    if change == "noncanonical":
        evidence.candidate.write_text(json.dumps(value))
    for index in range(2):
        change_review(
            evidence, index, lambda r: r.update(candidate_sha256=B.file_sha(evidence.candidate))
        )
    with pytest.raises(ValueError, match="editorial source or bindings"):
        build(evidence)


@pytest.mark.parametrize("change", ["duplicate", "shape", "unknown", "weak", "cross"])
def test_even_reviewed_bad_authoring_fails_live_graph_gate(evidence, monkeypatch, change):
    value = copy.deepcopy(evidence.artifact)
    row = value["boards"][0]
    if change == "duplicate":
        value["boards"][1]["id"] = row["id"]
    elif change == "shape":
        row["payload"]["members"] = row["payload"]["members"][:2]
    elif change == "unknown":
        row["payload"]["intruder"] = "n_nonexistent"
    elif change == "weak":
        row["payload"]["members"][0] = "n_v24_school_writing_caiet"
    else:
        row["payload"]["intruder"] = "n_v24_transport_terminals_gara"
    monkeypatch.setattr(B, "candidate", lambda: copy.deepcopy(value))
    write(evidence.candidate, value)
    ids = [r["id"] for r in value["boards"]]
    for index in range(2):
        review = json.loads(evidence.reviews[index].read_bytes())
        review["candidate_sha256"] = B.file_sha(evidence.candidate)
        for item, item_id in zip(review["items"], ids, strict=True):
            item["id"] = item_id
        write(evidence.reviews[index], review)
    with pytest.raises(ValueError):
        build(evidence)
    assert evidence.package.read_bytes() == b"original package bytes\n"


def test_dry_run_writes_only_reviewable_proposal(evidence):
    assert B.main(args(evidence)) == 0
    assert B.read_json(evidence.proposal) == build(evidence)
    assert evidence.package.read_bytes() == b"original package bytes\n"


@pytest.mark.parametrize("target", ["candidate", "package", "factual", "source"])
def test_proposal_cannot_overwrite_evidence_or_package(evidence, target):
    selected = {
        "candidate": evidence.candidate,
        "package": evidence.package,
        "factual": evidence.reviews[0],
        "source": B.SOURCE_PATH,
    }[target]
    before = selected.read_bytes()
    command = args(evidence)
    command[-1] = str(selected)
    assert B.main(command) == 2
    assert selected.read_bytes() == before


def test_write_cannot_bypass_final_audit(evidence):
    assert B.main([*args(evidence), "--write"]) == 2
    assert not evidence.proposal.exists()
    assert evidence.package.read_bytes() == b"original package bytes\n"


def test_final_acceptances_publish_exact_reviewed_proposal(evidence, monkeypatch):
    final = final_evidence(evidence, monkeypatch)
    assert B.main(final_args(evidence, final)) == 0
    assert evidence.package.read_bytes() == evidence.proposal.read_bytes()
    assert hashlib.sha256(evidence.package.read_bytes()).hexdigest() == B.Q.CATALOG_SHA256


@pytest.mark.parametrize("change", ["kind", "passed", "catalog", "candidate", "content", "runtime"])
def test_restamped_final_reviews_cannot_authorize_bad_live_audit(evidence, monkeypatch, change):
    final = final_evidence(evidence, monkeypatch)
    value = B.read_json(final.audit)
    if change == "kind":
        value["kind"] = "wrong"
    elif change == "passed":
        value["passed"] = 1
    elif change == "catalog":
        value["catalog_sha256"] = "0" * 64
    elif change == "candidate":
        value["candidate_sha256"] = "0" * 64
    elif change == "content":
        value["bindings"]["kg_sha256"] = "0" * 64
    else:
        value["runtime_sources"].pop(next(iter(value["runtime_sources"])))
    write(final.audit, value)
    for path in final.reviews:
        value = B.read_json(path)
        value["audit_sha256"] = B.file_sha(final.audit)
        write(path, value)
    assert B.main(final_args(evidence, final)) == 2
    assert evidence.package.read_bytes() == b"original package bytes\n"


@pytest.mark.parametrize(
    "change", ["kind", "role", "reviewer", "catalog", "audit", "verdict", "reason"]
)
def test_final_review_must_bind_exact_accepted_artifacts(evidence, monkeypatch, change):
    final = final_evidence(evidence, monkeypatch)
    value = B.read_json(final.reviews[0])
    key, replacement = {
        "kind": ("kind", "wrong"),
        "role": ("role", "quality"),
        "reviewer": ("reviewer", "some-other-reviewer"),
        "catalog": ("catalog_sha256", "0" * 64),
        "audit": ("audit_sha256", "0" * 64),
        "verdict": ("verdict", "hold"),
        "reason": ("rationale", " "),
    }[change]
    value[key] = replacement
    write(final.reviews[0], value)
    assert B.main(final_args(evidence, final)) == 2
    assert evidence.package.read_bytes() == b"original package bytes\n"


@pytest.mark.parametrize(
    "change", ["runtime", "missing_runtime", "pin", "proposal", "missing_final"]
)
def test_changed_implementation_or_missing_evidence_blocks_write(evidence, monkeypatch, change):
    final = final_evidence(evidence, monkeypatch)
    runtime_path = final.runtime / B.RUNTIME_SOURCES[0]
    if change == "runtime":
        runtime_path.write_text("new unreviewed implementation")
    elif change == "missing_runtime":
        runtime_path.unlink()
    elif change == "pin":
        monkeypatch.setattr(B.Q, "CATALOG_SHA256", "0" * 64)
    elif change == "proposal":
        evidence.proposal.write_bytes(b"changed proposal\n")
    else:
        final.reviews[0].unlink()
    assert B.main(final_args(evidence, final)) == 2
    assert evidence.package.read_bytes() == b"original package bytes\n"


def test_failed_atomic_replace_keeps_old_package(evidence, monkeypatch):
    final = final_evidence(evidence, monkeypatch)
    files_before = set(evidence.tmp.iterdir())

    def fail_replace(source, destination):
        raise OSError("simulated interrupted replacement")

    monkeypatch.setattr(T.os, "replace", fail_replace)
    assert B.main(final_args(evidence, final)) == 2
    assert evidence.package.read_bytes() == b"original package bytes\n"
    assert set(evidence.tmp.iterdir()) == files_before


def test_generate_candidate_is_separate_and_cannot_target_package(evidence):
    generated = evidence.tmp / "generated-candidate.json"
    assert B.main(["--generate-candidate", str(generated)]) == 0
    assert generated.read_bytes() == evidence.candidate.read_bytes()
    assert B.main(["--generate-candidate", str(generated), "--write"]) == 2
    assert B.main(["--generate-candidate", str(evidence.package)]) == 2
    assert evidence.package.read_bytes() == b"original package bytes\n"
