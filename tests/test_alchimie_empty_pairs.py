"""Observed empty experiments are bounded, private to a session and version-safe."""
from copy import deepcopy

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import validate_world
from cat_de_roman_esti.wordgames.service import SessionStore
from tests.test_alchimie_explore import BASE, craft, example_catalog, post


@pytest.fixture
def world(monkeypatch):
    current = validate_world(example_catalog(), check_graph=False)
    monkeypatch.setattr(E, "get_world", lambda: current)
    monkeypatch.setattr(E, "store", SessionStore())
    return current


def test_only_observed_empty_pairs_are_returned_and_reverse_attempts_deduplicate(world):
    state = post()
    assert state["empty_pairs"] == []
    initial_progress = deepcopy(state["progress"])
    state = craft(state, "c", "a")
    assert state["empty_pairs"] == [["a", "c"]]
    assert state["result"] is None and state["discovered"] == []
    assert state["progress"] == initial_progress and state["unlocked"] == []
    state = craft(state, "a", "c")
    assert state["empty_pairs"] == [["a", "c"]] and state["revision"] == 2
    assert Client().get(f"{BASE}/{state['game_id']}").json()["empty_pairs"] == [["a", "c"]]
    assert "empty_pairs" not in state["progress"]
    assert "recipes" not in state and "score" not in state and "moves" not in state


def test_success_and_known_results_never_become_empty_markers(world):
    state = craft(post(), "a", "c")
    state = craft(state, "a", "b")
    assert state["result"]["id"] == "x"
    state = craft(state, "b", "c")
    assert state["already_known"] and state["result"]["id"] == "x"
    assert state["empty_pairs"] == [["a", "c"]]
    assert state["discovered_count"] == 1


def test_empty_memory_is_bounded_and_evicts_the_oldest_distinct_pair(world, monkeypatch):
    assert E.MAX_EMPTY_PAIRS == 128
    monkeypatch.setattr(E, "MAX_EMPTY_PAIRS", 2)
    state = post()
    for pair in (("a", "c"), ("b", "d"), ("c", "d")):
        state = craft(state, *pair)
    assert state["empty_pairs"] == [["b", "d"], ["c", "d"]]
    state = craft(state, "d", "b")
    assert state["empty_pairs"] == [["b", "d"], ["c", "d"]]
    state = craft(state, "c", "a")
    assert state["empty_pairs"] == [["c", "d"], ["a", "c"]]
    assert state["discovered_count"] == 0 and not state["unlocked"]


@pytest.mark.parametrize("pair", [("a", "a"), ("a", "not-owned"), ("a", "e")])
def test_invalid_experiments_do_not_record_or_change_state(world, pair):
    state = post()
    url = f"{BASE}/{state['game_id']}"
    post(url + "/combine", {"a": pair[0], "b": pair[1]}, status=400)
    assert Client().get(url).json() == state


def test_goal_changes_keep_observations_but_restored_and_other_sessions_start_empty(world):
    state = craft(post(), "a", "c")
    changed = post(f"{BASE}/{state['game_id']}/goal", {"goal_id": "first-goal"})
    assert changed["empty_pairs"] == [["a", "c"]]
    assert post(data={"progress": state["progress"]})["empty_pairs"] == []
    assert post()["empty_pairs"] == []
    post(data={"progress": state["progress"], "empty_pairs": [["b", "d"]]}, status=422)


def test_compatible_book_upgrade_clears_old_empty_pairs_before_they_gain_recipes(
    world, monkeypatch,
):
    state = craft(post(), "a", "c")
    raw = example_catalog()
    raw["recipes"].append({"id": "new-alternative", "pair": ["a", "c"], "result": "x",
                           "explanation": "A new route to X.",
                           "sources": ["https://example.org/new-recipe"]})
    raw["compatible_versions"] = [{"world_id": world.id, "recipe_hash": world.recipe_hash,
                                    "source_sha256": "a" * 64, "mechanics": world.mechanics}]
    new = validate_world(raw, check_graph=False)
    monkeypatch.setattr(E, "get_world", lambda: new)
    upgraded = Client().get(f"{BASE}/{state['game_id']}").json()
    assert upgraded["empty_pairs"] == []
    assert upgraded["progress"]["recipe_hash"] == new.recipe_hash
    assert upgraded["progress"]["discoveries"] == state["progress"]["discoveries"]
    result = craft(upgraded, "a", "c")
    assert result["result"]["id"] == "x" and result["discovered_count"] == 1
    assert result["empty_pairs"] == []
