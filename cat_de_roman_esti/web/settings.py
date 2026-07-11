"""Django settings for the cat_de_roman_esti BFF.

Two modes, selected by the ``CAT_ACCOUNTS_ENABLED`` env flag:

* **accounts OFF (default)** — the historical *stateless* deployment: no accounts, no
  sessions, no forms, no database use. Live games sit in the in-memory ``SessionStore``s
  and the KG is a read-only in-memory fixture; contenttypes/auth are installed only because
  DRF imports them, and the sqlite ``:memory:`` DB is never queried. This is byte-identical
  to the anonymous arcade the fleet ships on the "no personal data" launch track.

* **accounts ON** — adds a real database (Postgres in prod), Django sessions/auth/CSRF,
  ``django-allauth`` with the **Google** provider, and the ``accounts`` app (profile,
  consent record, server-side saved progress). This collects personal data from (possibly
  minor) users and MUST run behind the compliance stack + a real controller entity — see
  ``docs/DEPLOY.md`` and ``docs/compliance/``. It is deliberately gated so the anonymous v1
  can ship now and accounts flip on later.

Divergences in the OFF mode (no sessions/CSRF/auth middleware, permissive ALLOWED_HOSTS)
all follow from statelessness; the ON mode restores the full production-safe posture.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # cat_de_roman_esti/web
STATIC_DIR = BASE_DIR / "static"  # the built SPA (Vite outDir; shipped in the wheel)


def _env_bool(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError(f"{name} must be a positive integer") from None
    if value <= 0:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


def _env_list(name: str) -> list[str]:
    return [x.strip() for x in os.environ.get(name, "").split(",") if x.strip()]


DEBUG = _env_bool("CAT_DEBUG")
# The launch flag. OFF = stateless anonymous arcade (default). ON = accounts + Google login.
ACCOUNTS_ENABLED = _env_bool("CAT_ACCOUNTS_ENABLED")

# Public domain the app is served on (e.g. "joc.example.ro"). Drives ALLOWED_HOSTS,
# CSRF_TRUSTED_ORIGINS, and the OAuth redirect origin. Empty in local dev.
CAT_DOMAIN = os.environ.get("CAT_DOMAIN", "").strip()

# --- Secret key -----------------------------------------------------------------------
# Nothing is signed in the stateless OFF mode, so the insecure default is tolerated there
# (and in DEBUG). A real key is REQUIRED once accounts are on in production (it signs the
# session + CSRF cookies that now carry auth state).
_INSECURE_SECRET = "insecure-stateless-cat-de-roman-esti"  # noqa: S105 (placeholder, OFF-mode only)
SECRET_KEY = os.environ.get("CAT_SECRET_KEY", _INSECURE_SECRET)
if ACCOUNTS_ENABLED and not DEBUG and SECRET_KEY == _INSECURE_SECRET:
    raise RuntimeError(
        "CAT_SECRET_KEY must be set to a real secret when CAT_ACCOUNTS_ENABLED=1 and "
        "CAT_DEBUG=0 — it signs the session/CSRF cookies that carry authentication state."
    )

# --- Allowed hosts / CSRF origins ------------------------------------------------------
if _env_list("CAT_ALLOWED_HOSTS"):
    ALLOWED_HOSTS = _env_list("CAT_ALLOWED_HOSTS")
elif CAT_DOMAIN:
    # Loopback is included so the container's own /api/health probe (Host: 127.0.0.1)
    # is not rejected as a DisallowedHost — it is not externally routable.
    ALLOWED_HOSTS = [CAT_DOMAIN, "127.0.0.1", "localhost"]
else:
    # Stateless public arcade behind the operator's proxy had no host-bound cookies/URLs,
    # so "*" was safe there. Kept as the OFF/DEBUG default only.
    ALLOWED_HOSTS = ["*"]

if ACCOUNTS_ENABLED and not DEBUG and (ALLOWED_HOSTS == ["*"] or not ALLOWED_HOSTS):
    raise RuntimeError(
        "Set CAT_DOMAIN (or CAT_ALLOWED_HOSTS) in production with accounts enabled — a "
        'wildcard host allows Host-header attacks against the auth cookies / OAuth redirect.'
    )

CSRF_TRUSTED_ORIGINS = _env_list("CAT_CSRF_TRUSTED_ORIGINS") or (
    [f"https://{CAT_DOMAIN}"] if CAT_DOMAIN else []
)

# --- Apps / middleware -----------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.contenttypes",  # DRF import-time requirement (+ auth/allauth models)
    "django.contrib.auth",  # DRF import-time requirement; the user store when accounts ON
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

if ACCOUNTS_ENABLED:
    INSTALLED_APPS += [
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.sites",
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        "allauth.socialaccount.providers.google",
        "cat_de_roman_esti.accounts",
    ]
    # Session must precede Auth; Csrf after Session. allauth's AccountMiddleware last.
    MIDDLEWARE = [
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "allauth.account.middleware.AccountMiddleware",
    ]

ROOT_URLCONF = "cat_de_roman_esti.web.urls"
WSGI_APPLICATION = "cat_de_roman_esti.web.wsgi.application"
ASGI_APPLICATION = "cat_de_roman_esti.web.asgi.application"

# The API has no trailing slashes (contract parity with the FastAPI era): a near-miss
# path must 404, never 301-redirect. (allauth's own /accounts/* routes are unaffected.)
APPEND_SLASH = False

# allauth + the messages framework need a template engine + a few context processors.
# The stateless OFF mode renders no templates, so it keeps the empty list.
if ACCOUNTS_ENABLED:
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        }
    ]
else:
    TEMPLATES = []

# --- Database --------------------------------------------------------------------------
_db_url = os.environ.get("CAT_DATABASE_URL") or os.environ.get("DATABASE_URL")
if ACCOUNTS_ENABLED:
    if _db_url:
        import dj_database_url

        DATABASES = {
            "default": dj_database_url.parse(
                _db_url, conn_max_age=600, ssl_require=_env_bool("CAT_DB_SSL")
            )
        }
    else:
        # Local dev / tests fallback: accounts need a persistent DB, so a real sqlite file
        # (not :memory:). Tests point CAT_DATABASE_URL at sqlite:// for an isolated test DB.
        _sqlite_name = os.environ.get("CAT_DB_PATH") or str(
            BASE_DIR.parent.parent / "cat_accounts.sqlite3"
        )
        DATABASES = {
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": _sqlite_name}
        }
else:
    # Configured because Django requires one; nothing reads or writes it. No migrations.
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
LANGUAGE_CODE = "ro"

# --- Auth / allauth (accounts ON only) -------------------------------------------------
if ACCOUNTS_ENABLED:
    SITE_ID = 1
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    ]
    LOGIN_REDIRECT_URL = "/"
    ACCOUNT_LOGOUT_REDIRECT_URL = "/"
    LOGIN_URL = "/accounts/google/login/"
    # Google is the ONLY sign-in path — no local username/password surface at all.
    ACCOUNT_EMAIL_VERIFICATION = "none"  # Google emails arrive pre-verified
    SOCIALACCOUNT_LOGIN_ON_GET = True  # click -> Google, no interstitial confirm page
    SOCIALACCOUNT_AUTO_SIGNUP = True
    SOCIALACCOUNT_STORE_TOKENS = False  # data minimisation: never persist OAuth tokens
    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "APP": {
                "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
                "secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
                "key": "",
            },
            "SCOPE": ["profile", "email"],
            "AUTH_PARAMS": {"access_type": "online"},
            "OAUTH_PKCE_ENABLED": True,
        }
    }

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # Global default stays anonymous so the word-game endpoints keep playing without login
    # (and never require CSRF). The account views opt INTO SessionAuthentication per-view.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Renders FastAPI-parity error bodies ({"detail": ...} / 422 pydantic arrays).
    "EXCEPTION_HANDLER": "cat_de_roman_esti.web.http.exception_handler",
}

# Every API body in this BFF is a small JSON command. Reject oversized requests
# before parsing them so anonymous game endpoints cannot consume megabytes per hit.
DATA_UPLOAD_MAX_MEMORY_SIZE = _env_positive_int("CAT_MAX_REQUEST_BYTES", 64 * 1024)

SPECTACULAR_SETTINGS = {
    "TITLE": "cat_de_roman_esti",
    "DESCRIPTION": "Server-authoritative word-game arcade over the Romanian knowledge graph.",
    "VERSION": "1.2.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Same origins the FastAPI app allowed (Vite dev server etc.). Prod is same-origin.
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"]
CORS_ALLOW_CREDENTIALS = True

# --- Production security posture (accounts ON, not DEBUG) ------------------------------
# Behind Caddy/Cloudflare terminating TLS and forwarding X-Forwarded-Proto. Off in DEBUG
# and in the stateless anonymous mode (no cookies to protect there).
if ACCOUNTS_ENABLED and not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = _env_bool("CAT_SSL_REDIRECT", "1")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False  # the SPA reads the csrftoken cookie to echo X-CSRFToken
    SESSION_COOKIE_SAMESITE = "Lax"  # sent on the top-level GET redirect back from Google
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    # HSTS is opt-in via env (raise once the domain + TLS are stable to avoid lock-in).
    SECURE_HSTS_SECONDS = int(os.environ.get("CAT_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("CAT_HSTS_SUBDOMAINS")
    SECURE_HSTS_PRELOAD = _env_bool("CAT_HSTS_PRELOAD")

# WhiteNoise's default immutable-name detector expects Django's 12-hex manifest
# format. Vite emits an 8-character URL-safe hash after a dash, so declare that
# format explicitly; otherwise versioned assets receive only a one-minute cache.
_VITE_HASHED_ASSET = re.compile(
    r"^/assets/.+-[A-Za-z0-9_-]{8}\.(?:css|js|woff|woff2)$"
)


def _vite_asset_is_immutable(path: str, url: str) -> bool:
    del path
    return _VITE_HASHED_ASSET.fullmatch(url) is not None


WHITENOISE_IMMUTABLE_FILE_TEST = _vite_asset_is_immutable

# WhiteNoise serves the built SPA from the URL root; deep links fall through to
# the SPA catch-all view.
WHITENOISE_ROOT = str(STATIC_DIR)
WHITENOISE_INDEX_FILE = True
STATIC_URL = "/static/"  # required by Django; the SPA is served from "/" by WhiteNoise

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": os.environ.get("CAT_LOG_LEVEL", "INFO").upper()},
}

# Age of digital consent in Romania (GDPR Art. 8, national derogation). Accounts for users
# below this age require verifiable parental consent — see accounts/views.py + docs/compliance/.
CAT_MIN_SELF_CONSENT_AGE = int(os.environ.get("CAT_MIN_SELF_CONSENT_AGE", "16"))
# Version stamp stored on every consent record so a policy change can force re-consent.
CAT_CONSENT_VERSION = os.environ.get("CAT_CONSENT_VERSION", "2026-07-09")

# Donations are the monetisation strategy (ONG donation-first). When set, the SPA shows a
# "Donează" button linking here (both modes). Empty = the button is hidden. The real
# donation page/provider (Stripe / redirecționează.ro / the ONG's link) is an owner task.
CAT_DONATE_URL = os.environ.get("CAT_DONATE_URL", "").strip()
