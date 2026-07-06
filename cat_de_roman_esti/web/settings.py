"""Django settings for the cat_de_roman_esti BFF (fleet-uniform backend shape).

This is a deliberately *stateless* Django deployment: the app has no accounts, no
sessions, no forms and no database use — live games sit in the in-memory
``SessionStore``s (single-process, same as the FastAPI era) and the KG is a
read-only in-memory fixture. contenttypes/auth are installed only because DRF
imports them; the configured sqlite ``:memory:`` DB is never queried and there is
nothing to migrate. Divergences from the fleet checklist (no sessions/CSRF/auth
middleware, permissive ALLOWED_HOSTS default) all follow from that statelessness.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # cat_de_roman_esti/web
STATIC_DIR = BASE_DIR / "static"  # the built SPA (Vite outDir; shipped in the wheel)

# No cookies are signed and no crypto features are used; overridable regardless.
SECRET_KEY = os.environ.get("CAT_SECRET_KEY", "insecure-stateless-cat-de-roman-esti")
DEBUG = os.environ.get("CAT_DEBUG", "0") == "1"
# Public arcade behind the operator's proxy; no host-bound cookies/URLs exist.
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("CAT_ALLOWED_HOSTS", "*").split(",") if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",  # DRF import-time requirement (unused at runtime)
    "django.contrib.auth",  # DRF import-time requirement (no auth is wired)
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "cat_de_roman_esti.web.urls"
WSGI_APPLICATION = "cat_de_roman_esti.web.wsgi.application"
ASGI_APPLICATION = "cat_de_roman_esti.web.asgi.application"

# The API has no trailing slashes (contract parity with the FastAPI era): a near-miss
# path must 404, never 301-redirect.
APPEND_SLASH = False

TEMPLATES: list = []

# Configured because Django requires one; nothing reads or writes it. No migrations.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
LANGUAGE_CODE = "ro"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Renders FastAPI-parity error bodies ({"detail": ...} / 422 pydantic arrays).
    "EXCEPTION_HANDLER": "cat_de_roman_esti.web.http.exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "cat_de_roman_esti",
    "DESCRIPTION": "Server-authoritative word-game arcade over the Romanian knowledge graph.",
    # 1.2.0: additive /api/manifest endpoint + stable operationIds for mobile clients.
    "VERSION": "1.2.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # operationIds are pinned per-view with @extend_schema (contract: <game>_<action>).
}

# Same origins the FastAPI app allowed (Vite dev server etc.). Prod is same-origin.
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"]
CORS_ALLOW_CREDENTIALS = True

# WhiteNoise serves the built SPA from the URL root (hashed /assets/* get immutable
# caching automatically); deep links fall through to the SPA catch-all view.
WHITENOISE_ROOT = str(STATIC_DIR)
WHITENOISE_INDEX_FILE = True
STATIC_URL = "/static/"  # required by Django; nothing is served from it

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": os.environ.get("CAT_LOG_LEVEL", "INFO").upper()},
}
