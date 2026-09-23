"""Reviewed relationship wording stays truthful in both directions and after resume."""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.lant_relations import REVIEWED_CAPTIONS, caption
from cat_de_roman_esti.wordgames.service import get_service

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v94-words-and-clearer-connections/captions"
CANDIDATE_SHA = "eb129bc088c20a498b0470484650177066fb382d84c845bf94067cb845ffce4f"
BATCHES = [(REVIEW, CANDIDATE_SHA), (REVIEW / "new-rounds",
           "56d9dbb83e167484a1dacb639f9134b3af0d75e2479f1f3f8cc525fa5188a227")]
ROWS = [row for directory, _ in BATCHES
        for row in json.loads((directory / "candidates.json").read_bytes())["captions"]]


def test_v94_caption_approvals_bind_exact_additions_and_preserve_all_old_records():
    # Reconstruct the exact landed V94 registry; later additions must preserve it.
    prior = (ROOT / "docs/reviews/v97-discovery-continuity-and-new-words/integration"
             "/captions/baseline_lant_relations.py.txt").read_bytes()
    assert hashlib.sha256(prior).hexdigest() == (
        "04196f152d541ec4175cf007c62fbfa338bd82b4b87428438bc05a765d7401b1"
    )
    registry_node = next(n.value.args[0] for n in ast.parse(prior).body
                         if isinstance(n, ast.Assign) and any(
                             isinstance(t, ast.Name) and t.id == "REVIEWED_CAPTIONS"
                             for t in n.targets))
    historical = ast.literal_eval(registry_node)
    assert all(REVIEWED_CAPTIONS[pair] == value for pair, value in historical.items())
    raw = (REVIEW / "candidates.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CANDIDATE_SHA
    candidate = json.loads(raw)
    before = (REVIEW / "baseline_lant_relations.py.txt").read_bytes()
    assert hashlib.sha256(before).hexdigest() == candidate["runtime_source_sha256"]
    node = next(n.value.args[0] for n in ast.parse(before).body
                if isinstance(n, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "REVIEWED_CAPTIONS" for t in n.targets))
    old = ast.literal_eval(node)
    assert len(old) == 80 and len(historical) == 101
    assert all(historical[pair] == value for pair, value in old.items())
    assert set(historical) - set(old) == {tuple(row["pair"]) for row in ROWS}
    for directory, candidate_sha in BATCHES:
        raw = (directory / "candidates.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == candidate_sha
        candidates = json.loads(raw)["captions"]
        identities = []
        for role in ("factual", "quality"):
            review = json.loads((directory / f"{role}-review.json").read_bytes())
            assert review["candidate_sha256"] == candidate_sha and review["role"] == role
            identities.append(review["reviewer"])
            assert len(review["items"]) == len(candidates)
            assert {tuple(row["pair"]) for row in review["items"]} == {
                tuple(row["pair"]) for row in candidates
            }
            for row in review["items"]:
                assert row["verdict"] == "accept"
                assert REVIEWED_CAPTIONS[tuple(row["pair"])] == (
                    row["edge_sha256"], row["caption"],
                )
        assert len(set(identities)) == 2



@pytest.mark.parametrize("row", ROWS, ids=lambda row: "+".join(row["pair"]))
@pytest.mark.parametrize("reverse", [False, True])
def test_v94_relationship_is_earned_and_resumes_in_each_direction(row, reverse):
    a, b = reversed(row["pair"]) if reverse else row["pair"]
    service = get_service()
    session = L.LantSession(start=a, target=b, optimal=1, chain=[a])
    gid = L.store.create(session)
    client = Client()
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        result = client.post(url + "/move", {"text": service.label(b)},
                             content_type="application/json")
        assert result.status_code == 200
        state = result.json()
        assert state["won"] and state["score"] == 1000 and state["moves"] == 1
        assert state["relation"] == row["caption"]
        assert state["path"][-1]["relation"] == row["caption"]
        fetched = client.get(url).json()
        assert fetched["path"] == state["path"] and fetched["score"] == 1000
        assert row["edge_sha256"] not in json.dumps(fetched)
        assert client.post(url + "/move", {"text": service.label(a)},
                           content_type="application/json").status_code == 200
        assert client.get(url).json() == fetched
    finally:
        L.store.delete(gid)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: "+".join(row["pair"]))
def test_v94_changed_snapshot_cannot_keep_an_approved_relationship(row):
    service = get_service()
    a, b = row["pair"]
    edge = service.link(a, b)
    changed = replace(edge, label_ro="unreviewed relationship", relation="related_to")
    fake = SimpleNamespace(link=lambda *_: changed)
    assert caption(fake, a, b) == "legătură directă"
    assert caption(fake, b, a) == "legătură directă"
    fake.link = lambda *_: None
    assert caption(fake, a, b) == ""
