"""New V94 recipes preserve old books, reconnect prepared ingredients and retain earned evidence."""

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
PREVIOUS = ROOT / "docs/reviews/v93-words-and-game-quality/alchimie/candidate.json"
PREVIOUS_SHA = "fd6d47853a424695d1c0ebf6c2a94b18196c9ce7e38560f4b7b4dcb1c4e6bbef"
NEW_WORDS = {
    "alw_food_cartofi_gratinati": "Cartofi gratinați",
    "alw_food_chiftele_peste": "Chiftele de pește",
    "alw_food_crochete_cartofi": "Crochete de cartofi",
    "alw_food_jeleu_fructe": "Jeleu de fructe",
    "alw_food_paste_pesto": "Paste cu pesto",
    "alw_food_piure_dovleac": "Piure de dovleac",
    "alw_food_tzatziki": "Tzatziki",
}

HISTORY = [
    (75, 39, "559abb0b475665f73b010b1a0acdc7650576d829819a50a2e99bdd50700f8fae"),
    (111, 58, "fc863ff35cebe88d1b2364fc3693f7d765bb33606d9a3191b1d8532540c37209"),
    (221, 117, "da5a2a1df2790a2cd3f9db0806f8112c7b0ccdb63ed6d7d2e3f418542d4e209a"),
    (221, 117, "ac3408616889175f21cd592b8d71ad0a3f63e95054705da8491097d39c0bf1da"),
    (225, 121, "e77e18626d928b58448869fd444a2623c72209450ef2e4a9effcffcb22fa42e8"),
    (235, 131, PREVIOUS_SHA),
]
NEW_RECIPES = (
    "tzatziki-iaurt-castravete", "tzatziki-sos-iaurt-castravete",
    "cartofi-gratinati-smantana", "cartofi-gratinati-cascaval",
    "crochete-cartofi-pesmet", "crochete-cartofi-cascaval", "paste-pesto-sos",
    "paste-pesto-busuioc", "chiftele-peste-ou", "piure-dovleac-copt-unt",
    "piure-dovleac-cratita", "jeleu-compot-gelatina", "jeleu-fruct-gelatina",
    "supa-crema-piure-dovleac", "placinte-piure-dovleac", "tarta-aluat-jeleu",
    "cascaval-pane-pesmet",
)


@pytest.fixture
def world(monkeypatch):
    world = get_world()
    assert len(world.concepts) == 242 and len(world.recipes) == 332
    monkeypatch.setattr(E, "store", SessionStore())
    return world


def post(path=BASE, data=None, status=200):
    response = Client().post(path, data or {}, content_type="application/json")
    assert response.status_code == status, response.content
    return response.json()


def complete_old_checkpoint(version):
    """Earn only the old book's rules, never borrowing current recipes or supplies."""
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
    return {
        "world_id": version.world_id, "recipe_hash": version.recipe_hash,
        "discoveries": discoveries,
    }, owned


def craft(state, world, recipe_id):
    pair, _ = next((pair, recipe) for pair, recipe in world.recipes.items()
                   if recipe.id == recipe_id)
    return post(f"{BASE}/{state['game_id']}/combine", {"a": pair[1], "b": pair[0]})


def test_additions_preserve_prior_records_and_create_reusable_puree_and_jelly():
    blob = PREVIOUS.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == PREVIOUS_SHA
    old, current = json.loads(blob), B.candidate()
    old_concepts = {c["id"]: c for c in old["concepts"]}
    new_concepts = {c["id"]: c for c in current["concepts"]}
    assert len(old_concepts) == 235
    assert {cid: c["label"] for cid, c in new_concepts.items()
            if cid not in old_concepts} == NEW_WORDS
    assert all(new_concepts[cid] == c for cid, c in old_concepts.items())
    old_recipes = {r["id"]: r for r in old["recipes"]}
    new_recipes = {r["id"]: r for r in current["recipes"]}
    assert len(old_recipes) == 315
    assert set(new_recipes) - set(old_recipes) == set(NEW_RECIPES)
    assert all(new_recipes[rid] == r for rid, r in old_recipes.items())
    for field in ("world", "unlocks", "goals"):
        assert current[field] == old[field]
    assert MAX_CONCEPTS == 256
    assert current["compatible_versions"][:-1] == old["compatible_versions"]
    assert len(current["compatible_versions"]) == 6
    counts = Counter(r["result"] for r in current["recipes"] if r["result"] in NEW_WORDS)
    assert counts == {cid: 1 if cid == "alw_food_chiftele_peste" else 2 for cid in NEW_WORDS}
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
        "alw_food_sos_iaurt", "n_v20gas_compot",
    }
    assert {"alw_food_piure_dovleac", "alw_food_jeleu_fructe"} <= used_now


