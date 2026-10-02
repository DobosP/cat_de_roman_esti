#!/usr/bin/env python3
"""Compare anonymous native backends over identical real loopback HTTP workloads.

Each backend runs alone in a fresh process, on the same two CPUs. Each client
thread keeps one HTTP connection across warmup and measurement. Backend CPU/RSS
exclude this client process. This fixed workload is not a saturation-capacity or
hosting-price prediction. Linux /proc and taskset are required.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import math
import os
import platform
import queue
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import threading
import time
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = Path.home() / "work/_temp/go-backend-pilot/rust-comparison"
EXPORT = ROOT / "go-backend/internal/content/bundled.json"
BASE = "/api/wordgames/intrusul/games"
ACTIONS = ("create", "resume", "wrong_guess", "hint", "correct_guess", "finished_resume")
PRIVATE_KEYS = {
    "intruder",
    "members",
    "group",
    "group_label",
    "source_id",
    "source_ring",
    "catalog_id",
    "rank",
    "standard_rank",
    "starter_rank",
    "standard_score",
    "starter_score",
    "selection_weight",
    "solution",
    "score",
    "share",
}


GAME_KEYS = ("intrusul", "perechi", "conexiuni", "contexto", "lant", "alchimie")


class BenchmarkFailure(RuntimeError):
    """A failed semantic check, child process, or explicitly bounded request."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkFailure(message)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def percentile(values: list[float], quantile: float) -> float:
    """Nearest-rank percentile, explicitly including endpoints."""
    if not values:
        raise ValueError("a percentile needs at least one sample")
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))]


def latency_summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "p50_ms": round(percentile(values, 0.50), 6),
        "p95_ms": round(percentile(values, 0.95), 6),
        "p99_ms": round(percentile(values, 0.99), 6),
        "max_ms": round(max(values), 6),
    }


