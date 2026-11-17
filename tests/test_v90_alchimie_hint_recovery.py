"""One earned Alchimie cue survives reads without replaying or charging a hint."""
from __future__ import annotations

import json
from itertools import combinations

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import alchimie as A
from cat_de_roman_esti.wordgames.service import SessionStore, WordGameService

BASE = "/api/wordgames/alchimie/games"
PUBLIC_HINT_KEYS = {"hint", "hint_kind", "hint_output", "message"}


@pytest.fixture()
def game(monkeypatch):
    labels = {**{n: f"Ingredient {n}" for n in "abcdef"},
              "x": "Rezultat intermediar", "secret_target": "Ținta afișată"}
    svc = WordGameService(Graph.from_records(
        [{"id": key, "label_ro": label, "category": "test"}
         for key, label in labels.items()], [],
    ))
    monkeypatch.setattr(A, "get_service", lambda: svc)
    monkeypatch.setattr(A, "store", SessionStore())
    session = A.AlchimieSession(
        seeds=list("abcdef"), target="secret_target", target_depth=2,
        recipes={("a", "b"): ("x",), ("c", "x"): ("secret_target",)},
    )
    for seed in session.seeds:
        session.add(seed, None)
    gid = A.store.create(session)
    return Client(), gid, session


def _post(game, action, data=None):
    client, gid, _ = game
    return client.post(f"{BASE}/{gid}/{action}", data or {}, content_type="application/json")


def _read(game):
    client, gid, _ = game
    return client.get(f"{BASE}/{gid}").json()


def _earn(game):
    response = _post(game, "hint")
    assert response.status_code == 200
    body = response.json()
    keys = PUBLIC_HINT_KEYS | ({"hint_ingredient"} if body["hint_kind"] == "category" else set())
    assert body["earned_hint"] == {key: body[key] for key in keys}
    return body


def test_get_restores_paid_output_cue_exactly_without_charge_or_private_ids(game):
    assert "earned_hint" not in _read(game)
    paid = _earn(game)
    assert paid["hints_used"] == 1
    assert paid["earned_hint"] == {
        "hint": None, "hint_kind": "output",
        "hint_output": {"label": "Rezultat intermediar"},
        "message": "Indiciu: caută mai întâi «Rezultat intermediar».",
    }
    for _ in range(4):
        resumed = _read(game)
        assert resumed["earned_hint"] == paid["earned_hint"]
        assert resumed["hints_used"] == 1
        assert resumed["moves"] == paid["moves"]
        assert resumed["target"]["id"] is None
        assert "secret_target" not in json.dumps(resumed)
        assert '"id": "x"' not in json.dumps(resumed)
        assert "recipes" not in resumed and "routes" not in resumed
    assert resumed["steps"] == 1 and resumed["hint_level"] == 1


def test_later_paid_pair_overwrites_one_cue_with_only_owned_ids(game):
    _earn(game)
    second = _earn(game)
    assert second["earned_hint"]["hint_ingredient"]["id"] == "a"
    third = _earn(game)
    cue = third["earned_hint"]
    assert third["hints_used"] == third["steps"] == 3
    assert _post(game, "hint").status_code == 400
    assert set(cue) == PUBLIC_HINT_KEYS
    assert cue["hint_kind"] == "pair" and cue["hint_output"] is None
    assert {item["id"] for item in cue["hint"]} == {"a", "b"}
    assert _read(game)["earned_hint"] == cue
    assert game[2].earned_hint is not None
    assert "secret_target" not in json.dumps(third)
    assert '"id": "x"' not in json.dumps(third)


@pytest.mark.parametrize("action", ["empty", "productive", "reset"])
def test_new_experiment_or_reset_clears_cue(game, action):
    paid = _earn(game)
    if action == "reset":
        response = _post(game, "reset")
    else:
        pair = ("a", "b") if action == "productive" else next(
            pair for pair in combinations(game[2].seeds, 2)
            if pair not in game[2].attempted_pairs and pair not in game[2].recipes
        )
        response = _post(game, "combine", dict(zip(("a", "b"), pair, strict=True)))
    assert response.status_code == 200
    body = response.json()
    assert "earned_hint" not in body and "earned_hint" not in _read(game)
    assert game[2].earned_hint is None
    assert body["hints_used"] == (0 if action == "reset" else paid["hints_used"])
    if action == "reset":
        assert body["moves"] == body["attempted_count"] == 0
        assert body["inventory"] == _read(game)["inventory"]


