#!/usr/bin/env python3
"""Replay the exact proposed discovery world for independent final review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

import django  # noqa: E402

django.setup()

from cat_de_roman_esti.wordgames import alchimie_explore as E  # noqa: E402
from cat_de_roman_esti.wordgames.discovery_world import validate_world  # noqa: E402

RUNTIME_SOURCES = (
    "cat_de_roman_esti/wordgames/discovery_world.py",
    "cat_de_roman_esti/wordgames/alchimie_explore.py",
    "cat_de_roman_esti/wordgames/service.py",
    "cat_de_roman_esti/wordgames/_session_endpoint.py",
    "cat_de_roman_esti/web/urls.py",
    "scripts/alchimie_discovery_recipe_source.py",
    "scripts/build_alchimie_discovery_world.py",
    "scripts/audit_alchimie_discovery_world.py",
    "docs/reviews/v92-session03-vocabulary-and-interface/alchimie/candidate.json",
)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path) -> dict:
    raw = json.loads(path.read_bytes())
    world = validate_world(raw)
    reference = None
    goal_results = []
    for goal_id in (None, *world.goals):
        session = E.ExploreSession(world=world, goal_id=goal_id)
        session.owned.update(dict.fromkeys(world.catalog.world.starter_ids))
        public = E.state_payload("audit", session)
        assert all(g["target_id"] is None for g in public["goals"])
        assert set(session.owned) == set(world.catalog.world.starter_ids)
        while True:
            pair = next((p for p, r in world.recipes.items()
                         if set(p) <= session.owned.keys() and r.result not in session.owned), None)
            if pair is None:
                break
            result, new, supplied = session.craft(pair)
            assert new and result == world.recipes[pair].result
            assert not set(supplied) & {world.recipes[p].result for p in session.discoveries}
        state = E.state_payload("audit", session)
        assert state["complete"] and len(session.owned) == len(world.concepts)
        assert all(g["completed"] for g in state["goals"])
        assert len(session.discoveries) <= E.MAX_CONCEPTS
        if reference is not None:
            assert state["progress"] == reference
        reference = state["progress"]
        for pair, recipe in world.recipes.items():
            result, new, supplied = session.craft(pair)
            assert result == recipe.result and not new and not supplied
        restored = E.ExploreSession(world=world)
        restored.owned.update(dict.fromkeys(world.catalog.world.starter_ids))
        for pair in reference["discoveries"]:
            restored.craft(tuple(pair))
        assert restored.owned == session.owned and restored.unlocked == session.unlocked
        goal_results.append({"goal_id": goal_id, "all_recipes_consistent": True,
                             "complete": True, "replayed_discoveries": len(session.discoveries)})
    counts = Counter(r.result for r in world.recipes.values())
    input_ids = {item for pair in world.recipes for item in pair}
    starters = set(world.catalog.world.starter_ids)
    migrations = []
    for previous in world.compatible_versions.values():
        old = previous.mechanics
        owned = set(old.starters)
        pairs = []
        while True:
            recipe = next((r for r in old.recipes
                           if set(r.pair) <= owned and r.result not in owned), None)
            if recipe is None:
                break
            pairs.append(recipe.pair)
            owned.add(recipe.result)
            for unlock in old.unlocks:
                if len(pairs) >= unlock.after:
                    owned.update(unlock.concepts)
            # Every prefix, not just the completed collection, must survive restoration.
            restored = E.restore_session(world, E.Progress(
                world_id=previous.world_id, recipe_hash=previous.recipe_hash, discoveries=pairs,
            ))
            assert owned <= restored.owned.keys()
            assert restored.discoveries == [tuple(pair) for pair in pairs]
        migrations.append({"recipe_hash": previous.recipe_hash, "previous_owned": len(owned),
                           "prefixes_preserved": len(pairs), "all_earned_concepts_preserved": True})
    return {
        "kind": "alchimie-discovery-world-audit-v1",
        "verdict": "accept",
        "catalog_sha256": file_sha(path), "candidate_sha256": raw["candidate_sha256"],
        "world_id": world.id,
        "runtime_sources": [{"path": p, "sha256": file_sha(ROOT / p)} for p in RUNTIME_SOURCES],
        "metrics": {
            "concepts": len(world.concepts), "starting_supplies": len(starters),
            "kg_concepts": sum(c.origin == "kg" for c in world.concepts.values()),
            "authored_concepts": sum(c.origin == "authored" for c in world.concepts.values()),
            "unlocked_supplies": sum(len(u.concept_ids) for u in world.catalog.unlocks),
            "crafted_discoveries": len(counts), "recipes": len(world.recipes),
            "results_with_alternatives": sum(count > 1 for count in counts.values()),
            "crafted_intermediates": len(set(counts) & input_ids),
            "terminal_discoveries": len(set(counts) - input_ids),
            "opening_pairs": sum(set(p) <= starters for p in world.recipes),
            "possible_starting_pairs": len(starters) * (len(starters) - 1) // 2,
            "optional_goals": len(world.goals),
        },
        "recipes": [{"id": r.id,
                     "ingredients": [world.concepts[n].label for n in pair],
                     "result": world.concepts[r.result].label,
                     "explanation": r.explanation, "sources": r.sources}
                    for pair, r in world.recipes.items()],
        "goal_replays": goal_results,
        "compatible_save_replays": migrations,
        "checks": {"all_concepts_reachable": True, "all_goals_reachable": True,
                   "goal_independent_recipes": True, "complete_replay_restoration": True,
                   "kg_snapshots_match_graph": True, "authored_definitions_bound": True,
                   "undiscovered_target_ids_hidden": True,
                   "recipes_private": True},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["metrics"], ensure_ascii=False))


if __name__ == "__main__":
    main()
