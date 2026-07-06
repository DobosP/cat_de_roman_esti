"""Smoke tests for the word-game arcade BFF (offline, server-authoritative, Django).

Per-game behaviour is covered by tests/test_wordgames_*.py; this asserts the URLconf
mounts all game views + the health surface + the SPA serving paths.
"""

from __future__ import annotations

import pytest

pytest.importorskip("django")

from django.test import Client, RequestFactory  # noqa: E402

from cat_de_roman_esti.web import spa  # noqa: E402


@pytest.fixture
def client() -> Client:
    return Client()


def test_health_lists_the_games(client: Client):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["source"] == "offline"
    assert body["concepts"] > 100
    keys = {g["key"] for g in body["games"]}
    assert keys == {"alchimie", "contexto", "lant", "conexiuni"}


@pytest.mark.parametrize("game", ["alchimie", "contexto", "lant", "conexiuni"])
def test_each_game_router_is_mounted(client: Client, game: str):
    # A new game can be created through the mounted views (deterministic via seed).
    resp = client.post(f"/api/wordgames/{game}/games?seed=1")
    assert resp.status_code in (200, 201)
    assert resp.json().get("game_id")


def test_unknown_api_path_stays_json_404(client: Client):
    resp = client.get("/api/nope")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}


def test_unsupported_method_is_starlette_parity_405(client: Client):
    # POST-only endpoint: GET and bare OPTIONS both 405 with the fixed detail string
    # (FastAPI/starlette behavior a generated client may rely on; DRF's default would
    # 200 the OPTIONS and interpolate the method name into the detail).
    for do in (client.get, client.options):
        resp = do("/api/wordgames/alchimie/games")
        assert resp.status_code == 405
        assert resp.json() == {"detail": "Method Not Allowed"}


def test_placeholder_served_when_no_static_build(monkeypatch, tmp_path):
    # The catch-all view owns the no-build path (WhiteNoise caches its file list at
    # startup, so this is asserted at the view level).
    monkeypatch.setattr(spa, "STATIC_DIR", tmp_path / "empty_static")
    rf = RequestFactory()
    resp = spa.spa_index(rf.get("/"))
    assert resp.status_code == 200
    assert "npm run build" in resp.content.decode()
    # Deep links without a build are a JSON 404, not the placeholder.
    resp = spa.spa_index(rf.get("/alchimie"))
    assert resp.status_code == 404


def _page_text(resp) -> str:
    # WhiteNoise serves files as streaming responses; view responses are buffered.
    if getattr(resp, "streaming", False):
        return b"".join(resp.streaming_content).decode()
    return resp.content.decode()


def test_built_spa_served_when_present(client: Client):
    if not (spa.STATIC_DIR / "index.html").exists():
        pytest.skip("no SPA build present (run: cd frontend && npm run build)")
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="root"' in _page_text(resp)
    # Deep links serve the SPA shell so the React router can take over.
    resp = client.get("/conexiuni")
    assert resp.status_code == 200
    assert 'id="root"' in _page_text(resp)
