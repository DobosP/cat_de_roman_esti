"""Player-facing freedom: coherent alternate pairs, exact goals and free misses."""

from itertools import combinations
from urllib.parse import urlencode

from django.test import Client

from cat_de_roman_esti.wordgames import alchimie as A
from cat_de_roman_esti.wordgames.packs import get_pack
from tests.content_scenarios import alchimie_seed


def create(*, seed=38, category=None):
    client = Client()
    query = {"seed": seed, "difficulty": "usor"}
    if category is not None:
        query["category"] = category
    response = client.post(f"/api/wordgames/alchimie/games?{urlencode(query)}")
    assert response.status_code == 200
    state = response.json()
    return client, state, A.store.get(state["game_id"])


def combine(client, game_id, pair):
    response = client.post(
        f"/api/wordgames/alchimie/games/{game_id}/combine",
        {"a": pair[0], "b": pair[1]}, content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()


def test_empty_experiments_and_repeats_do_not_reduce_a_later_perfect_score():
    client, initial, session = create()
    empty = [pair for pair in combinations(initial["inventory"], 2)
             if A._pair_key(pair[0]["id"], pair[1]["id"]) not in session.recipes]
    assert len(empty) >= 3
    for first, second in empty[:3]:
        reply = combine(client, initial["game_id"], (first["id"], second["id"]))
        assert reply["discovered"] == []
        assert "Fără penalizare" in reply["message"]
        assert session.score == 1000
    assert session.moves == 3
    first, second = empty[0]
    repeated = combine(client, initial["game_id"], (second["id"], first["id"]))
    assert repeated["already_tried"] and session.moves == 3
    plan = A._minimum_projected_plan(set(session.owned), session.target, session.recipes)
    assert len(plan) == 2
    for pair in plan:
        final = combine(client, initial["game_id"], pair)
    assert final["won"] and final["score"] == 1000
    assert final["moves"] == 5
    assert "✨" in final["share"]


def test_hints_and_extra_successful_crafts_keep_their_documented_costs():
    session = A.AlchimieSession(seeds=[], target="goal", target_depth=2)
    session.moves = 5
    session.fruitless_total = 2
    assert session.score == 880  # Three productive actions: one beyond par.
    session.hints_used = 1
    assert session.score == 730
    session.moves = 100
    assert session.score == 100


def test_all_football_club_pairs_share_the_same_club_result():
    names = ("Dinamo București", "Rapid București", "FCSB", "CFR Cluj")
    seed = alchimie_seed("al_sport_083", difficulty="usor", category="sport")
    for left, right in combinations(names, 2):
        client, initial, session = create(seed=seed, category="sport")
        assert session.pack_id == "al_sport_083"
        inventory = {item["label"]: item["id"] for item in initial["inventory"]}
        reply = combine(client, initial["game_id"], (inventory[left], inventory[right]))
        assert {item["label"] for item in reply["discovered"]} == {"Club sportiv"}
        assert not reply["won"]
        assert reply["target"]["id"] is None
        assert "recipes" not in reply and "routes" not in reply


def test_every_extended_live_book_retains_the_complete_core_and_exact_par():
    changed = []
    for item in get_pack().pool("alchimie"):
        seeds, target = item.payload["seeds"], item.payload["target"]
        core = A._build_recipe_projection(seeds, target, item.category)
        live = A._build_playable_recipe_projection(seeds, target, item.category)
        assert core and live
        assert live.par == core.par == item.payload["target_depth"]
        assert live.routes == core.routes
        assert all(live.recipes[pair] == outputs for pair, outputs in core.recipes.items())
        assert len(live.recipes) <= A.MAX_RECIPE_PAIRS
        assert all(len(outputs) <= A.MAX_RESULTS_PER_RECIPE for outputs in live.recipes.values())
        core_concepts = set(seeds).union(*(set(outputs) for outputs in core.recipes.values()))
        live_concepts = set(seeds).union(*(set(outputs) for outputs in live.recipes.values()))
        assert live_concepts == core_concepts
        assert len(live_concepts) <= A.MAX_PROJECTED_CONCEPTS
        plan = A._minimum_projected_plan(set(seeds), target, live.recipes)
        assert len(plan) == core.par
        if live.recipes != core.recipes:
            changed.append(item.id)
    assert "al_sport_083" in changed
    assert len(changed) > 1
