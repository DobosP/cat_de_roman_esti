"""Review and progression guards for authored, goal-independent discovery content."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_alchimie_discovery_world as B  # noqa: E402


@pytest.fixture
def candidate():
    return B.candidate()


@pytest.fixture
def reviewed_files(tmp_path, candidate):
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_bytes(B.json_bytes(candidate))
    files = [candidate_path]
    for role in ("factual", "quality"):
        path = tmp_path / f"{role}.json"
        path.write_bytes(B.json_bytes({
            "kind": B.REVIEW_KIND, "role": role, "reviewer": f"test-{role}",
            "candidate_sha256": B.file_sha(candidate_path),
            "world_verdict": "accept", "world_rationale": "Test fixture only.",
            "items": [{"id": r["id"], "verdict": "accept", "rationale": "Test fixture.",
                       "sources": ["https://example.test/recipe/" + r["id"]]}
                      for r in candidate["recipes"]],
            "concepts": [{"id": c["id"], "concept_sha256": B.concept_digest(c),
                          "verdict": "accept", "rationale": "Test concept fixture.",
                          "sources": ["https://example.test/concept/" + c["id"]]}
                         for c in candidate["concepts"]],
        }))
        files.append(path)
    return files


def mutate(path, change):
    value = json.loads(path.read_bytes())
    change(value)
    path.write_bytes(B.json_bytes(value))


def test_authored_world_has_broad_reachable_content(candidate):
    result = B.audit(candidate)
    assert result["discoverable_results"] >= 30
    assert result["opening_recipes"] >= 5
    assert result["results_with_alternatives"] >= 12
    assert result["supplies"] > result["starters"]
    assert result["closure_rounds"][-1]["total_owned"] == result["concepts"]
    assert set(result["closure_rounds"][0]["unlocked_tiers"]) == set()


def test_catalog_uses_same_recipes_for_every_optional_goal(reviewed_files):
    catalog = B.build_catalog(*reviewed_files)
    assert len({tuple(r["pair"]) for r in catalog["recipes"]}) == len(catalog["recipes"])
    assert all(set(g) == {"id", "title", "target"} for g in catalog["goals"])
    assert all("target" not in r and "goal" not in r for r in catalog["recipes"])
    assert {r["role"] for r in catalog["reviews"]} == {"factual", "quality"}
    assert all(r["sources"][0].startswith("https://example.test/")
               for r in catalog["recipes"])


def test_catalog_validates_with_serving_loader(reviewed_files):
    from cat_de_roman_esti.wordgames.discovery_world import validate_world

    catalog = B.build_catalog(*reviewed_files)
    world = validate_world(catalog)
    assert len(world.concepts) == B.audit(catalog)["concepts"]


def test_editorial_descriptions_keep_original_fixes_and_provenance(candidate):
    old = {c["id"]: c for c in json.loads(B.BASELINE.read_bytes())["concepts"]}
    current = {c["id"]: c for c in candidate["concepts"]}
    assert all(current[cid] == concept for cid, concept in old.items())
    for concept in candidate["concepts"]:
        assert concept["source"] == concept["snapshot"]["source"]
        assert concept["redistributable"] == concept["snapshot"]["redistributable"]


@pytest.mark.parametrize("role_index", [1, 2])
@pytest.mark.parametrize("change", [
    lambda r: r.update(candidate_sha256="0" * 64),
    lambda r: r["items"].pop(),
    lambda r: r["items"].append(copy.deepcopy(r["items"][0])),
    lambda r: r["items"][0].update(id="unknown"),
    lambda r: r["items"][0].update(verdict="hold"),
    lambda r: r["items"][0].update(verdict="reject"),
    lambda r: r["items"][0].update(rationale=""),
    lambda r: r["items"][0].update(sources=["file:///private"]),
    lambda r: r.update(world_verdict="reject"),
    lambda r: r.update(world_rationale=""),
])
def test_incomplete_stale_or_rejected_review_never_builds(reviewed_files, role_index, change):
    mutate(reviewed_files[role_index], change)
    with pytest.raises(ValueError):
        B.build_catalog(*reviewed_files)


def test_factual_acceptance_requires_checked_sources(reviewed_files):
    mutate(reviewed_files[1], lambda r: r["items"][0].update(sources=[]))
    with pytest.raises(ValueError, match="checked source"):
        B.build_catalog(*reviewed_files)


def test_same_reviewer_cannot_supply_both_judgments(reviewed_files):
    mutate(reviewed_files[2], lambda r: r.update(reviewer="test-factual"))
    with pytest.raises(ValueError, match="independent"):
        B.build_catalog(*reviewed_files)


def test_candidate_and_all_concept_metadata_are_source_bound(reviewed_files):
    mutate(reviewed_files[0], lambda r: r["concepts"][0].update(redistributable=True))
    with pytest.raises(ValueError, match="current editorial generator"):
        B.build_catalog(*reviewed_files)


def test_stale_kg_binding_rejected_before_review(reviewed_files):
    mutate(reviewed_files[0], lambda r: r["bindings"].update(kg_sha256="0" * 64))
    with pytest.raises(ValueError, match="stale source"):
        B.build_catalog(*reviewed_files)


def test_automatic_supplies_do_not_unlock_themselves(candidate):
    candidate["unlocks"][0]["after_discoveries"] = B.MAX_CONCEPTS
    with pytest.raises(ValueError, match="unreachable"):
        B.audit(candidate)


@pytest.mark.parametrize("mutation", [
    lambda c: c["recipes"].append({**c["recipes"][0], "id": "duplicate-pair"}),
    lambda c: c["recipes"][0].update(pair=[c["recipes"][0]["pair"][0]] * 2),
    lambda c: c["recipes"][0].update(result=c["world"]["starter_ids"][0]),
    lambda c: c["recipes"][0].update(result=c["unlocks"][0]["concept_ids"][0]),
    lambda c: c["unlocks"][0]["concept_ids"].append(c["world"]["starter_ids"][0]),
    lambda c: c["goals"][0].update(target=c["world"]["starter_ids"][0]),
])
def test_ambiguous_or_forged_progression_rejected(candidate, mutation):
    mutation(candidate)
    with pytest.raises(ValueError):
        B.audit(candidate)


@pytest.mark.parametrize("value", ["https://", "javascript:alert(1)", "http://x:bad",
                                  "https://user:pass@example.test", "https://x y"])
def test_source_urls_cannot_smuggle_other_schemes_or_credentials(value):
    assert B.valid_url(value) is False


def test_generate_candidate_cannot_replace_runtime_catalog(monkeypatch, tmp_path):
    target = tmp_path / "catalog.json"
    target.write_text("untouched")
    monkeypatch.setattr(B, "CATALOG", target)
    monkeypatch.setattr(sys, "argv", ["builder", "--candidate", str(target),
                                    "--generate-candidate"])
    with pytest.raises(ValueError, match="cannot replace package"):
        B.main()
    assert target.read_text() == "untouched"


def test_audit_output_cannot_replace_runtime_catalog(monkeypatch, tmp_path):
    target = tmp_path / "catalog.json"
    target.write_text("untouched")
    monkeypatch.setattr(B, "CATALOG", target)
    monkeypatch.setattr(sys, "argv", ["builder", "--candidate", str(tmp_path / "candidate.json"),
                                    "--generate-candidate", "--audit", str(target)])
    with pytest.raises(ValueError, match="audit cannot replace package"):
        B.main()
    assert target.read_text() == "untouched"


def test_rejected_review_does_not_touch_published_bytes(monkeypatch, tmp_path, reviewed_files):
    target = tmp_path / "catalog.json"
    target.write_text("untouched")
    monkeypatch.setattr(B, "CATALOG", target)
    mutate(reviewed_files[1], lambda r: r["items"][0].update(verdict="hold"))
    monkeypatch.setattr(sys, "argv", [
        "builder", "--candidate", str(reviewed_files[0]),
        "--factual-review", str(reviewed_files[1]), "--quality-review", str(reviewed_files[2]),
        "--write",
    ])
    with pytest.raises(ValueError):
        B.main()
    assert target.read_text() == "untouched"


@pytest.fixture
def final_files(tmp_path, reviewed_files):
    catalog = B.build_catalog(*reviewed_files)
    import hashlib

    catalog_sha = hashlib.sha256(B.json_bytes(catalog)).hexdigest()
    audit = tmp_path / "live-audit.json"
    audit.write_bytes(B.json_bytes({
        "verdict": "accept", "catalog_sha256": catalog_sha,
        "runtime_sources": [{"path": p, "sha256": B.file_sha(B.ROOT / p)}
                            for p in B.RUNTIME_SOURCES],
    }))
    reviews = []
    for role in ("factual", "quality"):
        path = tmp_path / f"final-{role}.json"
        path.write_bytes(B.json_bytes({
            "kind": B.FINAL_REVIEW_KIND, "role": role, "reviewer": f"test-{role}",
            "catalog_sha256": catalog_sha, "audit_sha256": B.file_sha(audit),
            "verdict": "accept", "rationale": "Test fixture final review.",
        }))
        reviews.append(path)
    return catalog, audit, *reviews


def test_complete_current_final_review_gate_accepts(final_files):
    B.confirm_final_reviews(*final_files)


def test_final_gate_and_actual_runtime_auditor_bind_the_same_files():
    import audit_alchimie_discovery_world as live

    assert set(B.RUNTIME_SOURCES) == set(live.RUNTIME_SOURCES)


@pytest.mark.parametrize("role_index", [2, 3])
@pytest.mark.parametrize("mutation", [
    lambda r: r.update(catalog_sha256="0" * 64),
    lambda r: r.update(audit_sha256="0" * 64),
    lambda r: r.update(verdict="hold"),
    lambda r: r.update(reviewer="unrelated-reviewer"),
    lambda r: r.update(rationale=""),
])
def test_stale_or_unapproved_final_review_rejected(final_files, role_index, mutation):
    mutate(final_files[role_index], mutation)
    with pytest.raises(ValueError):
        B.confirm_final_reviews(*final_files)


@pytest.mark.parametrize("mutation", [
    lambda r: r["runtime_sources"].pop(),
    lambda r: r["runtime_sources"][0].update(sha256="0" * 64),
    lambda r: r["runtime_sources"].append({"path": "unrelated", "sha256": "0" * 64}),
    lambda r: r.update(verdict="reject"),
    lambda r: r.update(catalog_sha256="0" * 64),
])
def test_final_gate_requires_every_current_runtime_source(final_files, mutation):
    mutate(final_files[1], mutation)
    with pytest.raises(ValueError):
        B.confirm_final_reviews(*final_files)


def test_package_write_requires_final_review_gate(monkeypatch, tmp_path, reviewed_files):
    target = tmp_path / "catalog.json"
    target.write_text("untouched")
    monkeypatch.setattr(B, "CATALOG", target)
    monkeypatch.setattr(sys, "argv", [
        "builder", "--candidate", str(reviewed_files[0]),
        "--factual-review", str(reviewed_files[1]), "--quality-review", str(reviewed_files[2]),
        "--write",
    ])
    with pytest.raises(ValueError, match="two final reviews"):
        B.main()
    assert target.read_text() == "untouched"


def test_expansion_preserves_all_prior_recipes_goals_and_collections(candidate):
    old = json.loads(B.BASELINE.read_bytes())
    before, after = B.audit(old), B.audit(candidate)
    assert after["concepts"] >= before["concepts"] + 25
    assert after["discoverable_results"] >= before["discoverable_results"] + 15
    assert after["recipes"] >= before["recipes"] + 30
    assert candidate["compatible_versions"] == B.compatible_versions(candidate)
    assert candidate["compatible_versions"][0]["recipe_hash"] == (
        "8b52b6ca9f7d83c804b8ed5cfb3489c6215b64b116583f1fc393569d551b182c"
    )
    assert {v["recipe_hash"] for v in candidate["compatible_versions"]} == {
        "8b52b6ca9f7d83c804b8ed5cfb3489c6215b64b116583f1fc393569d551b182c",
        "a5675c4564aea53abe956b8eacb609af65de08e42360f722bec4b6c3bb112b67",
    }


def drop_original_concept(candidate):
    original_id = json.loads(B.BASELINE.read_bytes())["concepts"][0]["id"]
    candidate["concepts"] = [c for c in candidate["concepts"] if c["id"] != original_id]


@pytest.mark.parametrize("mutation", [
    lambda c: c["recipes"].pop(0),
    lambda c: c["recipes"][0].update(result=c["recipes"][4]["result"]),
    lambda c: c["world"]["starter_ids"].pop(),
    lambda c: c["unlocks"][0].update(after_discoveries=4),
    lambda c: c["goals"].pop(0),
    drop_original_concept,
])
def test_incompatible_editorial_changes_cannot_claim_old_save_support(candidate, mutation):
    mutation(candidate)
    with pytest.raises(ValueError, match="original"):
        B.compatible_versions(candidate)


def test_archived_save_authority_is_bound_to_the_actual_reviewed_bytes(monkeypatch, tmp_path):
    edited = tmp_path / "edited-history.json"
    old = json.loads(B.BASELINE.read_bytes())
    old["recipes"][0]["result"] = "invented"
    edited.write_bytes(B.json_bytes(old))
    monkeypatch.setattr(B, "BASELINE", edited)
    with pytest.raises(ValueError, match="archive changed"):
        B.candidate()


@pytest.mark.parametrize("role_index", [1, 2])
@pytest.mark.parametrize("change", [
    lambda r: r.pop("concepts"),
    lambda r: r["concepts"].pop(),
    lambda r: r["concepts"].append(copy.deepcopy(r["concepts"][0])),
    lambda r: r["concepts"][0].update(id="unknown-concept"),
    lambda r: r["concepts"][0].update(concept_sha256="0" * 64),
    lambda r: r["concepts"][0].update(verdict="hold"),
    lambda r: r["concepts"][0].update(rationale=""),
    lambda r: r["concepts"][0].update(sources=["file:///private"]),
])
def test_every_concept_requires_complete_bound_review(reviewed_files, role_index, change):
    mutate(reviewed_files[role_index], change)
    with pytest.raises(ValueError, match="concept"):
        B.build_catalog(*reviewed_files)


def test_new_concept_cannot_forge_inherited_approval(reviewed_files):
    old_ids = {c["id"] for c in json.loads(B.BASELINE.read_bytes())["concepts"]}
    def forge(review):
        next(c for c in review["concepts"] if c["id"] not in old_ids).update(inherited=True)
    mutate(reviewed_files[1], forge)
    with pytest.raises(ValueError, match="inherited"):
        B.build_catalog(*reviewed_files)


def test_new_concept_needs_factual_sources(reviewed_files):
    old_ids = {c["id"] for c in json.loads(B.BASELINE.read_bytes())["concepts"]}
    def remove_sources(review):
        next(c for c in review["concepts"] if c["id"] not in old_ids).update(sources=[])
    mutate(reviewed_files[1], remove_sources)
    with pytest.raises(ValueError, match="checked sources"):
        B.build_catalog(*reviewed_files)


def test_reviewed_unchanged_concepts_can_inherit_without_new_source_claims(reviewed_files):
    old_ids = {c["id"] for c in json.loads(B.BASELINE.read_bytes())["concepts"]}
    def inherit(review):
        for row in review["concepts"]:
            if row["id"] in old_ids:
                row.update(inherited=True, sources=[])
    for path in reviewed_files[1:]:
        mutate(path, inherit)
    assert B.build_catalog(*reviewed_files)["concepts"]
