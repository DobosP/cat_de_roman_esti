"""Served legal pages (/legal/privacy, /legal/terms) — web/legal.py.

Covers the deploy-time CAT_LEGAL_OPERATOR / CAT_LEGAL_CONTACT_EMAIL knobs (web/settings.py):
unset keeps the DRAFT placeholder + "not finalized" wording; set replaces the placeholder
with a mailto link and the operator identity, and drops the "not finalized" sentence while
keeping the draft/lawyer-review wording. Always mounted (both accounts modes).
"""

from __future__ import annotations

import pytest

pytest.importorskip("django")

from django.test import Client, override_settings  # noqa: E402

UNFINALIZED_SENTENCE = "Operatorul și datele de contact nu sunt încă finalizate."
DRAFT_SENTENCE = "trebuie completat și verificat de un avocat specializat"


@pytest.fixture
def client() -> Client:
    return Client()


def test_privacy_default_shows_placeholder_and_unfinalized_banner(client: Client):
    resp = client.get("/legal/privacy")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "[[PLACEHOLDER: contact]]" in body
    assert UNFINALIZED_SENTENCE in body
    assert DRAFT_SENTENCE in body


def test_terms_default_shows_unfinalized_banner(client: Client):
    resp = client.get("/legal/terms")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert UNFINALIZED_SENTENCE in body
    assert DRAFT_SENTENCE in body


@override_settings(
    CAT_LEGAL_OPERATOR="Asociația Test",
    CAT_LEGAL_CONTACT_EMAIL="privacy@example.ro",
)
def test_privacy_with_operator_and_contact_configured(client: Client):
    resp = client.get("/legal/privacy")
    body = resp.content.decode()
    assert '<a href="mailto:privacy@example.ro">privacy@example.ro</a>' in body
    assert "Asociația Test" in body
    assert "[[PLACEHOLDER: contact]]" not in body
    assert UNFINALIZED_SENTENCE not in body
    # The draft / lawyer-review wording is unconditional — it remains true regardless.
    assert DRAFT_SENTENCE in body


@override_settings(
    CAT_LEGAL_OPERATOR="Asociația Test",
    CAT_LEGAL_CONTACT_EMAIL="privacy@example.ro",
)
def test_terms_with_operator_and_contact_configured(client: Client):
    resp = client.get("/legal/terms")
    body = resp.content.decode()
    assert UNFINALIZED_SENTENCE not in body
    assert DRAFT_SENTENCE in body


@override_settings(CAT_LEGAL_OPERATOR="Asociația Test")
def test_partial_config_keeps_unfinalized_banner(client: Client):
    # Only one of the two env vars set — the "not finalized" sentence must still hold.
    resp = client.get("/legal/privacy")
    body = resp.content.decode()
    assert UNFINALIZED_SENTENCE in body


@override_settings(
    CAT_LEGAL_OPERATOR="<script>alert(1)</script>",
    CAT_LEGAL_CONTACT_EMAIL='"><img src=x onerror=alert(1)>@example.ro',
)
def test_operator_and_contact_are_html_escaped(client: Client):
    resp = client.get("/legal/privacy")
    body = resp.content.decode()
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body
    assert "<img src=x onerror=alert(1)>" not in body
    assert "&lt;img" in body
