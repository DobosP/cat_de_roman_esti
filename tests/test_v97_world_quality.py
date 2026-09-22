"""Two cooked vegetable dishes preserve nine complete historical recipe books."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import alchimie_explore as E
from cat_de_roman_esti.wordgames.discovery_world import MAX_CATALOG_BYTES, get_world, validate_world
from cat_de_roman_esti.wordgames.service import SessionStore, get_service
from scripts import build_alchimie_discovery_world as B
from tests.test_v96_world_quality import HISTORY as OLD_HISTORY
from tests.test_v96_world_quality import checkpoint

ROOT = Path(__file__).resolve().parents[1]
BASE = '/api/alchimie/explore'
PREVIOUS = ROOT / 'docs/reviews/v96-words-and-input-clarity/integration/alchimie'
PREVIOUS_SHA = '6de6b98871c43e539402fff9680474cc31afe22f5b4923c13dbafa9bd5465496'
NEW_WORDS = {'alw_food_supa_rosii': 'Supă de roșii',
             'alw_food_mancare_spanac': 'Mâncare de spanac'}
NEW_RECIPES = ('supa-rosii-supa', 'supa-rosii-orez',
               'mancare-spanac-usturoi', 'mancare-spanac-lapte')
HISTORY = [*OLD_HISTORY, (249, 145, PREVIOUS_SHA)]


@pytest.fixture
def world(monkeypatch):
    current = get_world()
    assert len(current.concepts) == 251 and len(current.recipes) == 351
    monkeypatch.setattr(E, 'store', SessionStore())
    return current


def post(path=BASE, data=None, status=200):
    response = Client().post(path, data or {}, content_type='application/json')
    assert response.status_code == status, response.content
    return response.json()


def recipe_pair(world, recipe_id):
    return next((pair, recipe) for pair, recipe in world.recipes.items() if recipe.id == recipe_id)


def test_v97_retains_exact_prior_records_supplies_goals_and_history():
    blob = (PREVIOUS / 'candidate.json').read_bytes()
    assert hashlib.sha256(blob).hexdigest() == PREVIOUS_SHA
    old, current = json.loads(blob), B.candidate()
    old_concepts = {r['id']: r for r in old['concepts']}
    concepts = {r['id']: r for r in current['concepts']}
    old_recipes = {r['id']: r for r in old['recipes']}
    recipes = {r['id']: r for r in current['recipes']}
    assert len(old_concepts) == 249 and len(old_recipes) == 347
    assert all(concepts[k] == v for k, v in old_concepts.items())
    assert all(recipes[k] == v for k, v in old_recipes.items())
    assert {k: v['label'] for k, v in concepts.items() if k not in old_concepts} == NEW_WORDS
    assert set(recipes) - set(old_recipes) == set(NEW_RECIPES)
    for field in ('world', 'unlocks', 'goals'):
        assert current[field] == old[field]
    assert len(current['compatible_versions']) == 9
    assert current['compatible_versions'][:-1] == old['compatible_versions']
    assert current['compatible_versions'][-1]['source_sha256'] == PREVIOUS_SHA
    assert Counter(r['result'] for r in current['recipes'] if r['result'] in NEW_WORDS) == {
        cid: 2 for cid in NEW_WORDS
    }
    assert not set(NEW_WORDS) & {n for r in current['recipes'] for n in r['pair']}
    assert len(B.json_bytes(current)) < MAX_CATALOG_BYTES
    for cid, label in NEW_WORDS.items():
        concept = concepts[cid]
        assert get_service().resolve(label) is None
        assert concept['origin'] == 'authored' and not concept['redistributable']
        assert concept['description'] == concept['snapshot']['description']
        assert concept['references']


@pytest.mark.parametrize('index,expected', tuple(enumerate(HISTORY)))
def test_nine_previous_books_keep_every_earned_entry(world, index, expected):
    version = world.catalog.compatible_versions[index]
    count, discoveries, source_sha = expected
    assert version.source_sha256 == source_sha
    progress, owned = checkpoint(version)
    assert len(owned) == count and len(progress['discoveries']) == discoveries
    untouched = deepcopy(progress)
    state = post(data={'progress': progress})
    assert progress == untouched and state['progress']['discoveries'] == progress['discoveries']
    assert state['progress']['recipe_hash'] == world.recipe_hash != version.recipe_hash
    assert state['discovered_count'] == discoveries and not state['complete']
    assert owned <= {item['id'] for item in state['inventory']}
    assert Client().get(f"{BASE}/{state['game_id']}").json()['inventory'] == state['inventory']


@pytest.mark.parametrize('recipe_id', NEW_RECIPES)
def test_each_route_works_and_preserves_first_discovery_on_alternate_repeat(world, recipe_id):
    progress, _ = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={'progress': progress})
    pair, recipe = recipe_pair(world, recipe_id)
    path = f"{BASE}/{state['game_id']}/combine"
    state = post(path, {'a': pair[1], 'b': pair[0]})
    assert not state['already_known'] and state['discovered_count'] == 146
    item = next(x for x in state['inventory'] if x['id'] == recipe.result)
    assert [x['id'] for x in item['parents']] == list(pair)
    assert item['explanation'] == recipe.explanation and item['sources'] == list(recipe.sources)
    other = next(p for p, r in world.recipes.items() if r.result == recipe.result and p != pair)
    for a, b in [pair, other]:
        again = post(path, {'a': a, 'b': b})
        assert again['already_known'] and not again['discovered']
        assert again['progress'] == state['progress'] and again['inventory'] == state['inventory']
    assert post(data={'progress': state['progress']})['inventory'] == state['inventory']


@pytest.mark.parametrize('recipe_id', NEW_RECIPES)
def test_old_hash_rejects_each_new_pair_before_upgrade(world, recipe_id):
    progress, owned = checkpoint(world.catalog.compatible_versions[-1])
    pair, _ = recipe_pair(world, recipe_id)
    assert set(pair) <= owned
    progress['discoveries'].append(list(pair))
    post(data={'progress': progress}, status=400)
    assert len(E.store) == 0


def test_unknown_hash_rejected_without_session(world):
    progress, _ = checkpoint(world.catalog.compatible_versions[-1])
    progress['recipe_hash'] = '0' * 64
    post(data={'progress': progress}, status=409)
    assert len(E.store) == 0


def test_completed_v96_book_can_finish_new_foods_and_restore_exact_journal(world):
    progress, owned = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={'progress': progress})
    def journal(items):
        return {r['id']: {k: v for k, v in r.items() if k not in ('status', 'ready')}
                for r in items if r['id'] in owned}
    old_journal = journal(state['inventory'])
    for recipe_id in ('supa-rosii-orez', 'mancare-spanac-lapte'):
        pair, _ = recipe_pair(world, recipe_id)
        state = post(f"{BASE}/{state['game_id']}/combine", {'a': pair[0], 'b': pair[1]})
    assert state['complete'] and state['discovered_count'] == 147
    assert len(state['inventory']) == 251
    assert {r['id'] for r in state['inventory']} - owned == set(NEW_WORDS)
    assert state['progress']['discoveries'][:145] == progress['discoveries']
    assert journal(state['inventory']) == old_journal
    restored = post(data={'progress': state['progress']})
    assert restored['complete'] and restored['inventory'] == state['inventory']


def test_live_v96_upgrade_invalidates_empty_mark_for_new_recipe(world, monkeypatch):
    old = validate_world(json.loads((PREVIOUS / 'proposed-catalog.json').read_bytes()))
    monkeypatch.setattr(E, 'get_world', lambda: old)
    progress, _ = checkpoint(world.catalog.compatible_versions[-1])
    state = post(data={'progress': progress})
    pair, recipe = recipe_pair(world, 'mancare-spanac-usturoi')
    path = f"{BASE}/{state['game_id']}"
    empty = post(path + '/combine', {'a': pair[1], 'b': pair[0]})
    assert empty['empty_pairs'] == [list(pair)] and empty['result'] is None
    monkeypatch.setattr(E, 'get_world', lambda: world)
    upgraded = Client().get(path).json()
    assert upgraded['empty_pairs'] == []
    assert upgraded['progress']['discoveries'] == progress['discoveries']
    assert upgraded['progress']['recipe_hash'] == world.recipe_hash
    result = post(path + '/combine', {'a': pair[0], 'b': pair[1]})
    assert result['result']['id'] == recipe.result and result['discovered_count'] == 146
