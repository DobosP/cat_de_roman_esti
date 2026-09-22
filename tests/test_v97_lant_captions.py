"""Exact reviewed food captions explain earned steps without creating reverse links."""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import lant
from cat_de_roman_esti.wordgames.lant_relations import REVIEWED_CAPTIONS, caption
from cat_de_roman_esti.wordgames.recipe_extensions import digest, record_snapshot
from cat_de_roman_esti.wordgames.service import get_service

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/reviews/v97-discovery-continuity-and-new-words/integration/captions'
CANDIDATE_SHA = '610f5c85a282a0af6e7d8a9e04829665a6d58a3cdeda38154837e74b7feb72e0'
DRAFT = json.loads((REVIEW / 'drafts.json').read_bytes())
ROWS = DRAFT['items']


def test_v97_exact_caption_approvals_preserve_101_previous_records():
    assert hashlib.sha256((REVIEW / 'drafts.json').read_bytes()).hexdigest() == CANDIDATE_SHA
    before = (REVIEW / 'baseline_lant_relations.py.txt').read_bytes()
    runtime = 'cat_de_roman_esti/wordgames/lant_relations.py'
    assert hashlib.sha256(before).hexdigest() == DRAFT['bindings'][runtime]
    node = next(n.value.args[0] for n in ast.parse(before).body
                if isinstance(n, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == 'REVIEWED_CAPTIONS' for t in n.targets))
    old = ast.literal_eval(node)
    assert len(old) == 101 and len(REVIEWED_CAPTIONS) == 113
    assert all(REVIEWED_CAPTIONS[pair] == value for pair, value in old.items())
    expected = {tuple(row['pair']): row for row in ROWS}
    assert set(REVIEWED_CAPTIONS) - set(old) == set(expected)
    reviewers = []
    for role in ('factual', 'quality'):
        review = json.loads((REVIEW / f'{role}-review.json').read_bytes())
        assert review['candidate_sha256'] == CANDIDATE_SHA and review['role'] == role
        assert review['runtime_source_sha256'] == DRAFT['bindings'][runtime]
        assert review['kg_sha256'] == DRAFT['bindings']['cat_de_roman_esti/fixtures/kg_sample.json']
        reviewers.append(review['reviewer'])
        assert len(review['items']) == 12
        assert {tuple(row['pair']) for row in review['items']} == set(expected)
        for row in review['items']:
            candidate = expected[tuple(row['pair'])]
            assert row['verdict'] == 'accept' and row['caption'] == candidate['caption']
            assert row['edge_sha256'] == candidate['edge_snapshot_sha256']
            assert REVIEWED_CAPTIONS[tuple(row['pair'])] == (row['edge_sha256'], row['caption'])
            assert 0 < len(row['caption']) <= 34
    assert len(set(reviewers)) == 2
    assert sum(row['orientation_review'][direction]['graph_allows']
               for row in ROWS for direction in ('forward', 'reverse')) == 14


@pytest.mark.parametrize('row', ROWS, ids=lambda row: row['id'])
@pytest.mark.parametrize('direction', ['forward', 'reverse'])
def test_v97_earned_relation_survives_get_and_only_existing_directions_work(row, direction):
    orientation = row['orientation_review'][direction]
    a, b = orientation['from'], orientation['to']
    service = get_service()
    edge = service.link(a, b)
    assert (edge is not None) == orientation['graph_allows']
    session = lant.LantSession(start=a, target=b, optimal=1, chain=[a])
    gid = lant.store.create(session)
    client = Client()
    url = f'/api/wordgames/lant/games/{gid}'
    try:
        initial = client.get(url).json()
        assert len(initial['path']) == 1 and initial['moves'] == 0
        response = client.post(url + '/move', {'text': service.label(b)},
                               content_type='application/json')
        assert response.status_code == 200
        state = response.json()
        if edge is None:
            assert caption(service, a, b) == ''
            assert not state['ok']
        else:
            assert digest(record_snapshot(edge)) == row['edge_snapshot_sha256']
            assert state['won'] and state['moves'] == 1 and state['score'] == 1000
            assert state['relation'] == row['caption']
            assert state['path'][-1]['relation'] == row['caption']
        saved = client.get(url).json()
        if edge is None:
            assert not saved['won']
            assert saved['path'] == initial['path'] and saved['moves'] == 0
        else:
            assert saved['path'] == state['path'] and saved['moves'] == state['moves']
        assert row['edge_snapshot_sha256'] not in json.dumps(saved)
    finally:
        lant.store.delete(gid)


@pytest.mark.parametrize('row', ROWS, ids=lambda row: row['id'])
def test_v97_changed_edge_loses_its_reviewed_caption(row):
    orientation = row['orientation_review']['forward']
    a, b = orientation['from'], orientation['to']
    edge = get_service().link(a, b)
    changed = replace(edge, label_ro='new unreviewed claim', relation='related_to')
    fake = SimpleNamespace(link=lambda *_: changed)
    assert caption(fake, a, b) == 'legătură directă'
    fake.link = lambda *_: None
    assert caption(fake, a, b) == ''
