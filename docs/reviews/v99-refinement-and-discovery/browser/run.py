"""Reproduce the bounded V99 Edge check without touching application sources."""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[3]
node = Path(
    r"C:\Users\Paul Work\.cache\codex-runtimes\codex-primary-runtime\dependencies"
    r"\node\bin\node.exe"
)
modules = node.parent.parent / "node_modules"
python = Path(r"C:\Users\Paul Work\work\_temp\v99-refinement-discovery\venv\Scripts\python.exe")
scratch = python.parents[2]
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
base = f"http://127.0.0.1:{port}"
known = [
    "cat_de_roman_esti/wordgames/lant_relations.py",
    "cat_de_roman_esti/wordgames/lant.py",
    "cat_de_roman_esti/fixtures/kg_sample.json",
    "cat_de_roman_esti/fixtures/games_pack.json",
    "frontend/src/screens/Lant.tsx",
    "docs/reviews/v99-refinement-and-discovery/captions/proposal.json",
    "docs/reviews/v99-refinement-and-discovery/captions/implementation-review.json",
]
known += [
    str(p.relative_to(root)).replace("\\", "/")
    for p in sorted((root / "cat_de_roman_esti/web/static").rglob("*"))
    if p.is_file()
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


bindings = {p: sha(root / p) for p in known}
env = dict(
    os.environ,
    PYTHONPATH=str(root),
    PYTHONDONTWRITEBYTECODE="1",
    PYTHONIOENCODING="utf-8",
    CAT_DEBUG="1",
    CAT_ACCOUNTS_ENABLED="0",
    CAT_KG_FIXTURE=str(root / "cat_de_roman_esti/fixtures/kg_sample.json"),
)
server = None
result = {"kind": "v99-caption-browser-run-v1", "bindings": bindings, "base_url": base}
try:
    with (scratch / "browser-server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [
                str(python), "-B", "-m", "cat_de_roman_esti.web",
                "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning",
            ],
            cwd=root,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for _attempt in range(100):
            if server.poll() is not None:
                raise RuntimeError("Temporary BFF exited before readiness")
            try:
                with urllib.request.urlopen(base + "/", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("Temporary BFF readiness timed out")
        run = subprocess.run(
            [str(node), str(out / "probe.cjs"), base, str(modules)],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        (scratch / "browser-node.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        result["node_exit_code"] = run.returncode
        print(run.stdout.strip())
        if run.stderr:
            print(run.stderr[-1500:])
finally:
    if server is not None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=10)
        result["own_bff_terminated"] = server.poll() is not None
    result["bindings_unchanged"] = bindings == {p: sha(root / p) for p in known}
    result["script_bindings"] = {p.name: sha(p) for p in [out / "run.py", out / "probe.cjs"]}
    (out / "run-receipt.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
if result.get("node_exit_code"):
    sys.exit(result["node_exit_code"])