def test_free_repeated_pair_and_rejected_pair_preserve_earned_cue(game):
    pair = ("a", "c")
    _post(game, "combine", {"a": pair[0], "b": pair[1]})
    paid = _earn(game)
    repeat = _post(game, "combine", {"a": pair[1], "b": pair[0]}).json()
    assert repeat["already_tried"] is True
    assert repeat["earned_hint"] == paid["earned_hint"]
    assert repeat["moves"] == paid["moves"]
    assert repeat["hints_used"] == 1
    assert _post(game, "combine", {"a": "a", "b": "a"}).status_code == 400
    assert _read(game)["earned_hint"] == paid["earned_hint"]


def test_public_target_label_skips_output_rung_then_win_clears_ingredient(game):
    assert _post(game, "combine", {"a": "a", "b": "b"}).status_code == 200
    paid = _earn(game)
    assert paid["hint_kind"] == "category"
    assert paid["hint_level"] == 2 and paid["steps"] == 1
    assert paid["hint_output"] is None and paid["hint"] is None
    assert "secret_target" not in json.dumps(paid)
    won = _post(game, "combine", {"a": "c", "b": "x"}).json()
    assert won["won"] is True
    assert won["target"]["id"] == "secret_target"
    assert "earned_hint" not in won
    for _ in range(2):
        assert _read(game)["score"] == won["score"]
        assert "earned_hint" not in _read(game)
    assert _post(game, "hint").status_code == 400
    repeat = _post(game, "combine", {"a": "c", "b": "x"}).json()
    assert repeat["score"] == won["score"]
    assert "earned_hint" not in repeat


def test_no_forward_pair_does_not_charge_or_change_earned_cue(game):
    _earn(game)
    # Defensive no-forward state: this cannot occur in a valid projected game.
    game[2].recipes = {}
    before = _read(game)
    response = _post(game, "hint")
    assert response.status_code == 400
    assert before["hints_used"] == 1
    assert _read(game) == before


@pytest.fixture()
def branching_game(game):
    """A side discovery makes a different recipe route equally short."""
    session = game[2]
    session.recipes = {
        ("a", "b"): ("x",), ("c", "x"): ("secret_target",),
        ("c", "d"): ("w",), ("e", "w"): ("v",),
        ("b", "v"): ("secret_target",),
    }
    return game


def test_hint_subject_stays_fixed_after_a_different_productive_combine(branching_game):
    first = _earn(branching_game)
    assert first["hint_output"] == {"label": "Rezultat intermediar"}
    combined = _post(branching_game, "combine", {"a": "c", "b": "d"})
    assert combined.status_code == 200
    resumed = _read(branching_game)
    assert resumed["hint_level"] == 1 and resumed["hints_left"] == 2
    assert "earned_hint" not in resumed

    second = _earn(branching_game)
    assert second["hint_ingredient"]["id"] == "a"
    assert second["steps"] == second["hint_level"] == 2
    third = _earn(branching_game)
    assert [item["id"] for item in third["hint"]] == ["a", "b"]
    assert third["steps"] == third["hint_level"] == 3
    for body in (first, second, third):
        encoded = json.dumps(body)
        assert '"id": "x"' not in encoded
        assert "secret_target" not in encoded
        assert "recipes" not in body and "routes" not in body


@pytest.mark.parametrize("solve_pair", [("a", "b"), ("c", "d")])
def test_solving_the_hint_subject_ends_the_ladder_after_reset(branching_game, solve_pair):
    if solve_pair != ("a", "b"):
        branching_game[2].recipes[("a", "b")] = ("x", "v")
        branching_game[2].recipes[("c", "d")] = ("x",)
    _earn(branching_game)
    combined = _post(branching_game, "combine", dict(zip(("a", "b"), solve_pair, strict=True)))
    assert combined.status_code == 200
    assert combined.json()["won"] is False
    assert combined.json()["hints_left"] == 0
    for reset in (False, True):
        if reset:
            assert _post(branching_game, "reset").status_code == 200
        before = _read(branching_game)
        assert before["hints_left"] == 0 and before["hint_level"] == 1
        assert before["steps"] == 1
        assert _post(branching_game, "hint").status_code == 400
        assert _read(branching_game) == before


def test_reset_keeps_the_pinned_recipe_private_until_its_ingredients_return(game):
    assert _post(game, "combine", {"a": "a", "b": "b"}).status_code == 200
    ingredient = _earn(game)
    assert ingredient["hint_level"] == 2
    assert ingredient["hint_ingredient"]["id"] == "c"
    before = _post(game, "reset").json()
    assert before["hints_left"] == 0
    assert _post(game, "hint").status_code == 400
    assert _read(game) == before
    assert _post(game, "combine", {"a": "a", "b": "b"}).status_code == 200
    pair = _earn(game)
    assert pair["hint_level"] == 3 and pair["steps"] == 2
    assert [item["id"] for item in pair["hint"]] == ["c", "x"]
