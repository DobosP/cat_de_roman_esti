"""Meta endpoints: /api/health, /api/manifest, /healthz — plus the arcade metadata.

/api/health and /api/manifest are contract endpoints (byte-parity with the FastAPI
era, operationIds ``meta_health``/``meta_manifest``). /healthz is the fleet-uniform
cheap liveness probe (no KG touch).
"""

from __future__ import annotations

from functools import lru_cache

from django.http import HttpRequest, JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from ..data import fixture_manifest
from ..wordgames.service import get_service
from .http import ContractAPIView

# Arcade metadata — the SPA home screen mirrors this (kept here so /api/health can
# report it).
GAMES = [
    {
        "key": "alchimie",
        "label": "Alchimie",
        "blurb": "Combina doua concepte ca sa descoperi unul nou — pana ajungi la tinta.",
    },
    {
        "key": "contexto",
        "label": "Cald sau Rece",
        "blurb": "Ghiceste conceptul secret; fiecare incercare iti spune cat de aproape esti.",
    },
    {
        "key": "lant",
        "label": "Lantul Cuvintelor",
        "blurb": "Scrie un concept legat de cel curent si sari din cuvant in cuvant pana la tinta.",
    },
    {
        "key": "conexiuni",
        "label": "Conexiuni",
        "blurb": "Grupeaza cele 16 concepte in cele 4 categorii ascunse, cate 4 fiecare.",
    },
]


@lru_cache(maxsize=1)
def _manifest_payload() -> dict:
    """The offline fixture is immutable at runtime; compute its manifest once."""
    return fixture_manifest()


def warm() -> None:
    """Eagerly build the KG service + manifest (fail fast on a broken fixture).

    Called from asgi.py/wsgi.py so the first request doesn't pay the load — the
    Django twin of what ``create_app()`` did at construction time.
    """
    get_service()
    _manifest_payload()


class HealthView(ContractAPIView):
    @extend_schema(operation_id="meta_health", tags=["meta"])
    def get(self, request) -> Response:
        svc = get_service()
        return Response(
            {
                "ok": True,
                "source": "offline",
                "concepts": len(svc.all_ids()),
                "games": GAMES,
            }
        )


class ManifestView(ContractAPIView):
    @extend_schema(operation_id="meta_manifest", tags=["meta"])
    def get(self, request) -> Response:
        """Trust manifest for the bundled offline KG (version + schema + content hash)."""
        return Response(_manifest_payload())


def healthz(request: HttpRequest) -> JsonResponse:
    """Fleet-uniform liveness: cheap, no KG/service touch."""
    return JsonResponse({"ok": True})


def api_not_found(request: HttpRequest, *args, **kwargs) -> JsonResponse:
    """Unknown /api/* paths stay JSON 404 (starlette-parity, byte-identical), never the SPA."""
    return JsonResponse(
        {"detail": "Not Found"}, status=404, json_dumps_params={"separators": (",", ":")}
    )
