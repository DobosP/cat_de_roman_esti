#!/usr/bin/env python3
"""Apply the one reviewed V91 Alchimie seed correction, read-only unless --write.

This offline migration accepts only the frozen al_sport_083 before/after records.
It does not provide a general approved-content editor or change approval status.
Run the release artifact generators and complete gates after a successful write.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import critique_pack as critique  # noqa: E402
from scripts import validate_games_pack as validator  # noqa: E402
from scripts.content_file_transaction import atomic_write, file_transaction  # noqa: E402

REVIEW_DIR = Path("docs/reviews/v91-recovery-and-mobile-clarity/content")
PACK_PATHS = (
    Path("cat_de_roman_esti/fixtures/games_pack.json"),
    Path("tests/fixtures/games_pack.json"),
)
KG_PATHS = (
    Path("cat_de_roman_esti/fixtures/kg_sample.json"),
    Path("tests/fixtures/kg_sample.json"),
)
ITEM_ID = "al_sport_083"
BEFORE_SHA = "bb0ef938d92416b955abbf23602c47c63dd49700f0c866061b4ce0390c49b11a"
AFTER_SHA = "5666d5978c89ba537de7239f9ba205b395378bdfc20400466e4c2ced246aded5"
REVIEW_BINDING = "sha256:b5e181aa856470707564fa9ff3596c8bc73b3cd22ece22f1f441d7871cb573ba"
SOURCE_BINDINGS = {
    "cat_de_roman_esti/fixtures/games_pack.json":
        "e32139529aacc88e2f453ac1cee1d8cd9a2cd1b16f3ee0551a5a76779192391e",
    "cat_de_roman_esti/fixtures/kg_sample.json":
        "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "docs/CRITIQUE_RUBRIC.md":
        "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101",
    "cat_de_roman_esti/wordgames/alchimie.py":
        "4ffd2eaf65b5e942992d7d84b52b8e221f1e2c7dfb7edff19fe35e0e74236ec8",
    "cat_de_roman_esti/wordgames/packs.py":
        "801d9515711501201d26783a7f0eaf5008924d9d10c7b98192718515bbb1d3db",
}
INPUT_SHA256 = {
    "replacement-proposal.json":
        "1b5b5686d39c9f4ec6ac170a60b56180be38a9b8dd9c8c24f0458e9d0988658a",
    "candidate-dossier.json":
        "1167dd460ae618c5916a81b98426d1bdcf57938fb53670c50b51359eec4c349a",
    "candidate-profile.json":
        "1093381dc4e500661e04acc8d3797459c5a5231e69d18789f2c0f4115f9888e5",
    "before-profile.json":
        "ed1b09058e94f931fba762c2b6776887ee29fabafc9f6df1aaaf0ae27b2a1406",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _check_sources(root: Path, *, pack_applied: bool = False) -> None:
    for relative, expected in SOURCE_BINDINGS.items():
        if pack_applied and relative == str(PACK_PATHS[0]):
            continue
        _require(_sha((root / relative).read_bytes()) == expected,
                 f"stale source: {relative}")
    _require((root / KG_PATHS[0]).read_bytes() == (root / KG_PATHS[1]).read_bytes(),
             "KG mirrors differ")


def _review_inputs(root: Path) -> dict[str, dict]:
    folder = root / REVIEW_DIR
    inputs = {}
    for name, expected in INPUT_SHA256.items():
        blob = (folder / name).read_bytes()
        _require(_sha(blob) == expected, f"review input changed: {name}")
        inputs[name] = json.loads(blob)
    proposal = inputs["replacement-proposal.json"]
    _require(proposal["source_bindings"] == SOURCE_BINDINGS, "proposal source binding mismatch")
    before, after = proposal["before"], proposal["after"]
    _require(critique.canonical_json_sha256(before) == BEFORE_SHA, "wrong before record")
    _require(critique.canonical_json_sha256(after) == AFTER_SHA, "wrong after record")
    _require(before["id"] == after["id"] == ITEM_ID, "wrong item ID")
    _require(set(before) == set(after)
             and {key for key in before if before[key] != after[key]} == {"seeds"},
             "only seeds may change")
    _require(before["status"] == after["status"] == "approved", "status must remain approved")
    _require(proposal["changed_record_fields"] == ["seeds"], "wrong declared delta")
    _require(proposal["before_record_sha256"] == BEFORE_SHA
             and proposal["after_record_sha256"] == AFTER_SHA, "proposal record binding mismatch")
    reviewers = []
    for name in ("quality-review.json", "factual-review.json"):
        review = json.loads((folder / name).read_bytes())
        _require(review.get("kind") == "independent-approved-stock-revision-review"
                 and review.get("verdict") == "accept"
                 and review.get("proposal") == "revise", f"missing accept verdict: {name}")
        _require(review.get("item_id") == ITEM_ID
                 and review.get("review_binding") == REVIEW_BINDING
                 and review.get("before_record_sha256") == BEFORE_SHA
                 and review.get("after_record_sha256") == AFTER_SHA,
                 f"review record binding mismatch: {name}")
        _require(review.get("source_bindings") == SOURCE_BINDINGS
                 and review.get("input_sha256") == INPUT_SHA256,
                 f"review input/source binding mismatch: {name}")
        reviewer = review.get("reviewer")
        _require(isinstance(reviewer, str) and bool(reviewer.strip()),
                 f"missing reviewer identity: {name}")
        reviewers.append(reviewer.strip().casefold())
    _require(len(set(reviewers)) == 2, "two distinct independent reviewers are required")
    dossier = inputs["candidate-dossier.json"]
    _require(dossier.get("review_binding") == REVIEW_BINDING
             and critique.dossier_review_binding(dossier) == REVIEW_BINDING,
             "dossier binding mismatch")
    return inputs


def _live_candidate(root: Path, candidate: dict, reviewed: dict[str, dict]) -> None:
    """Rebuild the exact dossier, public start and uncached private recipe book."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")
    import django

    django.setup()
    from cat_de_roman_esti.wordgames import alchimie

    _, service, strong, regions = critique.load_all(root / PACK_PATHS[0], root / KG_PATHS[0])
    record = next(row for row in candidate["alchimie"] if row["id"] == ITEM_ID)
    errors = (validator.validate_envelope(record, "alchimie")
              + validator.validate_payload(record, "alchimie", service))
    _require(not errors, f"candidate validation failed: {errors}")
    _, _, selected = critique.run(candidate, service, strong, regions,
                                  ["alchimie"], {"approved"}, {ITEM_ID})
    _require(len(selected) == 1, "candidate critique selection mismatch")
    game, _, findings = selected[0]
    _require(not any(row["level"] == "FAIL" for row in findings), "candidate critique failed")
    # The checked bytes supply fresh digests without modifying process-global hash caches.
    with (patch.object(critique, "kg_sha256", lambda: SOURCE_BINDINGS[str(KG_PATHS[0])]),
          patch.object(critique, "rubric_sha256",
                       lambda: SOURCE_BINDINGS["docs/CRITIQUE_RUBRIC.md"])):
        dossier = critique.build_dossier(record, game, service, strong, findings, regions)
    _require(dossier == reviewed["candidate-dossier.json"], "live dossier differs from review")
    projection = alchimie._build_recipe_projection_cached.__wrapped__(
        tuple(record["seeds"]), record["target"], record["category"],
        alchimie._ProjectionServiceRef(service),
    )
    _require(projection is not None, "candidate has no live recipe book")
    _require(projection.par == 2 and len(projection.recipes) == 6
             and len(projection.routes) == 4, "candidate sparse book bounds changed")
    session = alchimie.AlchimieSession(
        seeds=record["seeds"], target=record["target"], target_depth=projection.par,
        difficulty=record["difficulty"], category=record["category"], pack_id=ITEM_ID,
        recipes=projection.recipes, routes=projection.routes,
    )
    for seed in session.seeds:
        session.add(seed, None)
    flags = alchimie._inventory_flags(session)
    _require(len(flags) == 6 and all(useful and ready and not depleted
                                    for _, useful, ready, depleted in flags.values()),
             "all six initial seeds must be useful and ready")
    _require(alchimie._projected_opening_pair_count(session.seeds, projection.recipes) == 4,
             "candidate must retain four productive opening pairs")

    def recipe(step: tuple) -> dict:
        pair, outputs = step
        return {
            "pair": list(pair), "pair_labels": [service.label(node) for node in pair],
            "outputs": list(outputs), "output_labels": [service.label(node) for node in outputs],
            "actual_edges": [dataclasses.asdict(service.link(parent, output))
                             for parent in pair for output in outputs],
        }

    with patch.object(alchimie, "get_service", lambda: service):
        initial = alchimie._state_payload("content-review-local", session)
    owned = set(session.seeds)
    profile = {
        "record": record, "record_sha256": AFTER_SHA, "validation_errors": errors,
        "initial_payload": initial,
        "opening_pairs": [recipe(step) for step in projection.recipes.items()
                          if set(step[0]) <= owned and any(n not in owned for n in step[1])],
        "book": {
            "par": projection.par,
            "recipes": [recipe(step) for step in projection.recipes.items()],
            "routes": [[recipe(step) for step in route] for route in projection.routes],
            "candidate_quality": projection.candidate_quality,
        },
    }
    # JSON normalizes tuple-valued runtime fields exactly as the author capture did.
    _require(json.loads(json.dumps(profile)) == reviewed["candidate-profile.json"],
             "live profile differs from review")


