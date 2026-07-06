"""Web backend-for-frontend (BFF) for the cat_de_roman_esti word-game arcade.

A Django (5.2 + DRF) app that serves the built React SPA at ``/`` and four
SERVER-AUTHORITATIVE text word-games under ``/api/wordgames/*``, all backed by the
bundled offline knowledge graph via :mod:`cat_de_roman_esti.wordgames.service`.
Game logic and secrets never reach the browser.

Public entry points:

    python -m cat_de_roman_esti.web --host 127.0.0.1 --port 8000   # uvicorn (ASGI)
    cat_de_roman_esti.web.asgi:application                          # any ASGI server
    cat_de_roman_esti.web.wsgi:application                          # gunicorn --workers 1

Single process on purpose: live game sessions are in-memory (SessionStore).
"""

from __future__ import annotations
