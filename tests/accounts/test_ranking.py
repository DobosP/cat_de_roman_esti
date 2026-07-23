"""Public ranking + profile handle (accounts ON)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import Client, override_settings

from cat_de_roman_esti.accounts.models import Profile, ScoreEntry, VerifiedBest
from cat_de_roman_esti.accounts.progress import record_verified_best

pytestmark = pytest.mark.django_db


def _post_score(client, game, score, at):
    return client.post(
        "/api/me/scores",
        data={
            "entries": [
                {
                    "game": game,
                    "score": score,
                    "detail": "x",
                    "at": 1_700_000_000_000 + at,
                }
            ]
        },
        content_type="application/json",
    )


def _set_handle(client, name, *, visible=True):
    return client.post(
        "/api/me/profile",
        data={"display_name": name, "show_on_ranking": visible},
        content_type="application/json",
    )


def test_ranking_is_public_and_ordered(auth_client, make_google_user, client, give_consent):
    give_consent(auth_client)
    _set_handle(auth_client, "Ana")
    record_verified_best(auth_client.cat_user, "contexto", 500)

    u2 = make_google_user(email="b@example.com", name="Bogdan")
    client.force_login(u2)
    give_consent(client)
    _set_handle(client, "Bogdan")
    record_verified_best(u2, "contexto", 900)

    # Anyone — even signed-out — can view the ranking.
    anon = Client()
    resp = anon.get("/api/ranking?game=contexto")
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert [e["name"] for e in entries] == ["Bogdan", "Ana"]  # 900 before 500
    assert entries[0]["score"] == 900 and entries[0]["rank"] == 1
    assert all(e["is_me"] is False for e in entries)
    # No PII on the public board.
    assert "email" not in entries[0] and "avatar" not in entries[0]


def test_ranking_me_shows_own_rank(auth_client, give_consent):
    give_consent(auth_client)
    _set_handle(auth_client, "Vlad")
    record_verified_best(auth_client.cat_user, "lant", 300)
    body = auth_client.get("/api/ranking?game=lant").json()
    assert body["me"] == {"rank": 1, "score": 300}
    assert body["entries"][0]["is_me"] is True


def test_hidden_player_excluded(auth_client, give_consent):
    give_consent(auth_client)
    _set_handle(auth_client, "Privat")
    record_verified_best(auth_client.cat_user, "contexto", 400)
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


def test_ranking_opt_in_requires_explicit_nickname(auth_client, give_consent):
    give_consent(auth_client)  # no display_name provided
    me = auth_client.get("/api/me").json()["user"]
    assert me["ranking_name"] == "Jucător"
    assert me["display_name"] == ""
    profile = Profile.objects.get(user=auth_client.cat_user)
    assert profile.show_on_ranking is False

    refused = auth_client.post(
        "/api/me/profile",
        data={"show_on_ranking": True},
        content_type="application/json",
    )
    assert refused.status_code == 400

    accepted = _set_handle(auth_client, "Vulpea Isteață")
    assert accepted.status_code == 200
    assert accepted.json()["user"]["show_on_ranking"] is True


def test_client_history_never_feeds_public_ranking(auth_client, give_consent):
    give_consent(auth_client)
    _set_handle(auth_client, "Ana")
    response = _post_score(auth_client, "contexto", 1000, 1)
    assert response.status_code == 200
    assert ScoreEntry.objects.filter(user=auth_client.cat_user).count() == 1
    assert VerifiedBest.objects.filter(user=auth_client.cat_user).count() == 0
    assert auth_client.get("/api/ranking?game=contexto").json()["entries"] == []


def test_verified_best_locks_profile_and_never_downgrades(auth_client, give_consent):
    give_consent(auth_client)
    with patch.object(
        Profile.objects,
        "select_for_update",
        wraps=Profile.objects.select_for_update,
    ) as locked:
        record_verified_best(auth_client.cat_user, "contexto", 400)
        record_verified_best(auth_client.cat_user, "contexto", 900)
        record_verified_best(auth_client.cat_user, "contexto", 500)

    assert locked.call_count == 3
    rows = VerifiedBest.objects.filter(user=auth_client.cat_user, game="contexto")
    assert rows.count() == 1
    assert rows.get().score == 900


def test_equal_scores_share_competition_rank_and_me_is_bounded_outside_limit(
    auth_client,
    make_google_user,
    client,
    give_consent,
):
    give_consent(auth_client)
    _set_handle(auth_client, "Ana")
    record_verified_best(auth_client.cat_user, "contexto", 800)

    tied = make_google_user(email="tie@example.com", name="Ignored")
    client.force_login(tied)
    give_consent(client)
    _set_handle(client, "Bia")
    record_verified_best(tied, "contexto", 800)

    lower = make_google_user(email="low@example.com", name="Ignored")
    client.force_login(lower)
    give_consent(client)
    _set_handle(client, "Cora")
    record_verified_best(lower, "contexto", 500)

    tied_board = Client().get("/api/ranking?game=contexto").json()
    assert [row["rank"] for row in tied_board["entries"]] == [1, 1, 3]

    client.force_login(lower)
    limited = client.get("/api/ranking?game=contexto&limit=1").json()
    assert len(limited["entries"]) == 1
    assert limited["entries"][0]["is_me"] is False
    assert limited["me"] == {"rank": 3, "score": 500}


@pytest.mark.parametrize("query", ["", "?game=necunoscut"])
def test_ranking_requires_an_exact_game(client, query):
    assert client.get(f"/api/ranking{query}").status_code == 400


@override_settings(CAT_DONATE_URL="https://example.ro/doneaza")
def test_donate_url_surfaced(auth_client):
    assert auth_client.get("/api/me").json()["donate_url"] == "https://example.ro/doneaza"
