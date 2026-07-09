"""Account data models — deliberately minimal (data minimisation, GDPR Art. 5).

We store only what the product needs:

* :class:`Profile` — the age gate + consent state bound to the Django user that allauth
  creates from the Google login. No date of birth is kept, only the birth *year* used to
  apply Romania's age-16 self-consent rule.
* :class:`ConsentRecord` — an immutable audit trail of privacy/ToS acceptance (ROPA input).
* :class:`ScoreEntry` — server-side saved game progress (the account-backed twin of the
  browser localStorage store in ``frontend/src/scores.ts``).

The Google account itself (subject id, email, name, avatar) lives in allauth's
``SocialAccount``; we do not duplicate it here, and OAuth tokens are never stored
(``SOCIALACCOUNT_STORE_TOKENS = False``).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


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
    # Public handle shown on the ranking (a chosen nickname, NOT the real Google name;
    # defaulted from the Google given name at consent but freely editable).
    display_name = models.CharField(max_length=80, blank=True)
    # Whether this player appears on the public ranking. The whole point of an account is
    # to be on the ranking, so it defaults on; users can opt out (privacy) at any time.
    show_on_ranking = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def can_save_progress(self) -> bool:
        """Progress persistence is gated on a completed adult/self consent."""
        return self.consent_completed and not self.parental_consent_required

    def ranking_name(self) -> str:
        """The label to show on the public ranking (never the email)."""
        return (self.display_name or "").strip() or f"Jucător {self.user_id}"

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
    """One finished game result saved to the account (mirrors the localStorage ScoreEntry)."""

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
