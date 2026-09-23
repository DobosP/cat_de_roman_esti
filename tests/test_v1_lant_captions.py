"""Reviewed V1 captions support the promoted schoolbag board on both natural routes."""
from __future__ import annotations

import ast
import gzip
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import lant
from cat_de_roman_esti.wordgames.lant_relations import (
    MAX_CAPTION_LENGTH,
    REVIEWED_CAPTIONS,
    caption,
)
from cat_de_roman_esti.wordgames.recipe_extensions import digest, record_snapshot
from cat_de_roman_esti.wordgames.service import get_service

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v1-testing-release/content"
CANDIDATE_SHA = "4f4e36af80bb232d77b60ec8711f9351f67b9ed49d6fb893420000c2cda35d5a"
PROPOSAL = json.loads((REVIEW / "lt211-caption-proposal.json").read_bytes())
ROWS = PROPOSAL["items"]
BOARD_ID = "lt_viata_de_roman_211"
PACK = json.loads((ROOT / "cat_de_roman_esti/fixtures/games_pack.json").read_bytes())
BOARD = next(row for row in PACK["lant"] if row["id"] == BOARD_ID)


def _registry(blob):
    mapping = next(node.value.args[0] for node in ast.parse(blob).body
                   if isinstance(node, ast.Assign) and any(
                       isinstance(target, ast.Name) and target.id == "REVIEWED_CAPTIONS"
                       for target in node.targets))
    return ast.literal_eval(mapping)


def _board_session():
    return lant.LantSession(
        start=BOARD["start"], target=BOARD["target"], optimal=BOARD["optimal"],
        category=BOARD["category"], difficulty=BOARD["difficulty"],
        pack_id=BOARD_ID, chain=[BOARD["start"]],
    )


def test_v1_installs_only_three_independently_reviewed_captions():
    assert hashlib.sha256((REVIEW / "lt211-caption-proposal.json").read_bytes()).hexdigest() == (
        CANDIDATE_SHA
    )
    baseline = (REVIEW / "baseline_lant_relations.py.txt").read_bytes()
    runtime = "cat_de_roman_esti/wordgames/lant_relations.py"
    assert hashlib.sha256(baseline).hexdigest() == PROPOSAL["bindings"][runtime]
    previous = _registry(baseline)
    assert len(previous) == 117
    assert all(REVIEWED_CAPTIONS[pair] == value for pair, value in previous.items())
    expected = {tuple(row["pair"]): row for row in ROWS}
    assert len(ROWS) == len(expected) == 3
    assert len(REVIEWED_CAPTIONS) == 120
    assert set(REVIEWED_CAPTIONS) - set(previous) == set(expected)
    baseline_kg = gzip.decompress((REVIEW / "kg-before-v1.json.gz").read_bytes())
    assert hashlib.sha256(baseline_kg).hexdigest() == PROPOSAL["bindings"][
        "cat_de_roman_esti/fixtures/kg_sample.json"
    ]
    identities = set()
    for role in ("factual", "quality"):
        review = json.loads((REVIEW / f"lt211-caption-{role}-review.json").read_bytes())
        assert review["role"] == role and review["candidate_sha256"] == CANDIDATE_SHA
        assert review["runtime_source_sha256"] == PROPOSAL["bindings"][runtime]
        assert review["kg_sha256"] == PROPOSAL["bindings"][
            "cat_de_roman_esti/fixtures/kg_sample.json"
        ]
        identities.add(review["reviewer"])
        assert len(review["items"]) == len(expected)
        assert {tuple(row["pair"]) for row in review["items"]} == set(expected)
        assert {row["id"] for row in review["items"]} == {row["id"] for row in ROWS}
        for row in review["items"]:
            candidate = expected[tuple(row["pair"])]
            assert row["id"] == candidate["id"] and row["verdict"] == "accept"
            assert row["caption"] == candidate["caption"]
            assert row["edge_sha256"] == candidate["edge_snapshot_sha256"]
            assert 0 < len(row["caption"]) <= MAX_CAPTION_LENGTH
            assert REVIEWED_CAPTIONS[tuple(row["pair"])] == (
                row["edge_sha256"], row["caption"]
            )
    assert len(identities) == 2 and PROPOSAL["author"] not in identities


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_v1_six_directions_bind_selected_edges_and_restore_paths(row, direction):
    orientation = row["orientation_review"][direction]
    a, b = orientation["from"], orientation["to"]
    service = get_service()
    edge = service.link(a, b)
    assert edge is not None and orientation["graph_allows"]
    assert record_snapshot(edge) == orientation["selected_edge_snapshot"]
    actual_sha = digest(record_snapshot(edge))
    assert actual_sha == orientation["selected_edge_sha256"]
    assert (actual_sha == row["edge_snapshot_sha256"]) == orientation["reviewed_caption_applies"]
    expected = orientation["expected_display_after_install"]
    assert caption(service, a, b) == expected
    if row["id"] == "v1_caption_de8091" and direction == "reverse":
        assert edge.id == "de7579" and expected == "legătură directă"
    else:
        assert orientation["reviewed_caption_applies"] and expected == row["caption"]
    gid = lant.store.create(lant.LantSession(start=a, target=b, optimal=1, chain=[a]))
    client = Client()
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        response = client.post(url + "/move", {"text": service.label(b)},
                               content_type="application/json")
        assert response.status_code == 200
        result = response.json()
        after = client.get(url).json()
        assert result["won"] and result["score"] == 1000
        assert result["relation"] == expected
        assert after["path"] == result["path"] and after["moves"] == 1
        assert after["path"][-1]["relation"] == expected
        assert actual_sha not in json.dumps(after)
    finally:
        lant.store.delete(gid)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_v1_changed_or_missing_edge_cannot_retain_reviewed_caption(row):
    direction = row["orientation_review"]["forward"]
    a, b = direction["from"], direction["to"]
    edge = get_service().link(a, b)
    changed = replace(edge, label_ro="unreviewed replacement", relation="related_to")
    fake = SimpleNamespace(link=lambda *_: changed)
    assert caption(fake, a, b) == "legătură directă"
    fake.link = lambda *_: None
    assert caption(fake, a, b) == ""


