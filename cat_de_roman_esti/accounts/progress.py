"""Avoid-repeats storage helpers (accounts ON only)."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import VERIFIED_GAME_KEYS, PlayedPuzzle, Profile, VerifiedBest


def _can_persist(user) -> bool:
    """Whether this user currently has valid consent for account-linked progress."""
    profile = Profile.objects.filter(user=user).first()
    return bool(profile and profile.can_save_progress())


def finished_pack_ids(user, game: str) -> set[str]:
    """The curated instance ids this player has already finished for ``game``."""
    if not _can_persist(user):
        return set()
    return set(
        PlayedPuzzle.objects.filter(user=user, game=game).values_list("pack_id", flat=True)
    )


def record_played(user, game: str, pack_id: str) -> None:
    """Mark a curated instance as finished (idempotent)."""
    if not _can_persist(user):
        return
    PlayedPuzzle.objects.get_or_create(user=user, game=game, pack_id=pack_id)


def record_verified_best(user, game: str, score: int) -> None:
    """Retain only the user's best server-authored score for an exact public game."""
    if game not in VERIFIED_GAME_KEYS:
        raise ValueError(f"unsupported verified game: {game}")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 1000:
        raise ValueError("verified score must be an integer from 0 to 1000")
    with transaction.atomic():
        # Serialize every terminal session for this player. Two different in-memory game
        # sessions can finish concurrently, so locking only a possibly absent best row
        # would not protect the create path. Re-check consent while holding the same lock.
        profile = Profile.objects.select_for_update().filter(user=user).first()
        if profile is None or not profile.can_save_progress():
            return
        row, _ = VerifiedBest.objects.get_or_create(
            user=user,
            game=game,
            defaults={"score": score},
        )
        if score > row.score:
            VerifiedBest.objects.filter(pk=row.pk, score__lt=score).update(
                score=score,
                updated=timezone.now(),
            )
