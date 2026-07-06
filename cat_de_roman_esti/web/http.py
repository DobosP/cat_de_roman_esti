"""HTTP shim for the Django/DRF port — FastAPI-parity error + parsing helpers.

The SPA and the generated mobile clients were built against the FastAPI error
surface, so this module reproduces it exactly:

* business errors  -> ``{"detail": "<string>"}`` with the endpoint's status code
  (raise :func:`http_error`, mirroring FastAPI's ``HTTPException``);
* validation errors -> ``422 {"detail": [<pydantic error dicts>]}`` with ``loc``
  prefixed by ``body`` / ``query`` (what FastAPI's RequestValidationError emits);
* request bodies keep their pydantic v2 models (fleet convention) — DRF is the
  view/transport layer only.

Import surface for the game modules: ``http_error``, ``parse_body``,
``query_int``, ``query_str``.
"""

from __future__ import annotations

import json
from typing import TypeVar

import pydantic
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler


class ContractAPIView(APIView):
    """APIView with FastAPI/starlette method semantics.

    ``metadata_class = None`` disables DRF's automatic 200-with-metadata OPTIONS
    handler, so an undeclared method (including OPTIONS outside CORS preflight)
    raises MethodNotAllowed — rendered below as the starlette-parity 405 body.
    """

    metadata_class = None


class ApiHttpError(Exception):
    """FastAPI-HTTPException-alike: a status code + a ``detail`` payload."""

    def __init__(self, status_code: int, detail: object) -> None:
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


def http_error(status_code: int, detail: str) -> ApiHttpError:
    """Build (to ``raise``) a business error rendered as ``{"detail": detail}``."""
    return ApiHttpError(status_code, detail)


def _validation_error(errors: list[dict], scope: str) -> ApiHttpError:
    """422 with pydantic error dicts, ``loc`` prefixed with body/query like FastAPI."""
    detail = [{**err, "loc": [scope, *err.get("loc", ())]} for err in errors]
    return ApiHttpError(422, detail)


M = TypeVar("M", bound=pydantic.BaseModel)


def parse_body(request, model: type[M]) -> M:
    """Validate the JSON request body against a pydantic model (FastAPI parity)."""
    raw = request.body or b""
    try:
        data = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError as exc:
        err = {
            "type": "json_invalid",
            "loc": [],
            "msg": "JSON decode error",
            "input": {},
            "ctx": {"error": exc.msg},
        }
        raise _validation_error([err], "body") from exc
    try:
        return model.model_validate(data)
    except pydantic.ValidationError as exc:
        raise _validation_error(exc.errors(include_url=False), "body") from exc


def query_int(request, name: str) -> int | None:
    """Optional integer query param; non-integers get FastAPI's 422 shape."""
    raw = request.query_params.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        raise _validation_error(
            [
                {
                    "type": "int_parsing",
                    "loc": [name],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "input": raw,
                }
            ],
            "query",
        ) from None


def query_str(request, name: str, default: str | None = None) -> str | None:
    """Optional string query param (absent -> ``default``, FastAPI semantics)."""
    value = request.query_params.get(name)
    return default if value is None else value


def exception_handler(exc, context):
    """DRF EXCEPTION_HANDLER: render ApiHttpError / 405s as FastAPI would."""
    if isinstance(exc, ApiHttpError):
        return Response({"detail": exc.detail}, status=exc.status_code)
    if isinstance(exc, MethodNotAllowed):
        # starlette parity: fixed detail string, no method name interpolation.
        return Response({"detail": "Method Not Allowed"}, status=405)
    return drf_exception_handler(exc, context)
