"""Accounts-OFF mode (the default stateless deployment): /api/me self-describes as disabled.

Runs in the default suite (CAT_ACCOUNTS_ENABLED unset), so the SPA can hide the login UI.
"""

from __future__ import annotations

from django.test import Client


def test_me_reports_accounts_disabled():
    body = Client().get("/api/me").json()
    assert body == {"accounts_enabled": False, "authenticated": False, "user": None}
