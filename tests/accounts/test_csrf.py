"""CSRF is enforced on authenticated writes (DRF SessionAuthentication)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_write_without_csrf_is_rejected(make_google_user):
    from django.test import Client

    user = make_google_user()
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(user)
    resp = strict.post(
        "/api/me/consent",
        data={"birth_year": 1990, "accept_privacy": True, "accept_tos": True},
        content_type="application/json",
    )
    assert resp.status_code == 403


def test_write_with_csrf_succeeds(make_google_user):
    from django.test import Client

    user = make_google_user()
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(user)
    # Seed + read the CSRF cookie the way the SPA does, then echo it as X-CSRFToken.
    strict.get("/api/me")
    token = strict.cookies["csrftoken"].value
    resp = strict.post(
        "/api/me/consent",
        data={"birth_year": 1990, "accept_privacy": True, "accept_tos": True},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
