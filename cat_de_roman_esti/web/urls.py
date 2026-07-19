"""URLconf for the cat_de_roman_esti BFF.

Order matters: contract API routes first, then (when accounts are enabled) the account
API + allauth's ``/accounts/*`` login routes, then the JSON 404 guard for anything else
under ``/api/``, then the SPA catch-all (WhiteNoise has already served real files by the
time a request reaches the resolver).
"""

from __future__ import annotations

from django.conf import settings
from django.urls import path, re_path
from drf_spectacular.views import SpectacularJSONAPIView

from ..wordgames import alchimie, conexiuni, contexto, intrusul, lant, submissions
from . import legal, meta, spa

urlpatterns = [
    path("api/health", meta.HealthView.as_view()),
    path("api/manifest", meta.ManifestView.as_view()),
    path("api/categories", meta.CategoriesView.as_view()),
    path("healthz", meta.healthz),
    # Same schema location the FastAPI app exposed (mobile clients generate from it).
    path("openapi.json", SpectacularJSONAPIView.as_view(), name="schema"),
    # Public legal pages (both modes) — linked from the consent gate + footer.
    path("legal/privacy", legal.privacy),
    path("legal/terms", legal.terms),
    *alchimie.urlpatterns,
    *contexto.urlpatterns,
    *lant.urlpatterns,
    *conexiuni.urlpatterns,
    *intrusul.urlpatterns,
    *submissions.urlpatterns,
]

if settings.ACCOUNTS_ENABLED:
    from django.urls import include

    from ..accounts import urls as accounts_urls

    urlpatterns += accounts_urls.urlpatterns
    # allauth's login/callback/logout machinery (Google provider), e.g.
    # /accounts/google/login/ and its OAuth callback.
    urlpatterns += [path("accounts/", include("allauth.urls"))]
else:
    # Accounts off: a stub /api/me so the SPA can detect the feature is disabled and hide
    # the login UI (keeps the anonymous arcade self-describing).
    urlpatterns += [path("api/me", meta.me_disabled)]

urlpatterns += [
    re_path(r"^api/", meta.api_not_found),
    re_path(r"^.*$", spa.spa_index),
]
