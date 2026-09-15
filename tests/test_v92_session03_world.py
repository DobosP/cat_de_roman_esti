"""Session03 discovers actual new words while preserving all four older save formats."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import validate_world
from cat_de_roman_esti.wordgames.service import SessionStore, get_service
from scripts import build_alchimie_discovery_world as B

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/alchimie/explore"
ARCHIVE = ROOT / "docs/reviews/v92-session03-vocabulary-and-interface/alchimie"
ARCHIVE_SHA256 = "e77e18626d928b58448869fd444a2623c72209450ef2e4a9effcffcb22fa42e8"
CATALOG_SHA256 = "b9ff7122f6499d4eea365cc6292249744e34c6576f5f16ca694d9644c19c327f"
PREVIOUS = ROOT / "docs/reviews/v92-entry-creation-and-gui/alchimie/candidate.json"
PREVIOUS_SHA256 = "ac3408616889175f21cd592b8d71ad0a3f63e95054705da8491097d39c0bf1da"
NEW_WORDS = {
    "alw_food_mere_coapte": "Mere coapte",
    "alw_food_ardei_copti": "Ardei copți",
    "alw_food_pilaf_legume": "Pilaf de legume",
    "alw_food_dovleac_copt": "Dovleac copt",
}
NEW_RECIPES = {
    "mere-coapte-cuptor", "ardei-copti-cuptor", "dovleac-copt-cuptor",
    "pilaf-orez-legume", "zacusca-ardei-copti", "supa-crema-dovleac-copt",
}
HISTORY = [
    (75, 39, "559abb0b475665f73b010b1a0acdc7650576d829819a50a2e99bdd50700f8fae"),
    (111, 58, "fc863ff35cebe88d1b2364fc3693f7d765bb33606d9a3191b1d8532540c37209"),
    (221, 117, "da5a2a1df2790a2cd3f9db0806f8112c7b0ccdb63ed6d7d2e3f418542d4e209a"),
    (221, 117, PREVIOUS_SHA256),
]


@pytest.fixture
def world(monkeypatch):
    # Keep the completed V92 session exactly testable after newer world expansions.
    world = validate_world(historical_catalog())
    monkeypatch.setattr(E, "get_world", lambda: world)
    assert len(world.concepts) == 225 and len(world.recipes) == 294
    monkeypatch.setattr(E, "store", SessionStore())
    return world


def session03_candidate():
    blob = (ARCHIVE / "candidate.json").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == ARCHIVE_SHA256
    return json.loads(blob)


def historical_catalog():
    """Reconstruct the exact served V92 bytes from its bound original reviews."""
    catalog = session03_candidate()
    reviews = []
    for role in ("factual", "quality"):
        blob = (ARCHIVE / f"{role}-review.json").read_bytes()
        review = json.loads(blob)
        assert review["candidate_sha256"] == ARCHIVE_SHA256
        assert review["role"] == role and review["world_verdict"] == "accept"
        assert {row["id"] for row in review["items"]} == {
            row["id"] for row in catalog["recipes"]
        }
        assert all(row["verdict"] == "accept" for row in review["items"])
        if role == "factual":
            rows = {row["id"]: row for row in review["items"]}
            for recipe in catalog["recipes"]:
                recipe["sources"] = sorted(set(rows[recipe["id"]]["sources"]))
        reviews.append({"role": role, "reviewer": review["reviewer"],
                        "candidate_sha256": ARCHIVE_SHA256,
                        "sha256": hashlib.sha256(blob).hexdigest()})
    catalog.pop("kind")
    catalog["candidate_sha256"] = ARCHIVE_SHA256
    catalog["reviews"] = reviews
    assert hashlib.sha256(B.json_bytes(catalog)).hexdigest() == CATALOG_SHA256
    return catalog


def previous():
    blob = PREVIOUS.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == PREVIOUS_SHA256
    return json.loads(blob)


def post(path=BASE, data=None, status=200):
    response = Client().post(path, data or {}, content_type="application/json")
    assert response.status_code == status, response.content
    return response.json()


def complete_old_checkpoint(version):
    """Replay only the saved generation's rules, never current recipes or supplies."""
    mechanics = version.mechanics.model_dump()
    owned = set(mechanics["starters"])
    discoveries = []
    while True:
        recipe = next((recipe for recipe in mechanics["recipes"]
                       if set(recipe["pair"]) <= owned and recipe["result"] not in owned), None)
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


def test_four_new_words_preserve_complete_previous_editorial_records_and_bounds(monkeypatch):
    old, current = previous(), session03_candidate()
    monkeypatch.setattr(B, "BASELINE", PREVIOUS)
    monkeypatch.setattr(B, "BASELINE_SHA", PREVIOUS_SHA256)
    assert len(old["concepts"]) == 221 and len(old["recipes"]) == 288
    old_concepts = {row["id"]: row for row in old["concepts"]}
    new_concepts = {row["id"]: row for row in current["concepts"]}
    assert {cid: row["label"] for cid, row in new_concepts.items()
            if cid not in old_concepts} == NEW_WORDS
    assert all(new_concepts[cid] == row for cid, row in old_concepts.items())
    old_recipes = {row["id"]: row for row in old["recipes"]}
    new_recipes = {row["id"]: row for row in current["recipes"]}
    assert set(new_recipes) - set(old_recipes) == NEW_RECIPES
    assert all(new_recipes[rid] == row for rid, row in old_recipes.items())
    for field in ("world", "unlocks", "goals"):
        assert current[field] == old[field]
    audit = B.audit(current)
    assert {key: audit[key] for key in (
        "concepts", "recipes", "discoverable_results", "starters", "supplies", "goals",
    )} == {
        "concepts": 225, "recipes": 294, "discoverable_results": 121,
        "starters": 8, "supplies": 96, "goals": 32,
    }
    assert current["compatible_versions"] == B.compatible_versions(current)
    assert len(current["compatible_versions"]) == 4


