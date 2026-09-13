"""Exploration keeps recipes fixed, preserves earned progress and never ends at a goal."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import (
    MAX_CONCEPTS,
    authored_snapshot,
    validate_world,
)
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
                            "discoveries": [["a", "b"]] * 257}},
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


def expanded_world(world):
    raw = example_catalog()
    raw["concepts"].extend([
        {"id": n, "label": n.upper(), "description": "", "source": "",
         "redistributable": False, "snapshot": {}} for n in ("f", "t")
    ])
    raw["unlocks"].append({"id": "extra-pantry", "after_discoveries": 3,
                           "concept_ids": ["f"], "title": "New supplies"})
    raw["recipes"].append({"id": "new-dish", "pair": ["f", "q"], "result": "t",
                           "explanation": "A new use for Q.",
                           "sources": ["https://example.org/new-dish"]})
    raw["compatible_versions"] = [{"world_id": world.id, "recipe_hash": world.recipe_hash,
                                    "source_sha256": "a" * 64, "mechanics": world.mechanics}]
    return validate_world(raw, check_graph=False)


def test_every_old_collection_prefix_restores_without_losing_discoveries(world, monkeypatch):
    state = post(data={"goal_id": "first-goal"})
    checkpoints = [state]
    for pair in (("a", "b"), ("x", "c"), ("x", "d"), ("y", "e"), ("z", "e")):
        state = craft(state, *pair)
        checkpoints.append(state)
    new = expanded_world(world)
    monkeypatch.setattr(E, "get_world", lambda: new)
    for old in checkpoints:
        restored = post(data={"progress": old["progress"], "goal_id": old["goal_id"]})
        assert restored["progress"]["discoveries"] == old["progress"]["discoveries"]
        assert restored["discovered_count"] == old["discovered_count"]
        assert restored["goal_id"] == old["goal_id"]
        assert {i["id"] for i in old["inventory"]} <= {i["id"] for i in restored["inventory"]}
        assert restored["progress"]["recipe_hash"] == new.recipe_hash
        assert restored["compatible_recipe_hashes"] == [world.recipe_hash]


def test_completed_collection_gets_more_content_and_clears_old_completion_hint(world, monkeypatch):
    state = post()
    for pair in (("a", "b"), ("x", "c"), ("x", "d"), ("y", "e"), ("z", "e")):
        state = craft(state, *pair)
    base = f"{BASE}/{state['game_id']}"
    completed = post(base + "/hint")
    assert completed["hint"]["stage"] == "complete"
    monkeypatch.setattr(E, "get_world", lambda: expanded_world(world))
    upgraded = Client().get(base).json()
    assert upgraded["game_id"] == state["game_id"]
    assert not upgraded["complete"] and upgraded["hint"] is None
    assert upgraded["revision"] == completed["revision"] + 1
    assert upgraded["discovered_count"] == 5
    assert next(i for i in upgraded["inventory"] if i["id"] == "q")["ready"]
    assert craft(upgraded, "q", "f")["complete"]


def test_live_mutation_upgrades_before_crafting_and_keeps_an_earned_hint(world, monkeypatch):
    state = post()
    hinted = post(f"{BASE}/{state['game_id']}/hint")
    new = expanded_world(world)
    monkeypatch.setattr(E, "get_world", lambda: new)
    miss = craft(state, "a", "c")
    assert miss["hint"] == hinted["hint"]
    assert miss["progress"]["recipe_hash"] == new.recipe_hash
    assert miss["world"]["total_concepts"] == 12


def test_old_fingerprint_cannot_claim_new_recipe_or_unearned_new_supplies(world, monkeypatch):
    old = post()
    for pair in (("a", "b"), ("x", "c"), ("x", "d"), ("z", "e")):
        old = craft(old, *pair)
    monkeypatch.setattr(E, "get_world", lambda: expanded_world(world))
    forged = deepcopy(old["progress"])
    forged["discoveries"].append(["q", "f"])
    post(data={"progress": forged}, status=400)


@pytest.mark.parametrize("change", [
    lambda raw: raw["compatible_versions"][0].update(recipe_hash="0" * 64),
    lambda raw: raw["compatible_versions"][0].update(world_id="unrelated"),
    lambda raw: raw["compatible_versions"].append(deepcopy(raw["compatible_versions"][0])),
    lambda raw: raw["recipes"][0].update(result="z"),
    lambda raw: raw["unlocks"][0].update(after_discoveries=1),
])
def test_compatibility_rejects_forged_hashes_or_changed_original_mechanics(world, change):
    raw = expanded_world(world).catalog.model_dump()
    change(raw)
    with pytest.raises(ValueError):
        validate_world(raw, check_graph=False)


def test_compatible_world_can_reorder_displayed_starters(world):
    expanded = expanded_world(world)
    raw = expanded.catalog.model_dump()
    raw["world"]["starter_ids"].reverse()
    assert validate_world(raw, check_graph=False).recipe_hash == expanded.recipe_hash


def authored_concept(concept_id="alw_food_test", label="Ingredient pentru test"):
    description = "Definiție originală pentru verificarea provenienței."
    references = ["https://example.test/ingredient"]
    return {"id": concept_id, "label": label, "description": description,
            "source": "authored:alchimie", "redistributable": False, "origin": "authored",
            "references": references,
            "snapshot": authored_snapshot(concept_id, label, description, references)}


def authored_world_record():
    raw = example_catalog()
    concept = authored_concept()
    raw["concepts"].append(concept)
    raw["recipes"].append({"id": "authored-dish", "pair": ["a", "q"],
                           "result": concept["id"], "explanation": "Test combination.",
                           "sources": ["https://example.test/recipe"]})
    return raw


@pytest.mark.parametrize("change", [
    lambda c: c.update(source="copied without provenance"),
    lambda c: c.update(redistributable=True),
    lambda c: c.update(description="Changed without updating its source snapshot"),
    lambda c: c.update(references=[]),
    lambda c: c.update(references=["file:///private"]),
    lambda c: c.update(references=["https://user:pass@example.test"]),
    lambda c: c.update(references=["https://bad host.example"]),
    lambda c: c["snapshot"].update(id="different"),
])
def test_authored_definitions_require_exact_provenance_and_checked_references(change):
    raw = authored_world_record()
    change(raw["concepts"][-1])
    with pytest.raises(ValueError, match="authored"):
        validate_world(raw, check_graph=False)


def test_authored_definitions_are_playable_without_mutating_the_global_graph(monkeypatch):
    from cat_de_roman_esti.wordgames.service import get_service

    service = get_service()
    before = len(service.graph.nodes)
    world = validate_world(authored_world_record(), check_graph=False)
    monkeypatch.setattr(E, "get_world", lambda: world)
    state = post()
    for pair in (("a", "b"), ("x", "d"), ("z", "e"), ("a", "q")):
        state = craft(state, *pair)
    assert state["discovered"][0]["id"] == "alw_food_test"
    assert service.node("alw_food_test") is None and len(service.graph.nodes) == before


def test_authored_namespace_and_existing_identity_shadowing_are_rejected():
    from cat_de_roman_esti.wordgames.discovery_world import _check_graph
    from cat_de_roman_esti.wordgames.service import get_service

    raw = authored_world_record()
    raw["concepts"][-1]["id"] = "n_forged"
    raw["recipes"][-1]["result"] = "n_forged"
    with pytest.raises(ValueError, match="namespace"):
        validate_world(raw, check_graph=False)
    world = validate_world(authored_world_record(), check_graph=False)
    # Isolate the authored definition to test collision against the actual KG.
    concept = world.concepts["alw_food_test"]
    concept.label = next(iter(get_service().graph.nodes.values())).label_ro
    world.concepts.clear()
    world.concepts[concept.id] = concept
    with pytest.raises(ValueError, match="shadows"):
        _check_graph(world)


@pytest.mark.parametrize("label", ["  INGREDIENT PENTRU TEST  ", "   "])
def test_authored_labels_cannot_be_blank_or_indistinguishable(label):
    raw = authored_world_record()
    concept = authored_concept("alw_food_second_test", label)
    raw["concepts"].append(concept)
    raw["recipes"].append({"id": "second-authored", "pair": ["b", "q"],
                           "result": concept["id"], "explanation": "Test.",
                           "sources": ["https://example.test/recipe"]})
    with pytest.raises(ValueError, match="labels"):
        validate_world(raw, check_graph=False)


def test_full_256_concept_collection_restores_more_than_128_earned_crafts(monkeypatch):
    raw = example_catalog()
    previous = "q"
    for number in range(MAX_CONCEPTS - len(raw["concepts"])):
        concept_id = f"test_{number}"
        raw["concepts"].append({"id": concept_id, "label": f"Test {number}", "description": "",
                                "source": "", "redistributable": False, "snapshot": {}})
        raw["recipes"].append({"id": f"chain-{number}", "pair": sorted(["a", previous]),
                               "result": concept_id, "explanation": "Test chain.",
                               "sources": ["https://example.test/chain"]})
        previous = concept_id
    world = validate_world(raw, check_graph=False)
    monkeypatch.setattr(E, "get_world", lambda: world)
    session = E.restore_session(world, None)
    while True:
        pair = next((p for p, r in world.recipes.items()
                     if set(p) <= session.owned.keys() and r.result not in session.owned), None)
        if pair is None:
            break
        session.craft(pair)
    checkpoint = E.state_payload("test", session)["progress"]
    assert len(checkpoint["discoveries"]) > 128 and len(session.owned) == MAX_CONCEPTS
    restored = post(data={"progress": checkpoint})
    assert restored["complete"] and len(restored["inventory"]) == MAX_CONCEPTS
    assert restored["progress"] == checkpoint
    raw["concepts"].append({**raw["concepts"][-1], "id": "one-too-many"})
    with pytest.raises(ValueError):
        validate_world(raw, check_graph=False)
