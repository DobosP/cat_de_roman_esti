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
        with (output / f"{name}.log").open("x", encoding="utf-8") as log:
            print(f"+ {shlex.join(command)}", file=log, flush=True)
            try:
                process = subprocess.run(command, cwd=repo if name == "10-diff" else source,
                                         env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=3900)
                code = process.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                print(exc, file=log)
                code = 125
        results.append({"name": name, "exit_code": code})
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
