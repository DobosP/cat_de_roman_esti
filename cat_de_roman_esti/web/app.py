"""FastAPI app factory for the cat_de_roman_esti word-game arcade (BFF).

``create_app()`` mounts three server-authoritative TEXT mini-games over the bundled
Romanian knowledge graph (no graph visualization) and serves the built SPA:

  * ``/api/wordgames/alchimie``  — combine two concepts into a new one until you craft the target.
  * ``/api/wordgames/contexto``  — find a hidden concept guided by "hot/cold" distance.
  * ``/api/wordgames/lant``      — type a linked concept to hop word-by-word to the target.

Each game is a self-contained ``APIRouter`` (``cat_de_roman_esti/wordgames/<game>.py``)
backed by the shared :mod:`cat_de_roman_esti.wordgames.service` (offline KG, loaded once).
All game logic + secrets stay server-side; the SPA only renders responses.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..wordgames.alchimie import router as alchimie_router
from ..wordgames.contexto import router as contexto_router
from ..wordgames.lant import router as lant_router
from ..wordgames.service import get_service

log = logging.getLogger("cat_de_roman_esti.web")

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Arcade metadata — the home screen mirrors this (kept here so /api/health can report it).
GAMES = [
    {
        "key": "alchimie",
        "label": "Alchimie",
        "blurb": "Combina doua concepte ca sa descoperi unul nou — pana ajungi la tinta.",
    },
    {
        "key": "contexto",
        "label": "Cald sau Rece",
        "blurb": "Ghiceste conceptul secret; fiecare incercare iti spune cat de aproape esti.",
    },
    {
        "key": "lant",
        "label": "Lantul Cuvintelor",
        "blurb": "Scrie un concept legat de cel curent si sari din cuvant in cuvant pana la tinta.",
    },
]

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
    <p>Build the SPA to play the word-game arcade:</p>
    <p><code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></p>
    <p>The API is at <a href="/api/health">/api/health</a>.</p>
  </div>
</body>
</html>
"""


def create_app() -> FastAPI:
    # Build the shared KG service once at startup (offline fixture) so the first request
    # doesn't pay the load, and a missing/broken fixture fails fast here.
    get_service()

    app = FastAPI(title="cat_de_roman_esti", version="1.1.0")

    # CORS for dev: the Vite dev server runs on a different localhost origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/api/health")
    def health() -> dict:
        svc = get_service()
        return {
            "ok": True,
            "source": "offline",
            "concepts": len(svc.all_ids()),
            "games": GAMES,
        }

    # The three text games (each self-contained, server-authoritative).
    app.include_router(alchimie_router)
    app.include_router(contexto_router)
    app.include_router(lant_router)

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
