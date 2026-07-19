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
from ..wordgames.categories import CATEGORIES
from ..wordgames.packs import get_pack
from ..wordgames.service import get_service
from .http import ContractAPIView

# Loose per-game node floors under which mining a category-scoped game is hopeless;
# the UI uses `available` to only offer categories that will actually start.
_MINE_FLOORS = {"contexto": 10, "lant": 10, "alchimie": 8}

# Arcade metadata — the SPA home screen mirrors this (kept here so /api/health can
# report it).
GAMES = [
    {
        "key": "alchimie",
        "label": "Alchimie",
        "blurb": "Combina doua concepte ca sa descoperi unul nou — pana ajungi la tinta.",
    },
    {
        "key": "conexiuni",
        "label": "Conexiuni",
        "blurb": "Grupeaza cele 16 concepte in cele 4 categorii ascunse, cate 4 fiecare.",
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


class CategoriesView(ContractAPIView):
    @extend_schema(operation_id="meta_categories", tags=["meta"])
    def get(self, request) -> Response:
        """The category taxonomy + per-game availability (curated counts included).

        ``available.<game>`` is true when the game can actually start for that
        category: a curated instance is approved, or (except Conexiuni, whose
        boards cannot be mined per-category) the fixture has enough nodes to mine.
        """
        svc = get_service()
        pack = get_pack()
        out = []
        for key, (label, kind) in CATEGORIES.items():
            curated = pack.counts(category=key)
            nodes = len(svc.by_category(key))
            available = {
                "conexiuni": curated["conexiuni"] > 0,
                "contexto": curated["contexto"] > 0 or nodes >= _MINE_FLOORS["contexto"],
                "lant": curated["lant"] > 0 or nodes >= _MINE_FLOORS["lant"],
                "alchimie": curated["alchimie"] > 0 or nodes >= _MINE_FLOORS["alchimie"],
            }
            out.append(
                {
                    "key": key,
                    "label": label,
                    "kind": kind,
                    "node_count": nodes,
                    "curated": curated,
                    "available": available,
                }
            )
        return Response({"categories": out})


class ManifestView(ContractAPIView):
    @extend_schema(operation_id="meta_manifest", tags=["meta"])
    def get(self, request) -> Response:
        """Trust manifest for the bundled offline KG (version + schema + content hash)."""
        return Response(_manifest_payload())


def healthz(request: HttpRequest) -> JsonResponse:
    """Fleet-uniform liveness: cheap, no KG/service touch."""
    return JsonResponse({"ok": True})


def me_disabled(request: HttpRequest) -> JsonResponse:
    """`/api/me` when accounts are OFF: report the feature disabled so the SPA hides login.

    Still carries ``donate_url`` so the anonymous arcade can show the Donează button.
    """
    from django.conf import settings

    return JsonResponse(
        {
            "accounts_enabled": False,
            "authenticated": False,
            "user": None,
            "donate_url": getattr(settings, "CAT_DONATE_URL", ""),
        }
    )


def api_not_found(request: HttpRequest, *args, **kwargs) -> JsonResponse:
    """Unknown /api/* paths stay JSON 404 (starlette-parity, byte-identical), never the SPA."""
    return JsonResponse(
        {"detail": "Not Found"}, status=404, json_dumps_params={"separators": (",", ":")}
    )
