#!/usr/bin/env python3
"""Build the reviewed quick-game supplement; final reviews gate package writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cat_de_roman_esti.wordgames import quick_catalog as Q  # noqa: E402
from cat_de_roman_esti.wordgames.derived_catalog import load_derived_catalog  # noqa: E402
from cat_de_roman_esti.wordgames.discovery_world import valid_reference  # noqa: E402
from cat_de_roman_esti.wordgames.recipe_extensions import record_snapshot  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402
from scripts import quick_game_content_source_v92 as S  # noqa: E402
from scripts.content_file_transaction import atomic_write  # noqa: E402

CANDIDATE_KIND = "quick-content-candidates-v1"
REVIEW_KIND = "quick-content-review-v1"
FINAL_KIND = "quick-content-final-v1"
AUDIT_KIND = "quick-content-live-audit-v1"
SOURCE_PATH = Path(S.__file__).resolve()
RUNTIME_SOURCES = (
    "cat_de_roman_esti/wordgames/quick_catalog.py",
    "cat_de_roman_esti/wordgames/derived_catalog.py",
    "cat_de_roman_esti/wordgames/release_reserve.py",
    "cat_de_roman_esti/fixtures/release_reserve_v1.json",
    "cat_de_roman_esti/wordgames/intrusul.py",
    "cat_de_roman_esti/wordgames/perechi.py",
    "cat_de_roman_esti/wordgames/service.py",
    "scripts/build_quick_content_v92.py",
    "scripts/audit_quick_content_v92.py",
    "scripts/quick_game_content_source_v92.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"quick content build: {message}")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def read_json(path: Path) -> dict:
    require(path.stat().st_size <= Q.MAX_BYTES, f"{path.name}: file exceeds size bound")
    value = json.loads(path.read_bytes(), parse_constant=_reject_constant)
    require(isinstance(value, dict), f"{path.name}: JSON object required")
    return value


def candidate() -> dict:
    """Reproduce the exact editorial batch without binding mutable pack approvals."""
    return {
        "kind": CANDIDATE_KIND,
        "boards": S.candidate_boards(),
        "bindings": {**Q.bindings(live=False), "editorial_source_sha256": file_sha(SOURCE_PATH)},
    }


def runtime_source_hashes() -> dict[str, str]:
    """Every final-audit source is required; absent files are never silently omitted."""
    return {relative: file_sha(ROOT / relative) for relative in RUNTIME_SOURCES}


def read_review(path: Path, role: str, candidate_sha: str, ids: set[str]) -> dict:
    review = read_json(path)
    require(
        review.get("kind") == REVIEW_KIND and review.get("role") == role,
        f"{role}: review kind/role mismatch",
    )
    identity = review.get("reviewer")
    require(
        isinstance(identity, str) and identity == identity.strip() and bool(identity),
        f"{role}: reviewer identity required",
    )
    require(review.get("candidate_sha256") == candidate_sha, f"{role}: stale candidate binding")
    items = review.get("items")
    require(
        isinstance(items, list) and all(isinstance(item, dict) for item in items),
        f"{role}: review items required",
    )
    reviewed_ids = [item.get("id") for item in items]
    require(
        all(isinstance(item_id, str) for item_id in reviewed_ids)
        and len(reviewed_ids) == len(set(reviewed_ids))
        and set(reviewed_ids) == ids,
        f"{role}: incomplete, unknown or duplicate candidate coverage",
    )
    for item in items:
        verdict, reason, sources = item.get("verdict"), item.get("rationale"), item.get("sources")
        require(
            isinstance(verdict, str)
            and verdict in {"accept", "reject", "hold"}
            and isinstance(reason, str)
            and bool(reason.strip())
            and isinstance(sources, list)
            and len(sources) <= 32,
            f"{role}: incomplete judgment",
        )
        require(
            all(isinstance(source, str) and valid_reference(source) for source in sources),
            f"{role}: invalid source URL",
        )
        if role == "factual" and verdict == "accept":
            require(bool(sources), "factual: accepted judgment needs source URLs")
    return review


def build_catalog(candidate_path: Path, factual_path: Path, quality_path: Path) -> dict:
    """Intersect complete independent judgments, then replay exact current graph gates."""
    raw = read_json(candidate_path)
    expected = candidate()
    require(
        raw == expected and candidate_path.read_bytes() == Q.json_bytes(expected),
        "candidate differs from current editorial source or bindings",
    )
    rows = raw["boards"]
    require(
        isinstance(rows, list)
        and 0 < len(rows) <= Q.MAX_BOARDS
        and all(isinstance(row, dict) for row in rows),
        "candidate board bound/shape",
    )
    ids = [row.get("id") for row in rows]
    require(
        all(isinstance(item_id, str) for item_id in ids) and len(ids) == len(set(ids)),
        "invalid or duplicate candidate id",
    )
    candidate_sha = file_sha(candidate_path)
    reviews = [
        read_review(path, role, candidate_sha, set(ids))
        for role, path in (("factual", factual_path), ("quality", quality_path))
    ]
    require(
        reviews[0]["reviewer"].casefold() != reviews[1]["reviewer"].casefold(),
        "reviewers must be independent",
    )
    accepted = set(ids)
    for review in reviews:
        accepted.intersection_update(
            item["id"] for item in review["items"] if item["verdict"] == "accept"
        )
    chosen = [row for row in rows if row["id"] in accepted]
    service, base = get_service(), load_derived_catalog()
    rated = Q.rated_boards(chosen, base, service)
    visible = {node_id for row in chosen for node_id in Q.visible_ids(row)}
    catalog = {
        "kind": "quick-content-catalog-v1",
        "candidate_sha256": candidate_sha,
        "bindings": Q.bindings(live=True),
        "reviews": [
            {"role": review["role"], "reviewer": review["reviewer"], "sha256": file_sha(path)}
            for review, path in zip(reviews, (factual_path, quality_path), strict=True)
        ],
        "authored": chosen,
        "boards": rated,
        "nodes": {node_id: record_snapshot(service.node(node_id)) for node_id in sorted(visible)},
        "excluded": sorted(set(ids) - accepted),
    }
    require(len(Q.json_bytes(catalog)) <= Q.MAX_BYTES, "catalog exceeds byte bound")
    Q.validate_catalog(catalog, base, service)
    return catalog


def confirm_final_reviews(
    catalog: dict, audit_path: Path, factual_path: Path, quality_path: Path
) -> None:
    """Require current live replay and both independent reviewers over exact bytes."""
    audit = read_json(audit_path)
    catalog_sha = hashlib.sha256(Q.json_bytes(catalog)).hexdigest()
    require(audit.get("kind") == AUDIT_KIND and audit.get("passed") is True, "live audit must pass")
    require(
        audit.get("catalog_sha256") == catalog_sha
        and audit.get("candidate_sha256") == catalog["candidate_sha256"],
        "live audit artifact binding drift",
    )
    require(audit.get("bindings") == Q.bindings(live=True), "live audit content source drift")
    require(audit.get("runtime_sources") == runtime_source_hashes(), "live audit runtime drift")
    audit_sha = file_sha(audit_path)
    identities = {review["role"]: review["reviewer"] for review in catalog["reviews"]}
    for role, path in (("factual", factual_path), ("quality", quality_path)):
        review = read_json(path)
        require(
            review.get("kind") == FINAL_KIND
            and review.get("role") == role
            and review.get("reviewer") == identities[role],
            f"{role}: final reviewer mismatch",
        )
        require(
            review.get("catalog_sha256") == catalog_sha and review.get("audit_sha256") == audit_sha,
            f"{role}: final artifact binding drift",
        )
        require(
            review.get("verdict") == "accept"
            and isinstance(review.get("rationale"), str)
            and bool(review["rationale"].strip()),
            f"{role}: final acceptance required",
        )


def _output_path(path: Path, protected: tuple[Path, ...] = ()) -> None:
    # Review evidence cannot overwrite source data or its own review inputs.
    target = path.resolve()
    fixed = {
        Q.CATALOG_PATH.resolve(),
        SOURCE_PATH,
        *(ROOT / p for p in RUNTIME_SOURCES),
        Q.DEFAULT_FIXTURE.resolve(),
        Q.DEFAULT_PACK.resolve(),
        Q.DEFAULT_RUBRIC.resolve(),
        Q.DEFAULT_DERIVED_CATALOG.resolve(),
    }
    require(
        target not in fixed and target not in {p.resolve() for p in protected},
        "output would overwrite a protected input",
    )
    require(
        not target.is_relative_to(ROOT / "cat_de_roman_esti" / "fixtures")
        and not target.is_relative_to(ROOT / "tests" / "fixtures"),
        "review output cannot overwrite a fixture",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-candidate", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--factual-review", type=Path)
    parser.add_argument("--quality-review", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--live-audit", type=Path)
    parser.add_argument("--final-factual-review", type=Path)
    parser.add_argument("--final-quality-review", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.generate_candidate is not None:
            require(
                not args.write
                and not any(
                    (
                        args.candidate,
                        args.factual_review,
                        args.quality_review,
                        args.proposal,
                        args.live_audit,
                        args.final_factual_review,
                        args.final_quality_review,
                    )
                ),
                "candidate generation must be a separate action",
            )
            _output_path(args.generate_candidate)
            atomic_write(args.generate_candidate, Q.json_bytes(candidate()))
            print(f"quick content: candidate written to {args.generate_candidate}")
            return 0
        require(
            all((args.candidate, args.factual_review, args.quality_review, args.proposal)),
            "candidate, both semantic reviews and proposal are required",
        )
        _output_path(
            args.proposal,
            tuple(
                p
                for p in (
                    args.candidate,
                    args.factual_review,
                    args.quality_review,
                    args.live_audit,
                    args.final_factual_review,
                    args.final_quality_review,
                )
                if p is not None
            ),
        )
        catalog = build_catalog(args.candidate, args.factual_review, args.quality_review)
        if args.write:
            require(
                all((args.live_audit, args.final_factual_review, args.final_quality_review)),
                "package write requires live audit and both final reviews",
            )
            confirm_final_reviews(
                catalog, args.live_audit, args.final_factual_review, args.final_quality_review
            )
            # Review must be of the saved proposal; stale or missing files cannot be replaced first.
            require(args.proposal.read_bytes() == Q.json_bytes(catalog), "saved proposal drift")
            require(
                Q.CATALOG_SHA256 == hashlib.sha256(Q.json_bytes(catalog)).hexdigest(),
                "runtime catalog pin does not match reviewed proposal",
            )
            atomic_write(Q.CATALOG_PATH, Q.json_bytes(catalog))
            print(f"quick content: wrote {len(catalog['boards'])} reviewed package boards")
        else:
            atomic_write(args.proposal, Q.json_bytes(catalog))
            print(f"quick content: proposal has {len(catalog['boards'])} boards; package unchanged")
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"quick content: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
