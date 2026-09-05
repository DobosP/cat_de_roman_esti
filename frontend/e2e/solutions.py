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


def solution(game: str) -> dict:
    module = importlib.import_module(f"cat_de_roman_esti.wordgames.{game}")
    query = {"seed": "38", "difficulty": "usor"}
    if game in {"intrusul", "perechi"}:
        query["starter"] = "1"
    response = Client().post(f"/api/wordgames/{game}/games?{urlencode(query)}")
    if response.status_code != 200:
        raise ValueError(f"{game} create failed: {response.status_code}")
    initial = response.json()
    session = module.store.get(initial["game_id"])
    svc = get_service()
    steps = []

    def tiles(action: str, ids: list[str]) -> None:
        payload = {"id": ids[0]} if game == "intrusul" else {"ids": ids}
        if game == "alchimie":
            payload = dict(zip(("a", "b"), ids, strict=True))
        steps.append({"action": action, "labels": [svc.label(i) for i in ids],
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
        practice = {"action": "guess", "labels": [svc.label(session.members[0])],
                    "payload": {"id": session.members[0]}}
    elif game == "perechi":
        ids = [session.pairs[0].members[0], session.pairs[1].members[0]]
        practice = {"action": "match", "labels": [svc.label(i) for i in ids],
                    "payload": {"ids": ids}}
    elif game == "conexiuni":
        groups = list(session.groups.values())
        ids = [*groups[0][:3], groups[1][0]]
        practice = {"action": "guess", "labels": [svc.label(i) for i in ids],
                    "payload": {"ids": ids}}
    elif game == "contexto":
        node = next(n for n in svc.predecessor_ids(session.target)
                    if n != session.target and svc.resolve(svc.label(n)) == n)
        practice = {"action": "guess", "payload": {"text": svc.label(node)}}
    initial.pop("game_id")
    return {"initial": initial, "steps": steps, "practice": practice}


if __name__ == "__main__":
    if sys.argv[1] == "--write-starts":
        games = ("alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant")
        starts = {game: solution(game)["initial"] for game in games}
        Path(__file__).with_name("seeded-starts.json").write_text(
            json.dumps(starts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    else:
        print(json.dumps(solution(sys.argv[1]), ensure_ascii=False))
