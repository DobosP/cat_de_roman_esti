#!/usr/bin/env python3
"""Build/check the finite, independently reviewed V1 release reserve manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cat_de_roman_esti.wordgames import release_reserve as reserve  # noqa: E402
from scripts.content_file_transaction import atomic_write  # noqa: E402

REVIEW_DIR = ROOT / "docs/reviews/v1-testing-release/content"
PROPOSAL = REVIEW_DIR / "selection-reserve-proposal.json"
ALCHIMIE_PROPOSAL = REVIEW_DIR / "alchimie-reserve-proposal.json"
QUALITY_REVIEW = REVIEW_DIR / "selection-reserve-quality-review.json"
PROPOSAL_SHA256 = "e02b1a624fb7df8edfbcf507a8c9d7bcfb39510cba771d9b3d660430b2360de4"
ALCHIMIE_SHA256 = "bcf35794a43f437f78d420b34a0e4ae44e1accd76c7eddde46a4bdf9e33728e6"
QUALITY_SHA256 = "54980fe74ac512b431eed9c8f3e3390c53e40a16a3efc1ad7fd207a528178758"
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
COPIES = (reserve.RESERVE_PATH, ROOT / "tests/fixtures/release_reserve_v1.json")


def _require(test: bool, message: str) -> None:
    if not test:
        raise ValueError("release reserve builder: " + message)


def _bound(path: Path, expected: str) -> dict:
    blob = path.read_bytes().replace(b"\r\n", b"\n")
    _require(hashlib.sha256(blob).hexdigest() == expected, f"source drift: {path.name}")
    return json.loads(blob)


def build_manifest(
    proposal_path: Path = PROPOSAL,
    alchimie_path: Path = ALCHIMIE_PROPOSAL,
    quality_path: Path = QUALITY_REVIEW,
    fixtures: Path = FIXTURES,
) -> dict:
    proposal = _bound(proposal_path, PROPOSAL_SHA256)
    alchimie = _bound(alchimie_path, ALCHIMIE_SHA256)
    quality = _bound(quality_path, QUALITY_SHA256)
    _require(proposal["baseline"] == alchimie["baseline"] == "cc0a6a4", "baseline")
    author = proposal["author"]
    reviewer = quality.get("reviewer")
    _require(author == alchimie["author"] == quality.get("author_of_proposals"), "author")
    _require(isinstance(reviewer, str) and reviewer.strip()
             and reviewer.strip().casefold() != author.strip().casefold(), "independence")
    _require(quality.get("role") == "quality"
             and quality.get("candidate_sha256") == PROPOSAL_SHA256
             and quality.get("alchimie_candidate_sha256") == ALCHIMIE_SHA256,
             "review input bindings")
    proposed = [*proposal["items"], *alchimie["items"]]
    judged = quality.get("items", [])
    ids = [r["id"] for r in proposed]
    reviewed_ids = [r.get("id") for r in judged]
    _require(len(ids) == len(set(ids)) == 23 and len(judged) == 23
             and set(ids) == set(reviewed_ids), "complete exact review coverage")
    reviews = {r["id"]: r for r in judged}
    pack_data = json.loads((fixtures / "games_pack.json").read_bytes())
    quick_data = [*json.loads((fixtures / "derived_catalog_v38.json").read_bytes())["boards"],
                  *json.loads((fixtures / "quick_games_v92.json").read_bytes())["boards"]]
    pack_rows, quick_rows = [], []
    for item in sorted(proposed, key=lambda r: r["id"]):
        item_id, game = item["id"], item["game"]
        review = reviews[item_id]
        expected = reserve.record_digest(item["record"])
        _require(item["record_sha256"] == expected
                 and review.get("record_sha256") == expected
                 and review.get("game") == game
                 and review.get("verdict") == "accept"
                 and review.get("action") == "reserve_from_new_selection",
                 f"unresolved or stale judgment: {item_id}")
        available = pack_data.get(game, []) if game in reserve.PACK_GAMES else quick_data
        matches = [r for r in available if r.get("id") == item_id]
        _require(len(matches) == 1 and reserve.record_digest(matches[0]) == expected,
                 f"current archived record drift: {item_id}")
        record = matches[0]
        row = {"id": item_id, "game": game, "record_sha256": expected}
        if game in reserve.PACK_GAMES:
            _require(record.get("status") == "approved", f"non-approved stock: {item_id}")
            pack_rows.append(row)
        else:
            _require(game in reserve.QUICK_GAMES, f"game: {item_id}")
            quick_rows.append({**row, "source_id": record["source_id"],
                               "definition_sha256": reserve.record_digest(
                                   reserve.quick_definition(record))})
    _require(len(pack_rows) == 20 and len(quick_rows) == 3, "finite batch counts")
    return {
        "meta": {
            "kind": "v1-release-reserve-v1", "baseline": "cc0a6a4",
            "count": len(pack_rows), "quick_count": len(quick_rows),
            "author": author, "reviewer": reviewer,
            "proposal_sha256": PROPOSAL_SHA256,
            "alchimie_proposal_sha256": ALCHIMIE_SHA256,
            "quality_review_sha256": QUALITY_SHA256,
        },
        "ids": [r["id"] for r in pack_rows], "pack": pack_rows, "quick": quick_rows,
    }


def render_manifest(manifest: dict) -> bytes:
    return (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_copies(blob: bytes, copies: tuple[Path, ...] = COPIES) -> None:
    """Rollback also covers first-time creation of this exact two-file artifact."""
    before = {p: p.read_bytes() if p.exists() else None for p in copies}
    try:
        for path in copies:
            atomic_write(path, blob)
        _require(all(p.read_bytes() == blob for p in copies), "mirror write drift")
    except BaseException:
        for path, old in before.items():
            if old is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, old)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    expected = render_manifest(build_manifest())
    _require(hashlib.sha256(expected).hexdigest() == reserve.MANIFEST_SHA256,
             "runtime manifest pin differs")
    if args.write:
        write_copies(expected)
    _require(all(p.read_bytes() == expected for p in COPIES), "stale artifact copies")
    for path in COPIES:
        reserve.load_reserve(path)
    print("release reserve GREEN: 20 pack / 3 quick, archived records unchanged")


if __name__ == "__main__":
    main()