@pytest.mark.parametrize("via", ["Carte", "copil"])
def test_v1_promoted_schoolbag_board_is_naturally_selected_and_restores_both_routes(via):
    client = Client()
    response = client.post(
        "/api/wordgames/lant/games?seed=9&category=viata_de_roman&difficulty=usor"
    )
    assert response.status_code == 200
    gid = response.json()["game_id"]
    assert lant.store.get(gid).pack_id == BOARD_ID
    assert BOARD["status"] == "approved"
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        state = client.get(url).json()
        assert state["start"]["label"] == "Ghiozdan"
        assert state["target"]["label"] == "Capra cu trei iezi"
        choices = {choice["label"]: choice["relation"] for choice in state["choices"]}
        assert choices["Carte"] == "carte purtată în ghiozdan"
        assert choices["copil"] == "ghiozdan folosit de școlari"
        for text in ("zzzzzzzzzz", "Ghiozdan", "Capra cu trei iezi"):
            result = client.post(url + "/move", {"text": text},
                                 content_type="application/json").json()
            assert not result["ok"]
            restored = client.get(url).json()
            assert restored["path"] == state["path"] and restored["moves"] == 0
        for index, label in enumerate((via, "Capra cu trei iezi"), 1):
            result = client.post(url + "/move", {"text": label},
                                 content_type="application/json").json()
            assert result["ok"] and result["moves"] == index
            assert result["path"][-1]["relation"] != "legătură directă"
            fetched = client.get(url).json()
            assert fetched["path"] == result["path"] and fetched["moves"] == index
            if index == 1:
                repeated = client.post(url + "/move", {"text": label},
                                       content_type="application/json").json()
                assert not repeated["ok"]
                assert client.get(url).json()["path"] == fetched["path"]
        expected_last = "poveste și carte" if via == "Carte" else "poveste în ediții pentru copii"
        assert result["path"][-1]["relation"] == expected_last
        assert result["won"] and result["score"] == 1000
    finally:
        lant.store.delete(gid)


def test_v1_private_schoolbag_hint_is_earned_and_restored_without_a_hop():
    gid = lant.store.create(_board_session())
    client = Client()
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        state = client.get(url).json()
        hint = client.post(url + "/hint").json()
        assert hint["stage"] == "direction"
        assert hint["relation"] in {
            "carte purtată în ghiozdan", "ghiozdan folosit de școlari"
        }
        saved = client.get(url).json()
        assert saved["earned_hint"] == hint
        assert saved["path"] == state["path"] and saved["moves"] == 0
    finally:
        lant.store.delete(gid)