def test_new_words_are_craftable_local_definitions_with_preparation_sources(world):
    candidate = session03_candidate()
    concepts = {row["id"]: row for row in candidate["concepts"]}
    recipes = {row["id"]: row for row in candidate["recipes"]}
    supplies = {cid for unlock in world.catalog.unlocks for cid in unlock.concept_ids}
    assert not set(NEW_WORDS) & (supplies | set(world.catalog.world.starter_ids))
    assert set(NEW_WORDS) <= {recipe.result for recipe in world.recipes.values()}
    for cid, label in NEW_WORDS.items():
        assert get_service().resolve(label) is None
        concept = concepts[cid]
        assert concept["origin"] == "authored" and concept["source"] == "authored:alchimie"
        assert concept["description"] == concept["snapshot"]["description"]
        assert concept["references"] == concept["snapshot"]["references"]
        assert concept["references"] and all(B.valid_url(url) for url in concept["references"])
    for rid in NEW_RECIPES:
        assert recipes[rid]["sources"] == B.SOURCE.RECIPE_SOURCES[rid]
        assert recipes[rid]["sources"] and all(B.valid_url(url) for url in recipes[rid]["sources"])
        served = next(recipe for recipe in world.recipes.values() if recipe.id == rid)
        assert served.explanation == recipes[rid]["explanation"] and served.sources
    for new_word, onward_id in (
        ("alw_food_ardei_copti", "zacusca-ardei-copti"),
        ("alw_food_dovleac_copt", "supa-crema-dovleac-copt"),
    ):
        assert new_word in recipes[onward_id]["pair"]


@pytest.mark.parametrize("index,expected", tuple(enumerate(HISTORY)))
def test_completed_predecessor_save_restores_without_losing_earned_words(world, index, expected):
    version = world.catalog.compatible_versions[index]
    old_concepts, old_discoveries, source_sha = expected
    assert version.source_sha256 == source_sha
    progress, old_owned = complete_old_checkpoint(version)
    assert len(old_owned) == old_concepts and len(progress["discoveries"]) == old_discoveries
    untouched = deepcopy(progress)
    state = post(data={"progress": progress})
    assert progress == untouched
    assert state["progress"]["discoveries"] == progress["discoveries"]
    assert state["progress"]["recipe_hash"] == world.recipe_hash != version.recipe_hash
    assert state["discovered_count"] == old_discoveries
    assert old_owned <= {item["id"] for item in state["inventory"]}
    assert not state["complete"]
    assert Client().get(f"{BASE}/{state['game_id']}").json()["progress"] == state["progress"]


def test_completed221_collection_gains_four_real_discoveries_and_keeps_its_journal(world):
    progress, old_owned = complete_old_checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={"progress": progress})
    assert len(old_owned) == 221 and len(state["inventory"]) == 221
    old_journal = {item["id"]: (item["parents"], item["explanation"], item["sources"])
                   for item in state["inventory"]}
    base = f"{BASE}/{state['game_id']}"
    result_ids = set()
    for rid in ("mere-coapte-cuptor", "ardei-copti-cuptor", "dovleac-copt-cuptor",
                "pilaf-orez-legume"):
        pair, recipe = next((pair, recipe) for pair, recipe in world.recipes.items()
                            if recipe.id == rid)
        state = post(base + "/combine", {"a": pair[1], "b": pair[0]})
        assert state["discovered"] == [{"id": recipe.result,
                                        "label": NEW_WORDS[recipe.result]}]
        result_ids.add(recipe.result)
        checkpoint = deepcopy(state["progress"])
        again = post(base + "/combine", {"a": pair[0], "b": pair[1]})
        assert again["already_known"] and again["discovered"] == []
        assert again["progress"] == checkpoint
    assert result_ids == set(NEW_WORDS)
    assert state["complete"] and state["discovered_count"] == 121
    assert len(state["inventory"]) == 225
    assert state["progress"]["discoveries"][:117] == progress["discoveries"]
    assert {item["id"]: (item["parents"], item["explanation"], item["sources"])
            for item in state["inventory"] if item["id"] in old_owned} == old_journal
    restored = post(data={"progress": state["progress"]})
    assert restored["complete"] and restored["progress"] == state["progress"]


def test_old_checkpoint_cannot_claim_new_recipe_even_when_its_inputs_were_owned(world):
    progress, owned = complete_old_checkpoint(world.catalog.compatible_versions[-1])
    pair, _ = next((pair, recipe) for pair, recipe in world.recipes.items()
                   if recipe.id == "mere-coapte-cuptor")
    assert set(pair) <= owned
    progress["discoveries"].append(list(pair))
    post(data={"progress": progress}, status=400)
    assert len(E.store) == 0