def apply_revision(*, root: Path = ROOT, write: bool = False) -> None:
    """Apply only the pinned revision; root is injectable for isolated migration tests."""
    paths = tuple(root / path for path in PACK_PATHS)
    with file_transaction(paths) as originals:
        _require(len(set(originals.values())) == 1, "pack mirrors must be byte-identical")
        _check_sources(root)
        reviewed = _review_inputs(root)
        before = json.loads(originals[paths[0]])
        proposal = reviewed["replacement-proposal.json"]
        rows = [row for game in validator.GAME_KINDS for row in before[game]
                if row.get("id") == ITEM_ID]
        _require(rows == [proposal["before"]],
                 "source record missing, duplicated or already revised")
        candidate = copy.deepcopy(before)
        for row in candidate["alchimie"]:
            if row["id"] == ITEM_ID:
                row["seeds"] = list(proposal["after"]["seeds"])
                _require(row == proposal["after"], "replacement exceeds reviewed seed delta")
        _live_candidate(root, candidate, reviewed)
        blob = (json.dumps(candidate, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        # Expensive projection/review must not hide a concurrent source or mirror edit.
        _check_sources(root)
        _require(all(path.read_bytes() == originals[path] for path in paths),
                 "pack changed during verification")
        if not write:
            print("V91 Sport seed revision verified; dry run, no writes")
            return
        for path in paths:
            atomic_write(path, blob)
        for path, kg in zip(paths, KG_PATHS, strict=True):
            errors = validator.validate(path, root / kg)
            _require(not errors, f"pack validation failed; rolling back: {errors}")
        _check_sources(root, pack_applied=True)
        _require(all(path.read_bytes() == blob for path in paths),
                 "written pack bytes differ; rolling back")
    print("V91 Sport seed revision GREEN: one revised round, both mirrors verified")
    print("Regenerate release artifacts and run the complete release gates before landing.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    apply_revision(write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
