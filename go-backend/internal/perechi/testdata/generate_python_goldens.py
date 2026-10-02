#!/usr/bin/env python3
"""Regenerate pair/group API goldens against the current Python reference.

Run explicitly with the repository Python environment. Native tests read only
the frozen JSON files and do not need Python or Django at runtime.
"""

import itertools
import json
import logging
import os
import platform
import sys
from pathlib import Path
from urllib.parse import urlencode


def main():
    root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(root))
    os.environ["DJANGO_SETTINGS_MODULE"] = "cat_de_roman_esti.web.settings"
    os.environ["CAT_ACCOUNTS_ENABLED"] = "0"
    import django

    django.setup()
    logging.getLogger("django.request").setLevel(logging.CRITICAL)
    from django.test import Client

    from cat_de_roman_esti.wordgames import conexiuni, perechi
    from cat_de_roman_esti.wordgames.packs import GamesPack, get_pack

    client = Client()

    def normalized(response):
        body = json.loads(response.content)
        if "game_id" in body:
            body["game_id"] = "<session>"
        return {"status": response.status_code, "body": body}

    def call(case, action, url, ids=None):
        response = (
            client.get(url)
            if action == "get"
            else client.post(
                url, {} if ids is None else {"ids": ids}, content_type="application/json"
            )
        )
        case["steps"].append({"action": action, "ids": ids or [], **normalized(response)})
        return response

    pcases = []
    previous = ""
    for name, seed, daily, category, starter, mode in [
        ("win", 17, "", "", False, "win"),
        ("loss", 18, "", "", False, "loss"),
        ("starter", 7, "", "", True, "win"),
        ("theme", 19, "", "muzica", False, "win"),
        ("daily", 999, "2026-10-03", "", True, "win"),
    ] + [(f"rotation-{i}", 31, "", "", False, "rotation") for i in range(7)]:
        case = {
            "name": name,
            "seed": str(seed),
            "daily": daily,
            "category": category,
            "starter": starter,
            "previous_case": len(pcases) - 1 if mode == "rotation" and previous else -1,
            "steps": [],
        }
        query = {"seed": seed, "starter": int(starter)}
        if daily:
            query["daily"] = daily
        if category:
            query["category"] = category
        if mode == "rotation" and previous:
            query["previous_game_id"] = previous
        response = client.post("/api/wordgames/perechi/games?" + urlencode(query))
        case["create"] = normalized(response)
        if response.status_code == 200:
            identifier = response.json()["game_id"]
            game = perechi.store.get(identifier)
            url = f"/api/wordgames/perechi/games/{identifier}"
            call(case, "get", url)
            if mode == "rotation":
                previous = identifier
            else:
                call(case, "hint", url + "/hint")
                pairs = [list(p.members) for p in game.pairs]
                allids = sorted(game.order)
                valid = {frozenset(p) for p in pairs}
                wrong = [
                    list(p) for p in itertools.combinations(allids, 2) if frozenset(p) not in valid
                ]
                call(case, "match", url + "/match", wrong[0])
                call(case, "match", url + "/match", wrong[0][::-1])
                call(case, "match", url + "/match", wrong[1])
                call(case, "hint", url + "/hint")
                call(case, "hint", url + "/hint")
                if mode == "loss":
                    for ids in wrong[2:6]:
                        call(case, "match", url + "/match", ids)
                else:
                    for index in [2, 0, 3, 1]:
                        call(case, "match", url + "/match", pairs[index][::-1])
                call(case, "get", url)
                call(case, "match", url + "/match", pairs[0])
                call(case, "hint", url + "/hint")
        pcases.append(case)
    cxspec = [
        ("curated-usor", 17, "", "", "usor", None, "win"),
        ("curated-normal", 17, "", "", "normal", None, "win"),
        ("curated-greu", 17, "", "", "greu", None, "loss"),
        ("themed", 33, "", "viata_de_roman", "normal", None, "win"),
        ("daily", 0, "2026-10-03", "", "normal", None, "win"),
    ]
    cxspec += [
        (f"mined-{difficulty}", 13, "", "", difficulty, 0, "win")
        for difficulty in ["usor", "normal", "greu"]
    ]
    cxspec += [
        ("global-daily-seven", 0, "2026-10-03", "", "normal", 7, "win"),
        ("global-daily-eight", 0, "2026-10-03", "", "normal", 8, "win"),
        ("scoped-daily-three", 0, "2026-10-03", "viata_de_roman", "normal", 3, "win"),
        ("scoped-daily-four", 0, "2026-10-03", "viata_de_roman", "normal", 4, "win"),
    ]
    ccases = []
    original = conexiuni.get_pack
    for name, seed, daily, category, difficulty, limit, mode in cxspec:
        case = {
            "name": name,
            "seed": str(seed),
            "daily": daily,
            "category": category,
            "difficulty": difficulty,
            "pack_limit": limit,
            "steps": [],
        }
        if limit is None:
            conexiuni.get_pack = original
        else:
            items = [
                item
                for item in get_pack().pool(
                    "conexiuni", category=category or None, difficulty=difficulty
                )
                if item._pilot_eligible
            ][:limit]
            selected = GamesPack(items, ranked=True)
            conexiuni.get_pack = lambda selected=selected: selected
        query = {"seed": seed, "difficulty": difficulty}
        if daily:
            query["daily"] = daily
        if category:
            query["category"] = category
        response = client.post("/api/wordgames/conexiuni/games?" + urlencode(query))
        case["create"] = normalized(response)
        if response.status_code == 200:
            identifier = response.json()["game_id"]
            game = conexiuni.store.get(identifier)
            url = f"/api/wordgames/conexiuni/games/{identifier}"
            groups = [game.groups[key] for key in sorted(game.groups)]
            call(case, "get", url)
            call(case, "clue", url + "/clue")
            wrong1 = groups[0][:3] + groups[1][:1]
            wrong2 = groups[0][:2] + groups[1][:2]
            wrong3 = [group[0] for group in groups]
            wrong4 = groups[2][:2] + groups[3][:2]
            call(case, "guess", url + "/guess", wrong1)
            call(case, "guess", url + "/guess", wrong1[::-1])
            call(case, "guess", url + "/guess", wrong2)
            call(case, "clue", url + "/clue")
            call(case, "clue", url + "/clue")
            call(case, "guess", url + "/guess", wrong3)
            call(case, "clue", url + "/clue")
            call(case, "clue", url + "/clue")
            if mode == "loss":
                call(case, "guess", url + "/guess", wrong4)
            else:
                for index in [2, 0, 3, 1]:
                    call(case, "guess", url + "/guess", groups[index][::-1])
            call(case, "get", url)
            call(case, "guess", url + "/guess", groups[0])
            call(case, "clue", url + "/clue")
        ccases.append(case)
    conexiuni.get_pack = original
    for game, cases in [("perechi", pcases), ("conexiuni", ccases)]:
        path = root / "go-backend/internal" / game / "testdata/python-goldens.json"
        path.write_text(
            json.dumps(
                {"python": platform.python_version(), "cases": cases},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )
        print(
            game,
            len(cases),
            "cases",
            sum(len(c["steps"]) + 1 for c in cases),
            "responses",
            path.stat().st_size,
            "bytes",
        )


if __name__ == "__main__":
    main()
