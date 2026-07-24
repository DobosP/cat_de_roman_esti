"""Private completed-score copy: consent, idempotency, cap, and per-user isolation."""

from __future__ import annotations

import pytest
from django.test import override_settings

pytestmark = pytest.mark.django_db


@override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=64)
def test_account_json_body_uses_the_global_size_ceiling(auth_client):
    response = auth_client.post(
        "/api/me/scores",
        data={"entries": [{"game": "contexto", "detail": "x" * 100}]},
        content_type="application/json",
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}


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
    assert auth_client.get("/api/me/scores").status_code == 403


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


@pytest.mark.parametrize(
    ("patch", "field"),
    [
        ({"game": "necunoscut"}, "game"),
        ({"score": -1}, "score"),
        ({"score": 1001}, "score"),
        ({"score": True}, "score"),
        ({"at": 1}, "at"),
        ({"daily": "2026-02-30"}, "daily"),
        ({"difficulty": "imposibil"}, "difficulty"),
        ({"category": "nu_exista"}, "category"),
        ({"puzzle_key": "abc\nsecret"}, "puzzle_key"),
    ],
)
def test_sync_rejects_unbounded_or_unknown_metadata(
    auth_client,
    give_consent,
    patch,
    field,
):
    give_consent(auth_client)
    response = _post(auth_client, [{**_ENTRY, **patch}])
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field


def test_history_is_transactionally_pruned_to_500_per_user(auth_client, give_consent):
    from cat_de_roman_esti.accounts.models import ScoreEntry

    give_consent(auth_client)
    for batch in range(5):
        entries = [
            {
                **_ENTRY,
                "at": _ENTRY["at"] + index,
                "puzzle_key": f"p-{index}",
            }
            for index in range(batch * 100, (batch + 1) * 100)
        ]
        response = _post(auth_client, entries)
        assert response.status_code == 200
        assert response.json() == {"saved": 100, "total": (batch + 1) * 100}

    newest = {
        **_ENTRY,
        "at": _ENTRY["at"] + 500,
        "puzzle_key": "p-500",
    }
    second = _post(auth_client, [newest])
    assert second.status_code == 200
    assert second.json() == {"saved": 1, "total": 500}
    rows = ScoreEntry.objects.filter(user=auth_client.cat_user)
    assert rows.count() == 500
    assert rows.filter(puzzle_key="p-500").exists()


@override_settings(CAT_CONSENT_VERSION="new-policy")
def test_stale_consent_blocks_progress_read_and_write(auth_client):
    from cat_de_roman_esti.accounts.models import Profile

    Profile.objects.create(
        user=auth_client.cat_user,
        birth_year=1990,
        consent_completed=True,
        consent_version="old-policy",
    )
    assert auth_client.get("/api/me/scores").status_code == 403
    assert _post(auth_client, [_ENTRY]).status_code == 403


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
