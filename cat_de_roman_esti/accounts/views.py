"""Account API — auth, private score-copy, repeat, and ranking surfaces.

Endpoints (all same-origin, session-cookie authenticated):

* ``GET  /api/me``          — current user + consent state (also seeds the CSRF cookie).
* ``POST /api/auth/logout`` — end the session.
* ``POST /api/me/consent``  — the age gate: birth year + privacy/ToS acceptance.
* ``GET  /api/me/scores``   — read the account's private completed-score copy.
* ``POST /api/me/scores``   — upload finished runs (idempotent, capped at 500).
* ``POST /api/me/delete``   — DSAR erasure: delete the account and all its data.

The word-game endpoints stay anonymous + CSRF-free; only these views opt into
``SessionAuthentication`` (which enforces CSRF for unsafe methods on logged-in users).
Login itself is handled by allauth at ``/accounts/google/login/``.
"""

from __future__ import annotations

from datetime import date

import pydantic
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..web.http import ContractAPIView, http_error, parse_data
from ..wordgames.categories import is_known
from .models import (
    VERIFIED_GAME_KEYS,
    ConsentRecord,
    Profile,
    ScoreEntry,
    VerifiedBest,
)

# Keep the private account copy bounded independently of the browser store.
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
    current_consent = profile.can_save_progress()
    return {
        "id": user.id,
        "email": user.email or extra.get("email", ""),
        # `name` = the account holder's name (for the chip); `ranking_name` = the public
        # handle shown on the leaderboard (a nickname, never the email).
        "name": profile.display_name or extra.get("name") or "",
        "avatar": extra.get("picture", ""),
        "ranking_name": profile.ranking_name(),
        "display_name": profile.display_name,
        # Stale policy acceptance reopens the consent gate and cannot leave a public
        # profile visible while account-linked persistence is disabled.
        "show_on_ranking": profile.show_on_ranking and current_consent,
        "consent_completed": current_consent,
        "can_save_progress": current_consent,
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
            "donate_url": getattr(settings, "CAT_DONATE_URL", ""),
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
    # Optional ranking handle chosen explicitly at sign-up; blank keeps rankings private.
    display_name: str = pydantic.Field(default="", max_length=80)


def _parental_consent_required(user) -> Response:
    return Response(
        {
            "status": "parental_consent_required",
            "min_self_consent_age": settings.CAT_MIN_SELF_CONSENT_AGE,
            "user": _user_payload(user),
        },
        status=403,
    )


class ConsentView(_SessionAuthedView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        body = parse_data(request, _ConsentBody)
        if not (body.accept_privacy and body.accept_tos):
            raise http_error(400, "Trebuie sa accepti politica de confidentialitate si termenii.")

        with transaction.atomic():
            profile = _profile_for(request.user)
            profile = Profile.objects.select_for_update().get(pk=profile.pk)

            # Once self-service has identified an underage player, only the future
            # verifiable parental flow may clear the hold. Recheck it under the same
            # lock as consent writes so a second request cannot replace the birth year.
            if profile.is_minor or profile.parental_consent_required:
                return _parental_consent_required(request.user)

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
                return _parental_consent_required(request.user)

            profile.is_minor = False
            profile.parental_consent_required = False
            profile.consent_completed = True
            profile.consent_version = version
            # A nickname is optional for private progress, but mandatory before public opt-in.
            # Never fill it from Google profile or email data.
            chosen = body.display_name.strip()
            if chosen:
                profile.display_name = " ".join(chosen.split())
            profile.save()
            for doc in (ConsentRecord.PRIVACY, ConsentRecord.TOS):
                ConsentRecord.objects.create(user=request.user, document=doc, version=version)
            return Response({"status": "ok", "user": _user_payload(request.user)})


class _ProfileBody(pydantic.BaseModel):
    display_name: str | None = pydantic.Field(default=None, max_length=80)
    show_on_ranking: bool | None = None


class ProfileView(_SessionAuthedView):
    """Update the ranking handle + visibility (POST /api/me/profile)."""

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        body = parse_data(request, _ProfileBody)
        with transaction.atomic():
            profile = _profile_for(request.user)
            profile = Profile.objects.select_for_update().get(pk=profile.pk)
            update_fields: list[str] = []

            if body.display_name is not None:
                handle = " ".join(body.display_name.split())
                if not handle:
                    raise http_error(400, "Numele din clasament nu poate fi gol.")
                profile.display_name = handle[:80]
                update_fields.append("display_name")
            if body.show_on_ranking is not None:
                if body.show_on_ranking and not profile.can_save_progress():
                    raise http_error(403, "Consimțământ valid necesar pentru clasament.")
                if body.show_on_ranking and not profile.display_name.strip():
                    raise http_error(400, "Alege o poreclă înainte să apari în clasament.")
                profile.show_on_ranking = body.show_on_ranking
                update_fields.append("show_on_ranking")

            if update_fields:
                profile.save(update_fields=[*update_fields, "updated"])
        return Response({"status": "ok", "user": _user_payload(request.user)})


class _ScoreIn(pydantic.BaseModel):
    game: str = pydantic.Field(max_length=20)
    score: int = pydantic.Field(strict=True, ge=0, le=1000)
    detail: str = pydantic.Field(min_length=1, max_length=120)
    # Fixed, database-safe browser timestamp envelope: 2000-01-01 through 2100-01-01.
    at: int = pydantic.Field(strict=True, ge=946_684_800_000, le=4_102_444_800_000)
    puzzle_key: str = pydantic.Field(default="", max_length=160)
    daily: str = pydantic.Field(default="", max_length=10)
    difficulty: str = pydantic.Field(default="", max_length=20)
    category: str = pydantic.Field(default="", max_length=40)

    @pydantic.field_validator("game")
    @classmethod
    def exact_game(cls, value: str) -> str:
        if value not in VERIFIED_GAME_KEYS:
            raise ValueError("unsupported game")
        return value

    @pydantic.field_validator("detail")
    @classmethod
    def clean_detail(cls, value: str) -> str:
        clean = " ".join(value.split())
        if not clean:
            raise ValueError("detail cannot be blank")
        return clean

    @pydantic.field_validator("puzzle_key")
    @classmethod
    def clean_puzzle_key(cls, value: str) -> str:
        clean = value.strip()
        if any(ord(char) < 32 or ord(char) == 127 for char in clean):
            raise ValueError("puzzle_key contains control characters")
        return clean

    @pydantic.field_validator("daily")
    @classmethod
    def valid_daily(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            return ""
        try:
            parsed = date.fromisoformat(clean)
        except ValueError:
            raise ValueError("daily must be a real YYYY-MM-DD date") from None
        if parsed.isoformat() != clean:
            raise ValueError("daily must use YYYY-MM-DD")
        return clean

    @pydantic.field_validator("difficulty")
    @classmethod
    def valid_difficulty(cls, value: str) -> str:
        clean = value.strip()
        if clean not in {"", "usor", "normal", "greu"}:
            raise ValueError("unsupported difficulty")
        return clean

    @pydantic.field_validator("category")
    @classmethod
    def valid_category(cls, value: str) -> str:
        clean = value.strip()
        if clean and not is_known(clean):
            raise ValueError("unsupported category")
        return clean


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
        profile = _profile_for(request.user)
        if not profile.can_save_progress():
            raise http_error(403, "Consent required before reading progress.")
        rows = ScoreEntry.objects.filter(user=request.user)[:_SCORES_READ_CAP]
        return Response({"entries": [_entry_payload(e) for e in rows]})

    def post(self, request) -> Response:
        body = parse_data(request, _ScoresSyncBody)
        with transaction.atomic():
            profile = Profile.objects.select_for_update().filter(user=request.user).first()
            if profile is None or not profile.can_save_progress():
                raise http_error(403, "Consent required before saving progress.")
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

            # Serialize by profile row, then retain the newest 500 arrivals. Client
            # timestamps affect personal display order but can never pin database rows.
            keep_ids = list(
                ScoreEntry.objects.filter(user=request.user)
                .order_by("-created", "-id")
                .values_list("id", flat=True)[:_SCORES_READ_CAP]
            )
            if keep_ids:
                ScoreEntry.objects.filter(user=request.user).exclude(id__in=keep_ids).delete()
            else:
                ScoreEntry.objects.filter(user=request.user).delete()
            total = len(keep_ids)
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


_RANKING_MAX = 200


class RankingView(_SessionAuthedView):
    """Public leaderboard — anyone can VIEW it; you only need an account to APPEAR on it.

    Shows one server-authored best per opted-in, currently consented player. Browser
    history never feeds this view. Equal scores share competition rank (1, 1, 3).
    """

    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        game = (request.query_params.get("game") or "").strip()
        if game not in VERIFIED_GAME_KEYS:
            raise http_error(400, "Alege unul dintre cele șase jocuri.")
        try:
            limit = int(request.query_params.get("limit") or 50)
        except ValueError:
            limit = 50
        limit = max(1, min(limit, _RANKING_MAX))

        eligible = (
            VerifiedBest.objects.filter(
                game=game,
                user__cat_profile__consent_completed=True,
                user__cat_profile__consent_version=settings.CAT_CONSENT_VERSION,
                user__cat_profile__parental_consent_required=False,
                user__cat_profile__show_on_ranking=True,
            )
            .exclude(user__cat_profile__display_name="")
            .select_related("user__cat_profile")
            .order_by("-score", "user_id")
        )
        top = list(eligible[:limit])
        requester_id = (
            request.user.id
            if getattr(request, "user", None) and request.user.is_authenticated
            else None
        )
        entries: list[dict] = []
        previous_score: int | None = None
        current_rank = 0
        for position, row in enumerate(top, start=1):
            if position == 1 or row.score != previous_score:
                current_rank = position
                previous_score = row.score
            entries.append(
                {
                    "rank": current_rank,
                    "name": row.user.cat_profile.ranking_name(),
                    "score": row.score,
                    "is_me": row.user_id == requester_id,
                }
            )

        me = None
        if requester_id is not None:
            own = eligible.filter(user_id=requester_id).first()
            if own is not None:
                me = {
                    "rank": 1 + eligible.filter(score__gt=own.score).count(),
                    "score": own.score,
                }
        return Response({"game": game, "entries": entries, "me": me})
