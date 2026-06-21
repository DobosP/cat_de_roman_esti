"""Web backend-for-frontend (BFF) for the cat_de_roman_esti semantic-hop game.

A FastAPI app that serves the built React SPA at ``/`` and a small JSON ``/api``
surface that is SERVER-AUTHORITATIVE: every hop is validated and scored through the
existing tested :class:`cat_de_roman_esti.engine.HopGame`; the cat-de-roman-dev API
key never reaches the browser. The data source is the bundled OFFLINE fixture by
default, or the live ``ro_data_server`` when ``ROEDU_API_URL`` is set and reachable
(fail-soft to offline otherwise).

Public entry point:

    from cat_de_roman_esti.web import create_app
    app = create_app()
"""

from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]
