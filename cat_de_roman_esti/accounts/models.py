"""Account data models — deliberately minimal (data minimisation, GDPR Art. 5).

We store only what the product needs:

* :class:`Profile` — the age gate + consent state bound to the Django user that allauth
  creates from the Google login. No date of birth is kept, only the birth *year* used to
  apply Romania's age-16 self-consent rule.
* :class:`ConsentRecord` — an immutable audit trail of privacy/ToS acceptance (ROPA input).
* :class:`ScoreEntry` — an upload-only private copy of completed-score rows. The browser
  localStorage document in ``frontend/src/scores.ts`` remains the source of truth.

The Google account itself (subject id, email, name, avatar) lives in allauth's
``SocialAccount``; we do not duplicate it here, and OAuth tokens are never stored
(``SOCIALACCOUNT_STORE_TOKENS = False``).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

VERIFIED_GAME_KEYS = (
    "alchimie",
    "intrusul",
    "perechi",
    "conexiuni",
    "contexto",
    "lant",
)


class Profile(models.Model):
    """Per-user age-gate + consent state. Created lazily on first authenticated request."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cat_profile"
    )
    # Birth YEAR only (not full DOB) — enough to apply the age-16 rule, minimal PII.
    birth_year = models.PositiveIntegerField(null=True, blank=True)
    consent_completed = models.BooleanField(default=False)
    consent_version = models.CharField(max_length=32, blank=True)
    # True when the user declared an age below the self-consent threshold at consent time.
    is_minor = models.BooleanField(default=False)
    # Under-threshold accounts cannot save progress until a verifiable parental-consent
    # flow is completed (not yet implemented; see docs/compliance/consent-and-age-gate-spec).
    parental_consent_required = models.BooleanField(default=False)
    # Explicitly chosen public handle; never derive or default it from Google identity.
    display_name = models.CharField(max_length=80, blank=True)
    # Public visibility is an explicit opt-in, separate from the private score copy.
    show_on_ranking = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def can_save_progress(self) -> bool:
        """Account-linked score, repeat, and verified-record writes require current consent."""
        return (
            self.consent_completed
            and not self.parental_consent_required
            and self.consent_version == settings.CAT_CONSENT_VERSION
        )

    def ranking_name(self) -> str:
        """The chosen public label; never derive it from Google identity data."""
        return (self.display_name or "").strip() or "Jucător"

    def __str__(self) -> str:  # pragma: no cover - admin/repr convenience
        return f"Profile<{self.user_id}>"


class ConsentRecord(models.Model):
    """Immutable record of a user accepting a policy document (audit / ROPA evidence)."""

    PRIVACY = "privacy"
    TOS = "tos"
    DOCUMENT_CHOICES = [(PRIVACY, "Privacy notice"), (TOS, "Terms of service")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cat_consents"
    )
    document = models.CharField(max_length=16, choices=DOCUMENT_CHOICES)
    version = models.CharField(max_length=32)
    text_hash = models.CharField(max_length=64, blank=True)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "document"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"Consent<{self.user_id}:{self.document}@{self.version}>"


class ScoreEntry(models.Model):
    """One uploaded completed-score row; never an automatic localStorage restore source."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cat_scores"
    )
    game = models.CharField(max_length=20)
    score = models.IntegerField()
    detail = models.CharField(max_length=120)
    # Client ms-epoch of the run (kept for parity + ordering with the browser store).
    at = models.BigIntegerField()
    puzzle_key = models.CharField(max_length=160, blank=True)
    daily = models.CharField(max_length=10, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=40, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-at"]
        indexes = [models.Index(fields=["user", "game", "-at"])]
        # Idempotent sync: re-uploading the same run does not duplicate it.
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game", "at", "puzzle_key"], name="uniq_user_run"
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Score<{self.user_id}:{self.game}:{self.score}>"


class VerifiedBest(models.Model):
    """One server-authored public-ranking record per player and game.

    The exact game allowlist plus the user/game uniqueness constraint bound this table
    to at most six rows per user. It deliberately stores no board id, answer, action
    trail, client timestamp, difficulty, category, or private board-ranking metadata.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cat_verified_bests",
    )
    game = models.CharField(max_length=20)
    score = models.PositiveSmallIntegerField()
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game"],
                name="uniq_user_verified_game",
            ),
            models.CheckConstraint(
                condition=models.Q(game__in=VERIFIED_GAME_KEYS),
                name="verified_game_allowlist",
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=0, score__lte=1000),
                name="verified_score_bounds",
            ),
        ]
        indexes = [models.Index(fields=["game", "-score"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"VerifiedBest<{self.user_id}:{self.game}:{self.score}>"


class PlayedPuzzle(models.Model):
    """A curated puzzle a signed-in player has FINISHED (won or gave up).

    Powers "don't serve me the same game again": the create endpoints exclude a player's
    finished ``pack_id``s. Only curated instances (which have a stable opaque id) are tracked
    — mined/random boards draw from a huge pool, so repeats there are already rare, and their
    identity can encode the hidden answer, so we never persist it. Never stores the solution.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cat_played"
    )
    game = models.CharField(max_length=20)
    pack_id = models.CharField(max_length=64)
    finished_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "game"])]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game", "pack_id"], name="uniq_user_played"
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Played<{self.user_id}:{self.game}:{self.pack_id}>"
