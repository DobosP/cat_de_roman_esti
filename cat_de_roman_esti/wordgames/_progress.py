"""Avoid-repeats glue between the always-loaded word-game views and the OPTIONAL accounts app.

Every function is a no-op when accounts are disabled or the request is anonymous, so the
stateless deployment and anonymous play are byte-unchanged. The game views authenticate with
``web.http.OptionalSessionAuth`` (session cookie, no CSRF) so ``request.user`` is set for a
signed-in player and absent otherwise.
"""

from __future__ import annotations

from django.conf import settings


def _user(request):
    user = getattr(request, "user", None)
    if user is None:  # fall back to the underlying Django request
        user = getattr(getattr(request, "_request", None), "user", None)
    return user if (user is not None and getattr(user, "is_authenticated", False)) else None


def excluded_pack_ids(request, game: str) -> set[str]:
    """Curated ids the signed-in player has finished (empty for anonymous / accounts off)."""
    if not getattr(settings, "ACCOUNTS_ENABLED", False):
        return set()
    user = _user(request)
    if user is None:
        return set()
    from ..accounts.progress import finished_pack_ids

    return finished_pack_ids(user, game)


def record_finished(request, game: str, pack_id, *, score: int | None = None) -> None:
    """Persist consented repeat avoidance and an optional server-authored best score."""
    if not getattr(settings, "ACCOUNTS_ENABLED", False):
        return
    user = _user(request)
    if user is None:
        return
    from ..accounts.progress import record_played, record_verified_best

    if pack_id:
        record_played(user, game, str(pack_id))
    if score is not None:
        record_verified_best(user, game, score)
