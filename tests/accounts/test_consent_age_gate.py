"""Consent + Romania age-16 gate (accounts ON)."""

from __future__ import annotations

import pytest
from django.utils import timezone

from cat_de_roman_esti.accounts.models import ConsentRecord, Profile

pytestmark = pytest.mark.django_db


def test_adult_consent_unlocks_saving(auth_client, give_consent):
    resp = give_consent(auth_client, birth_year=1990)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["user"]["consent_completed"] is True
    assert body["user"]["can_save_progress"] is True

    profile = Profile.objects.get(user=auth_client.cat_user)
    assert profile.consent_completed and not profile.parental_consent_required
    # One immutable record per document (privacy + tos).
    records = ConsentRecord.objects.filter(user=auth_client.cat_user)
    assert set(records.values_list("document", flat=True)) == {"privacy", "tos"}


def test_consent_requires_both_acceptances(auth_client):
    resp = auth_client.post(
        "/api/me/consent",
        data={"birth_year": 1990, "accept_privacy": True, "accept_tos": False},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_minor_is_blocked_pending_parental_consent(auth_client, give_consent):
    minor_year = timezone.now().year - 10  # age ~10, below RO 16
    resp = give_consent(auth_client, birth_year=minor_year)
    assert resp.status_code == 403
    assert resp.json()["status"] == "parental_consent_required"

    profile = Profile.objects.get(user=auth_client.cat_user)
    assert profile.is_minor is True
    assert profile.parental_consent_required is True
    assert profile.consent_completed is False
    assert profile.can_save_progress() is False
    # No consent record is written for a blocked minor.
    assert ConsentRecord.objects.filter(user=auth_client.cat_user).count() == 0
