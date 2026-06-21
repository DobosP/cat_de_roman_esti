"""FastAPI app factory for the cat_de_roman_esti BFF.

``create_app()`` loads the :class:`~cat_de_roman_esti.data.KgBundle` once at startup
(offline fixture by default, live ``ro_data_server`` when ``ROEDU_API_URL`` is set and
reachable — fail-soft to offline with a logged note), wires the ``/api`` routes from
the contract, and mounts the built SPA at ``/`` (or a small placeholder page when no
build is present). It is SERVER-AUTHORITATIVE: hops are validated + scored through
:class:`~cat_de_roman_esti.engine.HopGame`, and the API key never reaches the browser.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..data import KgBundle, load_fixture, load_from_client
from ..engine import HopGame, Mode
from ..roedu_client import RoeduClient
from .sessions import SessionStore, build_view
from .views import game_state

log = logging.getLogger("cat_de_roman_esti.web")

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Human-facing Romanian category labels for the menu (lever-free cosmetic copy).
CATEGORY_LABELS = {
    "istorie": "Istorie",
    "literatura": "Literatură",
    "geografie": "Geografie",
    "personalitati": "Personalități",
    "arta_cultura": "Artă și cultură",
    "stiinta": "Știință",
    "societate": "Societate",
    "limba": "Limbă",
    "mixed": "Mixt",
}

_PLACEHOLDER_HTML = """<!doctype html>
<html lang="ro">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>cat_de_roman_esti</title>
  <style>
    body { margin:0; min-height:100vh; display:flex; align-items:center;
      justify-content:center; font-family: system-ui, sans-serif; color:#e8e8f0;
      background: radial-gradient(1200px 800px at 30% 20%, #1b2350, #0a0d1f 70%); }
    .card { max-width: 34rem; padding: 2rem 2.5rem; border-radius: 18px;
      background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    h1 { margin:0 0 .5rem; font-size:1.6rem;
      background: linear-gradient(90deg,#ffd166,#ef476f,#118ab2);
      -webkit-background-clip:text; background-clip:text; color:transparent; }
    code { background: rgba(255,255,255,0.08); padding:.15rem .4rem; border-radius:6px; }
    a { color:#84d6ff; }
    p { line-height:1.55; }
  </style>
</head>
<body>
  <div class="card">
    <h1>cat_de_roman_esti</h1>
    <p>The API is live, but the front-end build is missing.</p>
    <p>Build the SPA to play the animated semantic-hop game:</p>
    <p><code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></p>
    <p>The API is at <a href="/api/health">/api/health</a> ·
       <a href="/api/catalog">/api/catalog</a>.</p>
  </div>
</body>
</html>
"""


# --------------------------------------------------------------------- DTOs (in)
class NewGameBody(BaseModel):
    category: str
    difficulty: str
    # Optional id of the just-finished puzzle: when more than one candidate exists, the
    # picker advances to the first candidate whose id != exclude (so "Next" moves on),
    # otherwise it replays candidates[0]. Additive + backward-compatible.
    exclude: str | None = None


class HopBody(BaseModel):
    to: str


# --------------------------------------------------------------- bundle loading
def _load_bundle() -> tuple[KgBundle, str, str | None]:
    """Load the KG bundle. Returns (bundle, source, server_url).

    Offline fixture by default. When ``ROEDU_API_URL`` is set we probe the live
    ``ro_data_server`` via the vendored client; any failure (unreachable / unhealthy)
    fails SOFT back to the offline fixture with a logged note. The API key is read from
    the environment server-side and never leaves the process.
    """
    server_url = os.environ.get("ROEDU_API_URL")
    if not server_url:
        log.info("ROEDU_API_URL unset — using bundled offline fixture")
        return load_fixture(), "offline", None

    api_key = os.environ.get("ROEDU_API_KEY", "cat-de-roman-dev")
    client = RoeduClient(server_url, api_key=api_key)
    try:
        health = client.health()
        if not health.get("ok", True):
            raise RuntimeError("server reports unhealthy")
        bundle = load_from_client(client)
    except Exception as exc:  # network down, server absent, gate refusal, etc.
        log.warning(
            "could not use live RO-EDU server at %s (%s) — falling back to offline fixture",
            server_url,
            exc,
        )
        return load_fixture(), "offline", None

    if not bundle.puzzles:
        log.warning(
            "live RO-EDU server at %s returned no puzzles — falling back to offline fixture",
            server_url,
        )
        return load_fixture(), "offline", None

    log.info("loaded live KG bundle from %s", server_url)
    return bundle, "live", server_url


# --------------------------------------------------------------------- factory
def create_app() -> FastAPI:
    bundle, source, server_url = _load_bundle()
    store = SessionStore()

    app = FastAPI(title="cat_de_roman_esti", version="0.1.0")

    # CORS for dev: the Vite dev server runs on a different localhost origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    def _catalog() -> list[dict]:
        """Per-category easy/hard puzzle counts for the menu."""
        cats = sorted({p.category for p in bundle.puzzles})
        out: list[dict] = []
        for cat in cats:
            easy = len(bundle.puzzles_for(category=cat, difficulty="easy"))
            hard = len(bundle.puzzles_for(category=cat, difficulty="hard"))
            out.append(
                {
                    "category": cat,
                    "label": CATEGORY_LABELS.get(cat, cat.capitalize()),
                    "easy": easy,
                    "hard": hard,
                }
            )
        return out

    # ----------------------------------------------------------------- /api
    @app.get("/api/health")
    def health() -> dict:
        # Agree with /api/catalog: the count is the number of distinct PUZZLE categories
        # the catalog lists (which is what the menu shows), not the node-category set.
        return {
            "ok": True,
            "source": source,
            "server_url": server_url,
            "categories": len(_catalog()),
        }

    @app.get("/api/catalog")
    def catalog() -> dict:
        return {"source": source, "categories": _catalog()}

    @app.post("/api/games", status_code=201)
    def new_game(body: NewGameBody) -> dict:
        try:
            mode = Mode.parse(body.difficulty)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        candidates = bundle.puzzles_for(category=body.category, difficulty=mode.value)
        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"no '{mode.value}' puzzle for category '{body.category}'",
            )
        # "Next" advances: when exclude is given and there's more than one candidate,
        # pick the first whose id != exclude; otherwise (single candidate or no exclude)
        # fall back to candidates[0], which gracefully replays the same puzzle.
        puzzle = candidates[0]
        if body.exclude is not None and len(candidates) > 1:
            puzzle = next((p for p in candidates if p.id != body.exclude), candidates[0])

        try:
            game = HopGame.load(bundle.graph, puzzle, mode)
        except ValueError as exc:  # unplayable puzzle (missing start/target node)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        view_nodes, view_edges = build_view(bundle.graph, puzzle, mode)
        session = store.create(
            game,
            category=body.category,
            view_nodes=view_nodes,
            view_edges=view_edges,
        )
        return game_state(session)

    @app.get("/api/games/{game_id}")
    def get_game(game_id: str) -> dict:
        session = store.get(game_id)
        if session is None:
            raise HTTPException(status_code=404, detail="game not found")
        return game_state(session)

    @app.post("/api/games/{game_id}/hop")
    def hop(game_id: str, body: HopBody) -> dict:
        session = store.get(game_id)
        if session is None:
            raise HTTPException(status_code=404, detail="game not found")
        with session.lock:
            result = session.game.hop(body.to)
            if not result.ok:
                return game_state(session, last_error=result.reason)
            return game_state(session)

    @app.post("/api/games/{game_id}/undo")
    def undo(game_id: str) -> dict:
        session = store.get(game_id)
        if session is None:
            raise HTTPException(status_code=404, detail="game not found")
        with session.lock:
            result = session.game.undo()
            if not result.ok:
                return game_state(session, last_error=result.reason)
            return game_state(session)

    @app.post("/api/games/{game_id}/reset")
    def reset(game_id: str) -> dict:
        session = store.get(game_id)
        if session is None:
            raise HTTPException(status_code=404, detail="game not found")
        session.reset()
        return game_state(session)

    # ----------------------------------------------------------------- static
    index_html = STATIC_DIR / "index.html"
    if index_html.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="spa")
        log.info("mounted built SPA from %s", STATIC_DIR)
    else:
        @app.get("/", response_class=HTMLResponse)
        def placeholder() -> HTMLResponse:
            return HTMLResponse(_PLACEHOLDER_HTML)

        log.info("no SPA build at %s — serving placeholder page at /", STATIC_DIR)

    return app
