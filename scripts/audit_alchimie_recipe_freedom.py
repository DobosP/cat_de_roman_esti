#!/usr/bin/env python3
"""Audit the exact proposed serving books before independently approved publication."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

import django  # noqa: E402

django.setup()

from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames import recipe_extensions as R  # noqa: E402
from cat_de_roman_esti.wordgames.packs import get_pack  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402

SOURCES = (
    "cat_de_roman_esti/wordgames/alchimie.py",
    "cat_de_roman_esti/wordgames/recipe_extensions.py",
    "cat_de_roman_esti/wordgames/packs.py",
    "cat_de_roman_esti/wordgames/service.py",
    "scripts/build_alchimie_recipe_extensions.py",
    "scripts/audit_alchimie_recipe_freedom.py",
    "scripts/audit_alchimie_projections.py",
    "scripts/apply_rereview.py",
    "frontend/src/screens/Alchimie.tsx",
)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile(seeds, target, projection):
    owned = set(seeds)
    openings = [pair for pair, outputs in projection.recipes.items()
                if set(pair) <= owned and set(outputs) - owned]
    active = owned & {node for pair in projection.recipes for node in pair}
    concepts = owned | {
        node for pair, outs in projection.recipes.items() for node in (*pair, *outs)
    }
    return {
        "recipes": len(projection.recipes), "par": projection.par,
        "stored_core_routes": len(projection.routes), "projected_concepts": len(concepts),
        "starting_pair_total": len(list(combinations(seeds, 2))),
        "productive_openings": len(openings), "active_seeds": len(active),
        "active_starting_pairs": len(active) * (len(active) - 1) // 2,
        "target_producing_pairs": sum(target in outputs for outputs in projection.recipes.values()),
    }


def audit(catalog_path: Path) -> dict:
    catalog = json.loads(catalog_path.read_bytes())
    R.validate_catalog(catalog)
    service = get_service()
    boards = []
    changed = []
    with patch.object(R, "CATALOG_PATH", catalog_path):
        for item in sorted(get_pack().pool("alchimie"), key=lambda item: item.id):
            seeds, target = item.payload["seeds"], item.payload["target"]
            core = A._build_recipe_projection(seeds, target, item.category)
            live = A._build_playable_recipe_projection(seeds, target, item.category)
            if core is None or live is None:
                raise ValueError(f"Missing projection: {item.id}")
            if core.par != live.par or core.routes != live.routes:
                raise ValueError(f"Core routes/par changed: {item.id}")
            if any(live.recipes.get(pair) != outputs for pair, outputs in core.recipes.items()):
                raise ValueError(f"Core recipe changed: {item.id}")
            plan = A._minimum_projected_plan(set(seeds), target, live.recipes)
            if plan is None or len(plan) != core.par:
                raise ValueError(f"Playable par changed: {item.id}")
            added = [
                {"pair": list(pair), "pair_labels": [service.label(n) for n in pair],
                 "outputs": list(outputs), "output_labels": [service.label(n) for n in outputs]}
                for pair, outputs in live.recipes.items() if pair not in core.recipes
            ]
            before, after = profile(seeds, target, core), profile(seeds, target, live)
            if before["projected_concepts"] != after["projected_concepts"]:
                raise ValueError(f"Concept space changed: {item.id}")
            if len(live.recipes) > A.MAX_RECIPE_PAIRS:
                raise ValueError(f"Recipe bound changed: {item.id}")
            if added:
                changed.append(item.id)
            session = A.AlchimieSession(
                seeds=seeds, target=target, target_depth=live.par, difficulty=item.difficulty,
                category=item.category, pack_id=item.id, recipes=live.recipes, routes=live.routes,
            )
            for seed in seeds:
                session.add(seed, None)
            public = A._state_payload("review-only", session)
            if public["target"]["id"] is not None or "recipes" in public or "routes" in public:
                raise ValueError(f"Answer disclosure: {item.id}")
            if public["recipe_summary"]["pairs"] != len(live.recipes):
                raise ValueError(f"Public count differs: {item.id}")
            boards.append({
                "id": item.id, "category": item.category, "target": service.label(target),
                "before": before, "after": after, "additions": added,
                "core_preserved": True, "exact_par_preserved": True, "target_id_hidden": True,
            })
    accepted = {b["id"]: len(b["additions"]) for b in catalog["boards"]}
    actual = {b["id"]: len(b["additions"]) for b in boards if b["additions"]}
    if actual != accepted:
        raise ValueError("Serving did not apply the exact approved additions")
    totals = {}
    for phase in ("before", "after"):
        totals[phase] = {
            key: sum(row[phase][key] for row in boards)
            for key in ("recipes", "productive_openings", "starting_pair_total", "active_seeds",
                        "active_starting_pairs", "target_producing_pairs")
        }
        totals[phase]["single_opening_boards"] = sum(
            row[phase]["productive_openings"] == 1 for row in boards
        )
        totals[phase]["single_ending_boards"] = sum(
            row[phase]["target_producing_pairs"] == 1 for row in boards
        )
    return {
        "kind": "alchimie-reviewed-freedom-audit-v1",
        "candidate_sha256": catalog["candidate_sha256"],
        "proposed_catalog_sha256": file_sha(catalog_path),
        "runtime_sources": [{"path": path, "sha256": file_sha(ROOT / path)} for path in SOURCES],
        "changed_board_ids": changed, "totals": totals,
        "scope": "Existing target challenges; no new concepts, side discoveries or free-play mode.",
        "score_policy": {"failed_attempt_penalty": 0, "extra_successful_craft_penalty": 120,
                         "hint_penalty": 150, "score_floor": 100},
        "boards": boards,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    if args.json.resolve() == args.catalog.resolve():
        parser.error("audit must not overwrite its input")
    result = audit(args.catalog)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "changed_boards": len(result["changed_board_ids"]), "totals": result["totals"],
    }))


if __name__ == "__main__":
    main()
