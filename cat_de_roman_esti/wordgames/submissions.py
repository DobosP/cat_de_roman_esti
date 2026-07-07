"""User-submitted games — the intake half of the curated pipeline (ADR-0011).

Players may propose a game instance for any of the four word games. A submission
is validated with the exact rules the curated pack validator applies (shape,
enums, node resolution, playability) and then appended — as ``status: pending``,
``source: user`` — to a JSONL queue on disk. Nothing a player submits is ever
served directly: promotion into ``fixtures/games_pack.json`` happens offline via
``scripts/review_submissions.py`` after human/AI review.

The server is deliberately stateless (no DB), so the queue lives on a mounted
volume named by ``CAT_SUBMISSIONS_DIR``. When the variable is unset the feature
is off and the endpoint answers 503 — deployments opt in explicitly.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path

from django.urls import path
from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.response import Response

from ..web.http import ContractAPIView, http_error, parse_body
from .packs import DIFFICULTIES, GAME_KINDS, item_fields, validate_pack_item

SUBMISSIONS_ENV = "CAT_SUBMISSIONS_DIR"
QUEUE_FILENAME = "submissions.jsonl"

# Abuse guards: submissions are tiny JSON documents from humans, not bulk uploads.
MAX_BODY_BYTES = 64 * 1024
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW_SECONDS = 3600.0

_rate_lock = threading.Lock()
_rate_hits: dict[str, list[float]] = {}


def _throttled(client: str, now: float | None = None) -> bool:
    """Sliding-window rate limit per client address (in-memory, single-process)."""
    now = time.monotonic() if now is None else now
    with _rate_lock:
        hits = [t for t in _rate_hits.get(client, []) if now - t < RATE_LIMIT_WINDOW_SECONDS]
        if len(hits) >= RATE_LIMIT_MAX:
            _rate_hits[client] = hits
            return True
        hits.append(now)
        _rate_hits[client] = hits
        return False


class SubmissionBody(BaseModel):
    game: str
    category: str
    difficulty: str
    payload: dict
    author: str | None = None


class CreateSubmissionView(ContractAPIView):
    @extend_schema(operation_id="submissions_create", tags=["submissions"])
    def post(self, request):
        outdir = os.environ.get(SUBMISSIONS_ENV)
        if not outdir:
            raise http_error(503, "Trimiterea de jocuri nu este activata pe acest server.")
        if len(request.body or b"") > MAX_BODY_BYTES:
            raise http_error(413, "Propunerea este prea mare.")
        client = str(request.META.get("REMOTE_ADDR") or "unknown")
        if _throttled(client):
            raise http_error(429, "Prea multe propuneri; incearca mai tarziu.")

        body = parse_body(request, SubmissionBody)
        if body.game not in GAME_KINDS:
            raise http_error(400, "Joc necunoscut.")
        if body.difficulty not in DIFFICULTIES:
            raise http_error(400, "Dificultate necunoscuta.")

        rec = {
            "id": f"sub_{uuid.uuid4().hex[:12]}",
            "category": body.category,
            "difficulty": body.difficulty,
            "source": "user",
            "status": "pending",
        }
        for field in item_fields(body.game) - set(rec):
            if field in body.payload:
                rec[field] = body.payload[field]
        errors = validate_pack_item(rec, body.game)
        if errors:
            raise http_error(400, "Propunere invalida: " + "; ".join(errors))

        line = json.dumps(
            {"game": body.game, "author": (body.author or "").strip()[:80] or None, "item": rec},
            ensure_ascii=False,
        )
        try:
            queue_dir = Path(outdir)
            queue_dir.mkdir(parents=True, exist_ok=True)
            with (queue_dir / QUEUE_FILENAME).open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            raise http_error(503, "Nu am putut salva propunerea; incearca mai tarziu.") from None

        return Response(
            {
                "ok": True,
                "id": rec["id"],
                "status": "pending",
                "message": "Multumim! Jocul tau intra in validare inainte de publicare.",
            },
            status=202,
        )


urlpatterns = [
    path("api/submissions", CreateSubmissionView.as_view()),
]
