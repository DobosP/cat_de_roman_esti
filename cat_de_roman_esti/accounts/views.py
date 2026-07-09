"""Account API — the SPA's auth + saved-progress surface (accounts ON only).

Endpoints (all same-origin, session-cookie authenticated):

* ``GET  /api/me``          — current user + consent state (also seeds the CSRF cookie).
* ``POST /api/auth/logout`` — end the session.
* ``POST /api/me/consent``  — the age gate: birth year + privacy/ToS acceptance.
* ``GET  /api/me/scores``   — saved game history for this account.
* ``POST /api/me/scores``   — upload finished runs (idempotent bulk sync).
* ``POST /api/me/delete``   — DSAR erasure: delete the account and all its data.

The word-game endpoints stay anonymous + CSRF-free; only these views opt into
``SessionAuthentication`` (which enforces CSRF for unsafe methods on logged-in users).
Login itself is handled by allauth at ``/accounts/google/login/``.
"""

from __future__ import annotations

import pydantic
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..web.http import ContractAPIView, http_error, parse_data
from .models import ConsentRecord, Profile, ScoreEntry

# Keep the saved-history response bounded (mirrors the browser store's caps).
_SCORES_READ_CAP = 500
_SCORES_SYNC_CAP = 500


def _profile_for(user) -> Profile:
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def _google_extra(user) -> dict:
    """Read display name / avatar from allauth's SocialAccount (we don't duplicate it)."""
    try:
        from allauth.socialaccount.models import SocialAccount

        acct = SocialAccount.objects.filter(user=user, provider="google").first()
        return dict(acct.extra_data) if acct and isinstance(acct.extra_data, dict) else {}
    except Exception:  # pragma: no cover - socialaccount always present when accounts ON
        return {}


def _user_payload(user) -> dict:
    profile = _profile_for(user)
    extra = _google_extra(user)
    name = (
        profile.display_name
        or extra.get("name")
        or (user.get_full_name() or "").strip()
        or (user.email or "").split("@")[0]
    )
    return {
        "id": user.id,
        "email": user.email or extra.get("email", ""),
        "name": name,
        "avatar": extra.get("picture", ""),
        "consent_completed": profile.consent_completed,
        "can_save_progress": profile.can_save_progress(),
        "is_minor": profile.is_minor,
        "parental_consent_required": profile.parental_consent_required,
    }


class _SessionAuthedView(ContractAPIView):
    """Account views authenticate via the session cookie (CSRF-enforced on writes)."""

    authentication_classes = [SessionAuthentication]


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(_SessionAuthedView):
    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        base = {
            "accounts_enabled": True,
            "min_self_consent_age": settings.CAT_MIN_SELF_CONSENT_AGE,
        }
        if request.user and request.user.is_authenticated:
            return Response({**base, "authenticated": True, "user": _user_payload(request.user)})
        return Response({**base, "authenticated": False, "user": None})


class LogoutView(_SessionAuthedView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        django_logout(request)
        return Response({"ok": True})


class _ConsentBody(pydantic.BaseModel):
    birth_year: int = pydantic.Field(ge=1900, le=2100)
    accept_privacy: bool
    accept_tos: bool


class ConsentView(_SessionAuthedView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        body = parse_data(request, _ConsentBody)
        if not (body.accept_privacy and body.accept_tos):
            raise http_error(400, "Trebuie sa accepti politica de confidentialitate si termenii.")

        profile = _profile_for(request.user)
        profile.birth_year = body.birth_year
        age = timezone.now().year - body.birth_year
        version = settings.CAT_CONSENT_VERSION

        if age < settings.CAT_MIN_SELF_CONSENT_AGE:
            # Below the RO self-consent age: block self-service accounts. A verifiable
            # parental-consent flow is required before this account may save any data.
            profile.is_minor = True
            profile.parental_consent_required = True
            profile.consent_completed = False
            profile.consent_version = ""
            profile.save()
            return Response(
                {
                    "status": "parental_consent_required",
                    "min_self_consent_age": settings.CAT_MIN_SELF_CONSENT_AGE,
                    "user": _user_payload(request.user),
                },
                status=403,
            )

        profile.is_minor = False
        profile.parental_consent_required = False
        profile.consent_completed = True
        profile.consent_version = version
        profile.save()
        for doc in (ConsentRecord.PRIVACY, ConsentRecord.TOS):
            ConsentRecord.objects.create(user=request.user, document=doc, version=version)
        return Response({"status": "ok", "user": _user_payload(request.user)})


class _ScoreIn(pydantic.BaseModel):
    game: str = pydantic.Field(max_length=20)
    score: int
    detail: str = pydantic.Field(max_length=120)
    at: int
    puzzle_key: str = pydantic.Field(default="", max_length=160)
    daily: str = pydantic.Field(default="", max_length=10)
    difficulty: str = pydantic.Field(default="", max_length=20)
    category: str = pydantic.Field(default="", max_length=40)


class _ScoresSyncBody(pydantic.BaseModel):
    entries: list[_ScoreIn] = pydantic.Field(max_length=_SCORES_SYNC_CAP)


def _entry_payload(e: ScoreEntry) -> dict:
    out = {"game": e.game, "score": e.score, "detail": e.detail, "at": e.at}
    for key in ("puzzle_key", "daily", "difficulty", "category"):
        val = getattr(e, key)
        if val:
            out[key] = val
    return out


class ScoresView(_SessionAuthedView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        rows = ScoreEntry.objects.filter(user=request.user)[:_SCORES_READ_CAP]
        return Response({"entries": [_entry_payload(e) for e in rows]})

    def post(self, request) -> Response:
        profile = _profile_for(request.user)
        if not profile.can_save_progress():
            raise http_error(403, "Consent required before saving progress.")
        body = parse_data(request, _ScoresSyncBody)
        saved = 0
        for item in body.entries:
            _, created = ScoreEntry.objects.get_or_create(
                user=request.user,
                game=item.game,
                at=item.at,
                puzzle_key=item.puzzle_key,
                defaults={
                    "score": item.score,
                    "detail": item.detail,
                    "daily": item.daily,
                    "difficulty": item.difficulty,
                    "category": item.category,
                },
            )
            saved += int(created)
        total = ScoreEntry.objects.filter(user=request.user).count()
        return Response({"saved": saved, "total": total})


class DeleteAccountView(_SessionAuthedView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """GDPR erasure: delete the user; cascade removes profile, scores, consent,
        and the linked SocialAccount. The session is ended immediately after."""
        user = request.user
        django_logout(request)
        user.delete()
        return Response({"ok": True})
