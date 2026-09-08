"""Earned Lanț help survives response loss without spending another request."""

from __future__ import annotations

import json

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import lant
from cat_de_roman_esti.wordgames.service import WordGameService


@pytest.fixture
def game(monkeypatch):
    nodes = [
        {"id": node, "label_ro": node.upper(), "category": "test"}
        for node in ("start", "mid", "other", "target", "dead")
    ]
    edges = [
        {"id": f"e_{i}", "src_id": source, "dst_id": target}
        for i, (source, target) in enumerate([
            ("start", "mid"), ("start", "other"), ("mid", "target"),
            ("other", "target"), ("mid", "start"), ("mid", "dead"),
        ])
    ]
    service = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(lant, "get_service", lambda: service)
    session = lant.LantSession(start="start", target="target", optimal=2, chain=["start"])
    game_id = lant.store.create(session)
    return Client(), f"/api/wordgames/lant/games/{game_id}", session


def move(client, url, text):
    return client.post(f"{url}/move", {"text": text}, content_type="application/json").json()


def test_unearned_get_never_computes_help_or_exposes_private_route(game, monkeypatch):
    client, url, session = game
    # Choice generation is independently allowed; producing earned help is not.
    monkeypatch.setattr(lant, "_earned_hint_response", lambda *_: pytest.fail("GET earned help"))
    for _ in range(3):
        state = client.get(url).json()
        assert "earned_hint" not in state
        assert not {"hint_requests", "remaining", "shortest", "corridor"} & state.keys()
    assert session.hint_requests == 0
    assert session.earned_hint is None


@pytest.mark.parametrize("stage,asks", [("direction", 1), ("alternatives", 2), ("hop", 3)])
def test_get_repeats_exact_earned_stage_without_escalating(game, stage, asks):
    client, url, session = game
    for _ in range(asks):
        earned = client.post(f"{url}/hint").json()
    assert earned["stage"] == stage
    for _ in range(4):
        state = client.get(url).json()
        assert state["earned_hint"] == earned
        assert session.hint_requests == asks
        assert "hint_requests" not in state
    if stage == "direction":
        assert earned["hint"] is None
        assert "alternatives_labels" not in earned
    if stage == "alternatives":
        assert earned["hint"] is None
        assert len(earned["alternatives_choices"]) <= 2
    # Changing a decoded response cannot alter the retained server payload.
    state["earned_hint"]["message"] = "client supplied"
    assert client.get(url).json()["earned_hint"] == earned


def test_invalid_move_and_noop_undo_preserve_earned_hint(game):
    client, url, session = game
    earned = client.post(f"{url}/hint").json()
    assert move(client, url, "TARGET")["ok"] is False
    assert move(client, url, "START")["ok"] is False
    assert client.get(url).json()["earned_hint"] == earned
    assert client.post(f"{url}/undo").json()["earned_hint"] == earned
    assert session.hint_requests == 1


def test_move_and_real_undo_clear_position_help_without_resetting_escalation(game):
    client, url, session = game
    client.post(f"{url}/hint")
    assert move(client, url, "MID")["ok"] is True
    assert session.earned_hint is None
    assert "earned_hint" not in client.get(url).json()
    next_hint = client.post(f"{url}/hint").json()
    assert next_hint["stage"] == "alternatives"
    assert client.get(url).json()["earned_hint"] == next_hint
    undone = client.post(f"{url}/undo").json()
    assert undone["moves"] == 0
    assert "earned_hint" not in undone
    assert session.earned_hint is None
    assert session.hint_requests == 2
    assert client.post(f"{url}/hint").json()["stage"] == "hop"


def test_dead_end_and_move_limit_backtrack_help_are_recoverable(game):
    client, url, session = game
    move(client, url, "MID")
    move(client, url, "DEAD")
    earned = client.post(f"{url}/hint").json()
    assert earned["stage"] == "backtrack"
    assert "MID" in earned["message"]
    assert client.get(url).json()["earned_hint"] == earned
    client.post(f"{url}/undo")
    session.chain = ["start", "mid"] * 32 + ["start"]
    limited = client.post(f"{url}/hint").json()
    assert limited["stage"] == "backtrack"
    assert client.get(url).json()["earned_hint"] == limited
    assert session.hint_requests == 1  # The 64-move limit spends no hint stage.


def test_retained_help_is_one_bounded_payload_and_clears_on_win(game):
    client, url, session = game
    for _ in range(25):
        for _ in range(4):
            earned = client.post(f"{url}/hint").json()
            assert session.earned_hint == earned
            assert len(json.dumps(session.earned_hint)) < 800
            assert session.hint_requests <= 3
        move(client, url, "MID")
        assert session.earned_hint is None
        move(client, url, "START")
        assert session.earned_hint is None
    # Keep the same bounded escalation state while returning to a short valid chain.
    session.chain = ["start", "mid"]
    client.post(f"{url}/hint")
    won = move(client, url, "TARGET")
    assert won["won"] is True
    assert session.earned_hint is None
    client.post(f"{url}/hint")
    assert "earned_hint" not in client.get(url).json()
    assert session.hint_requests == 3
    assert lant.LantSession(start="start", target="target", optimal=2).earned_hint is None
