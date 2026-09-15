"""V95 desserts preserve old collections and give prepared ingredients onward uses."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import MAX_CONCEPTS, get_world
from cat_de_roman_esti.wordgames.service import SessionStore, get_service
from scripts import build_alchimie_discovery_world as B

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/alchimie/explore"
PREVIOUS = ROOT / "docs/reviews/v94-words-and-clearer-connections/alchimie/candidate.json"
PREVIOUS_SHA = "d6432638a94e1ec2a422ec5ed54b060309fa1bb2cfdc1660fa8c4a8d90365188"
NEW_WORDS = {
    "alw_food_negresa": "Negresă",
    "alw_food_crema_zahar_ars": "Cremă de zahăr ars",
    "alw_food_budinca_paste": "Budincă de paste",
    "alw_food_pavlova": "Pavlova",
    "alw_food_profiterol": "Profiterol",
}
HISTORY = [
    (75, 39, "559abb0b475665f73b010b1a0acdc7650576d829819a50a2e99bdd50700f8fae"),
    (111, 58, "fc863ff35cebe88d1b2364fc3693f7d765bb33606d9a3191b1d8532540c37209"),
    (221, 117, "da5a2a1df2790a2cd3f9db0806f8112c7b0ccdb63ed6d7d2e3f418542d4e209a"),
    (221, 117, "ac3408616889175f21cd592b8d71ad0a3f63e95054705da8491097d39c0bf1da"),
    (225, 121, "e77e18626d928b58448869fd444a2623c72209450ef2e4a9effcffcb22fa42e8"),
    (235, 131, "fd6d47853a424695d1c0ebf6c2a94b18196c9ce7e38560f4b7b4dcb1c4e6bbef"),
    (242, 138, PREVIOUS_SHA),
]
NEW_RECIPES = (
    "negresa-faina-cacao", "negresa-ciocolata-unt",
    "crema-zahar-ars-caramel-ou", "crema-zahar-ars-caramel-lapte",
    "budinca-paste-branza-ou", "budinca-paste-stafide",
    "pavlova-bezea-frisca", "pavlova-bezea-fruct",
    "profiterol-oparit-inghetata", "profiterol-oparit-ganache",
)


@pytest.fixture
def world(monkeypatch):
    world = get_world()
    assert len(world.concepts) == 247 and len(world.recipes) == 342
    monkeypatch.setattr(E, "store", SessionStore())
    return world


def post(path=BASE, data=None, status=200):
    response = Client().post(path, data or {}, content_type="application/json")
    assert response.status_code == status, response.content
    return response.json()


def checkpoint(version):
    mechanics = version.mechanics.model_dump()
    owned = set(mechanics["starters"])
    discoveries = []
    while True:
        recipe = next((r for r in mechanics["recipes"]
                       if set(r["pair"]) <= owned and r["result"] not in owned), None)
        if recipe is None:
            break
        owned.add(recipe["result"])
        discoveries.append(recipe["pair"])
        for unlock in mechanics["unlocks"]:
            if len(discoveries) >= unlock["after"]:
                owned.update(unlock["concepts"])
    return {"world_id": version.world_id, "recipe_hash": version.recipe_hash,
            "discoveries": discoveries}, owned


def craft(state, world, recipe_id):
    pair = next(pair for pair, recipe in world.recipes.items() if recipe.id == recipe_id)
    return post(f"{BASE}/{state['game_id']}/combine", {"a": pair[1], "b": pair[0]})


def test_author_candidate_preserves_v94_and_reuses_two_previous_leaves():
    blob = PREVIOUS.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == PREVIOUS_SHA
    old, current = json.loads(blob), B.candidate()
    old_concepts = {c["id"]: c for c in old["concepts"]}
    new_concepts = {c["id"]: c for c in current["concepts"]}
    assert len(old_concepts) == 242
    assert {cid: c["label"] for cid, c in new_concepts.items()
            if cid not in old_concepts} == NEW_WORDS
    assert all(new_concepts[cid] == c for cid, c in old_concepts.items())
    old_recipes = {r["id"]: r for r in old["recipes"]}
    new_recipes = {r["id"]: r for r in current["recipes"]}
    assert len(old_recipes) == 332
    assert set(new_recipes) - set(old_recipes) == set(NEW_RECIPES)
    assert all(new_recipes[rid] == r for rid, r in old_recipes.items())
    for field in ("world", "unlocks", "goals"):
        assert current[field] == old[field]
    assert MAX_CONCEPTS == 256
    assert current["compatible_versions"][:-1] == old["compatible_versions"]
    assert len(current["compatible_versions"]) == 7
    assert Counter(r["result"] for r in current["recipes"] if r["result"] in NEW_WORDS) == {
        cid: 2 for cid in NEW_WORDS
    }
    for cid in NEW_WORDS:
        concept = new_concepts[cid]
        assert get_service().resolve(concept["label"]) is None
        assert concept["origin"] == "authored" and concept["source"] == "authored:alchimie"
        assert concept["description"] == concept["snapshot"]["description"]
        assert concept["references"] == concept["snapshot"]["references"]
        assert concept["references"] and not concept["redistributable"]
    used_before = {cid for r in old["recipes"] for cid in r["pair"]}
    results_before = {r["result"] for r in old["recipes"]}
    used_now = {cid for r in current["recipes"] for cid in r["pair"]}
    assert (results_before - used_before) & used_now == {
        "alw_food_bezea", "alw_food_paste_branza",
    }


@pytest.mark.parametrize("index,expected", tuple(enumerate(HISTORY)))
def test_seven_older_books_keep_all_earned_entries(world, index, expected):
    version = world.catalog.compatible_versions[index]
    old_count, old_discoveries, source_sha = expected
    assert version.source_sha256 == source_sha
    progress, owned = checkpoint(version)
    assert len(owned) == old_count and len(progress["discoveries"]) == old_discoveries
    untouched = deepcopy(progress)
    state = post(data={"progress": progress})
    assert progress == untouched
    assert state["progress"]["discoveries"] == progress["discoveries"]
    assert state["progress"]["recipe_hash"] == world.recipe_hash != version.recipe_hash
    assert state["discovered_count"] == old_discoveries and not state["complete"]
    assert owned <= {item["id"] for item in state["inventory"]}
    resumed = Client().get(f"{BASE}/{state['game_id']}").json()
    assert resumed["progress"] == state["progress"]
    assert resumed["inventory"] == state["inventory"]


@pytest.mark.parametrize("recipe_id", NEW_RECIPES)
def test_new_routes_work_both_ways_and_preserve_original_journal(world, recipe_id):
    progress, _ = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    pair, recipe = next((pair, r) for pair, r in world.recipes.items() if r.id == recipe_id)
    count_before = state["discovered_count"]
    state = craft(state, world, recipe_id)
    assert not state["already_known"]
    assert state["discovered_count"] == count_before + 1
    item = next(item for item in state["inventory"] if item["id"] == recipe.result)
    assert [parent["id"] for parent in item["parents"]] == list(pair)
    assert item["explanation"] == recipe.explanation and item["sources"] == list(recipe.sources)
    again = post(f"{BASE}/{state['game_id']}/combine", {"a": pair[0], "b": pair[1]})
    assert again["already_known"] and again["discovered"] == []
    assert again["progress"] == state["progress"]
    alternate = next(r for p, r in world.recipes.items()
                     if r.result == recipe.result and p != pair)
    alternate_state = craft(again, world, alternate.id)
    assert alternate_state["already_known"] and alternate_state["discovered"] == []
    assert alternate_state["progress"] == state["progress"]
    assert alternate_state["inventory"] == state["inventory"]
    restored = post(data={"progress": alternate_state["progress"]})
    assert restored["progress"] == state["progress"]
    assert restored["inventory"] == state["inventory"]


def test_completed242_book_earns_five_desserts_and_preserves_138_recipe_entries(world):
    progress, old_owned = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    old_journal = {item["id"]: (item["parents"], item["explanation"], item["sources"])
                   for item in state["inventory"]}
    for recipe_id in NEW_RECIPES[::2]:
        state = craft(state, world, recipe_id)
        assert len(state["discovered"]) == 1
    assert state["complete"] and state["discovered_count"] == 143
    assert len(state["inventory"]) == 247
    assert {item["id"] for item in state["inventory"]} - old_owned == set(NEW_WORDS)
    assert state["progress"]["discoveries"][:138] == progress["discoveries"]
    assert {item["id"]: (item["parents"], item["explanation"], item["sources"])
            for item in state["inventory"] if item["id"] in old_owned} == old_journal
    restored = post(data={"progress": state["progress"]})
    assert restored["complete"] and restored["progress"] == state["progress"]


def test_v94_book_cannot_claim_v95_recipe_before_upgrade(world):
    progress, owned = checkpoint(world.catalog.compatible_versions[-1])
    pair = next(pair for pair, recipe in world.recipes.items()
                if recipe.id == "pavlova-bezea-frisca")
    assert set(pair) <= owned
    progress["discoveries"].append(list(pair))
    post(data={"progress": progress}, status=400)
    assert len(E.store) == 0
