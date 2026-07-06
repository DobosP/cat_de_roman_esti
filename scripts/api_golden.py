"""Capture (or replay) golden /api responses for backend-parity testing.

Used for the FastAPI -> Django port: run against the OLD backend to snapshot the
contract, then against the NEW backend and diff. Deterministic: fixed seeds, and
volatile values (game ids, generated_at) are normalized before writing.

    python scripts/api_golden.py http://127.0.0.1:8000 out/golden-fastapi.json

Stdlib-only on purpose (no requests/httpx dependency).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

SEED = 123
DAILY = "2026-07-06"


def call(base: str, method: str, path: str, body: dict | list | None = None) -> dict:
    url = f"{base}{path}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            payload = json.loads(res.read().decode() or "null")
            status = res.status
    except urllib.error.HTTPError as err:
        raw = err.read().decode()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        status = err.code
    return {"status": status, "body": payload}


def main() -> int:
    base = sys.argv[1].rstrip("/")
    out_path = sys.argv[2]
    flows: dict[str, dict] = {}
    gids: dict[str, str] = {}

    def rec(name: str, method: str, path: str, body: dict | list | None = None) -> dict:
        result = call(base, method, path, body)
        flows[name] = {"request": f"{method} {path}", **result}
        return result

    # ------------------------------------------------------------------ meta
    rec("health", "GET", "/api/health")
    rec("manifest", "GET", "/api/manifest")

    # openapi: keep only the stable, contract-relevant surface.
    api = call(base, "GET", "/openapi.json")
    ops = sorted(
        op.get("operationId", "?")
        for methods in (api["body"].get("paths", {}) or {}).values()
        for op in methods.values()
        if isinstance(op, dict)
    )
    flows["openapi_operation_ids"] = {"request": "GET /openapi.json",
        "status": api["status"], "body": ops}

    # ------------------------------------------------------------------ alchimie
    r = rec("alchimie_create", "POST", f"/api/wordgames/alchimie/games?seed={SEED}&difficulty=usor")
    gid = r["body"]["game_id"]
    gids[gid] = "<GID_ALCHIMIE>"
    inv = [item["id"] for item in r["body"]["inventory"]]
    rec("alchimie_get", "GET", f"/api/wordgames/alchimie/games/{gid}")
    rec("alchimie_get_404", "GET", "/api/wordgames/alchimie/games/nope")
    rec("alchimie_combine_same", "POST",
        f"/api/wordgames/alchimie/games/{gid}/combine", {"a": inv[0], "b": inv[0]})
    rec("alchimie_combine_foreign", "POST",
        f"/api/wordgames/alchimie/games/{gid}/combine", {"a": inv[0], "b": "xyzzy"})
    rec("alchimie_combine_ok", "POST",
        f"/api/wordgames/alchimie/games/{gid}/combine", {"a": inv[0], "b": inv[1]})
    rec("alchimie_hint_early", "POST", f"/api/wordgames/alchimie/games/{gid}/hint")
    rec("alchimie_reset", "POST", f"/api/wordgames/alchimie/games/{gid}/reset")
    rec("alchimie_combine_422", "POST",
        f"/api/wordgames/alchimie/games/{gid}/combine", {"a": 1, "b": 2})
    rec("alchimie_combine_missing_field", "POST",
        f"/api/wordgames/alchimie/games/{gid}/combine", {"a": inv[0]})
    r = rec("alchimie_create_daily", "POST", f"/api/wordgames/alchimie/games?daily={DAILY}")
    gids[r["body"]["game_id"]] = "<GID_ALCHIMIE_DAILY>"
    r = rec("alchimie_create_bad_difficulty", "POST",
        "/api/wordgames/alchimie/games?seed=7&difficulty=impossible")
    gids[r["body"]["game_id"]] = "<GID_ALCHIMIE_BAD_DIFF>"
    rec("alchimie_create_bad_seed_422", "POST", "/api/wordgames/alchimie/games?seed=abc")

    # ------------------------------------------------------------------ contexto
    r = rec("contexto_create", "POST", f"/api/wordgames/contexto/games?seed={SEED}")
    gid = r["body"]["game_id"]
    gids[gid] = "<GID_CONTEXTO>"
    rec("contexto_get", "GET", f"/api/wordgames/contexto/games/{gid}")
    rec("contexto_get_404", "GET", "/api/wordgames/contexto/games/nope")
    rec("contexto_guess_empty", "POST",
        f"/api/wordgames/contexto/games/{gid}/guess", {"text": "   "})
    rec("contexto_guess_unknown", "POST",
        f"/api/wordgames/contexto/games/{gid}/guess", {"text": "xyzzy plugh"})
    rec("contexto_guess_real", "POST",
        f"/api/wordgames/contexto/games/{gid}/guess", {"text": "Mihai Eminescu"})
    rec("contexto_clue_early", "POST", f"/api/wordgames/contexto/games/{gid}/clue")
    rec("contexto_giveup", "POST", f"/api/wordgames/contexto/games/{gid}/giveup")
    rec("contexto_guess_after_end", "POST",
        f"/api/wordgames/contexto/games/{gid}/guess", {"text": "Carpati"})
    r = rec("contexto_create_daily", "POST", f"/api/wordgames/contexto/games?daily={DAILY}")
    gids[r["body"]["game_id"]] = "<GID_CONTEXTO_DAILY>"

    # ------------------------------------------------------------------ lant
    r = rec("lant_create", "POST", f"/api/wordgames/lant/games?seed={SEED}")
    gid = r["body"]["game_id"]
    gids[gid] = "<GID_LANT>"
    rec("lant_get", "GET", f"/api/wordgames/lant/games/{gid}")
    rec("lant_get_404", "GET", "/api/wordgames/lant/games/nope")
    rec("lant_move_empty", "POST", f"/api/wordgames/lant/games/{gid}/move", {"text": ""})
    rec("lant_move_unknown", "POST",
        f"/api/wordgames/lant/games/{gid}/move", {"text": "xyzzy plugh"})
    hint = rec("lant_hint", "POST", f"/api/wordgames/lant/games/{gid}/hint")
    if hint["body"].get("hint"):
        rec("lant_move_hinted", "POST",
            f"/api/wordgames/lant/games/{gid}/move", {"text": hint["body"]["hint"]["label"]})
    rec("lant_undo", "POST", f"/api/wordgames/lant/games/{gid}/undo")
    r = rec("lant_create_daily", "POST", f"/api/wordgames/lant/games?daily={DAILY}")
    gids[r["body"]["game_id"]] = "<GID_LANT_DAILY>"

    # ------------------------------------------------------------------ conexiuni
    r = rec("conexiuni_create", "POST", f"/api/wordgames/conexiuni/games?seed={SEED}")
    gid = r["body"]["game_id"]
    gids[gid] = "<GID_CONEXIUNI>"
    tiles = [t["id"] for t in r["body"]["tiles"]]
    rec("conexiuni_get", "GET", f"/api/wordgames/conexiuni/games/{gid}")
    rec("conexiuni_get_404", "GET", "/api/wordgames/conexiuni/games/nope")
    rec("conexiuni_guess_two", "POST",
        f"/api/wordgames/conexiuni/games/{gid}/guess", {"ids": tiles[:2]})
    rec("conexiuni_guess_offboard", "POST",
        f"/api/wordgames/conexiuni/games/{gid}/guess",
        {"ids": [tiles[0], tiles[1], tiles[2], "xyzzy"]})
    rec("conexiuni_guess_four", "POST",
        f"/api/wordgames/conexiuni/games/{gid}/guess", {"ids": tiles[:4]})
    rec("conexiuni_clue_early", "POST", f"/api/wordgames/conexiuni/games/{gid}/clue")
    r = rec("conexiuni_create_daily", "POST", f"/api/wordgames/conexiuni/games?daily={DAILY}")
    gids[r["body"]["game_id"]] = "<GID_CONEXIUNI_DAILY>"

    # ------------------------------------------------------------------ SPA serving
    spa_flows = [("spa_root", "/"), ("spa_deep_link", "/conexiuni"), ("api_404", "/api/nope")]
    for name, path in spa_flows:
        req = urllib.request.Request(f"{base}{path}")
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                flows[name] = {
                    "request": f"GET {path}",
                    "status": res.status,
                    "content_type": res.headers.get("content-type", ""),
                }
        except urllib.error.HTTPError as err:
            flows[name] = {
                "request": f"GET {path}",
                "status": err.code,
                "content_type": err.headers.get("content-type", ""),
                "body": err.read().decode()[:200],
            }

    # ------------------------------------------------------- normalize volatiles
    text = json.dumps(flows, ensure_ascii=False, indent=1, sort_keys=True)
    for real, placeholder in gids.items():
        text = text.replace(real, placeholder)
    # manifest generated_at is build-time volatile
    text = re.sub(r'"generated_at": "[^"]*"', '"generated_at": "<TS>"', text)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"captured {len(flows)} flows -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
