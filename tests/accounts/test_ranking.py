"""Public ranking + profile handle (accounts ON)."""

from __future__ import annotations

import pytest
from django.test import Client, override_settings

pytestmark = pytest.mark.django_db


def _post_score(client, game, score, at):
    return client.post(
        "/api/me/scores",
        data={"entries": [{"game": game, "score": score, "detail": "x", "at": at}]},
        content_type="application/json",
    )


def _set_handle(client, name):
    return client.post(
        "/api/me/profile", data={"display_name": name}, content_type="application/json"
    )


def test_ranking_is_public_and_ordered(auth_client, make_google_user, client, give_consent):
    give_consent(auth_client)
    _set_handle(auth_client, "Ana")
    _post_score(auth_client, "contexto", 500, 1)

    u2 = make_google_user(email="b@example.com", name="Bogdan")
    client.force_login(u2)
    give_consent(client)
    _set_handle(client, "Bogdan")
    _post_score(client, "contexto", 900, 2)

    # Anyone — even signed-out — can view the ranking.
    anon = Client()
    resp = anon.get("/api/ranking?game=contexto")
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert [e["name"] for e in entries] == ["Bogdan", "Ana"]  # 900 before 500
    assert entries[0]["score"] == 900 and entries[0]["rank"] == 1
    # No PII on the public board.
    assert "email" not in entries[0] and "avatar" not in entries[0]


def test_ranking_me_shows_own_rank(auth_client, give_consent):
    give_consent(auth_client)
    _set_handle(auth_client, "Vlad")
    _post_score(auth_client, "lant", 300, 1)
    body = auth_client.get("/api/ranking?game=lant").json()
    assert body["me"] == {"rank": 1, "score": 300}


def test_hidden_player_excluded(auth_client, give_consent):
    give_consent(auth_client)
    _post_score(auth_client, "contexto", 400, 1)
    auth_client.post(
        "/api/me/profile", data={"show_on_ranking": False}, content_type="application/json"
    )
    assert Client().get("/api/ranking?game=contexto").json()["entries"] == []


def test_profile_update_and_validation(auth_client, give_consent):
    give_consent(auth_client)
    ok = auth_client.post(
        "/api/me/profile", data={"display_name": "  Vlad  "}, content_type="application/json"
    )
    assert ok.status_code == 200 and ok.json()["user"]["ranking_name"] == "Vlad"
    bad = auth_client.post(
        "/api/me/profile", data={"display_name": "   "}, content_type="application/json"
    )
    assert bad.status_code == 400


def test_consent_defaults_handle_from_google(auth_client, give_consent):
    give_consent(auth_client)  # no display_name provided
    assert auth_client.get("/api/me").json()["user"]["ranking_name"] == "Test User"


@override_settings(CAT_DONATE_URL="https://example.ro/doneaza")
def test_donate_url_surfaced(auth_client):
    assert auth_client.get("/api/me").json()["donate_url"] == "https://example.ro/doneaza"
