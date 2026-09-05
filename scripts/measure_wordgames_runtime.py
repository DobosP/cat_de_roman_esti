#!/usr/bin/env python3
"""Measure offline Django route costs for the six anonymous word games.

This deliberately uses Django's in-process ``Client`` rather than calling game
functions.  It therefore includes URL routing, request parsing, response
serialization and the real SessionStore, while avoiding a network or a remote
service.  It never reads a server-private answer: every action is assembled
from the preceding public response (apart from harmless typed Contexto terms).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import resource
import statistics
import sys
import time
from pathlib import Path
from subprocess import check_output
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GAMES = ("alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant")
CONTEXT0_TERMS = (
    "Banat",
    "București",
    "România",
    "munte",
    "râu",
    "pădure",
    "oraș",
    "școală",
    "carte",
    "mâncare",
)
OFFLINE_FIXTURE = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"


def configure_offline_environment() -> None:
    """Make a standalone measurement independent of inherited service settings."""
    os.environ["CAT_ACCOUNTS_ENABLED"] = "0"
    os.environ["ROEDU_API_URL"] = ""
    os.environ["ROEDU_API_KEY"] = ""
    os.environ["CAT_KG_FIXTURE"] = str(OFFLINE_FIXTURE)
    os.environ["DJANGO_SETTINGS_MODULE"] = "cat_de_roman_esti.web.settings"


def rss_bytes() -> int | None:
    """Return current Linux RSS, not ru_maxrss's process high-water mark."""
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return None


def percentile95(values: list[float]) -> float:
    return sorted(values)[math.ceil(len(values) * 0.95) - 1]


def summarize(samples: list[dict[str, float]]) -> dict[str, float | int]:
    latencies = [sample["ms"] for sample in samples]
    sizes = [sample["bytes"] for sample in samples]
    return {
        "count": len(samples),
        "median_ms": round(statistics.median(latencies), 3),
        "p95_ms": round(percentile95(latencies), 3),
        "max_ms": round(max(latencies), 3),
        "median_response_bytes": int(statistics.median(sizes)),
        "max_response_bytes": int(max(sizes)),
    }


def timed(
    post: Any, url: str, body: dict[str, object] | None = None
) -> tuple[dict, dict[str, float]]:
    started = time.perf_counter_ns()
    response = post(url, body, content_type="application/json") if body is not None else post(url)
    elapsed = (time.perf_counter_ns() - started) / 1_000_000
    if response.status_code != 200:
        raise RuntimeError(f"{url} returned {response.status_code}: {response.content[:200]!r}")
    return response.json(), {"ms": elapsed, "bytes": float(len(response.content))}


def action_for(
    game: str, game_id: str, state: dict, guess_index: int = 0
) -> tuple[str, dict[str, object]]:
    gid = game_id
    base = f"/api/wordgames/{game}/games/{gid}"
    if game == "alchimie":
        inventory = state["inventory"]
        return f"{base}/combine", {"a": inventory[0]["id"], "b": inventory[1]["id"]}
    if game == "intrusul":
        return f"{base}/guess", {"id": state["tiles"][0]["id"]}
    if game == "perechi":
        return f"{base}/match", {"ids": [state["tiles"][0]["id"], state["tiles"][1]["id"]]}
    if game == "conexiuni":
        return f"{base}/guess", {"ids": [tile["id"] for tile in state["tiles"][:4]]}
    if game == "lant":
        return f"{base}/move", {"text": state["choices"][0]["label"]}
    if game == "contexto":
        return f"{base}/guess", {"text": CONTEXT0_TERMS[guess_index % len(CONTEXT0_TERMS)]}
    raise AssertionError(game)


def create_url(game: str, seed: int) -> str:
    return f"/api/wordgames/{game}/games?seed={seed}&difficulty=normal"


