#!/usr/bin/env python3
"""Run the ten fresh landing checks on a clean SHA and its pinned build."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import (DESCRIPTOR, EMBED, LOCK, LOCK_COPY, SYNC, build_identity, build_receipt, clean_source,
                     digest, exact_commit, git, read_artifact, read_json, registered_artifact,
                     relative_parts, require)


# The owning wrapper's initial snapshot . tree uses no KIT_* path exceptions.
# Mirror the names from scripts/gate.sh so the receipt binds the projected commit.
TREE_EXCLUDED = {
    ".git", "node_modules", ".gate", ".vitest", "dist", "test-results",
    "TASK_BRIEF.md", "TASK_RESULT.md", "SWARM_RESULT.md", ".env",
}


def gate_tree_entry(name, mode, file_digest):
    parts = name.split("/")
    if any(part in TREE_EXCLUDED or part.startswith(".env.") for part in parts):
        return None
    return os.fsencode(name) + b"\0" + (b"x" if mode & 0o111 else b"-") + b"\0" + file_digest


def extract_source(repo, sha, destination):
    # Git's archive supplies committed bytes. No ignored Go files, workspaces,
    # developer Go configs, or generated assets from the caller enter this tree.
    entries = {}
    with subprocess.Popen(["git", "-C", str(repo), "archive", sha], stdout=subprocess.PIPE) as proc:
        try:
            with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
                for member in archive:
                    require(member.isfile() or member.isdir(), "Git source archive must be regular")
                    archive.extract(member, destination, filter="data")
                    if member.isfile() and gate_tree_entry(member.name, member.mode, b"") is not None:
                        with (destination / member.name).open("rb") as stream:
                            file_digest = hashlib.file_digest(stream, "sha256").digest()
                        require(member.name not in entries, "Duplicate path in Git source archive")
                        entries[member.name] = gate_tree_entry(member.name, member.mode, file_digest)
        except BaseException:
            proc.terminate()
            raise
        require(proc.wait() == 0, "Git source archive failed")
    tree = hashlib.sha256()
    for name in sorted(entries):
        tree.update(entries[name])
    return tree.hexdigest()


def prepare_source(repo, sha, mirror, destination, raw, receipt, artifacts):
    tree = extract_source(repo, sha, destination)
    require(tree == receipt["tree_sha256"], "Git-projected source tree differs from the pinned build receipt")
    stage_assets(mirror, destination, raw, receipt, artifacts)
    return tree


def stage_assets(mirror, destination, raw, receipt, artifacts):
    descriptor, identity = build_identity(mirror, raw, receipt, artifacts)
    bound = ("sha", "tree_sha256", "toolchain_digest")
    sync = read_json(registered_artifact(mirror, artifacts, SYNC))
    require(sync.get("schema") == 1 and all(sync.get(key) == receipt[key] for key in bound),
            "Managed asset sync identity differs")
    lock = registered_artifact(mirror, artifacts, LOCK_COPY)
    require(lock == (destination / LOCK).read_bytes(), "Managed lock bytes differ")
    frozen = read_json((destination / "legacy/original-bundle.json").read_bytes())
    require(sync["legacy_sha256"] == frozen["sha256"] and sync["legacy"] == frozen["files"],
            "Legacy asset inventory differs from the committed proof")

    # Copy only receipt-listed artifacts; hashes are checked over the same bytes
    # written. Stray or subsequently replaced mirror files cannot affect Go.
    for tree in ("dist", "legacy"):
        rows = sync[tree]
        require(len(rows) == sync[f"{tree}_files"], f"{tree} asset inventory count differs")
        copied = set()
        for row in rows:
            name = row["path"]
            relative_parts(name)
            require(name != ".keep" and name not in copied, f"Unexpected asset in {tree}: {name}")
            copied.add(name)
            relative = f"{EMBED}/{tree}/{name}"
            data = read_artifact(mirror, relative)
            require(len(data) == row["bytes"] and digest(data) == row["sha256"],
                    f"Managed asset differs at {relative}")
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as file:
                file.write(data)
        require({"index.html", ".vite/manifest.json"} <= copied, f"Actual generated {tree} SPA required")
    manifest = (destination / EMBED / "dist/.vite/manifest.json").read_bytes()
    require(identity["manifest_sha256"] == digest(manifest) == sync["manifest_sha256"],
            "Managed compiled identity differs from the sync manifest")
    (destination / DESCRIPTOR).write_bytes(descriptor)
    (destination / LOCK_COPY).write_bytes(lock)
    (destination / EMBED / "legacy/.keep").unlink(missing_ok=True)


def go_environment():
    platform_keys = ("PATH", "HOME", "USERPROFILE", "LOCALAPPDATA", "SystemRoot", "ComSpec",
                     "PATHEXT", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "GOMODCACHE", "CC", "CXX")
    environment = {key: os.environ[key] for key in platform_keys if key in os.environ}
    environment.update(GOENV="off", GOTOOLCHAIN="local", GOWORK="off", GOPROXY="off",
                       GONOPROXY="none", GOSUMDB="off", GOVCS="*:off", CGO_ENABLED="1",
                       GOFLAGS="-mod=readonly -buildvcs=false", GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    return environment


PRODUCER_TEST_PATH = Path("go-backend/internal/contentops/readset_producer_test.go")
PRODUCER_TEST = "TestQuickPendingActualCompiledProducerReadset"
PRODUCER_PACKAGE = "github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
PRODUCER_MIN_BYTES = 32 << 20
PRODUCER_MAX_BYTES = 256 << 20
PRODUCER_STAT_KEYS = ("st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_gid", "st_nlink", "st_mtime_ns", "st_ctime_ns")


def actual_producer_registered(source):
    file = source / PRODUCER_TEST_PATH
    try:
        info = file.lstat()
    except FileNotFoundError:
        return False
    require(stat.S_ISREG(info.st_mode) and file.resolve(strict=True) == file, "Nonregular actual producer test registration")
    return True


def producer_identity(info):
    return tuple(getattr(info, key) for key in PRODUCER_STAT_KEYS)


def fingerprint_producer(file):
    before = file.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_uid == os.geteuid()
            and before.st_mode & stat.S_IXUSR and PRODUCER_MIN_BYTES < before.st_size <= PRODUCER_MAX_BYTES
            and file.resolve(strict=True) == file, "Actual producer executable is outside its regular-file, size or ownership bounds")
    identity = producer_identity(before)
    fd = os.open(file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        require(producer_identity(os.fstat(fd)) == identity and Path(f"/proc/self/fd/{fd}").resolve(strict=True) == file,
                "Actual producer changed before hashing")
        checksum = hashlib.sha256()
        remaining = before.st_size
        while remaining:
            block = stream.read(min(65536, remaining))
            require(block, "Actual producer was truncated while hashing")
            checksum.update(block)
            remaining -= len(block)
        require(not stream.read(1) and producer_identity(os.fstat(fd)) == identity
                and producer_identity(file.lstat()) == identity and file.resolve(strict=True) == file,
                "Actual producer changed while hashing")
    return {"bytes": before.st_size, "sha256": checksum.hexdigest()}, identity


def verify_producer_events(log, producer):
    positions = {"run": [], "fingerprint": [], "pass": [], "package_pass": []}
    with log.open("rb") as stream:
        for number, line in enumerate(stream):
            if not line.strip():
                continue
            event = read_json(line)
            action, output = event.get("Action"), event.get("Output", "")
            require(isinstance(action, str) and isinstance(output, str)
                    and isinstance(event.get("Test", ""), str), "Malformed Go race event")
            if event.get("Package") != PRODUCER_PACKAGE:
                continue
            require(action != "fail" and "(cached)" not in output, "Failed or cached actual producer package")
            if action == "pass" and "Test" not in event:
                positions["package_pass"].append(number)
            if event.get("Test") != PRODUCER_TEST:
                continue
            require(action in ("run", "output", "pass"), "Unexpected actual producer test action")
            if action in ("run", "pass"):
                positions[action].append(number)
            if action == "output" and "actual unstripped producer" in output:
                match = re.fullmatch(r"\s*readset_producer_test\.go:\d+: actual unstripped producer ([0-9]+) bytes sha256=([a-f0-9]{64}); source executable remained read-only\n", output)
                require(match and match.groups() == (str(producer["bytes"]), producer["sha256"]),
                        "Actual producer log differs from built executable")
                positions["fingerprint"].append(number)
    require(all(len(rows) == 1 for rows in positions.values()), "Actual producer must run, log and pass exactly once")
    order = [rows[0] for rows in positions.values()]
    require(order == sorted(order), "Actual producer event order differs")


def log_identity(file):
    with file.open("rb") as stream:
        return {"file": file.name, "bytes": os.fstat(stream.fileno()).st_size,
                "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}


def run_producer_race(backend, command, source, output, environment, log):
    proof = {"schema": 1, "status": "fail", "build": None, "producer": None, "race": None}
    code = 125
    try:
        require(sys.platform == "linux", "Registered actual producer race requires Linux")
        with tempfile.TemporaryDirectory(prefix=".cat-4i-pending-producer-", dir=output.parent) as temporary:
            scratch = Path(temporary)
            info = scratch.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                    and stat.S_IMODE(info.st_mode) == 0o700 and scratch.resolve(strict=True) == scratch,
                    "Private actual producer scratch required")
            file = scratch / "cat-content-rail"
            build_command = backend + ["build", "-mod=readonly", "-buildvcs=false", "-o", str(file), "./cmd/cat-content-rail"]
            build_log = output / "06-producer-build.log"
            proof["build"] = {"argv": build_command, "exit_code": None}
            try:
                with build_log.open("x", encoding="utf-8") as build:
                    print(f"+ {shlex.join(build_command)}", file=build, flush=True)
                    result = subprocess.run(build_command, cwd=source, env=environment, stdout=build,
                                            stderr=subprocess.STDOUT, timeout=3900)
                    proof["build"]["exit_code"] = result.returncode
            finally:
                proof["build"]["log"] = log_identity(build_log)
            require(result.returncode == 0, "Actual producer build failed")
            producer, identity = fingerprint_producer(file)
            proof["producer"] = producer
            print(f"actual unstripped producer {producer['bytes']} bytes sha256={producer['sha256']}", file=log, flush=True)

            race_json = output / "06-race.jsonl"
            proof["race"] = {"argv": command, "exit_code": None}
            race_env = {**environment, "PENDING_REVIEW_TOOL": str(file), "PENDING_REVIEW_TOOL_SHA256": producer["sha256"]}
            print(f"+ {shlex.join(command)}", file=log, flush=True)
            try:
                with race_json.open("xb") as raw:
                    result = subprocess.run(command, cwd=source, env=race_env, stdout=raw, stderr=log, timeout=3900)
                    proof["race"]["exit_code"] = result.returncode
                    code = result.returncode
            finally:
                proof["race"]["json"] = log_identity(race_json)
            require(code == 0, "Backend race process failed")
            verify_producer_events(race_json, producer)
            require(producer_identity(file.lstat()) == identity and file.resolve(strict=True) == file,
                    "Actual producer changed during race")
        proof["status"] = "pass"
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        proof["error"] = str(exc)
        print(exc, file=log)
        code = code or 125
    receipt = output / "06-producer.json"
    with receipt.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(proof, indent=2) + "\n")
    return code, log_identity(receipt)


def run_checks(go, repo, source, output, baseline, sha, environment):
    backend = [go, "-C", "go-backend"]
    commands = (
        ("01-rails", backend + ["run", "./cmd/cat-content-rail", "all", "--root", "..", "--check"]),
        ("02-validate", backend + ["run", "./cmd/cat-content", "validate", "--root", ".."]),
        ("03-export", backend + ["run", "./cmd/cat-content", "export", "--root", "..", "--check"]),
        ("04-ops", backend + ["run", "./cmd/cat-content-ops", "check", "--root", "..", "--check"]),
        ("05-mobile", backend + ["run", "./cmd/cat-mobile-pack", "--root", "..", "--check"]),
        ("06-race", backend + ["test", "-count=1", "-race", "-timeout=60m", "./..."]),
        ("07-vet", backend + ["vet", "./..."]),
        ("08-auth", [go, "-C", "shared-go/authcore", "test", "-count=1", "-race", "./..."]),
        ("09-doc", backend + ["run", "./cmd/cat-doc-check", "--root", "..", "--inventory", "docs/tracked-markdown.json"]),
        ("10-diff", ["git", "diff", "--check", "--no-ext-diff", "--no-textconv", baseline, sha, "--"]),
    )
    results = []
    for name, command in commands:
        preparation = None
        with (output / f"{name}.log").open("x", encoding="utf-8") as log:
            try:
                registered_race = name == "06-race" and actual_producer_registered(source)
                if registered_race:
                    command = [*command[:-1], "-json", command[-1]]
                    code, preparation = run_producer_race(backend, command, source, output, environment, log)
                else:
                    print(f"+ {shlex.join(command)}", file=log, flush=True)
                    process = subprocess.run(command, cwd=repo if name == "10-diff" else source,
                                             env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=3900)
                    code = process.returncode
            except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                print(exc, file=log)
                code = 125
        row = {"name": name, "exit_code": code}
        if preparation is not None:
            row["producer_preparation"] = preparation
        results.append(row)
        print(f"{name} {code}", flush=True)
    return results


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", required=True, help="full baseline commit SHA")
    parser.add_argument("--sha", required=True, help="full candidate commit SHA")
    parser.add_argument("--build-dir", type=Path, required=True, help="owning pinned build mirror root")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory outside the checkout")
    parser.add_argument("--go", default="go", help="pinned local Go executable on PATH, or an absolute path")
    parser.add_argument("--go-cache", type=Path, help="optional writable rolling Go cache outside checkout and mirror")
    args = parser.parse_args()
    repo = args.repo.resolve()
    mirror = args.build_dir.resolve()
    output = args.out.resolve()
    started = now()
    try:
        require(not output.is_relative_to(repo) and not output.is_relative_to(mirror),
                "Evidence directory must be outside the checkout and build mirror")
        require(Path(args.go).is_absolute() or not any(sep in args.go for sep in ("/", "\\")),
                "Go executable must be an absolute path or executable name")
        sha = exact_commit(repo, args.sha)
        baseline = exact_commit(repo, args.baseline)
        clean_source(repo, sha)
        raw, receipt, artifacts, lock = build_receipt(repo, sha)
        environment = go_environment()
        go_version = subprocess.check_output([args.go, "version"], cwd=repo, env=environment, timeout=30).decode().strip()
        versions = [row["version"] for row in lock["tools"] if (row["tool"], row["scope"]) == ("go", "core")]
        require(len(versions) == 1 and re.fullmatch(r"go version go" + re.escape(versions[0]) + r" \S+", go_version),
                f"Pinned Go version {versions} required, found {go_version}")
        output.mkdir(mode=0o700)
        with tempfile.TemporaryDirectory(prefix=".source-", dir=output) as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            cache = args.go_cache.resolve() if args.go_cache else Path(temporary) / "go-cache"
            require(not cache.is_relative_to(repo) and not cache.is_relative_to(mirror),
                    "Go cache must be outside the checkout and build mirror")
            require(not args.go_cache or not cache.is_relative_to(output),
                    "A reusable Go cache must be outside the evidence directory")
            cache.mkdir(mode=0o700, exist_ok=True)
            environment["GOCACHE"] = str(cache)
            tree = prepare_source(repo, sha, mirror, source, raw, receipt, artifacts)
            results = run_checks(args.go, repo, source, output, baseline, sha, environment)
        clean_source(repo, sha)
        report = {
            "sha": sha, "baseline": baseline, "source_tree_sha256": tree,
            "go_version": go_version, "started": started,
            "finished": now(), "build_receipt_sha256": digest(raw), "checks": results,
            "status": "fail" if any(row["exit_code"] for row in results) else "pass",
        }
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return int(report["status"] == "fail")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print(f"4i failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
