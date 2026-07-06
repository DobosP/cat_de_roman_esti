"""ASGI entrypoint — what `python -m cat_de_roman_esti.web` (uvicorn) serves."""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()

# Warm the KG service + fixture manifest once at startup so the first request
# doesn't pay the load and a broken fixture fails fast (create_app() parity).
from .meta import warm  # noqa: E402

warm()
