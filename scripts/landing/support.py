"""Exact Git inputs and receipt-bound managed build artifacts."""

import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import subprocess


BUILD = ".gate/build/result.json"
EMBED = "go-backend/embedfs"
DESCRIPTOR = f"{EMBED}/build/dist/.gui-build.json"
LOCK_COPY = f"{EMBED}/build/dist/versions.lock.json"
SYNC = ".gate/build/managed-assets/sync.json"
PLANNER = ".gate/build/cat-browser-plan"
LOCK = "versions.lock.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON field {key!r}")
        result[key] = value
    return result


def read_json(raw):
    result = json.loads(raw, object_pairs_hook=unique)
    require(isinstance(result, dict), "JSON object required")
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False, timeout=45,
    )
    require(result.returncode == 0, f"git {args[0]} failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def exact_commit(root, sha):
    require(re.fullmatch(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", sha), "Full lowercase commit SHA required")
    actual = git(root, "rev-parse", "--verify", f"{sha}^{{commit}}").decode().strip()
    require(actual == sha, f"Expected a literal commit SHA, got {sha}")
    return sha


def clean_source(root, sha):
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root,
            "Repository root required")
    require(git(root, "rev-parse", "HEAD").decode().strip() == sha, "Candidate SHA differs from HEAD")
    require(not git(root, "status", "--porcelain", "--untracked-files=normal"), "Clean checkout required")


def relative_parts(name):
    require(isinstance(name, str) and not re.search(r"[\\:\x00-\x1f\x7f]", name),
            f"Unsafe artifact path {name!r}")
    parts = name.split("/")
    require(all(part and not part.endswith((".", " ")) and not PureWindowsPath(part).is_reserved()
                for part in parts), f"Unsafe artifact path {name!r}")
    return parts


def regular(root, name):
    current = root
    parts = relative_parts(name)
    for i, part in enumerate(parts):
        current /= part
        require(not current.is_symlink(), f"Symlink artifact refused at {current}")
        require(current.is_file() if i == len(parts)-1 else current.is_dir(),
                f"Missing or nonregular artifact {current}")
    return current


def read_artifact(root, name, limit=64 * 1024 * 1024):
    with regular(root, name).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, f"Artifact exceeds size bound at {name}")
    return raw


def build_receipt(root, sha):
    raw = read_artifact(root, BUILD)
    receipt = read_json(raw)
    lock_raw = git(root, "show", f"{sha}:{LOCK}")
    lock = read_json(lock_raw)
    require((receipt.get("schema"), receipt.get("target"), receipt.get("status"), receipt.get("dirty"))
            == (1, "build", "pass", False) and receipt["dirty"] is False and receipt.get("sha") == sha
            and re.fullmatch(r"[a-f0-9]{64}", receipt.get("tree_sha256", ""))
            and receipt.get("versions_lock_sha256") == digest(lock_raw)
            and receipt.get("toolchain_digest") == lock["toolchain_image"]["image_id"],
            "Clean pinned build receipt for the exact candidate SHA required")
    checks = receipt["checks"]
    required = {
        "cat-build-fresh-build-output", "cat-build-frontend-build", "cat-build-emitted-inventory",
        "cat-build-assets", "cat-build-gui-identity", "cat-build-build-cat-server",
    }
    names = {row["name"] for row in checks}
    require(required <= names and len(names) == len(checks)
            and all(row["status"] == "pass" for row in checks), "Managed build checks are incomplete")
    artifacts = {}
    for entry in receipt["artifacts"]:
        match = re.fullmatch(r"(.+) sha256:([a-f0-9]{64})", entry)
        require(match, "Malformed build artifact row")
        name, sha256 = match.groups()
        relative_parts(name)
        require(name not in artifacts, f"Duplicate build artifact {name}")
        artifacts[name] = sha256
    return raw, receipt, artifacts, lock


def registered_artifact(root, artifacts, name):
    raw = read_artifact(root, name)
    require(artifacts.get(name) == digest(raw), f"Build artifact missing or changed at {name}")
    return raw


def build_identity(mirror, raw_receipt, receipt, artifacts):
    require(read_artifact(mirror, BUILD) == raw_receipt, "Source and mirror build receipts differ")
    raw = registered_artifact(mirror, artifacts, DESCRIPTOR)
    identity = read_json(raw)
    bound = ("sha", "tree_sha256", "versions_lock_sha256")
    require(identity.keys() == {*bound, "manifest_sha256"}
            and all(identity[key] == receipt[key] for key in bound)
            and re.fullmatch(r"[a-f0-9]{64}", identity["manifest_sha256"]),
            "Managed build descriptor identity differs")
    return raw, identity
