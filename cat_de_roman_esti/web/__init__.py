"""Web backend-for-frontend (BFF) for the cat_de_roman_esti word-game arcade.

A FastAPI app that serves the built React SPA at ``/`` and four SERVER-AUTHORITATIVE
text word-games under ``/api/wordgames/*``, all backed by
the bundled offline knowledge graph via :mod:`cat_de_roman_esti.wordgames.service`. Game
logic and secrets never reach the browser.

Public entry point:

    from cat_de_roman_esti.web import create_app
    app = create_app()
"""

from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]
