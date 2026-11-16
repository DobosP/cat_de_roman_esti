"""Record immutable screenshot stimuli from the offline rules-2 Python API."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

os.environ["DJANGO_SETTINGS_MODULE"] = "cat_de_roman_esti.web.settings"
os.environ["CAT_ACCOUNTS_ENABLED"] = "0"
os.environ["CAT_SUBMISSIONS_ENABLED"] = "0"

import django  # noqa: E402
from django.test import Client  # noqa: E402

django.setup()
from cat_de_roman_esti.wordgames import intrusul  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GAMES = ("intrusul", "perechi", "conexiuni", "lant", "contexto", "alchimie")
CLOCK = "2026-11-16T10:00:00.000Z"
DAY = CLOCK[:10]


def collect():
    client = Client()
    starts = {}
    requests = {}
    for game in GAMES:
        path = f"/api/wordgames/{game}/games?daily={DAY}"
        response = client.post(path)
        if response.status_code != 200:
            raise RuntimeError(f"{path}: {response.status_code}")
        state = response.json()
        original_id = state["game_id"]
        state["game_id"] = f"visual-{game}"
        if state.get("daily") != DAY or state.get("steps") != 0:
            raise RuntimeError(f"Expected an untouched rules-2 daily at {path}")
        starts[game] = state
        requests[game] = path

        if game == "intrusul":
            with intrusul.store.transaction(original_id) as session:
                answer = session.intruder
            request = {"id": answer}
            result = client.post(
                f"/api/wordgames/intrusul/games/{original_id}/guess",
                request,
                content_type="application/json",
            )
            win = result.json()
            win["game_id"] = state["game_id"]
            if result.status_code != 200 or not win.get("perfect"):
                raise RuntimeError("Expected an Intrusul Perfect result")

    oracle = {}
    for game in GAMES:
        relative = f"cat_de_roman_esti/wordgames/{game}.py"
        oracle[relative] = sha256((ROOT / relative).read_bytes()).hexdigest()
    bundled = ROOT / "go-backend/internal/content/bundled.json"
    return {
        "schema": 1,
        "rules_version": 2,
        "clock": CLOCK,
        "provenance": {
            "commit": subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
            ).strip(),
            "oracle_source_sha256": oracle,
            "content_source_pins": dict(sorted(json.loads(bundled.read_bytes())["sources"].items())),
        },
        "requests": requests,
        "starts": starts,
        "intrusul_result": {"request": request, "body": win},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = collect()
    if not re.fullmatch(r"[a-f0-9]{40}", fixture["provenance"]["commit"]):
        raise RuntimeError("Expected an exact producer commit")
    args.output.write_text(
        json.dumps(fixture, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