@pytest.mark.parametrize("index,expected", tuple(enumerate(HISTORY)))
def test_every_previous_book_keeps_completed_progress_and_earned_journal(world, index, expected):
    version = world.catalog.compatible_versions[index]
    old_count, old_discoveries, source_sha = expected
    assert version.source_sha256 == source_sha
    progress, owned = complete_old_checkpoint(version)
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
def test_every_new_recipe_and_alternative_works_in_either_order_without_duplicate_credit(
    world, recipe_id,
):
    progress, _ = complete_old_checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    if recipe_id in {"supa-crema-piure-dovleac", "placinte-piure-dovleac"}:
        state = craft(state, world, "piure-dovleac-cratita")
    if recipe_id == "tarta-aluat-jeleu":
        state = craft(state, world, "jeleu-compot-gelatina")
    pair, recipe = next((pair, r) for pair, r in world.recipes.items() if r.id == recipe_id)
    was_known = recipe.result in {item["id"] for item in state["inventory"]}
    discoveries_before = state["discovered_count"]
    state = craft(state, world, recipe_id)
    assert state["already_known"] is was_known
    assert state["discovered_count"] == discoveries_before + int(not was_known)
    item = next(item for item in state["inventory"] if item["id"] == recipe.result)
    if not was_known:
        assert [parent["id"] for parent in item["parents"]] == list(pair)
        assert item["explanation"] == recipe.explanation and item["sources"] == list(recipe.sources)
    again = post(f"{BASE}/{state['game_id']}/combine", {"a": pair[0], "b": pair[1]})
    assert again["already_known"] and again["discovered"] == []
    assert again["progress"] == state["progress"]
    restored = post(data={"progress": again["progress"]})
    assert restored["progress"] == again["progress"]
    assert restored["inventory"] == again["inventory"]


def test_completed235_book_gains_seven_words_without_losing_its_earned131_entries(world):
    progress, old_owned = complete_old_checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    old_journal = {item["id"]: (item["parents"], item["explanation"], item["sources"])
                   for item in state["inventory"]}
    for recipe_id in (
        "tzatziki-sos-iaurt-castravete", "cartofi-gratinati-smantana",
        "crochete-cartofi-pesmet", "paste-pesto-sos", "chiftele-peste-ou",
        "piure-dovleac-cratita", "jeleu-compot-gelatina",
    ):
        state = craft(state, world, recipe_id)
        assert len(state["discovered"]) == 1
    assert state["complete"] and state["discovered_count"] == 138
    assert len(state["inventory"]) == 242
    assert {item["id"] for item in state["inventory"]} - old_owned == set(NEW_WORDS)
    assert state["progress"]["discoveries"][:131] == progress["discoveries"]
    assert {item["id"]: (item["parents"], item["explanation"], item["sources"])
            for item in state["inventory"] if item["id"] in old_owned} == old_journal
    restored = post(data={"progress": state["progress"]})
    assert restored["complete"] and restored["progress"] == state["progress"]


def test_235_book_cannot_claim_new_recipe_before_upgrade(world):
    progress, owned = complete_old_checkpoint(world.catalog.compatible_versions[-1])
    pair, _ = next((pair, recipe) for pair, recipe in world.recipes.items()
                   if recipe.id == "tzatziki-sos-iaurt-castravete")
    assert set(pair) <= owned
    progress["discoveries"].append(list(pair))
    post(data={"progress": progress}, status=400)
    assert len(E.store) == 0
