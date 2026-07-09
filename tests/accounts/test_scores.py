"""Server-side saved progress: consent gate, idempotent sync, per-user isolation."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db

_ENTRY = {
    "game": "contexto",
    "score": 1000,
    "detail": "3 incercari",
    "at": 1_700_000_000_000,
    "difficulty": "greu",
    "category": "muzica",
}


def _post(client, entries):
    return client.post("/api/me/scores", data={"entries": entries}, content_type="application/json")


def test_saving_requires_consent(auth_client):
    resp = _post(auth_client, [_ENTRY])
    assert resp.status_code == 403


def test_sync_is_idempotent(auth_client, give_consent):
    give_consent(auth_client)
    first = _post(auth_client, [_ENTRY])
    assert first.status_code == 200
    assert first.json() == {"saved": 1, "total": 1}
    # Re-uploading the same run is a no-op (unique on user+game+at+puzzle_key).
    second = _post(auth_client, [_ENTRY])
    assert second.json() == {"saved": 0, "total": 1}

    got = auth_client.get("/api/me/scores").json()["entries"]
    assert len(got) == 1
    assert got[0]["game"] == "contexto"
    assert got[0]["difficulty"] == "greu"
    assert got[0]["category"] == "muzica"


def test_scores_are_per_user(auth_client, make_google_user, client, give_consent):
    give_consent(auth_client)
    _post(auth_client, [_ENTRY])

    other = make_google_user(email="other@example.com", name="Other")
    client.force_login(other)
    give_consent(client)
    assert client.get("/api/me/scores").json()["entries"] == []


def test_delete_account_erases_everything(auth_client, give_consent):
    from django.contrib.auth import get_user_model

    from cat_de_roman_esti.accounts.models import ScoreEntry

    give_consent(auth_client)
    _post(auth_client, [_ENTRY])
    user_id = auth_client.cat_user.id

    resp = auth_client.post("/api/me/delete", content_type="application/json")
    assert resp.status_code == 200 and resp.json() == {"ok": True}
    assert get_user_model().objects.filter(id=user_id).count() == 0
    assert ScoreEntry.objects.filter(user_id=user_id).count() == 0
    # Session is gone too.
    assert auth_client.get("/api/me").json()["authenticated"] is False
