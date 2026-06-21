"""Smoke tests for the word-game arcade BFF (offline, server-authoritative).

Per-game behaviour is covered by tests/test_wordgames_*.py; this asserts the app factory
mounts all three game routers + the health surface + the static fallback.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from cat_de_roman_esti.web import app as app_module  # noqa: E402
from cat_de_roman_esti.web import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_lists_the_three_games(client: TestClient):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["source"] == "offline"
    assert body["concepts"] > 100
    keys = {g["key"] for g in body["games"]}
    assert keys == {"alchimie", "contexto", "lant"}


@pytest.mark.parametrize("game", ["alchimie", "contexto", "lant"])
def test_each_game_router_is_mounted(client: TestClient, game: str):
    # A new game can be created through the mounted router (deterministic via seed).
    resp = client.post(f"/api/wordgames/{game}/games?seed=1")
    assert resp.status_code in (200, 201)
    assert resp.json().get("game_id")


def test_placeholder_served_when_no_static_build(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "STATIC_DIR", tmp_path / "empty_static")
    with TestClient(create_app()) as c:
        resp = c.get("/")
        assert resp.status_code == 200
        assert "npm run build" in resp.text


def test_built_spa_served_when_present():
    if not (app_module.STATIC_DIR / "index.html").exists():
        pytest.skip("no SPA build present (run: cd frontend && npm run build)")
    with TestClient(create_app()) as c:
        resp = c.get("/")
        assert resp.status_code == 200
        assert 'id="root"' in resp.text
