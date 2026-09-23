"""Test-process-only solutions for deterministic browser journeys.

Creates an independent in-process session with the browser's explicit seed. Private
answers never enter the web app, its bundle, a test endpoint, or browser storage.
The browser tests still perform every winning action against the real running BFF.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from itertools import combinations
from pathlib import Path
from urllib.parse import urlencode

os.environ["DJANGO_SETTINGS_MODULE"] = "cat_de_roman_esti.web.settings"
os.environ["CAT_ACCOUNTS_ENABLED"] = "0"
os.environ["CAT_DEBUG"] = "1"
os.environ["ROEDU_API_URL"] = ""
os.environ["ROEDU_API_KEY"] = ""

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402


def solution(game: str, pack_id: str | None = None, daily: str | None = None) -> dict:
    module = importlib.import_module(f"cat_de_roman_esti.wordgames.{game}")
    query = {"seed": "38", "difficulty": "usor"}
    if pack_id is not None:
        if game != "alchimie":
            raise ValueError("named browser fixtures currently support Alchimie only")
        from cat_de_roman_esti.wordgames.packs import get_pack
        from tests.content_scenarios import alchimie_seed

        items = [item for item in get_pack().pool(game) if item.id == pack_id]
        if len(items) != 1:
            raise ValueError(f"named browser fixture requires approved challenge {pack_id}")
        item = items[0]
        query = {
            "seed": str(alchimie_seed(
                pack_id, difficulty=item.difficulty, category=item.category,
            )),
            "difficulty": item.difficulty,
            "category": item.category,
        }
    if daily is not None:
        # The server derives a daily's seed from the day, so the browser's seed is ignored.
        query["daily"] = daily
    if game in {"intrusul", "perechi"}:
        query["starter"] = "1"
    response = Client().post(f"/api/wordgames/{game}/games?{urlencode(query)}")
    if response.status_code != 200:
        raise ValueError(f"{game} create failed: {response.status_code}")
    initial = response.json()
    session = module.store.get(initial["game_id"])
    if pack_id is not None and session.pack_id != pack_id:
        raise ValueError(f"public seed selected {session.pack_id}, expected {pack_id}")
    svc = get_service()
    # Tiles carry the served display label; Alchimie inventory labels stay raw.
    label = svc.label if game == "alchimie" else svc.display_label
    steps = []
    hint_setup = None

    def tiles(action: str, ids: list[str]) -> None:
        payload = {"id": ids[0]} if game == "intrusul" else {"ids": ids}
        if game == "alchimie":
            payload = dict(zip(("a", "b"), ids, strict=True))
        steps.append({"action": action, "labels": [label(i) for i in ids],
                      "payload": payload})

    if game == "intrusul":
        tiles("guess", [session.intruder])
    elif game == "perechi":
        for pair in session.pairs:
            tiles("match", list(pair.members))
    elif game == "conexiuni":
        for group in session.groups.values():
            tiles("guess", list(group))
    elif game == "alchimie":
        plan = module._minimum_projected_plan(set(session.owned), session.target, session.recipes)
        if not plan:
            raise ValueError("browser fixture needs a nonempty crafting plan")
        for pair in plan:
            tiles("combine", list(pair))
        # Only the test process reads this private projection. These inputs are
        # already-owned seeds; no output/target IDs or recipe map leave this helper.
        hint_setup = [
            {"a": a, "b": b}
            for a, b in combinations(sorted(session.owned), 2)
            if not session.recipes.get(module._pair_key(a, b))
        ]
        if len(hint_setup) < 2 * module.NUDGE_AFTER_FRUITLESS:
            raise ValueError("browser fixture needs enough barren pairs for both hint stages")
    elif game == "contexto":
        steps.append({"action": "guess", "payload": {"text": svc.label(session.target)}})
    elif game == "lant":
        distances = svc.distances_to(session.target)
        current = session.start
        while current != session.target:
            current = next(node for node in sorted(svc.neighbor_ids(current))
                           if distances.get(node) == distances[current] - 1)
            steps.append({"action": "move", "payload": {"text": svc.label(current)}})
    else:
        raise ValueError(f"unknown game: {game}")
    practice = steps[0]
    if game == "intrusul":
        practice = {"action": "guess", "labels": [label(session.members[0])],
                    "payload": {"id": session.members[0]}}
    elif game == "perechi":
        ids = [session.pairs[0].members[0], session.pairs[1].members[0]]
        practice = {"action": "match", "labels": [label(i) for i in ids],
                    "payload": {"ids": ids}}
    elif game == "conexiuni":
        groups = list(session.groups.values())
        ids = [*groups[0][:3], groups[1][0]]
        practice = {"action": "guess", "labels": [label(i) for i in ids],
                    "payload": {"ids": ids}}
    elif game == "contexto":
        node = next(n for n in svc.predecessor_ids(session.target)
                    if n != session.target and svc.resolve(svc.label(n)) == n)
        practice = {"action": "guess", "payload": {"text": svc.label(node)}}
    initial.pop("game_id")
    result = {"initial": initial, "steps": steps, "practice": practice}
    if hint_setup is not None:
        result["hint_setup"] = hint_setup
    if pack_id is not None:
        result.update(pack_id=pack_id, query=query)
    return result


if __name__ == "__main__":
    if sys.argv[1] == "--write-starts":
        games = ("alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant")
        starts = {game: solution(game)["initial"] for game in games}
        Path(__file__).with_name("seeded-starts.json").write_text(
            json.dumps(starts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    else:
        flags = [arg for arg in sys.argv[2:] if arg.startswith("--daily=")]
        daily = flags[0].split("=", 1)[1] if flags else None
        rest = [arg for arg in sys.argv[1:] if arg not in flags]
        print(json.dumps(solution(rest[0], rest[1] if len(rest) > 1 else None, daily),
                         ensure_ascii=False))
