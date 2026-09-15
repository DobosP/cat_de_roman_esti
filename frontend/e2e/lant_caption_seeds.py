"""Find public seeds for caption journeys without fixing a mutable pool position.

Only this test process reads pack IDs and native routes. The browser creates and
plays an ordinary seeded game against the real BFF; no test endpoint is installed.
"""

from __future__ import annotations

import json
import os
import random
import sys
from urllib.parse import urlencode

os.environ["DJANGO_SETTINGS_MODULE"] = "cat_de_roman_esti.web.settings"
os.environ["CAT_ACCOUNTS_ENABLED"] = "0"
os.environ["CAT_DEBUG"] = "1"
os.environ["ROEDU_API_URL"] = ""
os.environ["ROEDU_API_KEY"] = ""

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import lant  # noqa: E402
from cat_de_roman_esti.wordgames.packs import get_pack  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402


def journey(pack_id: str) -> dict:
    items = [item for item in get_pack().pool("lant") if item.id == pack_id]
    if len(items) != 1:
        raise ValueError(f"caption journey requires approved round {pack_id}")
    item = items[0]
    for seed in range(10_000):
        selected = lant._pick_curated(
            random.Random(seed), daily=None, category=item.category,
            difficulty=item.difficulty, exclude_ids=set(),
        )
        if selected is not None and selected.id == pack_id:
            break
    else:
        raise ValueError(f"caption round is not naturally selectable: {pack_id}")
    query = {"seed": seed, "category": item.category, "difficulty": item.difficulty}
    response = Client().post(f"/api/wordgames/lant/games?{urlencode(query)}")
    if response.status_code != 200:
        raise ValueError(f"caption journey create failed: {response.status_code}")
    initial = response.json()
    session = lant.store.get(initial["game_id"])
    if session.pack_id != pack_id:
        raise ValueError(f"public seed selected {session.pack_id}, expected {pack_id}")
    service = get_service()
    distances = service.distances_to(session.target)
    routes = []

    def walk(path: list[str]) -> None:
        if path[-1] == session.target:
            routes.append([{"id": node, "label": service.label(node)} for node in path])
            return
        for node in sorted(service.neighbor_ids(path[-1])):
            if distances.get(node) == distances[path[-1]] - 1:
                walk([*path, node])

    walk([session.start])
    return {"pack_id": pack_id, "query": query, "start": initial["start"],
            "target": initial["target"], "routes": routes}


if __name__ == "__main__":
    print(json.dumps(journey(sys.argv[1]), ensure_ascii=False))
