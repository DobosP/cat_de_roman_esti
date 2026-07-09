"""Fixtures for the accounts suite.

This whole directory is collect-ignored unless ``CAT_ACCOUNTS_ENABLED=1`` — with the flag
off the ``cat_accounts`` app + allauth are not installed, so these modules cannot even
import their models. Run it with::

    CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 pytest -q tests/accounts
"""

from __future__ import annotations

import os

import pytest

collect_ignore_glob = ["test_*.py"] if os.environ.get("CAT_ACCOUNTS_ENABLED") != "1" else []


@pytest.fixture
def make_google_user(db):
    """Factory: a Django user linked to a Google SocialAccount (what allauth would create)."""
    from allauth.socialaccount.models import SocialAccount
    from django.contrib.auth import get_user_model

    User = get_user_model()
    counter = {"n": 0}

    def _make(email: str = "user@example.com", name: str = "Test User"):
        counter["n"] += 1
        uid = f"google-uid-{counter['n']}"
        user = User.objects.create(username=uid, email=email)
        SocialAccount.objects.create(
            user=user,
            provider="google",
            uid=uid,
            extra_data={"email": email, "name": name, "picture": "https://img/a.png"},
        )
        return user

    return _make


@pytest.fixture
def client():
    from django.test import Client

    return Client()


@pytest.fixture
def auth_client(client, make_google_user):
    user = make_google_user()
    client.force_login(user)
    client.cat_user = user  # type: ignore[attr-defined]
    return client


@pytest.fixture
def give_consent():
    """Returns a callable that completes the adult consent gate for a logged-in client."""

    def _give(client, birth_year: int = 1990):
        return client.post(
            "/api/me/consent",
            data={"birth_year": birth_year, "accept_privacy": True, "accept_tos": True},
            content_type="application/json",
        )

    return _give
