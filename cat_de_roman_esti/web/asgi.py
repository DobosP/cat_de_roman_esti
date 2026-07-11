"""ASGI entrypoint — what `python -m cat_de_roman_esti.web` (uvicorn) serves."""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

from django.conf import settings  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402

from .asgi_limits import RequestBodyLimitASGI  # noqa: E402

django_application = get_asgi_application()
application = RequestBodyLimitASGI(
    django_application,
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE,
)

# Warm the KG service + fixture manifest once at startup so the first request
# doesn't pay the load and a broken fixture fails fast (create_app() parity).
from .meta import warm  # noqa: E402

warm()
