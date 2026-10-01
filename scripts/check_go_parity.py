"""Differentially replay anonymous Intrusul HTTP journeys against Django and Go.

No network listener, database, production service or account is used. Only random
session IDs are normalized. --benchmark adds aggregate local timings/peak memory,
not a full-arcade capacity claim. The Go executable must be built beforehand.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import resource
import subprocess
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/wordgames/intrusul/games"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if os.environ.get("CAT_ACCOUNTS_ENABLED", "").lower() in {"1", "true", "yes", "on"}:
        parser.exit(1, "Parity requires accounts OFF.\n")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")
    import django

    django.setup()
    logging.getLogger("django.request").setLevel(logging.ERROR)
    from django.test import Client

    from cat_de_roman_esti.wordgames import intrusul
    from cat_de_roman_esti.wordgames.categories import CATEGORY_LABELS
    from cat_de_roman_esti.wordgames.service import SessionStore

    intrusul.store = SessionStore()
    client = Client()
    child = subprocess.Popen(
        [str(args.binary.resolve()), "--replay"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    aliases: dict[str, str] = {}
    times_python: list[int] = []
    times_go: list[int] = []
    count = 0
    go_peak = 0

    def normalize(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: "<session>" if key == "game_id" else normalize(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    def request(method: str, path: str, raw: str = "") -> dict:
        nonlocal count, go_peak
        split = urlsplit(path)
        mapped_path = split.path
        for python_id, go_id in aliases.items():
            mapped_path = mapped_path.replace(python_id, go_id)
        query = split.query
        if "previous_game_id" in query:
            query = urlencode([
                (key, aliases.get(value, value))
                for key, value in parse_qsl(query, keep_blank_values=True)
            ])
        go_path = urlunsplit(("", "", mapped_path, query, ""))
        assert child.stdin is not None and child.stdout is not None
        child.stdin.write(json.dumps({"method": method, "path": go_path, "body": raw}) + "\n")
        child.stdin.flush()
        started = time.perf_counter_ns()
        response = client.generic(method, path, data=raw.encode(), content_type="application/json")
        elapsed = time.perf_counter_ns() - started
        line = child.stdout.readline()
        if not line:
            raise AssertionError(f"Go replay exited during {method} {path}")
        native = json.loads(line)
        expected = None if not response.content else response.json()
        if response.status_code == 200 and isinstance(expected, dict) and "game_id" in expected:
            aliases[expected["game_id"]] = native["body"]["game_id"]
        if response.status_code != native["status"] or normalize(expected) != normalize(
            native["body"]
        ):
            raise AssertionError(
                f"Parity mismatch: {method} {path} body={raw!r}\n"
                f"Python {response.status_code}: {normalize(expected)!r}\n"
                f"Go {native['status']}: {normalize(native['body'])!r}"
            )
        count += 1
        if response.status_code == 200:
            times_python.append(elapsed)
            times_go.append(native["duration_ns"])
        try:
            for row in Path(f"/proc/{child.pid}/status").read_text().splitlines():
                if row.startswith("VmHWM:"):
                    go_peak = max(go_peak, int(row.split()[1]) * 1024)
        except FileNotFoundError:
            pass
        return expected or {}

    try:
        for seed in [*range(-20, 80), -(2**130), 2**200 + 17]:
            request("POST", f"{BASE}?seed={seed}")
        for category in CATEGORY_LABELS:
            for starter in (0, 1):
                request("POST", f"{BASE}?seed=17&category={category}&starter={starter}")
                request("POST", f"{BASE}?daily=2026-10-01&category={category}&starter={starter}")
        for query in (
            "seed=١٢٣",
            "seed=\U00011bf1",
            "seed=\U0001e5f1",
            "seed=1_234",
            "seed=%20%2B12%20",
            "seed=3&seed=8",
            "seed=bad",
            "seed=%zz",
            "seed=%ff%ff",
            "seed=%e2%82",
            "seed=%e2%82A",
            "seed=1;category=muzica",
            "seed=1.2",
            "seed=",
            "starter=bad",
            "starter=2",
            "category=unknown",
            "category=",
            "daily=&seed=17",
            "daily=școală🧩&seed=99",
        ):
            request("POST", f"{BASE}?{query}")
        for method, path in (
            ("GET", BASE),
            ("OPTIONS", BASE),
            ("POST", BASE + "/missing"),
            ("GET", BASE + "/missing"),
            ("POST", BASE + "/missing/guess"),
            ("GET", BASE + "/missing/unknown"),
        ):
            request(method, path, "{}")
        # Exercise every distinct gameplay state with the real oracle's private answer.
        for seed in range(20):
            game = request("POST", f"{BASE}?seed={seed}")
            sid = game["game_id"]
            session = intrusul.store.get(sid)
            assert session is not None
            request("GET", f"{BASE}/{sid}")
            request("POST", f"{BASE}/{sid}/hint")
            for raw in (
                "",
                "null",
                "[]",
                "true",
                "{}",
                '{"id":null}',
                '{"id":12}',
                '{"id":[]}',
                '{"id":{}}',
                '{"id":true}',
                "{",
                '{"id":}',
                '{"id":"abc",}',
                '{"id":"abc"} {}',
                '{"id":"abc"',
                '{"id"',
                "[1,]",
                '"abc',
                '{"id":"bad\\q"}',
            ):
                request("POST", f"{BASE}/{sid}/guess", raw)
            request("POST", f"{BASE}/{sid}/guess", '{"id":"unknown"}')
            wrong = session.members[0]
            request("POST", f"{BASE}/{sid}/guess", json.dumps({"id": wrong}))
            request("POST", f"{BASE}/{sid}/guess", json.dumps({"id": wrong}))
            request("POST", f"{BASE}/{sid}/hint")
            request("POST", f"{BASE}/{sid}/hint")
            if seed % 2:
                for wrong in session.members[1:]:
                    request("POST", f"{BASE}/{sid}/guess", json.dumps({"id": wrong}))
            else:
                request(
                    "POST",
                    f"{BASE}/{sid}/guess",
                    json.dumps({"id": " \x1c" + session.intruder + "\x1f "}),
                )
            request("GET", f"{BASE}/{sid}")
            request("POST", f"{BASE}/{sid}/guess", json.dumps({"id": session.intruder}))
            request("POST", f"{BASE}/{sid}/hint")
        previous = "missing"
        for _ in range(20):
            game = request("POST", f"{BASE}?seed=17&starter=1&previous_game_id={previous}")
            previous = game["game_id"]
        request("POST", f"{BASE}?daily=2026-10-01&seed=999&starter=1&previous_game_id={previous}")
        request("POST", f"{BASE}?daily=2026-10-01")
        game = request("POST", f"{BASE}?seed=7")
        request("POST", f"{BASE}/{game['game_id']}/guess", " " * (64 * 1024 + 1))
        if args.benchmark:
            for seed in range(1000):
                game = request("POST", f"{BASE}?seed={seed}")
                request("GET", f"{BASE}/{game['game_id']}")
    finally:
        if child.stdin is not None:
            child.stdin.close()
        if child.poll() is None:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait(timeout=10)
    assert child.returncode == 0, f"Go replay exit {child.returncode}"
    print(f"Intrusul HTTP parity: {count} responses matched (only session IDs normalized)")
    if args.benchmark:

        def percentiles(values: list[int]) -> dict:
            ordered = sorted(values)
            return {
                "samples": len(ordered),
                "median_us": ordered[len(ordered) // 2] / 1000,
                "p95_us": ordered[int((len(ordered) - 1) * 0.95)] / 1000,
            }

        report = {
            "scope": (
                "local sequential Go httptest vs Django TestClient; Intrusul only; "
                "no listener/TLS/concurrency"
            ),
            "matched_responses": count,
            "python": percentiles(times_python),
            "go": percentiles(times_go),
            "python_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "go_peak_rss_bytes": go_peak,
            "limitations": (
                "Go contains only Intrusul content, Python loads the shared full graph; "
                "proxy mode retains both runtimes; not full-port savings or capacity proof"
            ),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.report:
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
