#!/usr/bin/env python3
"""Run the private native Cald audit on two committed forms-train bundles."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "landing"))
from support import exact_commit, git, read_artifact, read_json, require

BUNDLE = "go-backend/internal/content/bundled.json"
BUNDLE_PIN = "go-backend/internal/content/digest.go"
FIXTURES = "cat_de_roman_esti/fixtures"
SOURCE_FILES = ("kg_sample.json", "games_pack.json", "board_rankings_v37.json",
                "derived_catalog_v38.json", "quick_games_v92.json", "release_reserve_v1.json",
                "alchimie_discovery_world_v92.json", "alchimie_recipe_extensions_v92.json")
MAX_REPORT = 128 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bundle(repo, sha):
    raw = git(repo, "show", f"{sha}:{BUNDLE}")
    require(len(raw) <= 32 * 1024 * 1024, "Content bundle exceeds 32 MiB")
    data = read_json(raw)
    pin = re.search(rb'^const bundledSHA256 = "([0-9a-f]{64})"\r?$', git(repo, "show", f"{sha}:{BUNDLE_PIN}"),
                    re.MULTILINE)
    require(pin is not None and pin[1].decode("ascii") == digest(raw), f"Bundle pin differs at {sha}")
    for name in SOURCE_FILES:
        source = git(repo, "show", f"{sha}:{FIXTURES}/{name}")
        text = source.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        require(data["sources"][name] == digest(text), f"Stale source {name} at {sha}")
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--binary-sha256", required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--probes", type=Path)
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        baseline = exact_commit(repo, args.baseline)
        sha = exact_commit(repo, args.sha)
        before = read_bundle(repo, baseline)
        after = read_bundle(repo, sha)
        binary = args.binary.absolute()
        binary_sha = digest(read_artifact(binary.parent, binary.name))
        require(re.fullmatch(r"[0-9a-f]{64}", args.binary_sha256)
                and binary_sha == args.binary_sha256, "Resolver binary digest differs")
        scratch = args.scratch.absolute()
        require(scratch.is_dir() and scratch.resolve() == scratch, "Canonical scratch directory required")
        probes = None
        if args.probes:
            probes = read_artifact(args.probes.absolute().parent, args.probes.name, 512 * 1024)
        with tempfile.TemporaryDirectory(prefix="resolver-diff-", dir=scratch) as name:
            directory = Path(name)
            (directory / "before.json").write_bytes(before)
            (directory / "after.json").write_bytes(after)
            command = [str(binary), "--before", str(directory / "before.json"),
                       "--after", str(directory / "after.json")]
            if probes is not None:
                (directory / "probes.json").write_bytes(probes)
                command.extend(["--probes", str(directory / "probes.json")])
            with (directory / "report.json").open("wb") as stream:
                result = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE,
                                        check=False, timeout=3600)
            require(result.returncode == 0, result.stderr.decode(errors="replace").strip())
            report = read_json(read_artifact(directory, "report.json", MAX_REPORT))
        require(report["schema"] == "cat-resolver-diff-1"
                and report["before_bundle_sha256"] == digest(before)
                and report["after_bundle_sha256"] == digest(after)
                and report["checked_count"] == len(report["targets"]) * len(report["probes"]),
                "Resolver result binding differs")
        print(json.dumps({**report, "baseline": baseline, "sha": sha, "binary_sha256": binary_sha,
                          "extra_probes_sha256": digest(probes) if probes is not None else None},
                         ensure_ascii=True, allow_nan=False))
    except (OSError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"resolver diff: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
