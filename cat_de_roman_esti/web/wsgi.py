"""WSGI entrypoint (gunicorn option; the default deploy path is asgi.py/uvicorn).

The in-memory game sessions require a SINGLE process — with gunicorn use
``--workers 1`` (threads are fine; the stores are lock-guarded).
"""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()

from .meta import warm  # noqa: E402

warm()