def measure_game(game: str, rounds: int, contexto_guesses: int) -> dict[str, object]:
    import django

    configure_offline_environment()
    django.setup()
    from django.test import Client

    client = Client()
    creates: list[dict[str, float]] = []
    actions: list[dict[str, float]] = []
    rss_before = rss_bytes()
    contexto_distinct_total = 0
    contexto_distinct_max = 0
    for round_index in range(rounds):
        state, sample = timed(client.post, create_url(game, 10_000 + round_index))
        creates.append(sample)
        game_id = str(state["game_id"])
        attempts = contexto_guesses if game == "contexto" else 1
        previous_attempts = 0
        for guess_index in range(attempts):
            url, body = action_for(game, game_id, state, guess_index)
            state, sample = timed(client.post, url, body)
            actions.append(sample)
            if game == "contexto" and state.get("ok"):
                current_attempts = int(state.get("attempts", previous_attempts))
                contexto_distinct_total += max(0, current_attempts - previous_attempts)
                previous_attempts = current_attempts
                contexto_distinct_max = max(contexto_distinct_max, current_attempts)
            if state.get("won") or state.get("lost"):
                break
    rss_after = rss_bytes()
    return {
        "game": game,
        "rounds": rounds,
        "create": summarize(creates),
        "action": summarize(actions),
        "contexto_requested_guesses_per_round": contexto_guesses if game == "contexto" else None,
        "contexto_distinct_guesses_total": contexto_distinct_total if game == "contexto" else None,
        "contexto_max_distinct_guesses_per_session": (
            contexto_distinct_max if game == "contexto" else None
        ),
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "rss_delta_bytes": (
            None if rss_before is None or rss_after is None else rss_after - rss_before
        ),
    }


def cold_game(game: str, contexto_guesses: int) -> dict[str, object]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--one-game",
        game,
        "--rounds",
        "1",
        "--contexto-guesses",
        str(contexto_guesses),
    ]
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    raw = check_output(command, cwd=ROOT, env=env, text=True)
    return json.loads(raw)


def environment() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "load_average": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
        "rss_api": "/proc/self/status VmRSS (current resident bytes)",
        "rusage_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "transport": (
            "Django in-process test Client; no listener, network, remote KG, database, or accounts"
        ),
    }


def validate_workload(rounds: int, contexto_guesses: int) -> None:
    if rounds < 1:
        raise ValueError("--rounds must be positive")
    if not 1 <= contexto_guesses <= len(CONTEXT0_TERMS):
        raise ValueError(f"--contexto-guesses must be in 1..{len(CONTEXT0_TERMS)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rounds", type=int, default=9, help="warm create/action rounds per game (default: 9)"
    )
    parser.add_argument(
        "--contexto-guesses",
        type=int,
        default=10,
        help="distinct typed guesses per Contexto round, 1..10 (default: 10)",
    )
    parser.add_argument("--report", type=Path, help="write combined JSON evidence here")
    parser.add_argument("--one-game", choices=GAMES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        validate_workload(args.rounds, args.contexto_guesses)
    except ValueError as exc:
        parser.error(str(exc))
    configure_offline_environment()
    if args.one_game:
        result = measure_game(args.one_game, args.rounds, args.contexto_guesses)
        print(json.dumps({"environment": environment(), "measurement": result}, sort_keys=True))
        return 0
    report = {
        "schema": 1,
        "workload": {
            "cold": (
                "one fresh Python process per game, one create plus one action "
                "(Contexto sends up to 10 typed terms)"
            ),
            "warm": f"one initialized process, {args.rounds} deterministic seed rounds per game",
            "seeds": f"10000..{9999 + args.rounds}",
            "accounts_enabled": False,
            "no_private_answers_read": True,
        },
        "environment": environment(),
        "cold": [cold_game(game, args.contexto_guesses)["measurement"] for game in GAMES],
        "warm": [measure_game(game, args.rounds, args.contexto_guesses) for game in GAMES],
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
