"""Bound additive history without dropping a saved book or replacing oversized files."""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy

import pytest
from pydantic import ValidationError

from cat_de_roman_esti.wordgames import discovery_world as D
from scripts import build_alchimie_discovery_world as B


def additive_books(count):
    """Distinct, valid miniature books; each new recipe earns one new concept."""
    raw = json.loads(D.CATALOG_PATH.read_bytes())
    concepts = raw['concepts'][:21]
    ids = [c['id'] for c in concepts]
    recipes = [
        {'id': f'bounded-history-{i}', 'pair': sorted([ids[0], ids[i + 1]]),
         'result': ids[i + 2], 'explanation': 'Synthetic additive history fixture.',
         'sources': ['https://example.org/history']}
        for i in range(19)
    ]
    raw.update(concepts=concepts, recipes=recipes, unlocks=[], goals=[], compatible_versions=[])
    raw['world']['starter_ids'] = ids[:2]
    for size in range(2, count + 2):
        mechanics = D.mechanics_for(ids[:2], {
            tuple(r['pair']): r['result'] for r in recipes[:size]
        }, [])
        raw['compatible_versions'].append({
            'world_id': raw['world']['id'], 'recipe_hash': D.mechanics_hash(mechanics),
            'source_sha256': hashlib.sha256(f'synthetic-book-{size}'.encode()).hexdigest(),
            'mechanics': mechanics,
        })
    return raw


def generator_baseline(monkeypatch, tmp_path, raw):
    previous = deepcopy(raw)
    latest = previous['compatible_versions'].pop()
    pairs = {tuple(r['pair']) for r in latest['mechanics']['recipes']}
    previous['recipes'] = [r for r in previous['recipes'] if tuple(r['pair']) in pairs]
    used = set(previous['world']['starter_ids']) | {r['result'] for r in previous['recipes']}
    previous['concepts'] = [c for c in previous['concepts'] if c['id'] in used]
    D.validate_world(previous, check_graph=False)
    path = tmp_path / 'previous.json'
    path.write_bytes(B.json_bytes(previous))
    monkeypatch.setattr(B, 'BASELINE', path)
    monkeypatch.setattr(B, 'BASELINE_SHA', B.file_sha(path))
    return previous


@pytest.mark.parametrize('count', [8, 9, 16])
def test_valid_distinct_additive_books_fit_both_bounds(monkeypatch, tmp_path, count):
    raw = additive_books(count)
    world = D.validate_world(raw, check_graph=False)
    assert len(world.compatible_versions) == count
    assert len({v.recipe_hash for v in world.catalog.compatible_versions}) == count
    previous = generator_baseline(monkeypatch, tmp_path, raw)
    versions = B.compatible_versions(raw)
    assert versions[:-1] == previous['compatible_versions']
    assert versions[-1]['recipe_hash'] == raw['compatible_versions'][-1]['recipe_hash']
    assert len(versions) == count and len(B.catalog_bytes(raw)) < D.MAX_CATALOG_BYTES


def test_seventeenth_book_is_rejected_without_eviction(monkeypatch, tmp_path):
    raw = additive_books(17)
    with pytest.raises(ValidationError, match='compatible_versions'):
        D.validate_world(raw, check_graph=False)
    previous = generator_baseline(monkeypatch, tmp_path, raw)
    assert len(previous['compatible_versions']) == 16
    untouched = deepcopy(raw)
    with pytest.raises(ValueError, match='invalid compatible history'):
        B.compatible_versions(raw)
    assert raw == untouched


@pytest.mark.parametrize('mutation', ['duplicate', 'world', 'starter', 'result', 'supply', 'hash'])
def test_larger_bound_retains_every_historical_integrity_check(mutation):
    raw = additive_books(16)
    version = raw['compatible_versions'][0]
    if mutation == 'duplicate':
        raw['compatible_versions'][1] = deepcopy(version)
    elif mutation == 'world':
        version['world_id'] = 'other-world'
    elif mutation == 'starter':
        version['mechanics']['starters'][0] = raw['concepts'][-1]['id']
    elif mutation == 'result':
        version['mechanics']['recipes'][0]['result'] = raw['concepts'][-1]['id']
    elif mutation == 'supply':
        version['mechanics']['unlocks'] = [{'after': 1, 'concepts': [raw['concepts'][-1]['id']]}]
    else:
        version['recipe_hash'] = '0' * 64
    if mutation in {'starter', 'result', 'supply'}:
        m = version['mechanics']
        version['mechanics'] = D.mechanics_for(m['starters'], {
            tuple(r['pair']): r['result'] for r in m['recipes']
        }, [(u['after'], u['concepts']) for u in m['unlocks']])
        version['recipe_hash'] = D.mechanics_hash(version['mechanics'])
    with pytest.raises(ValueError):
        D.validate_world(raw, check_graph=False)


@pytest.mark.parametrize('mode', ['candidate', 'proposal', 'install'])
def test_oversized_generator_leaves_every_destination_untouched(monkeypatch, tmp_path, mode):
    raw = additive_books(9)
    # Audit metadata is permitted by Catalog; size must be checked independently.
    raw['oversized_audit_metadata'] = 'x' * D.MAX_CATALOG_BYTES
    D.validate_world(raw, check_graph=False)
    package = tmp_path / 'installed.json'
    candidate = tmp_path / 'candidate.json'
    proposal = tmp_path / 'proposal.json'
    for path in (package, candidate, proposal):
        path.write_bytes(b'previous bytes\n')
    before = {p: p.read_bytes() for p in (package, candidate, proposal)}
    monkeypatch.setattr(B, 'CATALOG', package)
    monkeypatch.setattr(B, 'candidate', lambda: raw)
    monkeypatch.setattr(B, 'build_catalog', lambda *args: raw)
    args = ['build', '--candidate', str(candidate)]
    if mode == 'candidate':
        args += ['--generate-candidate']
    else:
        args += ['--factual-review', 'factual.json', '--quality-review', 'quality.json',
                 '--proposal', str(proposal)]
        if mode == 'install':
            args += ['--write', '--live-audit', 'audit.json',
                     '--final-factual-review', 'final-factual.json',
                     '--final-quality-review', 'final-quality.json']
    monkeypatch.setattr(sys, 'argv', args)
    with pytest.raises(ValueError, match='catalog too large'):
        B.main()
    assert {p: p.read_bytes() for p in before} == before
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(p.name for p in before)


def test_existing_byte_and_content_bounds_are_unchanged():
    assert D.MAX_COMPATIBLE_VERSIONS == B.MAX_COMPATIBLE_VERSIONS == 16
    assert D.MAX_CATALOG_BYTES == B.MAX_CATALOG_BYTES == 2 * 1024 * 1024
    assert (D.MAX_CONCEPTS, D.MAX_RECIPES, D.MAX_SUPPLIES, D.MAX_SUPPLY_TIERS) == (256, 512, 96, 12)
    # Exactly fitting encoded bytes are allowed; the next byte fails closed.
    value = {'padding': ''}
    value['padding'] = 'x' * (D.MAX_CATALOG_BYTES - len(B.json_bytes(value)))
    assert len(B.catalog_bytes(value)) == D.MAX_CATALOG_BYTES
    value['padding'] += 'x'
    with pytest.raises(ValueError, match='catalog too large'):
        B.catalog_bytes(value)
