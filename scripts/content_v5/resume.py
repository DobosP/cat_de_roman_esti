#!/usr/bin/env python3
"""Replay the V5 campaign ledger and append validated metering events.

The orchestrator owns the campaign directory, contract and metering inputs.
Job outputs are evidence, never ledger instructions. A recorded dispatch is
an observation target, never proof that a worker is live. The caller polls
its original thread ID before any retry. A partial or inconsistent ledger
fails closed. The state file is a disposable cache of the append-only ledger.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile


MAX_LEDGER = 64 * 1024 * 1024
MAX_ROW = 16 * 1024
STATE_LIMIT = 2048
TOKEN_FIELDS = ("tokens_uncached_in", "tokens_out", "tokens_cached")
SHA = re.compile(r"[0-9a-f]{40}")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
TRAIN_STEPS = {
    "train-candidate": ("train-open", "train-candidate"),
    "train-qualified": ("train-candidate",),
    "train-landed": ("train-qualified",),
    "train-closed": ("train-open", "train-candidate", "train-qualified"),
}
REQUIRED = {
    "owner-override": (
        "owner", "decision_date", "quote", "contract_sha256",
        "previous_start_quota_pct_max", "start_quota_pct_max",
        "start_limit_exclusive", "quota_pct", "stop_at_pct", "restrict_new_intake_at_pct",
    ),
    "campaign-start": ("kit_sha", "goal_meter_tokens", "quota_pct", "ordinary_usage"),
    "campaign-stop": ("reason",),
    "job-dispatch": ("job_id", "train_id", "item_ids", "lane", "game", "role", "thread_id"),
    "job-complete": ("job_id", "thread_id", "wall_s", *TOKEN_FIELDS, "verdict"),
    "turn": ("free_slots", "queue_len", "waiting", "quota_pct"),
    "root-meter": TOKEN_FIELDS,
    "train-open": ("train_id", "kind"),
    "train-candidate": ("train_id", "sha"),
    "train-qualified": ("train_id", "sha"),
    "train-landed": ("train_id", "sha"),
    "train-closed": ("train_id", "reason"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON field {key}")
        result[key] = value
    return result


def parse_json(raw):
    def reject_constant(value):
        raise ValueError(f"unsupported JSON constant {value}")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def timestamp(value):
    require(isinstance(value, str), "at must be an ISO timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.utcoffset() == timedelta(0), "at must specify UTC")
    return result


def integer(value, name, low=0, high=None):
    require(type(value) is int and value >= low and (high is None or value <= high),
            f"invalid {name}")
    return value


def identifier(value, name):
    require(isinstance(value, str) and ID.fullmatch(value), f"invalid {name}")
    return value


def full_sha(value):
    require(isinstance(value, str) and SHA.fullmatch(value), "invalid commit SHA")


def as_regular(path):
    require(not path.is_symlink(), f"symlink refused: {path.name}")
    require(not path.exists() or path.is_file(), f"not a regular file: {path.name}")
    return path


def read_bounded(path, limit):
    with as_regular(path).open("rb") as handle:
        data = handle.read(limit + 1)
    require(len(data) <= limit, f"oversize {path.name}")
    return data


@contextmanager
def ledger_lock(directory):
    # The operating system releases the lock when the writer exits.
    path = as_regular(directory / "ledger.lock")
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX)
            yield


def campaign_contract(directory):
    raw = read_bounded(directory / "contract.json", MAX_ROW)
    data = parse_json(raw)
    require(isinstance(data, dict), "invalid contract")
    full_sha(data["base_sha"])
    identifier(data["campaign"], "campaign")
    integer(data["ends"]["days"], "days", 1, 365)
    integer(data["ends"]["goal_meter_tokens"], "goal-meter token limit", 1)
    integer(data["threads"]["max"], "thread limit", 1, 6)
    integer(data["start_quota_pct_max"], "start quota", 0, 90)
    require(data["train"]["max_open"] == 1, "V5 supports one open train")
    require(data["start_quota_pct_max"] <= 20 or isinstance(data.get("quota_override"), dict),
            "elevated start quota needs an owner override")
    return data, hashlib.sha256(raw).hexdigest()


def quota_mode(contract, quota_pct, ordinary, starting):
    integer(quota_pct, "quota percentage", 0, 100)
    require(type(ordinary) is bool, "ordinary usage must be a boolean")
    if quota_pct >= 90 or not ordinary:
        return "stop"
    if starting and quota_pct > contract["start_quota_pct_max"]:
        return "blocked-start"
    if quota_pct >= 70:
        return "finish-judged-only"
    return "intake"


class Ledger:
    def __init__(self, contract, contract_sha):
        self.contract = contract
        self.contract_sha = contract_sha
        self.last_at = None
        self.start = None
        self.override = None
        self.turn = None
        self.stop = None
        self.jobs = {}
        self.completed = {}
        self.threads = set()
        self.trains = {}
        self.active_train = None
        self.root = dict.fromkeys(TOKEN_FIELDS, 0)

    def accept(self, row):
        require(isinstance(row, dict), "ledger entry must be an object")
        event = row.get("event")
        require(isinstance(event, str) and event in REQUIRED, "unknown ledger event")
        require(set(row) == {"event", "at", *REQUIRED[event]}, f"invalid fields for {event}")
        at = timestamp(row["at"])
        require(self.last_at is None or at >= self.last_at, "ledger timestamps run backward")
        if "quota_pct" in row:
            integer(row["quota_pct"], "quota percentage", 0, 100)
        if self.stop is not None:
            require(event in {"turn", "job-complete", "root-meter", "train-closed"},
                    "campaign stopped; only closeout events are allowed")
        if event == "owner-override":
            self.accept_override(row)
        elif event == "campaign-start":
            require(self.start is None, "campaign clock already started")
            full_sha(row["kit_sha"])
            integer(row["goal_meter_tokens"], "goal-meter tokens")
            require(quota_mode(self.contract, row["quota_pct"], row["ordinary_usage"], True)
                    in {"intake", "finish-judged-only"}, "quota prohibits campaign start")
            require("quota_override" not in self.contract or self.override is not None,
                    "missing contract override receipt")
            self.start = row
        elif event == "campaign-stop":
            self.stop = identifier(row["reason"], "stop reason")
        elif event == "job-dispatch":
            self.accept_dispatch(row)
        elif event == "job-complete":
            self.accept_completion(row)
        elif event == "root-meter":
            for field in TOKEN_FIELDS:
                count = integer(row[field], field)
                require(count >= self.root[field], "cumulative root meter moved backward")
                self.root[field] = count
        elif event == "turn":
            integer(row["free_slots"], "free slots", 0, self.contract["threads"]["max"])
            integer(row["queue_len"], "queue length")
            require(isinstance(row["waiting"], (bool, list)), "invalid waiting value")
            if isinstance(row["waiting"], list):
                for thread in row["waiting"]:
                    identifier(thread, "waiting thread")
            self.turn = row
            if self.stop is None and row["quota_pct"] >= 90:
                self.stop = "weekly-quota"
        else:
            self.accept_train(row)
        self.last_at = at

    def accept_override(self, row):
        expected = self.contract.get("quota_override", {})
        require(self.override is None and self.start is None, "late or repeated override")
        require(row["contract_sha256"] == self.contract_sha, "override contract digest differs")
        require(row["owner"] == expected.get("by")
                and row["decision_date"] == expected.get("date")
                and row["quote"] == expected.get("quote"), "override owner record differs")
        require(row["start_quota_pct_max"] == self.contract["start_quota_pct_max"]
                and row["start_limit_exclusive"] is True
                and expected.get("start_limit_exclusive") is True
                and row["stop_at_pct"] == expected.get("stop_at_pct") == 90
                and row["restrict_new_intake_at_pct"] == expected.get("restrict_new_intake_at_pct") == 70
                and expected.get("paid_credits") is False, "override quota rule differs")
        integer(row["previous_start_quota_pct_max"], "previous start quota", 0, 90)
        self.override = row

    def accept_dispatch(self, row):
        for field in ("job_id", "lane", "game", "role", "thread_id"):
            identifier(row[field], field)
        require(row["job_id"] not in self.jobs and row["thread_id"] not in self.threads,
                "job or thread ID has been used")
        require(len(self.jobs) - len(self.completed) < self.contract["threads"]["max"],
                "thread capacity exhausted")
        if row["train_id"] is not None:
            require(row["train_id"] == self.active_train, "dispatch refers to an inactive train")
        require(isinstance(row["item_ids"], list), "item_ids must be a list")
        items = [identifier(item, "item id") for item in row["item_ids"]]
        require(len(items) == len(set(items)), "duplicate job item")
        self.jobs[row["job_id"]] = row
        self.threads.add(row["thread_id"])

    def accept_completion(self, row):
        job_id = identifier(row["job_id"], "job ID")
        job = self.jobs.get(job_id)
        require(job is not None and job["thread_id"] == row["thread_id"],
                "completion does not match a dispatch")
        require(job_id not in self.completed, "job already completed")
        wall = row["wall_s"]
        require(type(wall) in (int, float) and 0 <= wall <= 1e9 and math.isfinite(wall),
                "invalid wall time")
        for field in TOKEN_FIELDS:
            integer(row[field], field)
        identifier(row["verdict"], "verdict")
        self.completed[job_id] = row

    def accept_train(self, row):
        event = row["event"]
        train = identifier(row["train_id"], "train ID")
        if event == "train-open":
            require(self.start is not None, "campaign clock must start before a train opens")
            require(self.active_train is None and train not in self.trains,
                    "only one train may be open and train IDs cannot be reused")
            require(row["kind"] in {"boards", "forms", "mixed"}, "invalid train kind")
            self.active_train = train
        else:
            require(train == self.active_train and train in self.trains, "train is not open")
            prior = self.trains[train]
            require(prior["event"] in TRAIN_STEPS[event], "out-of-order train transition")
            if "sha" in row:
                full_sha(row["sha"])
            if event in {"train-qualified", "train-landed"}:
                require(row["sha"] == prior["sha"], "train SHA changed")
            if event == "train-closed":
                identifier(row["reason"], "closure reason")
            if event in {"train-closed", "train-landed"}:
                self.active_train = None
        self.trains[train] = row

    def elapsed(self, now):
        if self.start is None:
            return None
        return int((now - timestamp(self.start["at"])).total_seconds())

    def snapshot(self, now, quota_pct, ordinary, goal_meter_tokens):
        require(self.last_at is None or now >= self.last_at, "clock precedes the ledger")
        mode = quota_mode(self.contract, quota_pct, ordinary, self.start is None)
        if self.start is None and "quota_override" in self.contract and self.override is None:
            require(mode == "stop", "missing contract override receipt")
        stops = [self.stop] if self.stop is not None else []
        if quota_pct >= 90 and "weekly-quota" not in stops:
            stops.append("weekly-quota")
        if not ordinary and "ordinary-usage-unavailable" not in stops:
            stops.append("ordinary-usage-unavailable")
        clock = None
        if self.start:
            consumed = goal_meter_tokens - self.start["goal_meter_tokens"]
            require(consumed >= 0, "goal meter precedes the campaign clock baseline")
            elapsed = self.elapsed(now)
            clock = {"kit_sha": self.start["kit_sha"], "started_at": self.start["at"],
                     "tokens": consumed, "elapsed_s": elapsed}
            if elapsed >= self.contract["ends"]["days"] * 86400 and "days-spent" not in stops:
                stops.append("days-spent")
            if consumed >= self.contract["ends"]["goal_meter_tokens"] and "tokens-spent" not in stops:
                stops.append("tokens-spent")

        pending = [job for job_id, job in self.jobs.items() if job_id not in self.completed]
        totals = {field: sum(row[field] for row in self.completed.values()) for field in TOKEN_FIELDS}
        return {
            "campaign": self.contract["campaign"], "contract_sha256": self.contract_sha,
            "quota_pct": quota_pct, "mode": "stop" if stops else mode,
            "stop_reasons": stops, "clock": clock, "active_train": self.active_train,
            "free_slots": self.contract["threads"]["max"] - len(pending),
            "dispatches_to_poll": pending, "last_turn": self.turn,
            "job_meter": {**totals, "completed": len(self.completed),
                          "wall_s": sum(row["wall_s"] for row in self.completed.values())},
            "root_meter": self.root,
        }


def replay(directory, contract, contract_sha):
    ledger = Ledger(contract, contract_sha)
    path = as_regular(directory / "ledger.jsonl")
    if not path.exists():
        return ledger
    size = 0
    with path.open("rb") as handle:
        line = 0
        while row := handle.readline(MAX_ROW + 1):
            line += 1
            size += len(row)
            require(size <= MAX_LEDGER, "ledger exceeds size limit")
            require(len(row) <= MAX_ROW and row.endswith(b"\n"),
                    f"incomplete or oversize ledger row {line}")
            try:
                ledger.accept(parse_json(row))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"invalid ledger row {line}: {exc}") from exc
    return ledger


def save_state(directory, snapshot):
    compact = {key: value for key, value in snapshot.items()
               if key not in {"dispatches_to_poll", "last_turn"}}
    compact["poll_count"] = len(snapshot["dispatches_to_poll"])
    blob = encode(compact)
    require(len(blob) < STATE_LIMIT, "state exceeds size limit")
    target = as_regular(directory / "state.json")
    fd, name = tempfile.mkstemp(dir=directory, prefix=".state-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)


def append_bytes(path, blob):
    require(not path.exists() or path.stat().st_size + len(blob) <= MAX_LEDGER,
            "ledger exceeds size limit")
    with path.open("ab") as handle:
        handle.write(blob)
        handle.flush()
        os.fsync(handle.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-dir", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    resume = subparsers.add_parser("resume", help="replay and print the current campaign")
    resume.add_argument("--quota-pct", type=int, required=True)
    resume.add_argument("--goal-meter-tokens", type=int, required=True)
    resume.add_argument("--ordinary-usage", choices=("yes", "no"), required=True)
    resume.add_argument("--at", help="UTC clock for repeatable recovery")
    resume.add_argument("--save-state", action="store_true")
    append = subparsers.add_parser(
        "append", help="append one orchestrator-owned event (root-meter values are cumulative)"
    )
    append.add_argument("--input", type=Path, help="default: bounded stdin")
    args = parser.parse_args(argv)
    try:
        directory = args.campaign_dir.absolute()
        require(directory.is_dir() and directory.resolve() == directory, "invalid campaign directory")
        with ledger_lock(directory):
            contract, contract_sha = campaign_contract(directory)
            ledger = replay(directory, contract, contract_sha)
            if args.command == "append":
                raw = read_bounded(args.input, MAX_ROW) if args.input else sys.stdin.buffer.read(MAX_ROW + 1)
                require(len(raw) <= MAX_ROW, "oversize event")
                row = parse_json(raw)
                ledger.accept(row)
                blob = encode(row)
                require(len(blob) <= MAX_ROW, "oversize event")
                path = as_regular(directory / "ledger.jsonl")
                append_bytes(path, blob)
                output = row
            else:
                now = timestamp(args.at) if args.at else datetime.now(timezone.utc)
                ordinary = args.ordinary_usage == "yes"
                live_mode = quota_mode(contract, args.quota_pct, ordinary, ledger.start is None)
                elapsed = ledger.elapsed(now)
                reason = None
                if live_mode == "stop":
                    reason = "weekly-quota" if args.quota_pct >= 90 else "ordinary-usage-unavailable"
                elif elapsed is not None and elapsed >= contract["ends"]["days"] * 86400:
                    reason = "days-spent"
                if args.save_state and reason is not None and ledger.stop is None:
                    stop_at = max(now, ledger.last_at) if ledger.last_at is not None else now
                    row = {"event": "campaign-stop", "at": stop_at.isoformat(), "reason": reason}
                    ledger.accept(row)
                    append_bytes(as_regular(directory / "ledger.jsonl"), encode(row))
                goal_meter = integer(args.goal_meter_tokens, "goal-meter tokens")
                output = ledger.snapshot(now, args.quota_pct, ordinary, goal_meter)
                if args.save_state:
                    if output["stop_reasons"] and ledger.stop is None:
                        row = {"event": "campaign-stop", "at": now.isoformat(),
                               "reason": output["stop_reasons"][0]}
                        ledger.accept(row)
                        append_bytes(as_regular(directory / "ledger.jsonl"), encode(row))
                    save_state(directory, output)
        sys.stdout.buffer.write(encode(output))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"resume: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
