#!/usr/bin/env python3
"""Consume the actual build receipt; local dev is not a qualification lane."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).absolute().parent.parent


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def canonical(directory):
    require(directory.is_absolute() and directory.resolve() == directory, "Path alias refused")
    for part in (directory, *directory.parents):
        require(stat.S_ISDIR(part.lstat().st_mode), "Directory/symlink ancestor refused")
    return directory


def regular(base, relative):
    path = Path(relative)
    require(not path.is_absolute() and path.parts and all(x not in (".", "..") for x in path.parts), "Unsafe receipt path")
    current = base
    for index, part in enumerate(path.parts):
        current /= part
        mode = current.lstat().st_mode
        require(stat.S_ISREG(mode) if index == len(path.parts) - 1 else stat.S_ISDIR(mode), "Nonregular receipt/input path")
    return current


def read(base, relative):
    path = regular(base, relative)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 64 * 1024 * 1024, "Local input exceeds bound")
        data = stream.read(64 * 1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and len(data) == before.st_size, "Input changed during read")
    regular(base, relative)
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "Duplicate JSON field")
        out[key] = value
    return out


def document(base, relative):
    return json.loads(read(base, relative), object_pairs_hook=unique)


def command(args, capture=False, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None, **kwargs)


def clean_source(sha):
    require(command(["git", "rev-parse", "--show-toplevel"], True).stdout.strip() == str(ROOT), "Repository root differs")
    require(command(["git", "rev-parse", "HEAD"], True).stdout.strip() == sha, "Qualified SHA differs from HEAD")
    require(not command(["git", "status", "--porcelain", "--untracked-files=normal"], True).stdout, "Clean checkout required")


def prepared(sha, tree, mirror):
    """Existing schema/artifact consumption, never a replacement tree algorithm."""
    clean_source(sha)
    receipt_bytes = read(ROOT, ".gate/build/result.json")
    require(receipt_bytes == read(mirror, ".gate/build/result.json"), "Source/mirror build receipts differ")
    receipt = json.loads(receipt_bytes, object_pairs_hook=unique)
    lock = document(ROOT, "versions.lock.json")
    image = lock["toolchain_image"]
    require(receipt.get("schema") == 1 and receipt.get("target") == "build" and receipt.get("status") == "pass"
            and receipt.get("dirty") is False and receipt.get("sha") == sha and receipt.get("tree_sha256") == tree
            and receipt.get("toolchain_digest") == image["image_id"]
            and receipt.get("versions_lock_sha256") == digest(read(ROOT, "versions.lock.json")), "Actual PASS build identity differs")
    checks = receipt.get("checks", [])
    names = [row.get("name") for row in checks]
    needed = {"cat-build-fresh-build-output", "cat-build-frontend-build", "cat-build-emitted-inventory",
              "cat-build-assets", "cat-build-gui-identity", "cat-build-build-cat-server"}
    require(checks and len(names) == len(set(names)) and needed.issubset(names)
            and all(row.get("status") == "pass" for row in checks), "Actual managed build checks are incomplete")
    descriptor_bytes = read(ROOT, ".gate/build/wrapper-current.json")
    require(descriptor_bytes == read(mirror, ".gate/build/wrapper-current.json") == read(mirror, ".gate/wrapper-current.json"),
            "Mirror has another wrapper invocation")
    descriptor = json.loads(descriptor_bytes, object_pairs_hook=unique)
    require(all(descriptor.get(key) == receipt.get(key) for key in ("sha", "tree_sha256", "toolchain_digest", "target")),
            "Wrapper/build context differs")
    config = read(ROOT, ".gate/build/wrapper-kit-config.json")
    require(config == read(mirror, ".gate/build/wrapper-kit-config.json")
            and digest(config) == descriptor.get("config_file_sha256"), "Frozen configuration differs")
    for relative in ("versions.lock.json", "frontend/package.json", "frontend/package-lock.json", "Taskfile.repo.yml", ".gate.env"):
        require(read(ROOT, relative) == read(mirror, relative), "Source/mirror dependency/configuration inputs differ")
    artifacts = {}
    for entry in receipt.get("artifacts", []):
        match = re.fullmatch(r"(.+) sha256:([a-f0-9]{64})", entry)
        require(match is not None and match[1] not in artifacts, "Malformed/duplicate artifact registration")
        artifacts[match[1]] = match[2]

    def artifact(relative, source=False):
        data = read(mirror, relative)
        require(artifacts.get(relative) == digest(data), "Required artifact is absent or changed")
        if source:
            require(data == read(ROOT, relative), "Source/mirror binary differs")
        return data

    binary = ".gate/build/cat-server"
    artifact(binary, True)
    binary_mode = stat.S_IMODE(regular(ROOT, binary).stat().st_mode)
    require(binary_mode & 0o111 and binary_mode == stat.S_IMODE(regular(mirror, binary).stat().st_mode),
            "Built server executable modes differ")
    identity = json.loads(artifact("go-backend/embedfs/build/dist/.gui-build.json"), object_pairs_hook=unique)
    require(identity == {"sha": sha, "tree_sha256": tree,
                         "manifest_sha256": digest(read(mirror, "go-backend/embedfs/dist/.vite/manifest.json")),
                         "versions_lock_sha256": digest(read(ROOT, "versions.lock.json"))}, "Managed compiled identity differs")
    require(re.fullmatch(r"sha256:[a-f0-9]{64}", image["image_id"]) is not None, "Pinned toolchain image ID required")
    return identity, lock, artifacts[binary]


DEV = r'''
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createServer } from '/work/frontend/node_modules/vite/dist/node/index.js';
const expected = JSON.parse(process.argv[1]);
assert.equal(process.versions.node, expected.node);
assert.equal(JSON.parse(readFileSync('/work/frontend/node_modules/vite/package.json')).version, expected.vite);
const api = spawn('/work/.gate/build/cat-server', ['-listen', '0.0.0.0:8000'], {
  stdio: 'inherit', env: { PATH: process.env.PATH, HOME: '/home/runner', CAT_ACCOUNTS_ENABLED: '0', CAT_SUBMISSIONS_DIR: '' }
});
let vite, stopping = false;
async function stop(code) {
  if (stopping) return;
  stopping = true;
  try { await vite?.close(); } catch (error) { console.error(error); code = 1; }
  if (api.exitCode === null && api.signalCode === null) {
    api.kill('SIGTERM');
    await Promise.race([new Promise(resolve => api.once('exit', resolve)), new Promise(resolve => setTimeout(resolve, 5000))]);
    if (api.exitCode === null && api.signalCode === null) api.kill('SIGKILL');
  }
  process.exit(code);
}
process.once('SIGINT', () => void stop(130));
process.once('SIGTERM', () => void stop(143));
api.once('error', error => { console.error(error); void stop(1); });
api.once('exit', () => { if (!stopping) void stop(1); });
try {
  let identity;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/gui-build', { signal: AbortSignal.timeout(500) });
      if (response.ok) { identity = await response.json(); break; }
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  assert.deepEqual(identity, expected.identity, 'Prepared API must serve its actual compiled identity');
  vite = await createServer({ root: '/work/frontend', configFile: '/work/frontend/vite.config.ts',
    configLoader: 'runner', cacheDir: '/scratch/_temp/cat-dev/vite',
    server: { host: '0.0.0.0', port: 5173, strictPort: true, fs: { strict: true, allow: ['/work/frontend'] } } });
  for (const route of ['/api', '/accounts']) assert.equal(vite.config.server.proxy[route].target, 'http://127.0.0.1:8000');
  await vite.listen();
  console.log('Development HMR only: http://127.0.0.1:5173; API :8000. Source edits do not create a new qualified identity.');
} catch (error) { console.error(error); await stop(1); }
'''


def dev(identity, lock, mirror, lock_fd):
    manifest = document(ROOT, "frontend/package.json")
    owning = document(ROOT, "frontend/package-lock.json")["packages"]
    installed = document(mirror, "frontend/node_modules/.package-lock.json")["packages"]
    for name, row in installed.items():
        require(name.startswith("node_modules/") and name in owning, "Installed package is outside the owning lock")
        require(all(row.get(key) == owning[name].get(key) for key in ("version", "resolved", "integrity", "link")),
                "Installed dependency lock differs")
    for name in {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}:
        location = "node_modules/" + name
        require(location in installed, "Required dependency is not installed in the fresh mirror")
        package = document(mirror, "frontend/" + location + "/package.json")
        require(package.get("version") == owning[location].get("version"), "Installed direct package version differs")
    selected = {}
    for name in ("node", "vite"):
        rows = [row for row in lock["tools"] if row.get("tool") == name and row.get("scope") == "core"]
        require(len(rows) == 1, "One selected core runtime/tool required")
        selected[name] = rows[0]["version"]
    image = lock["toolchain_image"]["image_id"]
    require(command(["docker", "image", "inspect", "--format", "{{.Id}}", image], True).stdout.strip() == image,
            "Exact local toolchain image is unavailable")
    for volume in ("roedu-gocache", "roedu-gomodcache", "roedu-npmcache"):
        command(["docker", "volume", "inspect", volume], True)
    scratch = Path.home() / "work/_temp" / ROOT.name / "local-run"
    scratch.mkdir(parents=True, exist_ok=True)
    canonical(scratch)
    with tempfile.TemporaryDirectory(prefix="dev-", dir=scratch) as temporary:
        cidfile = Path(temporary) / "container.cid"
        args = ["docker", "run", "--rm", "--init", "--pull=never", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--cpus", "4", "--memory", "6g", "--user", f"{os.getuid()}:{os.getgid()}",
                "--cidfile", str(cidfile), "--workdir", "/work/frontend",
                "--publish", "127.0.0.1:8000:8000", "--publish", "127.0.0.1:5173:5173",
                "--mount", f"type=bind,source={mirror},target=/work,readonly",
                "--mount", f"type=bind,source={ROOT / 'frontend/src'},target=/work/frontend/src,readonly",
                "--mount", f"type=bind,source={regular(ROOT, 'frontend/index.html')},target=/work/frontend/index.html,readonly",
                "--tmpfs", "/scratch/_temp/cat-dev:rw,nosuid,nodev,mode=1777,size=512m",
                "--env", "HOME=/home/runner", "--env", "npm_config_cache=/cache/npm",
                "--env", "GOCACHE=/cache/go-build", "--env", "GOMODCACHE=/cache/go-mod",
                "--env", "CAT_ACCOUNTS_ENABLED=0", "--env", "CAT_SUBMISSIONS_DIR="]
        for volume, destination in (("roedu-gocache", "/cache/go-build"), ("roedu-gomodcache", "/cache/go-mod"), ("roedu-npmcache", "/cache/npm")):
            args += ["--mount", f"type=volume,source={volume},target={destination}"]
        public = ROOT / "frontend/public"
        if public.exists():
            canonical(public)
            args += ["--mount", f"type=bind,source={public},target=/work/frontend/public,readonly"]
        args += ["--entrypoint", "node", image, "--input-type=module", "-e", DEV,
                 json.dumps({"identity": identity, **selected}, separators=(",", ":"))]
        child = None
        try:
            child = subprocess.Popen(args, pass_fds=(lock_fd,))
            return child.wait()
        finally:
            # Only the CID created in this invocation's private scratch is ours.
            if cidfile.exists():
                cid = cidfile.read_text().strip()
                if re.fullmatch(r"[a-f0-9]{64}", cid):
                    try:
                        subprocess.run(["docker", "stop", "--time", "6", cid], timeout=10,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except subprocess.TimeoutExpired:
                        print("[run] Timed out stopping this invocation's dev container", file=sys.stderr)
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("build", "run", "dev"), "Unsupported local mode")
    mode = sys.argv[1]
    canonical(ROOT)
    fleet = canonical(Path.home() / "work/_worktrees/cat_de_roman_esti")
    require(ROOT.parent == fleet and re.fullmatch(r"[a-z0-9_-]+", ROOT.name), "Actual Cat fleet task worktree required")
    require(command(["git", "branch", "--show-current"], True).stdout.strip() != "main", "Use the actual task worktree")
    sha, tree = os.environ.get("GATE_SHA", ""), os.environ.get("GATE_TREE_SHA256", "")
    require(re.fullmatch(r"[a-f0-9]{40}", sha) is not None and int(sha, 16) != 0
            and re.fullmatch(r"[a-f0-9]{64}", tree) is not None and int(tree, 16) != 0, "Explicit owner-qualified SHA/tree required")
    clean_source(sha)
    host, port = os.environ.get("HOST", "127.0.0.1"), os.environ.get("PORT", "8000")
    require(host and re.fullmatch(r"[0-9]{1,5}", port) is not None and 1 <= int(port) <= 65535, "Invalid listener")
    if mode == "dev":
        require(host == "127.0.0.1" and port == "8000", "Dev requires the existing 127.0.0.1:8000 proxy")
    command(["bash", str(regular(ROOT, "scripts/gate.sh")), "build", "--sha", sha])
    storage = canonical(Path.home() / "work/_temp" / ROOT.name / "gates")
    mirror = canonical(storage / "cat_de_roman_esti")
    lock_path = regular(storage, "cat_de_roman_esti.lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        identity, lock, binary_sha = prepared(sha, tree, mirror)
        if mode == "build":
            print("Actual owning build and registered server artifact verified; no app started.")
            return 0
        if mode == "dev":
            return dev(identity, lock, mirror, fd)
        address = f"[{host}]:{port}" if ":" in host and not host.startswith("[") else f"{host}:{port}"
        os.set_inheritable(fd, True)
        # Forward no database/provider/session settings from the host.
        environment = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
        environment.update(CAT_ACCOUNTS_ENABLED="0", CAT_SUBMISSIONS_DIR="")
        binary = regular(ROOT, ".gate/build/cat-server")
        require(os.execve in os.supports_fd, "Descriptor-based execution required; no path fallback")
        with os.fdopen(os.open(binary, os.O_RDONLY | os.O_NOFOLLOW), "rb") as executable:
            require(stat.S_ISREG(os.fstat(executable.fileno()).st_mode)
                    and digest(executable.read(64 * 1024 * 1024 + 1)) == binary_sha, "Server changed before execution")
            os.execve(executable.fileno(), [str(binary), "-listen", address], environment)
    finally:
        os.close(fd)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"[run] {error}", file=sys.stderr)
        sys.exit(1)
