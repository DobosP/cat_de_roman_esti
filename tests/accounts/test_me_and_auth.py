"""/api/me identity + session lifecycle (accounts ON)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_me_anonymous(client):
    resp = client.get("/api/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["accounts_enabled"] is True
    assert body["authenticated"] is False
    assert body["user"] is None
    assert body["min_self_consent_age"] == 16
    # /api/me seeds the CSRF cookie the SPA echoes on writes.
    assert "csrftoken" in resp.cookies


def test_me_authenticated(auth_client):
    body = auth_client.get("/api/me").json()
    assert body["authenticated"] is True
    user = body["user"]
    assert user["email"] == "user@example.com"
    assert user["name"] == "Test User"
    assert user["avatar"] == "https://img/a.png"
    assert user["consent_completed"] is False
    assert user["can_save_progress"] is False


def test_logout_ends_session(auth_client):
    assert auth_client.get("/api/me").json()["authenticated"] is True
    out = auth_client.post("/api/auth/logout", content_type="application/json")
    assert out.status_code == 200 and out.json() == {"ok": True}
    assert auth_client.get("/api/me").json()["authenticated"] is False


def test_logout_requires_auth(client):
    assert client.post("/api/auth/logout", content_type="application/json").status_code == 403
