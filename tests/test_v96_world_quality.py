"""V96 preserves eight saved books and makes cooked vegetable patties useful again."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import MAX_CONCEPTS, MAX_RECIPES, validate_world
from cat_de_roman_esti.wordgames.service import SessionStore, get_service
from tests.test_v95_world_quality import HISTORY as OLD_HISTORY
from tests.test_v95_world_quality import checkpoint

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/alchimie/explore"
PREVIOUS = ROOT / "docs/reviews/v95-discovery-and-game-quality/alchimie/candidate.json"
PREVIOUS_SHA = "c86748941134ea7dc1e6b7869b4f970c5839f0f39f44f68c661e61476332e801"
ARCHIVE = ROOT / "docs/reviews/v96-words-and-input-clarity/integration/alchimie"
ARCHIVE_SHA = "6de6b98871c43e539402fff9680474cc31afe22f5b4923c13dbafa9bd5465496"
CATALOG_SHA = "356270c25d61f16cac3fdb59efa1e0399b18606ee796d498f132a92ad3c9d5c4"
NEW_WORDS = {"alw_food_ostropel": "Ostropel", "alw_food_salata_fructe": "Salată de fructe"}
NEW_RECIPES = ("ostropel-pui-usturoi", "ostropel-pui-sos-rosii",
               "salata-fructe-cutit", "salata-fructe-frisca", "sandvis-chiftele-legume")
HISTORY = [*OLD_HISTORY, (247, 143, PREVIOUS_SHA)]


@pytest.fixture
def world(monkeypatch):
    blob = (ARCHIVE / "proposed-catalog.json").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == CATALOG_SHA
    world = validate_world(json.loads(blob))
    monkeypatch.setattr(E, "get_world", lambda: world)
    assert len(world.concepts) == 249 and len(world.recipes) == 347
    monkeypatch.setattr(E, "store", SessionStore())
    return world


def post(path=BASE, data=None, status=200):
    response = Client().post(path, data or {}, content_type="application/json")
    assert response.status_code == status, response.content
    return response.json()


def recipe_pair(world, recipe_id):
    return next((pair, recipe) for pair, recipe in world.recipes.items() if recipe.id == recipe_id)


def test_v96_preserves_complete_records_and_reconnects_one_leaf():
    blob = PREVIOUS.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == PREVIOUS_SHA
    current_blob = (ARCHIVE / "candidate.json").read_bytes()
    assert hashlib.sha256(current_blob).hexdigest() == ARCHIVE_SHA
    old, current = json.loads(blob), json.loads(current_blob)
    old_concepts = {r["id"]: r for r in old["concepts"]}
    concepts = {r["id"]: r for r in current["concepts"]}
    old_recipes = {r["id"]: r for r in old["recipes"]}
    recipes = {r["id"]: r for r in current["recipes"]}
    assert len(old_concepts) == 247 and len(old_recipes) == 342
    assert all(concepts[k] == v for k, v in old_concepts.items())
    assert all(recipes[k] == v for k, v in old_recipes.items())
    assert {k: v["label"] for k, v in concepts.items() if k not in old_concepts} == NEW_WORDS
    assert set(recipes) - set(old_recipes) == set(NEW_RECIPES)
    assert (MAX_CONCEPTS, MAX_RECIPES) == (256, 512)
    for field in ("world", "unlocks", "goals"):
        assert current[field] == old[field]
    assert len(current["compatible_versions"]) == 8
    assert current["compatible_versions"][:-1] == old["compatible_versions"]
    assert Counter(r["result"] for r in current["recipes"] if r["result"] in NEW_WORDS) == {
        cid: 2 for cid in NEW_WORDS
    }
    old_results = {r["result"] for r in old["recipes"]}
    old_inputs = {i for r in old["recipes"] for i in r["pair"]}
    new_inputs = {i for r in current["recipes"] for i in r["pair"]}
    assert (old_results - old_inputs) & new_inputs == {"alw_food_chiftele_legume"}
    for cid, label in NEW_WORDS.items():
        concept = concepts[cid]
        assert get_service().resolve(label) is None
        assert concept["origin"] == "authored" and concept["source"] == "authored:alchimie"
        assert not concept["redistributable"] and concept["references"]
        assert concept["description"] == concept["snapshot"]["description"]


@pytest.mark.parametrize("index,expected", tuple(enumerate(HISTORY)))
def test_eight_previous_books_keep_earned_entries(world, index, expected):
    version = world.catalog.compatible_versions[index]
    count, discoveries, source_sha = expected
    assert version.source_sha256 == source_sha
    progress, owned = checkpoint(version)
    assert len(owned) == count and len(progress["discoveries"]) == discoveries
    untouched = deepcopy(progress)
    state = post(data={"progress": progress})
    assert progress == untouched and state["progress"]["discoveries"] == progress["discoveries"]
    assert state["progress"]["recipe_hash"] == world.recipe_hash != version.recipe_hash
    assert state["discovered_count"] == discoveries and not state["complete"]
    assert owned <= {item["id"] for item in state["inventory"]}
    assert Client().get(f"{BASE}/{state['game_id']}").json()["inventory"] == state["inventory"]


@pytest.mark.parametrize("recipe_id", NEW_RECIPES[:4])
def test_new_food_has_two_routes_without_replacing_first_earned_entry(world, recipe_id):
    progress, _ = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    pair, recipe = recipe_pair(world, recipe_id)
    path = f"{BASE}/{state['game_id']}/combine"
    state = post(path, {"a": pair[1], "b": pair[0]})
    assert not state["already_known"] and state["discovered_count"] == 144
    item = next(x for x in state["inventory"] if x["id"] == recipe.result)
    assert [x["id"] for x in item["parents"]] == list(pair)
    assert item["explanation"] == recipe.explanation and item["sources"] == list(recipe.sources)
    other = next(p for p, r in world.recipes.items() if r.result == recipe.result and p != pair)
    for a, b in [pair, other]:
        again = post(path, {"a": a, "b": b})
        assert again["already_known"] and not again["discovered"]
        assert again["progress"] == state["progress"] and again["inventory"] == state["inventory"]
    restored = post(data={"progress": state["progress"]})
    assert restored["inventory"] == state["inventory"]


def test_onward_sandwich_pair_retains_original_sandwich_and_journal(world):
    progress, owned = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    pair, recipe = recipe_pair(world, "sandvis-chiftele-legume")
    assert set(pair) <= owned and recipe.result in owned
    result = post(f"{BASE}/{state['game_id']}/combine", {"a": pair[1], "b": pair[0]})
    assert result["already_known"] and result["discovered_count"] == 143
    assert result["progress"] == state["progress"] and result["inventory"] == state["inventory"]


def test_completed_v95_book_can_finish_two_new_foods_and_restore(world):
    progress, owned = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    def journal(items):
        return {r["id"]: {k: v for k, v in r.items() if k not in ("status", "ready")}
                for r in items if r["id"] in owned}
    old_journal = journal(state["inventory"])
    for recipe_id in ("ostropel-pui-usturoi", "salata-fructe-cutit"):
        pair, _ = recipe_pair(world, recipe_id)
        state = post(f"{BASE}/{state['game_id']}/combine", {"a": pair[0], "b": pair[1]})
    assert state["complete"] and state["discovered_count"] == 145
    assert len(state["inventory"]) == 249
    assert {r["id"] for r in state["inventory"]} - owned == set(NEW_WORDS)
    assert state["progress"]["discoveries"][:143] == progress["discoveries"]
    assert journal(state["inventory"]) == old_journal
    restored = post(data={"progress": state["progress"]})
    assert restored["complete"] and restored["inventory"] == state["inventory"]


def test_old_book_cannot_forge_new_craft_before_upgrade(world):
    progress, owned = checkpoint(world.catalog.compatible_versions[-1])
    pair, _ = recipe_pair(world, "ostropel-pui-usturoi")
    assert set(pair) <= owned
    progress["discoveries"].append(list(pair))
    post(data={"progress": progress}, status=400)
    assert len(E.store) == 0
