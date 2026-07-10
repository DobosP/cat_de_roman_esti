"""Avoid-repeats storage helpers (accounts ON only)."""

from __future__ import annotations

from .models import PlayedPuzzle


def finished_pack_ids(user, game: str) -> set[str]:
    """The curated instance ids this player has already finished for ``game``."""
    return set(
        PlayedPuzzle.objects.filter(user=user, game=game).values_list("pack_id", flat=True)
    )


def record_played(user, game: str, pack_id: str) -> None:
    """Mark a curated instance as finished (idempotent)."""
    PlayedPuzzle.objects.get_or_create(user=user, game=game, pack_id=pack_id)
