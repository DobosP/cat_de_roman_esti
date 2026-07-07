"""URLconf for the cat_de_roman_esti BFF.

Order matters: contract API routes first, then the JSON 404 guard for anything
else under /api/, then the SPA catch-all (WhiteNoise has already served real
files by the time a request reaches the resolver).
"""

from __future__ import annotations

from django.urls import path, re_path
from drf_spectacular.views import SpectacularJSONAPIView

from ..wordgames import alchimie, conexiuni, contexto, lant, submissions
from . import meta, spa

urlpatterns = [
    path("api/health", meta.HealthView.as_view()),
    path("api/manifest", meta.ManifestView.as_view()),
    path("api/categories", meta.CategoriesView.as_view()),
    path("healthz", meta.healthz),
    # Same schema location the FastAPI app exposed (mobile clients generate from it).
    path("openapi.json", SpectacularJSONAPIView.as_view(), name="schema"),
    *alchimie.urlpatterns,
    *contexto.urlpatterns,
    *lant.urlpatterns,
    *conexiuni.urlpatterns,
    *submissions.urlpatterns,
    re_path(r"^api/", meta.api_not_found),
    re_path(r"^.*$", spa.spa_index),
]
