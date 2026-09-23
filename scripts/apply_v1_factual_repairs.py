#!/usr/bin/env python3
"""Apply the seven exact V1 factual repairs; default is a validated dry run.

Both served fixture mirrors are replaced atomically with verified rollback on
failure. Existing puzzles are preserved: a broken route rejects the repair and
never triggers puzzle regeneration. Other release bindings need separate gates.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import validate_fixture as validator  # noqa: E402
from scripts.content_file_transaction import atomic_write, file_transaction  # noqa: E402
from scripts.densify_content import remove_reviewed_edges  # noqa: E402

REVIEW_DIR = Path("docs/reviews/v1-testing-release/content")
PROPOSAL_PATH = REVIEW_DIR / "factual-repair-proposal.json"
REVIEW_PATHS = {
    role: REVIEW_DIR / f"factual-repair-{role}-review.json"
    for role in ("factual", "quality")
}
FIXTURE_PATHS = (
    Path("cat_de_roman_esti/fixtures/kg_sample.json"),
    Path("tests/fixtures/kg_sample.json"),
)
RUBRIC_PATH = Path("docs/CRITIQUE_RUBRIC.md")
PROPOSAL_SHA256 = "18c9d50981c9b6cb4288f928174ba0f4dfafd798ef846dd2361a22193f488717"
BASELINE_KG_SHA256 = "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109"
BUILD_VERSION = "fixture-v1-reviewed-content"
NOTE = (
    "V1: three reviewed description corrections, three historical Cristina Neagu "
    "relationship labels, and removal of one unsupported casting link. "
    "All 180 existing puzzles are preserved and validated without regeneration."
)
EXPECTED_CHANGES = {
    "n_v20geo_crucea_caraiman": ("node", "replace_field", "description"),
    "n_v17art_muzeul_satului": ("node", "replace_field", "description"),
    "n_ateneul_roman": ("node", "replace_field", "description"),
    "de1218": ("edge", "replace_field", "label_ro"),
    "de2664": ("edge", "replace_field", "label_ro"),
    "de2665": ("edge", "replace_field", "label_ro"),
    "de427": ("edge", "remove_exact_record", None),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def record_sha256(record: object) -> str:
    return sha256(json.dumps(record, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8"))


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _document(blob: bytes) -> dict:
    data = json.loads(blob, object_pairs_hook=_unique_object)
    _require(isinstance(data, dict), "expected a JSON object")
    return data


def _index(rows: object, description: str) -> dict[str, dict]:
    _require(isinstance(rows, list), f"{description} must be a list")
    result = {}
    for row in rows:
        _require(isinstance(row, dict) and isinstance(row.get("id"), str),
                 f"{description} must contain records with string IDs")
        _require(row["id"] not in result, f"duplicate {description} ID: {row['id']}")
        result[row["id"]] = row
    return result


def _validate_pair(paths: tuple[Path, Path]) -> None:
    # The committed validator compares against two module-level canonical paths.
    # Bind those to the isolated candidate pair (dry run) or transaction pair.
    with patch.object(validator, "PACKAGE_FIXTURE", paths[0]), \
            patch.object(validator, "TESTS_FIXTURE", paths[1]):
        errors = validator.validate(paths[0])
    _require(not errors, "fixture validation failed: " + "; ".join(errors))
    _require(paths[0].read_bytes() == paths[1].read_bytes(), "fixture mirrors differ")


def validate_candidate(blob: bytes) -> None:
    """Run the real fixture validator without writing either served mirror."""
    with tempfile.TemporaryDirectory(prefix="v1-factual-candidate-") as directory:
        paths = (Path(directory) / "package.json", Path(directory) / "tests.json")
        for path in paths:
            path.write_bytes(blob)
        _validate_pair(paths)


@dataclass(frozen=True)
class RepairPlan:
    candidate: bytes
    report: dict
    inputs: dict[Path, bytes]


def _unchanged(inputs: dict[Path, bytes], *, exclude: tuple[Path, ...] = ()) -> None:
    for path, original in inputs.items():
        if path not in exclude:
            _require(path.read_bytes() == original, f"input changed during verification: {path}")


def prepare_repairs(*, root: Path = ROOT) -> RepairPlan:
    """Return a validated candidate and report, with no served-file mutations."""
    paths = (*FIXTURE_PATHS, PROPOSAL_PATH, *REVIEW_PATHS.values(), RUBRIC_PATH)
    inputs = {root / path: (root / path).read_bytes() for path in paths}
    baseline = inputs[root / FIXTURE_PATHS[0]]
    _require(baseline == inputs[root / FIXTURE_PATHS[1]], "baseline mirrors differ")
    _require(sha256(baseline) == BASELINE_KG_SHA256, "stale baseline KG SHA256")
    candidate_blob = inputs[root / PROPOSAL_PATH]
    _require(sha256(candidate_blob) == PROPOSAL_SHA256, "proposal SHA256 changed")
    proposal = _document(candidate_blob)
    _require(proposal.get("kg_sha256") == BASELINE_KG_SHA256, "proposal KG binding differs")
    author = proposal.get("author")
    _require(isinstance(author, str) and bool(author.strip()), "proposal author missing")
    changes = _index(proposal.get("changes"), "proposal changes")
    _require(set(changes) == set(EXPECTED_CHANGES), "proposal must contain exact seven IDs")
    graph = _document(baseline)
    nodes = _index(graph["kg_nodes"], "baseline nodes")
    edges = _index(graph["kg_edges"], "baseline edges")
    for item_id, expected in EXPECTED_CHANGES.items():
        change = changes[item_id]
        _require((change.get("kind"), change.get("operation"), change.get("field")) == expected,
                 f"unapproved operation or field: {item_id}")
        current = (nodes if expected[0] == "node" else edges).get(item_id)
        before = change.get("before")
        _require(isinstance(before, dict) and current is not None and
                 record_sha256(before) == record_sha256(current),
                 f"complete before record mismatch: {item_id}")
        _require(record_sha256(before) == change.get("before_record_sha256"),
                 f"before record digest mismatch: {item_id}")
        after = change.get("after")
        if expected[1] == "remove_exact_record":
            _require(after is None and change.get("after_record_sha256") is None,
                     "removal must have null after record and digest")
        else:
            _require(isinstance(after, dict) and set(after) == set(before),
                     f"complete after record missing: {item_id}")
            field = expected[2]
            _require(isinstance(after[field], str) and bool(after[field].strip()),
                     f"replacement text missing: {item_id}")
            _require({key for key in before if before[key] != after[key]} == {field},
                     f"replacement exceeds approved field: {item_id}")
            _require(record_sha256(after) == change.get("after_record_sha256"),
                     f"after record digest mismatch: {item_id}")
    reviewers = {author.strip().casefold()}
    for role, relative in REVIEW_PATHS.items():
        review = _document(inputs[root / relative])
        _require(review.get("role") == role, f"wrong review role: {role}")
        _require("verdict" not in review or review["verdict"] == "accept",
                 f"unapproved overall review verdict: {role}")
        reviewer = review.get("reviewer")
        _require(isinstance(reviewer, str) and bool(reviewer.strip()),
                 f"reviewer missing: {role}")
        identity = reviewer.strip().casefold()
        _require(identity not in reviewers,
                 "reviewers must be independent of author and each other")
        reviewers.add(identity)
        _require(review.get("candidate_sha256") == PROPOSAL_SHA256 and
                 review.get("kg_sha256") == BASELINE_KG_SHA256,
                 f"stale candidate or KG review binding: {role}")
        if role == "quality":
            _require(review.get("rubric_sha256") == sha256(inputs[root / RUBRIC_PATH]),
                     "stale quality rubric binding")
        rows = _index(review.get("items"), f"{role} review items")
        _require(set(rows) == set(EXPECTED_CHANGES), f"incomplete or extra {role} review IDs")
        for item_id, row in rows.items():
            _require(row.get("verdict") == "accept", f"unapproved {role} verdict: {item_id}")
            for field in ("before_record_sha256", "after_record_sha256"):
                _require(field in row and row[field] == changes[item_id].get(field),
                         f"{role} {field} mismatch: {item_id}")
            _require(bool(row.get("rationale")) and isinstance(row.get("sources"), list)
                     and bool(row["sources"]) and all(isinstance(url, str) and url.strip()
                                                     for url in row["sources"]),
                     f"{role} review evidence missing: {item_id}")
    result = copy.deepcopy(graph)
    for kind, key in (("node", "kg_nodes"), ("edge", "kg_edges")):
        result[key] = [copy.deepcopy(changes[row["id"]]["after"])
                       if row["id"] in changes and changes[row["id"]]["kind"] == kind
                       and changes[row["id"]]["operation"] == "replace_field" else row
                       for row in result[key]]
    removal = changes["de427"]["before"]
    result["kg_edges"] = remove_reviewed_edges(result["kg_edges"], [removal])
    affected = {removal["src_id"], removal["dst_id"]}
    degrees = Counter(endpoint for edge in result["kg_edges"]
                      for endpoint in (edge["src_id"], edge["dst_id"]))
    degree_changes = []
    for node in result["kg_nodes"]:
        if node["id"] in affected:
            degree_changes.append({"id": node["id"], "before": node["degree"],
                                   "after": degrees[node["id"]]})
            node["degree"] = degrees[node["id"]]
    result["meta"]["build_version"] = BUILD_VERSION
    result["meta"]["note"] = NOTE
    result["meta"]["counts"] = {
        "nodes": len(result["kg_nodes"]), "edges": len(result["kg_edges"]),
        "puzzles": len(result["kg_puzzles"]),
        "by_category": dict(sorted(Counter(n["category"] for n in result["kg_nodes"]).items())),
        "puzzles_by_cat_diff": dict(sorted(Counter(
            f"{p['category']}/{p['difficulty']}" for p in result["kg_puzzles"]
        ).items())),
    }
    _require(result["kg_puzzles"] == graph["kg_puzzles"], "puzzle mutation is forbidden")
    blob = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    validate_candidate(blob)
    _unchanged(inputs)
    report = {
        "kind": "v1-factual-repair-generation-v1", "written": False,
        "proposal_sha256": PROPOSAL_SHA256, "baseline_kg_sha256": BASELINE_KG_SHA256,
        "candidate_kg_sha256": sha256(blob), "changed_ids": list(EXPECTED_CHANGES),
        "review_sha256": {role: sha256(inputs[root / path])
                          for role, path in REVIEW_PATHS.items()},
        "counts_before": graph["meta"]["counts"], "counts_after": result["meta"]["counts"],
        "degree_changes": degree_changes,
        "preserved_puzzles_sha256": record_sha256(graph["kg_puzzles"]),
        "fixture_validation": "GREEN", "puzzles_regenerated": False,
    }
    return RepairPlan(blob, report, inputs)


def apply_repairs(*, root: Path = ROOT, write: bool = False) -> RepairPlan:
    plan = prepare_repairs(root=root)
    if not write:
        return plan
    paths = tuple(root / path for path in FIXTURE_PATHS)
    _unchanged(plan.inputs)
    with file_transaction(paths) as originals:
        _require(all(originals[path] == plan.inputs[path] for path in paths),
                 "fixtures changed before transaction")
        _unchanged(plan.inputs)
        for path in paths:
            atomic_write(path, plan.candidate)
        _validate_pair(paths)
        _unchanged(plan.inputs, exclude=paths)
        _require(all(path.read_bytes() == plan.candidate for path in paths),
                 "written fixture bytes differ")
    return RepairPlan(plan.candidate, {**plan.report, "written": True}, plan.inputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="replace the two served KG mirrors")
    parser.add_argument("--candidate-output", type=Path,
                        help="save validated candidate to a new file outside the repository")
    args = parser.parse_args(argv)
    if args.candidate_output:
        output = args.candidate_output.resolve()
        if args.write:
            parser.error("candidate export is a dry-run option; use --write separately")
        if output.is_relative_to(ROOT.resolve()):
            parser.error("candidate output must be outside the repository")
        if output.exists():
            parser.error("candidate output already exists")
    try:
        plan = apply_repairs(root=ROOT, write=args.write)
        if args.candidate_output:
            # Exclusive creation prevents a diagnostic export from overwriting evidence.
            with args.candidate_output.open("xb") as handle:
                handle.write(plan.candidate)
        print(json.dumps(plan.report, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"V1 factual repair rejected: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
