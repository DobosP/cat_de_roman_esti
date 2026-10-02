"""Export the validated private arcade bundle for the Go and Rust servers.

Python remains the content-validation authority. This file is a build input,
never a browser/mobile asset. --check detects any source or export drift.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import unicodedata
from collections.abc import Mapping
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from cat_de_roman_esti import __version__
from cat_de_roman_esti.data import fixture_manifest
from cat_de_roman_esti.wordgames import contexto_feedback, contexto_projection, lant_relations
from cat_de_roman_esti.wordgames.categories import CATEGORY_LABELS, known_keys
from cat_de_roman_esti.wordgames.derived_catalog import get_derived_catalog
from cat_de_roman_esti.wordgames.discovery_world import get_world
from cat_de_roman_esti.wordgames.packs import GAME_KINDS, get_pack
from cat_de_roman_esti.wordgames.service import get_service

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "go-backend/internal/content/bundled.json"
PIN = OUTPUT.with_name("digest.go")
SOURCES = (
    "kg_sample.json",
    "derived_catalog_v38.json",
    "quick_games_v92.json",
    "board_rankings_v37.json",
    "release_reserve_v1.json",
    "games_pack.json",
    "alchimie_discovery_world_v92.json",
    "alchimie_recipe_extensions_v92.json",
)


def plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [plain(item) for item in sorted(value)]
    return value


@lru_cache(maxsize=1)
def unicode_tables() -> tuple[dict, dict, list, dict]:
    normalized, accented, ranges, casefolded = {}, {}, [], {}
    start = None
    for code in range(0x110000):
        char = chr(code)
        decomposed = unicodedata.normalize("NFKD", char)
        full = decomposed.casefold()
        folded = "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()
        if folded != char:
            normalized[char] = folded
        if full != char:
            accented[char] = full
        if char.casefold() != char:
            casefolded[char] = char.casefold()
        letter = unicodedata.category(char).startswith("L")
        if letter and start is None:
            start = code
        if not letter and start is not None:
            ranges.append([start, code - 1])
            start = None
    if start is not None:
        ranges.append([start, 0x10FFFF])
    return normalized, accented, ranges, casefolded


def export_bytes() -> bytes:
    if any(
        os.environ.get(name)
        for name in (
            "CAT_KG_FIXTURE",
            "CAT_GAMES_PACK",
            "CAT_BOARD_RANKINGS",
        )
    ):
        raise ValueError("Go export requires bundled content without source overrides")
    if unicodedata.unidata_version != "15.0.0":
        raise ValueError("Native content export requires Python 3.12 / Unicode 15.0.0")
    service = get_service()
    catalog = get_derived_catalog()  # verifies ranking, KG, payload and reserve identities
    pack = get_pack()
    world = get_world()
    normalized, accented, letter_ranges, casefolded = unicode_tables()
    from django.test import Client, override_settings

    from scripts.export_openapi import export_openapi

    with contextlib.redirect_stderr(io.StringIO()):
        schema = export_openapi()
    from cat_de_roman_esti.wordgames.conexiuni import _label_pattern

    client = Client()
    metadata = {
        path: client.get(path).json()
        for path in ("/api/health", "/api/manifest", "/api/categories")
    }
    metadata["openapi"] = schema
    # Public runtime identity belongs in the server configuration, never the
    # deterministic private build input or content digest.
    with override_settings(
        CAT_LEGAL_OPERATOR="",
        CAT_LEGAL_CONTACT_EMAIL="",
        CAT_CONSENT_VERSION="2026-07-09",
        CAT_MIN_SELF_CONSENT_AGE=16,
    ):
        metadata["privacy_html"] = client.get("/legal/privacy").content.decode()
        metadata["terms_html"] = client.get("/legal/terms").content.decode()
    pack_items = [item for game in GAME_KINDS for item in pack.pool(game)]
    group_labels = set(CATEGORY_LABELS.values())
    for item in pack_items:
        if item.game == "conexiuni":
            group_labels.update(item.payload.get("group_labels", {}).values())
    projection_terms = [
        {**asdict(term), "key": term.key, "label": term.label, "public_id": term.public_id}
        for term in contexto_projection.PROJECTION_TERMS
    ]
    payload = {
        "schema_version": 2,
        "app_version": __version__,
        "sources": {
            name: hashlib.sha256(
                (ROOT / "cat_de_roman_esti/fixtures" / name)
                .read_bytes()
                .replace(b"\r\n", b"\n")
                .replace(b"\r", b"\n")
            ).hexdigest()
            for name in SOURCES
        },
        "labels": {node_id: service.display_label(node_id) for node_id in service.all_ids()},
        "category_labels": CATEGORY_LABELS,
        "category_order": list(known_keys()),
        "letter_ranges": letter_ranges,
        "label_patterns": {label: _label_pattern(label) for label in sorted(group_labels)},
        "nodes": [plain(asdict(node)) for node in service.graph.nodes.values()],
        "edges": [plain(asdict(edge)) for edge in service.graph.edges],
        "normalization_map": normalized,
        "accent_normalization_map": accented,
        "casefold_map": casefolded,
        "normalized_index": service._index,
        "pack_ranked": pack.ranked,
        "pack_items": [
            {
                "game": i.game,
                "id": i.id,
                "category": i.category or "",
                "difficulty": i.difficulty,
                "source": i.source,
                "status": i.status,
                "payload": plain(i.payload),
                "pilot_score": i._pilot_score,
                "pilot_eligible": i._pilot_eligible,
                "selection_weight": i._selection_weight,
            }
            for i in pack_items
        ],
        "contexto_data": {
            "projection_terms": projection_terms,
            "neighborhoods": {
                k: asdict(v) for k, v in contexto_projection.PROJECTION_NEIGHBORHOODS.items()
            },
            "feedback_proxies": contexto_feedback.COMMON_FEEDBACK_PROXIES,
            "ingredient_policies": {
                k: asdict(v) for k, v in contexto_feedback.INGREDIENT_FEEDBACK_POLICIES.items()
            },
            "exact_pairs": sorted(map(list, contexto_feedback.EXACT_TARGET_FEEDBACK_PAIRS)),
        },
        "lant_captions": {
            a + "\u0000" + b: lant_relations.caption(service, a, b)
            for a in service.all_ids()
            for b in service.neighbor_ids(a)
        },
        "discovery_world": {
            **world.catalog.model_dump(),
            "recipe_hash": world.recipe_hash,
            "mechanics": world.mechanics,
        },
        "recipe_extensions": json.loads(
            (ROOT / "cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json").read_text()
        ),
        "alchimie_projections": {},
        "metadata": metadata,
        "manifest": fixture_manifest(),
        "boards": [
            {
                "game": board.game,
                "catalog_id": board._catalog_id,
                "source_id": board._source_id,
                "category": board.category,
                "difficulty": board.difficulty,
                "overall_score": board._standard_score,
                "starter_score": board._starter_score,
                "overall_rank": board._standard_rank,
                "starter_rank": board._starter_rank,
                "starter_safe": board._starter_eligible,
                "payload": plain(board.payload),
            }
            for game in ("intrusul", "perechi")
            for board in catalog.pool(game)
        ],
    }
    return (
        json.dumps(plain(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = export_bytes()
    pin = (
        "// Code generated by scripts/export_go_content.py; DO NOT EDIT.\n"
        "package content\n\n"
        f'const bundledSHA256 = "{hashlib.sha256(expected).hexdigest()}"\n'
    ).encode()
    if args.check:
        if (
            not OUTPUT.is_file()
            or OUTPUT.read_bytes() != expected
            or not PIN.is_file()
            or PIN.read_bytes() != pin
        ):
            parser.exit(1, "Go private content is stale; run scripts/export_go_content.py.\n")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(expected)
        PIN.write_bytes(pin)
    print(f"Go private content {'current' if args.check else 'exported'}: {len(expected)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
