"""Exploration keeps recipes fixed, preserves earned progress and never ends at a goal."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import validate_world
from cat_de_roman_esti.wordgames.service import SessionStore

BASE = "/api/alchimie/explore"


def example_catalog():
    recipes = [
        ("a", "b", "x"), ("b", "c", "x"), ("x", "c", "y"), ("a", "d", "y"),
        ("x", "d", "z"), ("y", "e", "w"), ("z", "e", "q"),
    ]
    return {
        "schema_version": 1,
        "world": {"id": "test-world-v1", "title": "Test world", "description": "A world",
                  "starter_ids": ["a", "b", "c", "d"]},
        "concepts": [{"id": n, "label": n.upper(), "description": "", "source": "",
                      "redistributable": False, "snapshot": {}} for n in "abcdexyzwq"],
        "recipes": [{"id": f"r{i}", "pair": [a, b], "result": result,
                     "explanation": f"{a} and {b} make {result}",
                     "sources": ["https://example.org/recipe"]}
                    for i, (a, b, result) in enumerate(recipes)],
        "goals": [{"id": "first-goal", "target": "z", "title": "First goal"},
                  {"id": "second-goal", "target": "w", "title": "Second goal"}],
        "unlocks": [{"id": "pantry", "after_discoveries": 2,
                     "concept_ids": ["e"], "title": "More supplies"}],
        "candidate_sha256": "a" * 64,
        "bindings": {"kg_sha256": "b" * 64, "rubric_sha256": "c" * 64},
        "reviews": [{"role": role, "reviewer": role, "candidate_sha256": "a" * 64,
                     "sha256": "d" * 64} for role in ("factual", "quality")],
    }


@pytest.fixture
def world(monkeypatch):
    world = validate_world(example_catalog(), check_graph=False)
    monkeypatch.setattr(E, "get_world", lambda: world)
    monkeypatch.setattr(E, "store", SessionStore())
    return world


def post(path=BASE, data=None, status=200):
    response = Client().post(
        path, data if data is not None else {}, content_type="application/json",
    )
    assert response.status_code == status, response.content
    return response.json()


def craft(state, a, b):
    return post(f"{BASE}/{state['game_id']}/combine", {"a": a, "b": b})


def test_goals_never_select_recipes_or_stop_discoveries(world):
    states = [post(data={"goal_id": goal}) for goal in (None, "first-goal", "second-goal")]
    for index, state in enumerate(states):
        state = craft(state, "a", "b")
        assert state["discovered"] == [{"id": "x", "label": "X"}]
        state = craft(state, "x", "d")
        assert state["goals"][0]["completed"]
        assert state["goals"][0]["target_id"] == "z"
        assert state["supplied"] == [{"id": "e", "label": "E"}]
        state = craft(state, "z", "e")
        assert state["discovered"] == [{"id": "q", "label": "Q"}]
        assert not state["complete"]
        states[index] = state
    assert states[0]["progress"] == states[1]["progress"] == states[2]["progress"]


def test_alternative_recipes_are_commutative_and_repeat_safe(world):
    state = craft(post(), "b", "a")
    assert state["discovered_count"] == 1
    again = craft(state, "c", "b")
    assert again["discovered"] == [] and again["already_known"]
    assert again["result"] == {"id": "x", "label": "X"}
    assert again["progress"] == state["progress"]
    assert again["revision"] == state["revision"] + 1


def test_misses_are_free_and_cannot_advance_pantry_unlocks(world):
    state = post()
    for _ in range(8):
        state = craft(state, "a", "c")
    assert state["discovered_count"] == 0 and state["unlocked"] == []
    assert state["next_unlock"]["remaining"] == 2
    assert "score" not in state and "moves" not in state
    assert state["progress"]["discoveries"] == []


def test_hint_progression_survives_get_and_misses_and_never_leaks_output_id(world):
    state = post(data={"goal_id": "first-goal"})
    base = f"{BASE}/{state['game_id']}"
    hinted = post(base + "/hint")
    assert hinted["hint"]["stage"] == "output"
    assert hinted["hint"]["output"] == {"label": "X"}
    assert hinted["hint"]["pair"] is None
    assert Client().get(base).json()["hint"] == hinted["hint"]
    assert craft(state, "a", "c")["hint"] == hinted["hint"]
    paired = post(base + "/hint")
    assert paired["hint"]["stage"] == "pair"
    assert {i["id"] for i in paired["hint"]["pair"]} == {"a", "b"}
    assert craft(state, "a", "b")["hint"] is None


def test_goal_changes_only_guidance_and_preserves_collection(world):
    state = craft(post(), "a", "b")
    base = f"{BASE}/{state['game_id']}"
    post(base + "/hint")
    changed = post(base + "/goal", {"goal_id": "second-goal"})
    assert changed["progress"] == state["progress"]
    assert changed["hint"] is None and changed["goal_id"] == "second-goal"
    assert post(base + "/goal", {"goal_id": None})["goal_id"] is None
    post(base + "/goal", {"goal_id": "fake"}, status=400)


def test_full_world_can_be_completed_and_encyclopedia_keeps_final_items(world):
    state = post()
    for pair in (("a", "b"), ("x", "c"), ("x", "d"), ("y", "e"), ("z", "e")):
        state = craft(state, *pair)
    assert state["complete"] and state["discovered_count"] == 5
    assert len(state["inventory"]) == len(world.concepts)
    assert all(item["status"] != "active" for item in state["inventory"])
    terminal = next(item for item in state["inventory"] if item["id"] == "q")
    assert terminal["status"] == "final" and terminal["parents"]
    assert terminal["explanation"] and terminal["sources"]
    assert post(f"{BASE}/{state['game_id']}/hint")["hint"]["stage"] == "complete"


def test_expired_session_restores_earned_collection_and_supplies(world):
    state = craft(craft(post(), "a", "b"), "x", "c")
    E.store.delete(state["game_id"])
    assert Client().get(f"{BASE}/{state['game_id']}").status_code == 404
    restored = post(data={"progress": state["progress"], "goal_id": "second-goal"})
    assert restored["game_id"] != state["game_id"]
    assert restored["inventory"] == state["inventory"]
    assert restored["unlocked"] == state["unlocked"]
    assert restored["progress"] == state["progress"]


@pytest.mark.parametrize("pairs", [
    [["x", "c"]], [["a", "a"]], [["a", "c"]], [["a"]], [["a", "b", "c"]],
    [["unknown", "b"]], [["a", "b"], ["z", "e"]],
])
def test_invalid_replay_cannot_invent_discoveries_or_supplies(world, pairs):
    post(data={"progress": {"world_id": world.id, "recipe_hash": world.recipe_hash,
                            "discoveries": pairs}}, status=400)
    assert len(E.store) == 0


def test_checkpoint_union_accepts_duplicate_valid_recipes_and_retains_both_branches(world):
    state = post(data={"progress": {"world_id": world.id, "recipe_hash": world.recipe_hash,
                                   "discoveries": [
        ["a", "b"], ["x", "c"], ["b", "a"], ["x", "d"],
    ]}})
    assert state["discovered_count"] == 3
    assert {"x", "y", "z", "e"} <= {i["id"] for i in state["inventory"]}
    assert len(state["progress"]["discoveries"]) == 3


def test_stale_or_malformed_checkpoint_fails_without_allocating_session(world):
    post(data={"progress": {"world_id": "old-world", "recipe_hash": world.recipe_hash,
                            "discoveries": []}}, status=409)
    post(data={"progress": {"world_id": world.id, "recipe_hash": world.recipe_hash,
                            "discoveries": [["a", "b"]] * 129}},
         status=422)
    post(data={"owned": ["q"]}, status=422)
    post(data={"goal_id": "unknown"}, status=400)
    assert len(E.store) == 0


def test_rejected_moves_do_not_mutate_or_invalidate_hint(world):
    state = post()
    base = f"{BASE}/{state['game_id']}"
    before = post(base + "/hint")
    for body in ({"a": "a", "b": "a"}, {"a": "a", "b": "q"}):
        post(base + "/combine", body, status=400)
    post(base + "/combine", {"a": 1, "b": "b"}, status=422)
    assert Client().get(base).json() == before


def test_parallel_same_pair_earns_only_one_discovery(world):
    state = post()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: craft(state, "a", "b"), range(2)))
    assert sum(len(result["discovered"]) for result in results) == 1
    final = Client().get(f"{BASE}/{state['game_id']}").json()
    assert final["discovered_count"] == 1 and final["revision"] == 2


def test_unavailable_catalog_is_503_and_keeps_other_modes_available(world, monkeypatch):
    def unavailable():
        raise ValueError("catalog changed")
    monkeypatch.setattr(E, "get_world", unavailable)
    post(status=503)
    assert len(E.store) == 0


def test_public_state_hides_recipebook_and_undiscovered_ids(world):
    state = post()
    assert all(g["target_id"] is None for g in state["goals"])
    assert "recipes" not in state and "concepts" not in state and "routes" not in state
    assert {item["id"] for item in state["inventory"]} == {"a", "b", "c", "d"}
    assert state["next_unlock"] == {"title": "More supplies", "after_discoveries": 2,
                                    "remaining": 2}


def test_world_validation_detects_unreachable_supply_cycle():
    raw = deepcopy(example_catalog())
    raw["unlocks"][0]["after_discoveries"] = 5
    with pytest.raises(ValueError, match="unreachable"):
        validate_world(raw, check_graph=False)


def test_same_world_id_cannot_silently_replace_earned_results(world, monkeypatch):
    earned = craft(post(), "a", "b")
    updated = example_catalog()
    updated["recipes"][0]["result"] = "z"
    changed_world = validate_world(updated, check_graph=False)
    assert changed_world.id == world.id and changed_world.recipe_hash != world.recipe_hash
    monkeypatch.setattr(E, "get_world", lambda: changed_world)
    post(data={"progress": earned["progress"]}, status=409)
    # The old active session still uses its original pinned world.
    result = craft(earned, "a", "b")
    assert result["result"]["id"] == "x"
    assert result["progress"] == earned["progress"]


def test_harmless_copy_and_goal_edits_keep_saved_discoveries_compatible(world, monkeypatch):
    earned = craft(post(), "a", "b")
    updated = example_catalog()
    updated["recipes"][0]["explanation"] = "A clearer explanation."
    updated["goals"][0]["title"] = "A clearer goal title"
    updated["world"]["description"] = "A clearer description"
    changed_world = validate_world(updated, check_graph=False)
    assert changed_world.recipe_hash == world.recipe_hash
    monkeypatch.setattr(E, "get_world", lambda: changed_world)
    restored = post(data={"progress": earned["progress"]})
    assert restored["progress"] == earned["progress"]


def test_supply_threshold_changes_invalidate_replay_fingerprint(world):
    updated = example_catalog()
    updated["unlocks"][0]["after_discoveries"] = 1
    changed_world = validate_world(updated, check_graph=False)
    assert changed_world.recipe_hash != world.recipe_hash
