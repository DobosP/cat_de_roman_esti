"""Re-record the existing Alchimie mechanics journeys from the Python oracle.

The checked-in request sequences define the journeys. Every response digest is
computed afresh by Django. Projection, mining and exploration vectors stay in
the same document because this command updates the challenge hint semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "go-backend/internal/alchimie/testdata/python_parity_rules_v2.json"


def normalize(value):
    if isinstance(value, dict):
        return {
            key: "<session>" if key == "game_id" else normalize(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")
    if os.environ.get("CAT_ACCOUNTS_ENABLED", "").lower() in {"1", "true", "yes", "on"}:
        raise SystemExit("Mechanics recording requires the anonymous oracle.")
    import django

    django.setup()
    from django.test import Client

    document = json.loads(OUTPUT.read_bytes())
    client = Client()
    count = 0
    base = "/api/wordgames/alchimie/games"
    for journey in document["challenge_journeys"]:
        game_id = None
        for step in journey:
            action = step["action"]
            if action == "create":
                response = client.post(f"{base}?seed={step['seed']}")
            elif action == "combine":
                response = client.post(
                    f"{base}/{game_id}/combine",
                    {"a": step["a"], "b": step["b"]},
                    content_type="application/json",
                )
            elif action in {"hint", "reset"}:
                response = client.post(f"{base}/{game_id}/{action}")
            else:
                raise ValueError(f"Unknown challenge action {action!r}")
            if response.status_code != 200:
                raise ValueError(f"Oracle {action} returned {response.status_code}")
            body = response.json()
            if action == "create":
                game_id = body["game_id"]
            data = json.dumps(
                normalize(body), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            ).encode()
            step["hash"] = hashlib.sha256(data).hexdigest()
            count += 1
    OUTPUT.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Recorded {count} Alchimie challenge responses from Django.")


if __name__ == "__main__":
    main()
