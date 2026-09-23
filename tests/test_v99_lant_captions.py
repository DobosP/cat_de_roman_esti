"""Reviewed V99 route explanations preserve directed play and historical evidence."""
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
REVIEW = ROOT / "docs/reviews/v99-refinement-and-discovery/captions"
CANDIDATE_SHA = "1c735c02e88809cc325a64f0a426925814d2b985776d04a0beb9a14274589324"
PROPOSAL = json.loads((REVIEW / "proposal.json").read_bytes())
ROWS = PROPOSAL["items"]


def test_v99_installs_only_independently_reviewed_additions():
    assert hashlib.sha256((REVIEW / "proposal.json").read_bytes()).hexdigest() == CANDIDATE_SHA
    before = (REVIEW / "baseline_lant_relations.py.txt").read_bytes()
    runtime = "cat_de_roman_esti/wordgames/lant_relations.py"
    assert hashlib.sha256(before).hexdigest() == PROPOSAL["bindings"][runtime]
    registry = next(n.value.args[0] for n in ast.parse(before).body
                    if isinstance(n, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == "REVIEWED_CAPTIONS" for t in n.targets))
    previous = ast.literal_eval(registry)
    assert len(previous) == 113
    assert all(REVIEWED_CAPTIONS[pair] == value for pair, value in previous.items())
    expected = {tuple(row["pair"]): row for row in ROWS}
    # V99's exact four-addition claim binds its complete pre-V1 registry.
    historical = (
        ROOT / "docs/reviews/v1-testing-release/content/baseline_lant_relations.py.txt"
    ).read_bytes()
    assert hashlib.sha256(historical).hexdigest() == (
        "5d250a4314955713739411f997054fc3869b62e393a54930a6f194a45eeaba81"
    )
    historical_registry = next(n.value.args[0] for n in ast.parse(historical).body
                               if isinstance(n, ast.Assign) and any(
                                   isinstance(t, ast.Name) and t.id == "REVIEWED_CAPTIONS"
                                   for t in n.targets))
    after_v99 = ast.literal_eval(historical_registry)
    assert len(after_v99) == 117
    assert all(after_v99[pair] == value for pair, value in previous.items())
    assert set(after_v99) - set(previous) == set(expected)
    assert all(REVIEWED_CAPTIONS[pair] == value for pair, value in after_v99.items())
    identities = set()
    for role in ("factual", "quality"):
        review = json.loads((REVIEW / f"{role}-review.json").read_bytes())
        assert review["role"] == role and review["candidate_sha256"] == CANDIDATE_SHA
        assert review["runtime_source_sha256"] == PROPOSAL["bindings"][runtime]
        assert review["kg_sha256"] == PROPOSAL["bindings"][
            "cat_de_roman_esti/fixtures/kg_sample.json"]
        identities.add(review["reviewer"])
        assert len(review["items"]) == len(expected) == 4
        assert {tuple(row["pair"]) for row in review["items"]} == set(expected)
        for row in review["items"]:
            candidate = expected[tuple(row["pair"])]
            assert row["verdict"] == "accept"
            assert row["caption"] == candidate["caption"]
            assert row["edge_sha256"] == candidate["edge_snapshot_sha256"]
            assert REVIEWED_CAPTIONS[tuple(row["pair"])] == (row["edge_sha256"], row["caption"])
    assert len(identities) == 2


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_v99_captions_follow_only_existing_directions_and_survive_get(row, direction):
    orientation = row["orientation_review"][direction]
    a, b = orientation["from"], orientation["to"]
    service = get_service()
    edge = service.link(a, b)
    assert (edge is not None) == orientation["graph_allows"]
    gid = lant.store.create(lant.LantSession(start=a, target=b, optimal=1, chain=[a]))
    client = Client()
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        before = client.get(url).json()
        response = client.post(url + "/move", {"text": service.label(b)},
                               content_type="application/json")
        assert response.status_code == 200
        result = response.json()
        after = client.get(url).json()
        if edge is None:
            assert caption(service, a, b) == ""
            assert not result["ok"] and after["path"] == before["path"]
            assert after["moves"] == 0 and not after["won"]
        else:
            assert digest(record_snapshot(edge)) == row["edge_snapshot_sha256"]
            assert result["won"] and result["score"] == 1000
            assert result["relation"] == row["caption"]
            assert after["path"] == result["path"] and after["moves"] == 1
            assert after["path"][-1]["relation"] == row["caption"]
        assert row["edge_snapshot_sha256"] not in json.dumps(after)
    finally:
        lant.store.delete(gid)


@pytest.mark.parametrize("via", ["Înghețată", "Chec"])
def test_v99_public_cacao_round_explains_both_routes_without_replaying_moves(via):
    client = Client()
    response = client.post("/api/wordgames/lant/games?seed=0&category=gastronomie&difficulty=usor")
    assert response.status_code == 200
    state = response.json()
    gid = state["game_id"]
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        assert lant.store.get(gid).pack_id == "lt_gastronomie_246"
        assert state["start"]["label"] == "Cacao" and state["target"]["label"] == "Lapte"
        choices = {choice["label"]: choice["relation"] for choice in state["choices"]}
        assert choices["Înghețată"] == "înghețată cu aromă de cacao"
        assert choices["Chec"] == "chec în variantă cu cacao"
        for text in ("zzzzzzzzzz", "Cacao"):
            assert not client.post(url + "/move", {"text": text},
                                   content_type="application/json").json()["ok"]
            assert client.get(url).json()["path"] == state["path"]
        for index, label in enumerate((via, "Lapte"), 1):
            result = client.post(url + "/move", {"text": label},
                                 content_type="application/json").json()
            assert result["ok"] and result["moves"] == index
            assert result["path"][-1]["relation"] != "legătură directă"
            fetched = client.get(url).json()
            assert fetched["path"] == result["path"]
            assert fetched["moves"] == result["moves"]
            if index == 1:
                repeat = client.post(url + "/move", {"text": label},
                                     content_type="application/json").json()
                assert not repeat["ok"] and client.get(url).json()["path"] == fetched["path"]
        assert result["won"] and result["score"] == 1000
    finally:
        lant.store.delete(gid)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_v99_changed_or_missing_edge_cannot_retain_reviewed_wording(row):
    direction = row["orientation_review"]["forward"]
    a, b = direction["from"], direction["to"]
    edge = get_service().link(a, b)
    changed = replace(edge, label_ro="unreviewed replacement", relation="related_to")
    fake = SimpleNamespace(link=lambda *_: changed)
    assert caption(fake, a, b) == "legătură directă"
    fake.link = lambda *_: None
    assert caption(fake, a, b) == ""


def test_v99_meaningful_first_hint_is_earned_and_restored_without_a_hop():
    client = Client()
    state = client.post(
        "/api/wordgames/lant/games?seed=0&category=gastronomie&difficulty=usor"
    ).json()
    gid = state["game_id"]
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        assert lant.store.get(gid).pack_id == "lt_gastronomie_246"
        hint = client.post(url + "/hint").json()
        assert hint["stage"] == "direction"
        visible_relations = {choice["relation"] for choice in state["choices"]}
        assert hint["relation"] in visible_relations
        assert hint["relation"] != "legătură directă"
        saved = client.get(url).json()
        assert saved["earned_hint"] == hint
        assert saved["path"] == state["path"] and saved["moves"] == 0
    finally:
        lant.store.delete(gid)
