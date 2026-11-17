"""Differentially replay anonymous arcade HTTP journeys against Django and native servers.

No network listener, database, production service or account is used. Only random
session IDs are normalized. --benchmark adds aggregate local timings/peak memory,
not a full-arcade capacity claim. Comparison uses a prebuilt native executable. The independent recording mode uses
Django TestClient alone and writes both the source-bound gzip and a provenance manifest.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import os
import resource
import select
import subprocess
import time
from itertools import combinations
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/wordgames/intrusul/games"


def write_python_corpus(path: Path, cases: list[dict]) -> None:
    def encoded(value: object) -> bytes:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()

    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    # The export supplies names only. The digest of every real Python input is
    # independently recomputed and checked against its published source identity.
    export = json.loads((ROOT / "go-backend/internal/content/bundled.json").read_bytes())
    content = ROOT / "cat_de_roman_esti/fixtures"
    sources = {name: sha((content / name).read_bytes()) for name in export["sources"]}
    if sources != export["sources"]:
        raise RuntimeError("Published export and Django source identities differ")
    reference = {
        "schema_version": 1,
        "rules_version": 2,
        "reference": "Independent Django oracle for ADR-0232, anonymous arcade HTTP journeys",
        "sources": sources,
        "cases": cases,
    }
    raw = encoded(reference)
    compressed = gzip.compress(raw, mtime=0)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    producer = Path(__file__).resolve()
    producer_paths = [str(producer.relative_to(ROOT)), "cat_de_roman_esti"]
    producer_dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain", "--", *producer_paths], cwd=ROOT
    ))
    manifest = {
        "cases": len(cases),
        "compressed_bytes": len(compressed),
        "gzip_sha256": sha(compressed),
        "json_sha256": sha(raw),
        "producer_commit": source_commit,
        "producer_dirty": producer_dirty,
        "producer_sha256": sha(producer.read_bytes()),
        "request_set_sha256": sha(encoded([case["request"] for case in cases])),
        "rules_version": 2,
        "sources": sources,
    }
    path.write_bytes(compressed)
    path.with_name(path.name + ".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Recorded {len(cases)} rules-2 responses from Django ({manifest['gzip_sha256']}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--binary", type=Path, help="compare the Python and native responses")
    mode.add_argument("--record-python", type=Path, help="record independently from Django")
    parser.add_argument("--runtime", choices=("go", "rust"), default="go")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if os.environ.get("CAT_ACCOUNTS_ENABLED", "").lower() in {"1", "true", "yes", "on"}:
        parser.exit(1, "Parity requires accounts OFF.\n")
    if args.record_python:
        if args.benchmark or args.report or args.runtime != "go":
            parser.error("Recording only accepts --record-python.")
        overrides = (
            "CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS", "CAT_DEBUG",
            "CAT_DOMAIN", "CAT_DATABASE_URL", "DATABASE_URL", "CAT_BOARD_STATS_DIR",
        )
        if any(os.environ.get(key) for key in overrides):
            parser.error("Recording requires the bundled content and default anonymous settings.")
        if os.environ.get("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings") != (
            "cat_de_roman_esti.web.settings"
        ):
            parser.error("Recording requires the repository's Django settings.")
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
    ) if args.binary else None
    replay_buffer = bytearray()

    def replay_line() -> bytes:
        assert child is not None and child.stdout is not None
        deadline = time.monotonic() + 60
        while b"\n" not in replay_buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([child.stdout], [], [], remaining)[0]:
                raise TimeoutError(f"{args.runtime} replay response exceeded 60 seconds")
            chunk = os.read(child.stdout.fileno(), 65536)
            if not chunk:
                return bytes(replay_buffer)
            replay_buffer.extend(chunk)
            if len(replay_buffer) > 16 * 1024 * 1024:
                raise AssertionError("Replay response exceeded 16 MiB")
        line, _, remaining = replay_buffer.partition(b"\n")
        replay_buffer[:] = remaining
        return bytes(line)

    aliases: dict[str, str] = {}
    cases: list[dict] = []
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

    def freeze(value):
        # Case paths may deliberately percent-encode the first byte of a session id.
        if isinstance(value, str):
            for old, new in aliases.items():
                value = value.replace(f"%{ord(old[0]):02x}{old[1:]}", f"%{ord(new[0]):02x}{new[1:]}")
                value = value.replace(old, new)
            return value
        if isinstance(value, dict):
            return {key: freeze(item) for key, item in value.items()}
        if isinstance(value, list):
            return [freeze(item) for item in value]
        return value

    def request(method: str, path: str, raw: str = "") -> dict:
        nonlocal count, go_peak
        if child is None:
            response = client.generic(method, path, data=raw.encode(), content_type="application/json")
            expected = response.json() if response.content else None
            if response.status_code == 200 and isinstance(expected, dict) and "game_id" in expected:
                sid = expected["game_id"]
                if sid not in aliases:
                    aliases[sid] = f"session-{len(aliases)}"
            cases.append({
                "request": {"method": method, "path": freeze(path), "body": freeze(raw)},
                "status": response.status_code,
                "body": freeze(expected),
            })
            count += 1
            return expected or {}

        split = urlsplit(path)
        mapped_path = split.path
        for python_id, go_id in aliases.items():
            mapped_path = mapped_path.replace(
                "%" + format(ord(python_id[0]), "02x") + python_id[1:],
                "%" + format(ord(go_id[0]), "02x") + go_id[1:],
            )
            mapped_path = mapped_path.replace(python_id, go_id)
        query = split.query
        if "previous_game_id" in query:
            query = urlencode(
                [
                    (key, aliases.get(value, value))
                    for key, value in parse_qsl(query, keep_blank_values=True)
                ]
            )
        go_path = urlunsplit(("", "", mapped_path, query, ""))
        assert child.stdin is not None and child.stdout is not None
        child.stdin.write(json.dumps({"method": method, "path": go_path, "body": raw}) + "\n")
        child.stdin.flush()
        started = time.perf_counter_ns()
        response = client.generic(method, path, data=raw.encode(), content_type="application/json")
        elapsed = time.perf_counter_ns() - started
        line = replay_line()
        if not line:
            raise AssertionError(f"Native replay exited during {method} {path}")
        native = json.loads(line)
        expected = None if not response.content else response.json()
        if (
            response.status_code == native["status"] == 200
            and isinstance(expected, dict)
            and "game_id" in expected
        ):
            aliases[expected["game_id"]] = native["body"]["game_id"]
        if response.status_code != native["status"] or normalize(expected) != normalize(
            native["body"]
        ):
            raise AssertionError(
                f"Parity mismatch: {method} {path} (native {go_path}) body={raw!r}\n"
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
            "seed=%1c17%1f",
            "seed=%c2%8517%c2%85",
            "seed=%0017",
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
            *([("OPTIONS", BASE)] if not args.record_python else []),
            ("POST", BASE + "/missing"),
            ("GET", BASE + "/missing"),
            ("POST", BASE + "/missing/guess"),
            ("GET", BASE + "/missing/unknown"),
        ):
            request(method, path, "{}")
        request("POST", "/api/wordgames/intrusul/%67ames?seed=17")
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
                '{"id":18446744073709551617}',
                '{"id":' + "9" * 500 + "}",
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
            request(
                "POST",
                f"{BASE}/{sid}/guess",
                '{"id":"unknown","extra":' + "[" * 150 + "0" + "]" * 150 + "}",
            )
            encoded_id = "%" + format(ord(sid[0]), "02x") + sid[1:]
            request("GET", f"{BASE}/{encoded_id}")
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
        # Qualify the actual HTTP boundary for every other native engine, not only
        # direct service goldens. Seeded sessions use the oracle's private state to
        # drive complete games; no answer is exposed by a native response.
        from collections import deque

        from cat_de_roman_esti.wordgames import (
            alchimie,
            conexiuni,
            contexto,
            lant,
            perechi,
        )
        from cat_de_roman_esti.wordgames.service import get_service

        for path in ("/api/health", "/api/manifest", "/api/categories", "/api/me"):
            request("GET", path)
        if args.record_python:
            request("GET", "/openapi.json")
            for method in ("POST", "GET", "HEAD"):
                request(method, "/api/wordgames/lant/games/missing/giveup")
        for module in (perechi, conexiuni, contexto, lant, alchimie):
            base = f"/api/wordgames/{module.GAME_KEY}/games"
            for query in (
                "seed=bad&category=unknown",
                "seed=17&category=unknown&starter=bad",
                "seed=17&category=",
                "seed=17&difficulty=",
                "seed=17&difficulty=invalid",
                "seed=17&daily=",
                "seed=17&starter=2",
                "seed=17&starter=bad",
            ):
                request("POST", f"{base}?{query}")
            for method, suffix in (
                ("GET", ""),
                ("POST", "/missing"),
                ("GET", "/missing"),
                ("GET", "/missing/unknown"),
            ):
                request(method, base + suffix, "{}")
            for seed, difficulty in ((7, "usor"), (17, "normal"), (31, "greu")):
                created = request("POST", f"{base}?seed={seed}&difficulty={difficulty}")
                sid = created["game_id"]
                session = module.store.get(sid)
                assert session is not None
                path = f"{base}/{sid}"
                request("GET", path)
                if module is perechi:
                    action, field = "match", "ids"
                    answers = [{"ids": list(pair.members)} for pair in session.pairs]
                elif module is conexiuni:
                    action, field = "guess", "ids"
                    answers = [{"ids": ids} for ids in session.groups.values()]
                elif module is contexto:
                    action, field = "guess", "text"
                    answers = [{"text": session.target}]
                    request("POST", path + "/clue")
                    request("POST", path + "/guess", '{"text":"cuvantxyz"}')
                elif module is lant:
                    action, field = "move", "text"
                    graph = get_service().graph
                    todo = deque([(session.start, [])])
                    seen = {session.start}
                    while todo:
                        node, route = todo.popleft()
                        if node == session.target:
                            answers = [{"text": step} for step in route]
                            break
                        for neighbor in graph.neighbors(node, include_distractors=False):
                            node_id = neighbor.node.id
                            if node_id not in seen:
                                seen.add(node_id)
                                todo.append((node_id, [*route, node_id]))
                    else:
                        raise AssertionError("oracle Lanț has no route")
                    request("POST", path + "/hint")
                else:
                    action, field = "combine", "a"
                    answers = [{"a": pair[0], "b": pair[1]} for pair, _ in session.routes[0]]
                    request("POST", path + "/reset")
                for raw in (
                    "",
                    "null",
                    "[]",
                    "{}",
                    json.dumps({field: None}),
                    json.dumps({field: 18446744073709551617}),
                ):
                    request("POST", path + "/" + action, raw)
                for body in answers:
                    request("POST", path + "/" + action, json.dumps(body))
                request("GET", path)
                request("POST", path + "/" + action, "{malformed")
        for raw in ("", "null", "[]", '{"extra":1}', '{"progress":1}', '{"goal_id":"missing"}'):
            request("POST", "/api/alchimie/explore", raw)
        explore = request("POST", "/api/alchimie/explore", "{}")
        eid = explore["game_id"]
        for op, body in (
            ("hint", ""),
            ("goal", '{"goal_id":null}'),
            ("combine", '{"a":"missing","b":"missing"}'),
        ):
            request("POST", f"/api/alchimie/explore/{eid}/{op}", body)
        request("GET", f"/api/alchimie/explore/{eid}")
        # Rules-2 additions reuse stable private oracle seeds to drive complete ladders
        # and prove that exhausting a ladder leaves the resumed state untouched.
        actions = (
            (intrusul, "hint", "guess", lambda s: {"id": s.intruder}),
            (perechi, "hint", "match", lambda s: {"ids": list(s.pairs[-1].members)}),
            (conexiuni, "clue", "guess", lambda s: {"ids": next(reversed(s.groups.values()))}),
            (contexto, "clue", "guess", lambda s: {"text": s.target}),
            (lant, "hint", "move", lambda s: {"text": s.target}),
            (alchimie, "hint", "combine", lambda s: {"a": s.seeds[0], "b": s.seeds[1]}),
        )
        for module, hint, action, sample_move in actions:
            base = f"/api/wordgames/{module.GAME_KEY}/games"
            daily = request("POST", base + "?daily=2026-11-16&category=literatura&difficulty=greu")
            if daily.get("game_id"):
                request("GET", f"{base}/{daily['game_id']}")
            replay = request("POST", base + "?daily=2026-11-16&replay=true")
            request("GET", f"{base}/{replay['game_id']}")
            query = "?seed=31&difficulty=greu" if module is lant else "?seed=17&difficulty=usor"
            game = request("POST", base + query)
            path = f"{base}/{game['game_id']}"
            session = module.store.get(game["game_id"])
            assert session is not None

            if module is lant:
                # Taking an accepted hop and undoing it leaves the path unchanged
                # while retaining the move for the final cumulative outcome.
                next_hop = lant._shortest_hops(session, get_service().distances_to(session.target))[0]
                raw = json.dumps({"text": next_hop})
                assert request("POST", path + "/move", raw)["ok"]
                request("POST", path + "/undo")
            if module is alchimie:
                dry = next(pair for pair in combinations(session.seeds, 2) if not session.recipes.get(tuple(sorted(pair))))
                request("POST", path + "/combine", json.dumps({"a": dry[0], "b": dry[1]}))
                request("POST", path + "/combine", json.dumps({"a": dry[1], "b": dry[0]}))

            for _ in range(4):
                request("POST", path + "/" + hint)
                request("GET", path)
            if module is alchimie:
                request("POST", path + "/reset")
                request("POST", path + "/combine", json.dumps({"a": dry[0], "b": dry[1]}))
                for a, b in alchimie._minimum_projected_plan(set(session.owned), session.target, session.recipes):
                    request("POST", path + "/combine", json.dumps({"a": a, "b": b}))
            elif module is lant:
                while not session.won:
                    route = lant._shortest_hops(session, get_service().distances_to(session.target))
                    assert route
                    assert request("POST", path + "/move", json.dumps({"text": route[0]}))["ok"]
            elif module is contexto:
                request("POST", path + "/guess", '{"text":"cuvantxyz"}')
                request("POST", path + "/giveup")
            else:
                request("POST", path + "/" + action, json.dumps(sample_move(session)))
            request("GET", path)
            request("POST", path + "/" + hint)
        # Once three sets are solved, the remaining membership is public.
        for module, action, hint in ((perechi, "match", "hint"), (conexiuni, "guess", "clue")):
            base = f"/api/wordgames/{module.GAME_KEY}/games"
            initial = request("POST", base + "?seed=38")
            path = f"{base}/{initial['game_id']}"
            session = module.store.get(initial["game_id"])
            assert session is not None
            for _ in range(2):
                request("POST", path + "/" + hint)
            sets = [pair.members for pair in session.pairs] if module is perechi else list(session.groups.values())
            for ids in sets[:3]:
                request("POST", path + "/" + action, json.dumps({"ids": list(ids)}))
            before = request("GET", path)
            assert before["hints_left"] == 0
            request("POST", path + "/" + hint)
            assert request("GET", path) == before
        # Solving the original subject publishes its later rungs. Replaying the
        # planner never picks a new subject on behalf of an exhausted ladder.
        for module, action, hint in ((perechi, "match", "hint"), (conexiuni, "guess", "clue")):
            base = f"/api/wordgames/{module.GAME_KEY}/games"
            initial = request("POST", base + "?seed=38")
            path = f"{base}/{initial['game_id']}"
            session = module.store.get(initial["game_id"])
            assert session is not None
            request("POST", path + "/" + hint)
            if module is perechi:
                ids = session.pairs[session.hinted_pair].members
            else:
                ids = session.groups[session.clue_category]
            request("POST", path + "/" + action, json.dumps({"ids": list(ids)}))
            before = request("GET", path)
            assert before["hint_level"] == before["steps"] == 1 and before["hints_left"] == 0
            request("POST", path + "/" + hint)
            assert request("GET", path) == before
        # Alchimie keeps the first hinted subject when another recipe is made,
        # and ends that ladder after its subject is discovered, including Reset.
        base = "/api/wordgames/alchimie/games"
        for solve_subject in (False, True):
            initial = request("POST", base + "?seed=17&difficulty=usor")
            path = f"{base}/{initial['game_id']}"
            session = alchimie.store.get(initial["game_id"])
            assert session is not None
            first = request("POST", path + "/hint")
            original = session.hint_pair
            subject = session.hint_subject
            assert original is not None and subject is not None and first["hint_level"] == 1
            if solve_subject:
                pair = original
            else:
                # Find an unrelated discovery that would change a fresh planner.
                def changes_plan(pair):
                    discovered = set(session.recipes.get(pair, ())) - set(session.owned)
                    if not discovered or subject in discovered:
                        return False
                    plan = alchimie._minimum_projected_plan(
                        set(session.owned) | discovered, session.target, session.recipes,
                    )
                    return bool(plan and plan[0] != original)
                pair = next(pair for pair in combinations(sorted(session.owned), 2)
                            if changes_plan(pair))
            request("POST", path + "/combine", json.dumps({"a": pair[0], "b": pair[1]}))
            state = request("GET", path)
            if solve_subject:
                assert state["hints_left"] == 0
                request("POST", path + "/hint")
                request("POST", path + "/reset")
                before = request("GET", path)
                assert before["hints_left"] == 0
                request("POST", path + "/hint")
                assert request("GET", path) == before
            else:
                second = request("POST", path + "/hint")
                assert second["hint_kind"] == "category"
                assert second["hint_ingredient"]["id"] in original
                third = request("POST", path + "/hint")
                assert {item["id"] for item in third["hint"]} == set(original)
                request("GET", path)
                request("POST", path + "/hint")
        if args.benchmark:
            for seed in range(1000):
                game = request("POST", f"{BASE}?seed={seed}")
                request("GET", f"{BASE}/{game['game_id']}")
    finally:
        if child is not None:
            if child.stdin is not None:
                child.stdin.close()
            if child.poll() is None:
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=10)
    if args.record_python:
        write_python_corpus(args.record_python, cases)
        return 0
    assert child is not None
    assert child.returncode == 0, f"Native replay exit {child.returncode}"
    print(
        f"{args.runtime} arcade HTTP parity: {count} responses matched "
        "(only session IDs normalized)"
    )
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
                "local sequential native replay recorder vs Django TestClient; arcade; "
                "no listener/TLS/concurrency"
            ),
            "matched_responses": count,
            "python": percentiles(times_python),
            args.runtime: percentiles(times_go),
            "python_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            f"{args.runtime}_peak_rss_bytes": go_peak,
            "limitations": (
                "Native servers load the full arcade export; replay harnesses differ; "
                "proxy mode retains both runtimes; not full-port savings or capacity proof"
            ),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.report:
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
