"""Consent + Romania age-16 gate (accounts ON)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import override_settings
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


def test_parental_hold_cannot_be_cleared_by_adult_year_resubmission(
    auth_client,
    give_consent,
):
    minor_year = timezone.now().year - 10
    with patch.object(
        Profile.objects,
        "select_for_update",
        wraps=Profile.objects.select_for_update,
    ) as locked:
        first = give_consent(auth_client, birth_year=minor_year)
        second = auth_client.post(
            "/api/me/consent",
            data={
                "birth_year": 1990,
                "accept_privacy": True,
                "accept_tos": True,
                "display_name": "Adult",
            },
            content_type="application/json",
        )

    assert first.status_code == 403
    assert second.status_code == 403
    assert second.json()["status"] == "parental_consent_required"
    assert locked.call_count == 2

    profile = Profile.objects.get(user=auth_client.cat_user)
    assert profile.birth_year == minor_year
    assert profile.is_minor is True
    assert profile.parental_consent_required is True
    assert profile.consent_completed is False
    assert profile.consent_version == ""
    assert profile.display_name == ""
    assert ConsentRecord.objects.filter(user=auth_client.cat_user).count() == 0

    me = auth_client.get("/api/me").json()["user"]
    assert me["parental_consent_required"] is True
    assert me["consent_completed"] is False
    assert me["can_save_progress"] is False
    assert me["show_on_ranking"] is False

    score = {
        "game": "contexto",
        "score": 500,
        "detail": "3 încercări",
        "at": 1_700_000_000_000,
    }
    assert auth_client.get("/api/me/scores").status_code == 403
    assert (
        auth_client.post(
            "/api/me/scores",
            data={"entries": [score]},
            content_type="application/json",
        ).status_code
        == 403
    )
    with patch.object(
        Profile.objects,
        "select_for_update",
        wraps=Profile.objects.select_for_update,
    ) as profile_locked:
        ranking_response = auth_client.post(
            "/api/me/profile",
            data={"display_name": "Adult", "show_on_ranking": True},
            content_type="application/json",
        )
    assert ranking_response.status_code == 403
    assert profile_locked.call_count == 1

    profile.refresh_from_db()
    assert profile.birth_year == minor_year
    assert profile.is_minor is True
    assert profile.parental_consent_required is True
    assert profile.consent_completed is False
    assert profile.consent_version == ""
    assert profile.display_name == ""
    assert profile.show_on_ranking is False


@override_settings(CAT_CONSENT_VERSION="renewed-policy")
def test_stale_consent_reopens_gate_and_hides_public_visibility(auth_client):
    profile = Profile.objects.create(
        user=auth_client.cat_user,
        birth_year=1990,
        consent_completed=True,
        consent_version="old-policy",
        display_name="Poreclă",
        show_on_ranking=True,
    )
    assert profile.can_save_progress() is False

    user = auth_client.get("/api/me").json()["user"]
    assert user["consent_completed"] is False
    assert user["can_save_progress"] is False
    assert user["show_on_ranking"] is False
