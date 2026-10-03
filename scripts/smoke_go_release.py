"""Bounded release smoke against an explicit Go URL; prints aggregate evidence only.

The browser fixture oracle runs in this test process. No Python serving process,
private answer endpoint, accounts activation, or operator/contact output is used.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
from itertools import combinations
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
MAX_REQUESTS = 600
MAX_RESPONSE = 4 * 1024 * 1024
GAMES = ("alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant")


class SmokeError(RuntimeError):
    pass


def require(value: object, message: str) -> None:
    if not value:
        raise SmokeError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, url: str):
        parsed = urlsplit(url)
        require(
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and parsed.path in {"", "/"},
            "URL must be an explicit HTTP(S) origin without credentials, path or query",
        )
        self.url = url.rstrip("/")
        self.count = 0
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(
        self, method: str, path: str, payload=None, *, expected=200, raw=None, headers=None
    ):
        require(self.count < MAX_REQUESTS, "Smoke request budget exceeded")
        self.count += 1
        data = raw
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode()
        request = Request(
            self.url + path,
            data=data,
            method=method,
            headers={"Accept-Encoding": "identity", **(headers or {})},
        )
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            response = self.opener.open(request, timeout=15)
        except HTTPError as exc:
            response = exc
        except (URLError, TimeoutError, OSError) as exc:
            raise SmokeError("HTTP connection failed or exceeded the 15-second timeout") from exc
        with response:
            body = response.read(MAX_RESPONSE + 1)
            require(len(body) <= MAX_RESPONSE, "Smoke response budget exceeded")
            # Caddy enforces the public body ceiling before forwarding oversized
            # requests; its expected 413 legitimately has no upstream Go header.
            require(
                response.headers.get("X-Cat-Runtime") == "go"
                or (
                    expected == response.status == 413
                    and response.headers.get("Server", "").lower() == "caddy"
                ),
                f"{method} {urlsplit(path).path} HTTP {response.status}: "
                "response lacks Go runtime header",
            )
            require(
                response.status == expected,
                f"Unexpected HTTP status for {method} {path.split('?')[0]}",
            )
            return body, response.headers

    def json(self, method: str, path: str, payload=None, *, expected=200):
        raw, _ = self.request(method, path, payload, expected=expected)
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise SmokeError("API returned invalid JSON") from exc


def oracle():
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(
        "release_browser_oracle", ROOT / "frontend/e2e/solutions.py"
    )
    require(spec and spec.loader, "Local browser oracle unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(url: str) -> dict:
    start = time.monotonic()
    client = Client(url)
    export = json.loads((ROOT / "go-backend/internal/content/bundled.json").read_bytes())
    health = client.json("GET", "/api/health")
    manifest = client.json("GET", "/api/manifest")
    require(
        health.get("ok") and health.get("concepts") == len(export["nodes"]),
        "Health graph inventory drift",
    )
    require(health.get("version") == export["app_version"], "Release version drift")
    require(manifest == export["manifest"], "Served manifest differs from reviewed release")
    categories = client.json("GET", "/api/categories")
    require(
        len(categories.get("categories", [])) == len(export["category_order"]),
        "Category inventory drift",
    )
    me = client.json("GET", "/api/me")
    require(
        me.get("accounts_enabled") is False
        and me.get("authenticated") is False
        and me.get("user") is None,
        "Anonymous account gate failed",
    )
    shell, shell_headers = client.request("GET", "/")
    require(
        shell == (ROOT / "cat_de_roman_esti/web/static/index.html").read_bytes(),
        "HTML shell differs from release build",
    )
    cache_tokens = {
        value.strip().casefold() for value in shell_headers.get("Cache-Control", "").split(",")
    }
    require(bool(cache_tokens & {"no-cache", "max-age=0"}), "HTML shell is not revalidated")
    head, head_headers = client.request("HEAD", "/")
    require(
        not head and head_headers.get("Cache-Control") == shell_headers.get("Cache-Control"),
        "HEAD shell/cache mismatch",
    )
    asset_paths = set(re.findall(rb'(?:src|href)="(/assets/[^"]+)"', shell))
    build_manifest = json.loads(
        (ROOT / "cat_de_roman_esti/web/static/.vite/manifest.json").read_bytes()
    )
    for chunk in build_manifest.values():
        for file in [chunk["file"], *chunk.get("css", []), *chunk.get("assets", [])]:
            if file.startswith("assets/"):
                asset_paths.add(("/" + file).encode())
    asset_paths = sorted(asset_paths)
    require(asset_paths, "HTML shell has no built assets")
    for path_bytes in asset_paths:
        path = path_bytes.decode()
        body, headers = client.request("GET", path)
        require(
            body == (ROOT / "cat_de_roman_esti/web/static" / path.lstrip("/")).read_bytes(),
            "Static asset bytes differ",
        )
        require(
            "immutable" in headers.get("Cache-Control", ""), "Hashed asset lacks immutable caching"
        )
        empty, _ = client.request("HEAD", path)
        require(not empty, "HEAD asset returned a body")
        if headers.get("ETag"):
            empty, _ = client.request(
                "GET", path, expected=304, headers={"If-None-Match": headers["ETag"]}
            )
            require(not empty, "Conditional asset response has a body")
    legal_hashes = {}
    for path in ("/legal/privacy", "/legal/terms"):
        body, _ = client.request("GET", path)
        require(b"<!doctype html>" in body.lower(), "Legal notice is not HTML")
        require(b"[[PLACEHOLDER" not in body, "Legal notice remains unconfigured")
        if path == "/legal/privacy":
            require(
                b"mailto:" in body and b"Operatorul serviciului este" in body,
                "Legal operator/contact remains unconfigured",
            )
        legal_hashes[path] = hashlib.sha256(body).hexdigest()
    require(
        client.json("POST", "/api/submissions", {}, expected=503).get("detail"),
        "Submissions gate failed",
    )
    client.json("GET", "/api/release-smoke-not-found", expected=404)
    client.request("POST", "/api/wordgames/intrusul/games", expected=413, raw=b" " * 65537)
    local = oracle()
    for game in GAMES:
        fixture = local.solution(game)
        query = {"seed": "38", "difficulty": "usor"}
        if game in {"intrusul", "perechi"}:
            query["starter"] = "1"
        base = f"/api/wordgames/{game}/games"
        state = client.json("POST", base + "?" + urlencode(query))
        identifier = state.get("game_id")
        require(isinstance(identifier, str) and identifier, "Game create omitted session id")
        require(
            not state.get("won") and "score" not in state and "solution" not in state,
            "New game exposed terminal state",
        )
        path = base + "/" + identifier
        require(client.json("GET", path) == state, "Game resume drift")
        if game == "alchimie":
            for pair in fixture["hint_setup"][:3]:
                client.json("POST", path + "/combine", pair)
            client.json("POST", path + "/hint", {})
        elif game == "lant":
            client.json("POST", path + "/hint", {})
        else:
            practice = fixture["practice"]
            state = client.json("POST", path + "/" + practice["action"], practice["payload"])
            if game == "perechi":
                solved_pairs = {frozenset(step["payload"]["ids"]) for step in fixture["steps"]}
                played = frozenset(practice["payload"]["ids"])
                wrong = next(
                    pair
                    for pair in combinations([tile["id"] for tile in state["tiles"]], 2)
                    if frozenset(pair) not in solved_pairs and frozenset(pair) != played
                )
                state = client.json("POST", path + "/match", {"ids": list(wrong)})
            if game == "conexiuni":
                groups = [step["payload"]["ids"] for step in fixture["steps"]]
                state = client.json("POST", path + "/guess", {"ids": groups[0][:2] + groups[1][:2]})
            if game == "contexto":
                target = local.get_service().resolve(fixture["steps"][0]["payload"]["text"])
                for node in local.get_service().all_ids():
                    if state.get("attempts", 0) >= 3:
                        break
                    if node != target:
                        state = client.json("POST", path + "/guess", {"text": node})
                client.json("POST", path + "/clue", {})
            else:
                client.json("POST", path + ("/clue" if game == "conexiuni" else "/hint"), {})
        for step in fixture["steps"]:
            state = client.json("POST", path + "/" + step["action"], step["payload"])
        require(
            state.get("won") is True and isinstance(state.get("score"), int),
            "Seeded winning journey failed",
        )
        terminal = client.json("GET", path)
        require(
            terminal.get("won") is True and terminal.get("score") == state["score"],
            "Terminal session resume failed",
        )
    base = "/api/alchimie/explore"
    state = client.json("POST", base, {})
    path = base + "/" + state["game_id"]
    require(client.json("GET", path) == state, "Exploration resume drift")
    client.json("POST", path + "/hint", {})
    hinted = client.json("POST", path + "/hint", {})
    pair = hinted.get("hint", {}).get("pair")
    require(isinstance(pair, list) and len(pair) == 2, "Exploration pair hint failed")
    state = client.json("POST", path + "/combine", {"a": pair[0]["id"], "b": pair[1]["id"]})
    require(len(state.get("discovered", [])) == 1, "Exploration craft failed")
    checkpoint = state["progress"]
    resumed = client.json("GET", path)
    require(resumed["progress"] == checkpoint, "Exploration checkpoint drift")
    restored = client.json("POST", base, {"progress": checkpoint, "goal_id": state.get("goal_id")})
    require(
        restored["game_id"] != state["game_id"] and restored["progress"] == checkpoint,
        "Exploration restore failed",
    )
    require(restored["inventory"] == resumed["inventory"], "Restored inventory drift")
    return {
        "ok": True,
        "runtime": "go",
        "requests": client.count,
        "request_limit": MAX_REQUESTS,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "games_completed": len(GAMES),
        "exploration_restore": True,
        "assets_verified": len(asset_paths),
        "legal_sha256": legal_hashes,
        "content_hash": manifest["content_hash"],
        "accounts_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.url)
    except SmokeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