def all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for child in value.values():
            result.update(all_keys(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(all_keys(child))
        return result
    return set()


def canonical_state(body: dict[str, Any]) -> bytes:
    normalized = {**body, "game_id": "<session>"}
    return json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def board_index(content: dict[str, Any]) -> dict[frozenset[str], dict[str, Any]]:
    """Use reviewed private answers only to drive this local benchmark client.

    Some reviewed variants share four visible tiles but have different labels or
    difficulty. Their answer is unique; validate the clue against its allowed
    variants, and also compare exact normalized responses across all backends.
    """
    result: dict[frozenset[str], dict[str, Any]] = {}
    for board in (b for b in content["boards"] if b["game"] == "intrusul"):
        payload = board["payload"]
        tiles = frozenset([*payload["members"], payload["intruder"]])
        require(len(tiles) == 4, "export has an invalid Intrusul board")
        entry = result.setdefault(
            tiles,
            {
                "intruder": payload["intruder"],
                "group_labels": set(),
                "difficulties": set(),
            },
        )
        require(entry["intruder"] == payload["intruder"], "four-tile set has ambiguous answers")
        entry["group_labels"].add(payload["group_label"])
        entry["difficulties"].add(board["difficulty"])
    require(bool(result), "export contains no Intrusul boards")
    return result


def daily_for(flow: int, every: int) -> str:
    if every and flow % every == 0:
        return (date(2026, 10, 1) + timedelta(days=flow % 28)).isoformat()
    return ""


class CountingConnection(http.client.HTTPConnection):
    def __init__(self, port: int, timeout: float):
        super().__init__("127.0.0.1", port, timeout=timeout)
        self.connections = 0

    def connect(self) -> None:
        self.connections += 1
        super().connect()


class Client:
    def __init__(self, port: int, timeout: float, stop: threading.Event):
        self.connection = CountingConnection(port, timeout)
        self.stop = stop

    def request(self, method: str, path: str, body: dict | None = None) -> tuple[dict, float]:
        require(not self.stop.is_set(), "benchmark cancelled")
        encoded = (
            json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
            if body is not None
            else b""
        )
        headers = {"Connection": "keep-alive", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        started = time.perf_counter_ns()
        self.connection.request(
            method, path, body=encoded if method == "POST" else None, headers=headers
        )
        response = self.connection.getresponse()
        raw = response.read(65537)
        milliseconds = (time.perf_counter_ns() - started) / 1_000_000
        require(
            response.status == 200, f"{method} {path.split('?')[0]} returned HTTP {response.status}"
        )
        require(len(raw) <= 65536, "response exceeded the benchmark's JSON budget")
        parsed = json.loads(raw)
        require(isinstance(parsed, dict), "response is not a JSON object")
        return parsed, milliseconds


def journey(
    client: Client,
    flow: int,
    daily_every: int,
    content: dict[str, Any],
    index: dict[frozenset[str], dict[str, Any]],
) -> tuple[dict[str, float], str, float]:
    samples: dict[str, float] = {}
    digest = hashlib.sha256()
    started = time.perf_counter_ns()
    daily = daily_for(flow, daily_every)
    query: dict[str, int | str] = {"seed": flow}
    if daily:
        query["daily"] = daily
    created, samples["create"] = client.request("POST", f"{BASE}?{urlencode(query)}")
    identifier = created.get("game_id")
    require(isinstance(identifier, str) and bool(identifier), "create omitted its session id")
    tiles = created.get("tiles")
    require(isinstance(tiles, list) and len(tiles) == 4, "create did not expose four tiles")
    ids = [tile["id"] for tile in tiles]
    require(
        len(set(ids)) == 4 and frozenset(ids) in index, "create selected an unknown reviewed board"
    )
    board = index[frozenset(ids)]
    intruder = board["intruder"]
    wrong = sorted(node for node in ids if node != intruder)[0]
    for tile in tiles:
        require(
            tile == {"id": tile["id"], "label": content["labels"][tile["id"]]},
            "display label drift",
        )
    require(created["difficulty"] in board["difficulties"], "unreviewed board difficulty")
    require(
        created["wrong_ids"] == [] and created["attempts"] == 0 and created["mistakes"] == 0,
        "initial progress is not empty",
    )
    require(
        created["remaining_mistakes"] == 3
        and created["hints_used"] == 0
        and not created["hint_available"],
        "incorrect initial budgets",
    )
    require(created["won"] is False and created["lost"] is False, "new game is already terminal")
    require("board_category" not in created, "unrequested category provenance leaked")

    def check_daily(body: dict) -> None:
        require(body.get("daily", "") == daily, "daily intent changed during a journey")

    def check_private(body: dict, *, hinted: bool = False) -> None:
        require(not (all_keys(body) & PRIVATE_KEYS), "unrevealed answer or provenance leaked")
        if not hinted:
            require("clue" not in body, "clue exposed before earning a hint")

    def record(body: dict) -> None:
        require(body["game_id"] == identifier, "a journey changed session id")
        require(body["tiles"] == tiles, "a journey changed visible tile order")
        check_daily(body)
        digest.update(canonical_state(body))
        digest.update(b"\n")

    check_private(created)
    record(created)
    path = f"{BASE}/{identifier}"
    resumed, samples["resume"] = client.request("GET", path)
    require(resumed == created, "resumed initial state differs")
    check_private(resumed)
    record(resumed)
    mistaken, samples["wrong_guess"] = client.request("POST", f"{path}/guess", {"id": wrong})
    require(
        mistaken["correct"] is False
        and mistaken["already_tried"] is False
        and mistaken["ok"] is True,
        "wrong guess did not register",
    )
    require(
        mistaken["attempts"] == 1
        and mistaken["mistakes"] == 1
        and mistaken["wrong_ids"] == [wrong],
        "wrong guess cost drift",
    )
    require(
        mistaken["remaining_mistakes"] == 2 and mistaken["hint_available"] is True,
        "hint did not unlock after one mistake",
    )
    require(
        mistaken["won"] is False and mistaken["lost"] is False, "first wrong tap ended the game"
    )
    check_private(mistaken)
    record(mistaken)
    hinted, samples["hint"] = client.request("POST", f"{path}/hint")
    require(
        hinted["hints_used"] == 1 and hinted["hint_available"] is False and hinted["attempts"] == 1,
        "hint budget drift",
    )
    clue = hinted["clue"]
    require(
        set(clue) == {"label", "message"} and clue["label"] in board["group_labels"],
        "unreviewed clue",
    )
    require(clue["message"] == f"Trei cuvinte țin de: {clue['label']}.", "hint message drift")
    check_private(hinted, hinted=True)
    record(hinted)
    won, samples["correct_guess"] = client.request("POST", f"{path}/guess", {"id": intruder})
    require(
        won["won"] is True
        and won["lost"] is False
        and won["correct"] is True
        and won["already_tried"] is False,
        "answer failed to win",
    )
    require(
        won["attempts"] == 2
        and won["mistakes"] == 1
        and won["hints_used"] == 1
        and won["score"] == 650,
        "terminal score drift",
    )
    require(
        won["wrong_ids"] == [wrong] and won["hint_available"] is False, "terminal progress drift"
    )
    solution = won["solution"]
    require(
        solution["intruder"]["id"] == intruder and solution["group"]["label"] == clue["label"],
        "wrong solution",
    )
    require(
        {tile["id"] for tile in solution["group"]["tiles"]} == set(ids) - {intruder},
        "wrong terminal group",
    )
    expected_share = "cat_de_roman_esti · Intrusul\n🟩 2 încercări · indiciu" + (
        f"\n{daily}" if daily else ""
    )
    require(won["share"] == expected_share, "share text drift")
    record(won)
    finished, samples["finished_resume"] = client.request("GET", path)
    expected_finished = {
        key: value
        for key, value in won.items()
        if key not in {"ok", "correct", "already_tried", "message"}
    }
    require(finished == expected_finished, "terminal resume changed the result")
    record(finished)
    return samples, digest.hexdigest(), (time.perf_counter_ns() - started) / 1_000_000


def cpu_seconds(pid: int) -> float:
    # /proc/pid/stat's parenthesized executable name may contain spaces or ')'.
    rest = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return (int(rest[11]) + int(rest[12])) / os.sysconf("SC_CLK_TCK")


def memory_bytes(pid: int) -> tuple[int, int]:
    values: dict[str, int] = {}
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, raw = line.split(":", 1)
            values[key] = int(raw.split()[0]) * 1024
    require("VmRSS" in values, "backend RSS is unavailable")
    return values["VmRSS"], values.get("VmHWM", values["VmRSS"])


class MemorySampler:
    def __init__(self, pid: int, interval: float):
        self.pid, self.interval = pid, interval
        self.stop = threading.Event()
        self.samples: list[int] = []
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self.stop.is_set():
            try:
                self.samples.append(memory_bytes(self.pid)[0])
            except (OSError, BenchmarkFailure):
                break
            self.stop.wait(self.interval)

    def start(self) -> None:
        self.thread.start()

    def finish(self) -> None:
        self.stop.set()
        self.thread.join(timeout=2)
        require(not self.thread.is_alive(), "RSS sampler did not stop")


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        return reservation.getsockname()[1]


class Server:
    def __init__(self, target: str, args: argparse.Namespace, cpus: list[int], log: Path):
        self.port = ephemeral_port()
        address = f"127.0.0.1:{self.port}"
        if target == "go":
            command = [str(args.go_binary), "-listen", address]
        elif target == "rust":
            command = [str(args.rust_binary), "--listen", address]
        else:
            command = [
                str(args.python),
                "-m",
                "uvicorn",
                "cat_de_roman_esti.web.asgi:application",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--workers",
                "1",
                "--no-access-log",
                "--log-level",
                "warning",
                "--lifespan",
                "off",
            ]
        self.command = [
            shutil.which("taskset") or "taskset",
            "-c",
            ",".join(map(str, cpus)),
            *command,
        ]
        environment = os.environ.copy()
        for name in (
            "CAT_KG_FIXTURE",
            "CAT_GAMES_PACK",
            "CAT_BOARD_RANKINGS",
            "ROEDU_API_URL",
            "ROEDU_API_KEY",
        ):
            environment.pop(name, None)
        environment.update(
            {
                "CAT_ACCOUNTS_ENABLED": "0",
                "CAT_DEBUG": "0",
                "CAT_ALLOWED_HOSTS": "127.0.0.1,localhost",
                "CAT_MAX_REQUEST_BYTES": "65536",
                "CAT_SESSION_TTL_SECONDS": "7200",
                "CAT_MAX_SESSIONS_PER_GAME": "1000",
                "GOMAXPROCS": "2",
                "PYTHONPATH": str(ROOT),
            }
        )
        self.log_path = log
        self.log = log.open("wb")
        try:
            self.process = subprocess.Popen(
                self.command,
                cwd=ROOT,
                env=environment,
                stdout=self.log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except BaseException:
            self.log.close()
            raise

    def ready(self, content: dict[str, Any], timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            require(
                self.process.poll() is None, f"backend exited during startup; log: {self.log_path}"
            )
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=0.5)
            try:
                connection.request("GET", "/api/health")
                response = connection.getresponse()
                if response.status == 200:
                    response.read()
                    break
            except (OSError, http.client.HTTPException):
                pass
            finally:
                connection.close()
            time.sleep(0.05)
        else:
            raise BenchmarkFailure(f"backend startup timed out; log: {self.log_path}")
        client = Client(self.port, 5, threading.Event())
        try:
            manifest, _ = client.request("GET", "/api/manifest")
            require(
                manifest == content["manifest"],
                "backend does not serve the identical reviewed manifest",
            )
            account, _ = client.request("GET", "/api/me")
            require(
                account.get("accounts_enabled") is False and account.get("authenticated") is False,
                "backend has accounts enabled",
            )
        finally:
            client.connection.close()

    def stop(self) -> None:
        try:
            if self.process.poll() is None:
                for requested, timeout in (
                    (signal.SIGINT, 8),
                    (signal.SIGTERM, 2),
                    (signal.SIGKILL, 2),
                ):
                    try:
                        os.killpg(self.process.pid, requested)
                    except ProcessLookupError:
                        break
                    try:
                        self.process.wait(timeout=timeout)
                        break
                    except subprocess.TimeoutExpired:
                        continue
                require(self.process.poll() is not None, "benchmark backend did not stop")
            self.process.wait(timeout=1)
        finally:
            self.log.close()


def create_journey(client: Client, flow: int, daily_every: int, content: dict, index: dict):
    """Equal-weight six-game creates, rotating seeded difficulty and daily inputs.

    Native answers remain private. Every complete response is compared with the
    Python run, normalizing only the randomly generated game_id.
    """
    game = GAME_KEYS[flow % len(GAME_KEYS)]
    query = {"seed": flow, "difficulty": ("usor", "normal", "greu")[(flow // len(GAME_KEYS)) % 3]}
    daily = daily_for(flow, daily_every)
    if daily:
        query["daily"] = daily
    body, elapsed = client.request("POST", f"/api/wordgames/{game}/games?{urlencode(query)}")
    require(isinstance(body.get("game_id"), str) and bool(body["game_id"]), "create omitted id")
    require(
        "score" not in body and "share" not in body and "solution" not in body,
        "new puzzle exposed terminal/private state",
    )
    require(
        body.get("won") is not True and body.get("lost") is not True,
        "new puzzle is already terminal",
    )
    return {"create": elapsed}, hashlib.sha256(canonical_state(body)).hexdigest(), elapsed


def measure(
    server: Server,
    args: argparse.Namespace,
    concurrency: int,
    content: dict[str, Any],
    index: dict[frozenset[str], dict[str, Any]],
) -> tuple[dict[str, Any], dict[int, str]]:
    start = threading.Event()
    stop = threading.Event()
    ready: queue.Queue[BaseException | None] = queue.Queue()
    finished: queue.Queue[dict | BaseException] = queue.Queue()
    warm_per_thread = max(1, math.ceil(args.warmup_flows / concurrency))
    driver = create_journey if args.workload == "creates" else journey
    sampler = MemorySampler(server.process.pid, args.rss_interval)

    def worker(number: int) -> None:
        client = Client(server.port, args.request_timeout, stop)
        announced = False
        try:
            for iteration in range(warm_per_thread):
                driver(
                    client,
                    1_000_000 + number * warm_per_thread + iteration,
                    args.daily_every,
                    content,
                    index,
                )
            ready.put(None)
            announced = True
            require(start.wait(args.startup_timeout), "measurement start timed out")
            require(not stop.is_set(), "benchmark cancelled")
            connection_count = client.connection.connections
            samples: dict[str, list[float]] = defaultdict(list)
            traces: dict[int, str] = {}
            flow_ms = []
            for flow in range(number, args.flows, concurrency):
                require(not stop.is_set(), "benchmark cancelled")
                timing, trace, duration = driver(client, flow, args.daily_every, content, index)
                for action, milliseconds in timing.items():
                    samples[action].append(milliseconds)
                flow_ms.append(duration)
                traces[flow] = trace
            finished.put(
                {
                    "samples": samples,
                    "traces": traces,
                    "flow_ms": flow_ms,
                    "new_connections_during_measurement": client.connection.connections
                    - connection_count,
                }
            )
        except BaseException as failure:
            if not announced:
                ready.put(failure)
            finished.put(failure)
        finally:
            client.connection.close()

    threads = [
        threading.Thread(target=worker, args=(number,), daemon=True)
        for number in range(concurrency)
    ]
    normal_completion = False
    try:
        for thread in threads:
            thread.start()
        warmup_deadline = time.monotonic() + args.startup_timeout
        for _ in threads:
            response = ready.get(timeout=max(0.001, warmup_deadline - time.monotonic()))
            if response is not None:
                raise response
        # Connections remain open while workers wait, so measured requests reuse
        # the warmed transports as well as the application paths.
        time.sleep(0.10)
        idle_rss, _ = memory_bytes(server.process.pid)
        backend_cpu_before = cpu_seconds(server.process.pid)
        client_cpu_before = time.process_time()
        sampler.start()
        started = time.perf_counter()
        start.set()
        deadline = time.monotonic() + args.run_timeout
        results = []
        for _ in threads:
            response = finished.get(timeout=max(0.001, deadline - time.monotonic()))
            if isinstance(response, BaseException):
                raise response
            results.append(response)
        elapsed = time.perf_counter() - started
        backend_cpu = cpu_seconds(server.process.pid) - backend_cpu_before
        client_cpu = time.process_time() - client_cpu_before
        final_rss, lifetime_hwm = memory_bytes(server.process.pid)
        sampler.finish()
        traces: dict[int, str] = {}
        samples: dict[str, list[float]] = defaultdict(list)
        flow_ms: list[float] = []
        for result in results:
            traces.update(result["traces"])
            for action, milliseconds in result["samples"].items():
                samples[action].extend(milliseconds)
            flow_ms.extend(result["flow_ms"])
        require(
            len(traces) == args.flows and set(traces) == set(range(args.flows)),
            "some journeys were not completed",
        )
        require(
            set(samples) == set(ACTIONS)
            and all(len(samples[action]) == args.flows for action in ACTIONS),
            "request sample counts differ",
        )
        normalized_trace = hashlib.sha256(
            json.dumps(sorted(traces.items()), separators=(",", ":")).encode()
        ).hexdigest()
        record = {
            "pid": server.process.pid,
            "flows": args.flows,
            "requests": args.flows * len(ACTIONS),
            "warmup_flows": warm_per_thread * concurrency,
            "elapsed_seconds": elapsed,
            "sessions_per_second": args.flows / elapsed,
            "requests_per_second": args.flows * len(ACTIONS) / elapsed,
            "backend_cpu_seconds": backend_cpu,
            "backend_cpu_seconds_per_session": backend_cpu / args.flows,
            "client_cpu_seconds": client_cpu,
            "idle_rss_bytes": idle_rss,
            "peak_sampled_rss_bytes": max([idle_rss, final_rss, *sampler.samples]),
            "process_lifetime_hwm_bytes": lifetime_hwm,
            "rss_sample_count": len(sampler.samples),
            "rss_sample_interval_seconds": args.rss_interval,
            "latency": latency_summary(
                [duration for durations in samples.values() for duration in durations]
            ),
            "action_latency": {action: latency_summary(samples[action]) for action in ACTIONS},
            "journey_latency": latency_summary(flow_ms),
            "new_connections_during_measurement": sum(
                result["new_connections_during_measurement"] for result in results
            ),
            "normalized_responses_sha256": normalized_trace,
        }
        normal_completion = True
        return record, traces
    finally:
        stop.set()
        start.set()
        if sampler.thread.ident is not None:
            sampler.finish()
        if not normal_completion:
            # Stopping the owned server also releases clients blocked in reads.
            server.stop()
        deadline = time.monotonic() + args.request_timeout + 2
        for thread in threads:
            thread.join(timeout=max(0, deadline - time.monotonic()))
        require(
            not any(thread.is_alive() for thread in threads),
            "benchmark client threads did not stop",
        )


def aggregate(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[(run["target"], run["concurrency"])].append(run)
    keys = (
        "sessions_per_second",
        "requests_per_second",
        "backend_cpu_seconds_per_session",
        "idle_rss_bytes",
        "peak_sampled_rss_bytes",
    )
    result = []
    for (target, concurrency), members in sorted(groups.items()):
        row: dict[str, Any] = {
            "target": target,
            "concurrency": concurrency,
            "repeats": len(members),
        }
        for key in keys:
            values = [member[key] for member in members]
            row[key] = {"median": statistics.median(values), "min": min(values), "max": max(values)}
        row["request_latency_ms"] = {
            key: statistics.median(member["latency"][f"{key}_ms"] for member in members)
            for key in ("p50", "p95", "p99")
        }
        result.append(row)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--go-binary", required=True, type=Path)
    parser.add_argument("--rust-binary", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--python", type=Path, default=Path.home() / "work/cat_de_roman_esti/.venv/bin/python"
    )
    parser.add_argument("--flows", type=int, default=200)
    parser.add_argument(
        "--targets", default="go,rust,python", help="backend rotation; default all three"
    )
    parser.add_argument("--workload", choices=("journeys", "creates"), default="journeys")
    parser.add_argument(
        "--games", default=",".join(GAME_KEYS), help="create-workload game rotation"
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--concurrency", default="1,8,32")
    parser.add_argument(
        "--cpus", help="two CPUs from the current allowed affinity; default first two"
    )
    parser.add_argument("--client-cpus", help="optional disjoint comma-separated client CPUs")
    parser.add_argument("--warmup-flows", type=int, default=24)
    parser.add_argument(
        "--daily-every",
        type=int,
        default=0,
        help="also send daily on every Nth journey; 0 = seeded only",
    )
    parser.add_argument("--startup-timeout", type=float, default=60)
    parser.add_argument("--request-timeout", type=float, default=10)
    parser.add_argument("--run-timeout", type=float, default=120)
    parser.add_argument("--rss-interval", type=float, default=0.01)
    parser.add_argument("--go-toolchain", default="supplied release binary")
    parser.add_argument(
        "--rust-toolchain", default="supplied release binary; Tokio worker_threads=2"
    )
    args = parser.parse_args()
    args.targets = args.targets.split(",")
    if (
        not args.targets
        or len(set(args.targets)) != len(args.targets)
        or not set(args.targets).issubset({"go", "rust", "python"})
    ):
        parser.error("targets must be distinct go, rust or python keys")
    args.games = args.games.split(",")
    if (
        not args.games
        or len(set(args.games)) != len(args.games)
        or not set(args.games).issubset(GAME_KEYS)
    ):
        parser.error("games must be distinct supported game keys")
    try:
        args.concurrency = [int(part) for part in args.concurrency.split(",")]
        allowed = sorted(os.sched_getaffinity(0))
        args.cpus = [int(part) for part in args.cpus.split(",")] if args.cpus else allowed[:2]
    except (ValueError, AttributeError) as failure:
        parser.error(f"invalid Linux affinity or concurrency: {failure}")
    if len(args.cpus) != 2 or len(set(args.cpus)) != 2 or not set(args.cpus).issubset(allowed):
        parser.error("exactly two distinct allowed backend CPUs are required")
    try:
        args.client_cpus = (
            [int(part) for part in args.client_cpus.split(",")]
            if args.client_cpus
            else [cpu for cpu in allowed if cpu not in args.cpus] or allowed
        )
    except ValueError:
        parser.error("client-cpus must be a comma-separated list of integers")
    if not args.client_cpus or not set(args.client_cpus).issubset(allowed):
        parser.error("client-cpus must be a nonempty subset of allowed CPUs")
    if (
        not args.concurrency
        or min(args.concurrency) < 1
        or len(set(args.concurrency)) != len(args.concurrency)
    ):
        parser.error("concurrency levels must be distinct positive integers")
    if (
        args.flows < max(args.concurrency)
        or args.repeats < 1
        or args.warmup_flows < 1
        or args.daily_every < 0
    ):
        parser.error(
            "flows must cover every worker; repeats/warmup must be positive "
            "and daily-every nonnegative"
        )
    if min(args.startup_timeout, args.request_timeout, args.run_timeout, args.rss_interval) <= 0:
        parser.error("all timeouts and RSS interval must be positive")
    if not Path("/proc/self/stat").exists() or not shutil.which("taskset"):
        parser.error("Linux /proc and taskset are required")
    for name in ("go_binary", "rust_binary", "python"):
        # Resolving the venv python symlink would discard its site-packages.
        binary = (
            getattr(args, name).absolute() if name == "python" else getattr(args, name).resolve()
        )
        if not binary.is_file() or not os.access(binary, os.X_OK):
            parser.error(f"{name.replace('_', '-')} must be an executable file")
        setattr(args, name, binary)
    args.report = args.report.resolve()
    return args


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    args = parse_args()
    global ACTIONS, GAME_KEYS
    GAME_KEYS = tuple(args.games)
    os.sched_setaffinity(0, args.client_cpus)
    if args.workload == "creates":
        ACTIONS = ("create",)
    content_bytes = EXPORT.read_bytes()
    content = json.loads(content_bytes)
    index = board_index(content)
    invocation = datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + f"-{os.getpid()}"
    logs = SCRATCH / invocation
    logs.mkdir(parents=True, exist_ok=False)
    python_version = subprocess.check_output(
        [str(args.python), "-VV"], text=True, timeout=10
    ).strip()
    report: dict[str, Any] = {
        "schema_version": 1,
        "started_utc": utc_now(),
        "status": "running",
        "mode": f"real loopback HTTP; standalone backends; anonymous {args.workload}",
        "workload": args.workload,
        "create_game_rotation": list(GAME_KEYS),
        "target_rotation": args.targets,
        "platform": platform.platform(),
        "backend_cpu_affinity": args.cpus,
        "client_cpu_affinity": sorted(os.sched_getaffinity(0)),
        "flows_per_run": args.flows,
        "repeats": args.repeats,
        "concurrency_levels": args.concurrency,
        "daily_every": args.daily_every,
        "cpu_tick_seconds": 1 / os.sysconf("SC_CLK_TCK"),
        "toolchains": {
            "go": args.go_toolchain,
            "rust": args.rust_toolchain,
            "python": python_version,
        },
        "content_export_sha256": hashlib.sha256(content_bytes).hexdigest(),
        "content_hash": content["manifest"]["content_hash"],
        "native_binaries": {
            target: {
                "path": str(binary),
                "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "bytes": binary.stat().st_size,
            }
            for target, binary in (("go", args.go_binary), ("rust", args.rust_binary))
        },
        "notes": [
            (
                "One create per flow; equal-weight listed game rotation, usor/normal/greu; "
                "curated unscoped selection, no gameplay mutations."
                if args.workload == "creates"
                else "Six requests per Intrusul journey: create, resume, wrong tap, hint, win, "
                "terminal resume; score 650."
            ),
            "Identical measured seed sequence, content manifest, CPUs and client checks "
            "for every target; full normalized response traces must match.",
            "Selected target orders rotate across repeats; every run uses a new backend "
            "process without a Python proxy for native servers.",
            "Warmup and startup are excluded from elapsed time and backend CPU. Worker "
            "HTTP connections remain open into measurement.",
            "Backend affinity is reset by taskset; client threads inherit the separately "
            "reported client affinity. On a host with only two allowed CPUs they share.",
            "Backend CPU is /proc/pid/stat utime+stime; parent/client CPU is reported "
            "separately and excluded.",
            "Idle RSS is after warmup; sampled peak is measurement-only; process lifetime "
            "HWM also includes startup/warmup.",
            "Latency measures complete HTTP response transfer before client JSON decoding; "
            "percentiles use nearest rank.",
            "Fixed-load throughput may be limited by this client or other host activity; "
            "it is not maximum server capacity.",
            "Selected processes load the full six-game graph and bounded sessions; "
            "native servers have no Python upstream.",
            "These measurements establish neither hosting-plan capacity nor percentage "
            "hosting savings.",
        ],
        "runs": [],
    }
    expected_traces: dict[int, str] | None = None
    active_server: Server | None = None
    try:
        for level_index, concurrency in enumerate(args.concurrency):
            for repeat in range(args.repeats):
                targets = args.targets.copy()
                offset = (repeat + level_index) % len(targets)
                order = targets[offset:] + targets[:offset]
                for position, target in enumerate(order):
                    print(
                        f"{target}: concurrency={concurrency}, repeat={repeat + 1}/{args.repeats}",
                        flush=True,
                    )
                    log = logs / f"c{concurrency}-r{repeat + 1}-{target}.log"
                    load_before = list(os.getloadavg())
                    active_server = Server(target, args, args.cpus, log)
                    try:
                        active_server.ready(content, args.startup_timeout)
                        result, traces = measure(active_server, args, concurrency, content, index)
                        if expected_traces is None:
                            expected_traces = traces
                        require(
                            traces == expected_traces,
                            f"{target} response traces differ from the first backend",
                        )
                        result.update(
                            {
                                "target": target,
                                "concurrency": concurrency,
                                "repeat": repeat + 1,
                                "position_in_rotated_order": position + 1,
                                "loadavg_before": load_before,
                                "loadavg_after": list(os.getloadavg()),
                                "log": str(log),
                                "command": active_server.command,
                            }
                        )
                        report["runs"].append(result)
                    finally:
                        active_server.stop()
                        active_server = None
                    write_report(args.report, report)
        report["status"] = "passed"
        report["all_normalized_response_traces_match"] = True
        return_code = 0
    except (Exception, KeyboardInterrupt) as failure:
        report["status"] = "interrupted" if isinstance(failure, KeyboardInterrupt) else "failed"
        report["error"] = f"{type(failure).__name__}: {failure}"
        print(report["error"], file=sys.stderr)
        return_code = 1
    finally:
        if active_server is not None:
            active_server.stop()
        report["finished_utc"] = utc_now()
        report["summary"] = aggregate(report["runs"])
        write_report(args.report, report)
    print(f"Report: {args.report}", flush=True)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
