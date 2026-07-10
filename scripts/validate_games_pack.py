#!/usr/bin/env python3
"""Committed CI gate for the curated games pack (games_pack.json, ADR-0011).

Validates both bundled pack copies (package + tests) against their sibling KG
fixture: packaging shape, per-item field shapes + enums, id uniqueness, and —
for every ``approved`` item — full playability (node resolution, Lanț BFS distance +
shortest-path branch floor, Contexto reachability/warm-band floors, Alchimie exact
action par). Non-approved items (``pending`` / ``rejected``) only
need a valid envelope: they are review inventory, not served content.

The deep checks are the SAME functions the server and the submissions endpoint
use (``cat_de_roman_esti.wordgames.packs``), so this gate cannot drift from the
runtime rules.

Usage::

    python scripts/validate_games_pack.py [pack_path [kg_fixture_path]]

Exits 0 (GREEN) when clean, 1 on any error, after a per-class summary.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    GAME_KINDS,
    validate_envelope,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

PACKAGE_PACK = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "games_pack.json"
TESTS_PACK = _REPO_ROOT / "tests" / "fixtures" / "games_pack.json"
PACKAGE_KG = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
TESTS_KG = _REPO_ROOT / "tests" / "fixtures" / "kg_sample.json"

TOP_LEVEL_KEYS = ("meta", *GAME_KINDS)

ERROR_CLASSES = (
    "copies_identical",
    "structure",
    "item_shape",
    "unique_ids",
    "playability",
    "meta_counts",
)


def validate(pack_path: Path, kg_path: Path) -> list[str]:
    """All invariant violations for one pack file (empty list == clean)."""
    errors: list[str] = []
    try:
        raw = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"structure: cannot read {pack_path}: {exc}"]
    if not isinstance(raw, dict):
        return ["structure: top level must be an object"]

    for key in TOP_LEVEL_KEYS:
        if key not in raw:
            errors.append(f"structure: missing top-level key {key!r}")
    for key in raw:
        if key not in TOP_LEVEL_KEYS:
            errors.append(f"structure: unexpected top-level key {key!r}")
    if not isinstance(raw.get("meta"), dict):
        errors.append("structure: meta must be an object")
    for game in GAME_KINDS:
        if not isinstance(raw.get(game), list):
            errors.append(f"structure: {game} must be an array")
    if errors:
        return errors

    svc = WordGameService(graph=load_fixture(kg_path).graph)

    ids: Counter[str] = Counter()
    for game in GAME_KINDS:
        for rec in raw[game]:
            if not isinstance(rec, dict):
                errors.append(f"item_shape: {game} carries a non-object record")
                continue
            rid = str(rec.get("id"))
            ids[rid] += 1
            for msg in validate_envelope(rec, game):
                errors.append(f"item_shape: {game} {rid}: {msg}")
            if rec.get("status") == "approved":
                for msg in validate_payload(rec, game, svc):
                    errors.append(f"playability: {game} {rid}: {msg}")

    for rid, count in sorted(ids.items()):
        if count > 1:
            errors.append(f"unique_ids: id {rid!r} appears {count} times")

    declared = raw["meta"].get("counts")
    if not isinstance(declared, dict):
        errors.append("meta_counts: meta.counts must be an object")
    else:
        for game in GAME_KINDS:
            actual = len(raw[game])
            if declared.get(game) != actual:
                errors.append(
                    f"meta_counts: counts.{game} is {declared.get(game)!r}, actual {actual}"
                )

    return errors


def main(argv: list[str]) -> int:
    pack_path = Path(argv[1]) if len(argv) > 1 else PACKAGE_PACK
    kg_path = Path(argv[2]) if len(argv) > 2 else PACKAGE_KG

    errors = validate(pack_path, kg_path)

    # The two bundled copies must stay byte-identical (same rule as the KG fixture),
    # and the tests copy must be clean against the tests KG fixture.
    if pack_path == PACKAGE_PACK and TESTS_PACK.exists():
        if pack_path.read_bytes() != TESTS_PACK.read_bytes():
            errors.append(
                "copies_identical: cat_de_roman_esti/fixtures/games_pack.json and "
                "tests/fixtures/games_pack.json differ"
            )
        errors.extend(validate(TESTS_PACK, TESTS_KG))

    by_class = Counter(err.split(":", 1)[0] for err in errors)
    for cls in ERROR_CLASSES:
        status = "FAIL" if by_class.get(cls) else "ok"
        print(f"  {cls:<24} {status}" + (f" ({by_class[cls]})" if by_class.get(cls) else ""))
    if errors:
        print(f"\n{len(errors)} error(s):")
        for err in errors:
            print(" -", err)
        return 1
    print("\ngames pack GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
