"""Earned graph associations explain crafts without exposing the private recipe book."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Edge, Graph  # noqa: E402
from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames.service import SessionStore, WordGameService  # noqa: E402

BASE = "/api/wordgames/alchimie/games"


@pytest.fixture()
def game(monkeypatch):
    labels = {
        "a": "Primul concept", "b": "Al doilea concept", "c": "Al treilea concept",
        "x": "Rezultat descoperit", "y": "Alt rezultat", "private_target": "Scopul jocului",
        "private_neighbor": "Alt concept secret",
    }
    edges = [
        ("a", "x", "asociere secundară", 0.4, False),
        ("a", "x", "prima legătură", 0.9, False),
        # Reverse-authored, bidirectional edge: its label must not be reversed.
        ("x", "b", "a doua legătură", 0.8, False),
        ("a", "y", "   ", 0.8, False),
        ("b", "y", "legătură falsă", 1.0, True),
        ("x", "private_target", "apropie ținta", 0.9, False),
        ("c", "private_target", "completează ținta", 0.9, False),
        ("x", "private_neighbor", "nu este câștigată", 0.9, False),
    ]
    svc = WordGameService(Graph.from_records(
        [{"id": key, "label_ro": label, "category": "test"} for key, label in labels.items()],
        [{"id": f"edge_{i}", "src_id": src, "dst_id": dst, "label_ro": label,
          "strength": strength, "is_distractor": distractor, "bidirectional": True}
         for i, (src, dst, label, strength, distractor) in enumerate(edges)],
    ))
    monkeypatch.setattr(A, "get_service", lambda: svc)
    monkeypatch.setattr(A, "store", SessionStore())

    def create():
        session = A.AlchimieSession(
            seeds=["a", "b", "c"], target="private_target", target_depth=2,
            recipes={("a", "b"): ("x", "y"), ("c", "x"): ("private_target",)},
        )
        for seed in session.seeds:
            session.add(seed, None)
        return A.store.create(session), session

    return Client(), svc, create


def _combine(client, game_id, a="a", b="b"):
    response = client.post(
        f"{BASE}/{game_id}/combine", {"a": a, "b": b}, content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()


def _inventory(state):
    return {item["id"]: item for item in state["inventory"]}


def test_earned_links_keep_strongest_actual_edge_and_authored_orientation(game):
    client, _svc, create = game
    game_id, _session = create()
    initial = client.get(f"{BASE}/{game_id}").json()
    assert all(item["links"] == [] for item in initial["inventory"])

    body = _combine(client, game_id)
    inventory = _inventory(body)
    assert inventory["x"]["links"] == [
        {"source": {"id": "a", "label": "Primul concept"},
         "target": {"id": "x", "label": "Rezultat descoperit"}, "label": "prima legătură"},
        {"source": {"id": "x", "label": "Rezultat descoperit"},
         "target": {"id": "b", "label": "Al doilea concept"}, "label": "a doua legătură"},
    ]
    # A blank relation and a distractor are not explanations for the second output.
    assert inventory["y"]["links"] == []
    assert body["discovered"] == [
        {"id": "x", "label": "Rezultat descoperit"}, {"id": "y", "label": "Alt rezultat"},
    ]
    assert "private_target" not in json.dumps(body)
    assert "private_neighbor" not in json.dumps(body)
    assert "nu este câștigată" not in json.dumps(body, ensure_ascii=False)
    for item in inventory.values():
        assert len(item["links"]) <= 2
        for link in item["links"]:
            assert set(link) == {"source", "target", "label"}
            assert {link["source"]["id"], link["target"]["id"]} <= set(inventory)


def test_explanations_survive_resume_and_free_repeats_and_reset_with_progress(game):
    client, _svc, create = game
    game_id, _session = create()
    crafted = _combine(client, game_id)
    assert client.get(f"{BASE}/{game_id}").json()["inventory"] == crafted["inventory"]
    repeated = _combine(client, game_id, "b", "a")
    assert repeated["already_tried"] is True
    assert repeated["discovered"] == []
    assert repeated["inventory"] == crafted["inventory"]
    assert repeated["moves"] == crafted["moves"] == 1
    reset = client.post(f"{BASE}/{game_id}/reset").json()
    assert [item["id"] for item in reset["inventory"]] == ["a", "b", "c"]
    assert all(item["links"] == [] for item in reset["inventory"])


def test_selection_order_does_not_reverse_or_reorder_graph_claims(game):
    client, _svc, create = game
    first_id, _first = create()
    second_id, _second = create()
    forward = _inventory(_combine(client, first_id))
    reverse = _inventory(_combine(client, second_id, "b", "a"))
    assert forward["x"]["parents"] == list(reversed(reverse["x"]["parents"]))
    assert forward["x"]["links"] == reverse["x"]["links"]


def test_empty_combine_has_no_explanations_and_won_target_gets_only_earned_links(game):
    client, _svc, create = game
    game_id, _session = create()
    empty = _combine(client, game_id, "a", "c")
    assert empty["discovered"] == []
    assert all(item["links"] == [] for item in empty["inventory"])
    _combine(client, game_id)
    won = _combine(client, game_id, "x", "c")
    assert won["won"] is True
    target = _inventory(won)["private_target"]
    assert len(target["links"]) == 2
    assert {link["label"] for link in target["links"]} == {"apropie ținta", "completează ținta"}
    assert "private_neighbor" not in json.dumps(won)
    finished = _combine(client, game_id, "a", "b")
    assert finished["discovered"] == []
    assert finished["inventory"] == won["inventory"]
    assert finished["score"] == won["score"]


def test_missing_or_mismatched_edges_cannot_invent_claims_or_leak_other_nodes(game, monkeypatch):
    _client, svc, _create = game
    assert A._earned_links("x", ("a", "c"), {"a", "c", "x"}) == [
        {"source": {"id": "a", "label": "Primul concept"},
         "target": {"id": "x", "label": "Rezultat descoperit"}, "label": "prima legătură"},
    ]
    assert A._earned_links("x", ("a", "b"), {"a", "b"}) == []
    assert A._earned_links("x", ("a", "b"), {"x"}) == []
    monkeypatch.setattr(svc, "link", lambda *_args: Edge(
        id="bad-edge", src_id="private_neighbor", dst_id="x", relation="related_to",
        label_ro="nu este câștigată", strength=1.0,
    ))
    assert A._earned_links("x", ("a", "b"), {"a", "b", "x"}) == []
