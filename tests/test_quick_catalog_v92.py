"""Serving integrity, frozen history and V38 rating parity for reviewed quick boards."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import random
from collections import Counter
from dataclasses import replace
from types import SimpleNamespace

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import intrusul, perechi
from cat_de_roman_esti.wordgames import quick_catalog as Q
from cat_de_roman_esti.wordgames.derived_catalog import (
    get_derived_catalog,
    load_derived_catalog,
)
from cat_de_roman_esti.wordgames.service import SessionStore, WordGameService, get_service
from scripts import build_derived_catalog_v38 as V38

FROZEN_CORE_SHA256 = "b78f069479f99741bf5187db638eebbc476eccf2d914c4a48b072b895446dc29"
REVIEWED_QUICK_SHA256 = "36f5fc575ed5ae36735d792dd71df5860d917dba1b3b58090f792afd4f3b0d39"


@pytest.fixture(autouse=True)
def isolated_catalog_cache():
    get_derived_catalog.cache_clear()
    yield
    get_derived_catalog.cache_clear()


@pytest.fixture
def catalog():
    return json.loads(Q.CATALOG_PATH.read_bytes())


@pytest.fixture(scope="module")
def core():
    return load_derived_catalog()


def _strings(value):
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(_strings(item) for item in value.values())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(_strings(item) for item in value)) if value else set()
    return set()


def test_installed_supplement_preserves_every_frozen_core_field_and_adds_reviewed_stock(core):
    core_rows = json.loads(Q.DEFAULT_DERIVED_CATALOG.read_bytes())["boards"]
    canonical = (json.dumps(core_rows, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    assert hashlib.sha256(canonical.encode()).hexdigest() == FROZEN_CORE_SHA256
    assert len(core_rows) == 336
    assert Q.CATALOG_SHA256 == REVIEWED_QUICK_SHA256
    assert Q.normalized_text_sha256(Q.CATALOG_PATH) == REVIEWED_QUICK_SHA256

    served = get_derived_catalog()
    current = {board._catalog_id: board for board in served._boards}
    # DerivedBoard equality intentionally ignores private fields; compare all fields
    # so an unnoticed ranking/source/identity change cannot pass as preserved stock.
    for original in core._boards:
        assert vars(current[original._catalog_id]) == vars(original)
    additions = [board for board in served._boards if board._source_id.startswith("aq92_")]
    assert Counter(board.game for board in additions) == {"intrusul": 25, "perechi": 20}
    assert served.counts() == {"intrusul": 208, "perechi": 173}
    assert len(current) == len(served._boards) == 381
    assert all(board._standard_score >= 55 for board in additions)


def test_all_shipped_scores_equal_original_v38_derivation(catalog):
    service = get_service()
    kg = json.loads(Q.DEFAULT_FIXTURE.read_bytes())
    old_strengths, linked = V38._edge_maps(kg)
    current_strengths = Q.graph_strengths(service)
    score_fields = (
        "romanian_familiarity", "play_quality", "standard_score",
        "starter_score", "starter_eligible",
    )
    for authored in catalog["authored"]:
        payload = authored["payload"]
        record = {"id": authored["source_id"], "category": authored["category"],
                  "difficulty": authored["difficulty"]}
        if authored["game"] == "intrusul":
            record["groups"] = {"A": payload["members"], "B": [payload["intruder"]]}
            record["group_labels"] = {"A": payload["group_label"], "B": "foreign tile"}
            original = V38._intrusul_candidates([record], service, old_strengths, linked)
        else:
            record["groups"] = {str(i): pair["members"]
                                for i, pair in enumerate(payload["pairs"])}
            record["group_labels"] = {str(i): pair["group_label"]
                                      for i, pair in enumerate(payload["pairs"])}
            original = V38._perechi_candidates([record], service, old_strengths)
        assert len(original) == 1
        rated = Q.rate_board(authored, service, current_strengths)
        assert {key: rated[key] for key in score_fields} == {
            key: original[0][key] for key in score_fields
        }, authored["id"]


def test_perechi_familiarity_keeps_quartile_weight_for_uneven_recognition(catalog):
    row = next(row for row in catalog["authored"] if row["game"] == "perechi")
    service = get_service()
    values = [0.40, 0.44, 0.50, 0.55, 0.80, 0.90, 0.95, 1.0]
    visible = [node for pair in row["payload"]["pairs"] for node in pair["members"]]
    saliences = dict(zip(visible, values, strict=True))
    varied = SimpleNamespace(
        exists=service.exists,
        node=lambda node_id: replace(service.node(node_id), salience=saliences[node_id]),
    )
    actual = Q.rate_board(row, varied, Q.graph_strengths(service))
    legacy = V38._base_row(
        {"id": row["source_id"], "category": row["category"],
         "difficulty": row["difficulty"]}, "perechi", row["payload"], values,
    )
    # Mean-only or Intrusul's 65/35 mix changes this observable rating. The original
    # Perechi 50% mean / 30% lower quartile / 20% minimum gives 56, not 59 or 69.
    assert actual["romanian_familiarity"] == legacy["romanian_familiarity"] == 56


@pytest.mark.parametrize("game,module", [("intrusul", intrusul), ("perechi", perechi)])
def test_real_api_selects_and_solves_an_installed_authored_board(game, module, monkeypatch):
    monkeypatch.setattr(module, "store", SessionStore())
    loaded = get_derived_catalog()
    board = next(board for board in loaded.pool(game)
                 if board._source_id.startswith("aq92_"))
    seed = next(seed for seed in range(5000) if loaded.pick_seeded(
        game, random.Random(seed), category=board.category,
    )._catalog_id == board._catalog_id)
    client = Client()
    root = f"/api/wordgames/{game}/games"
    response = client.post(f"{root}?seed={seed}&category={board.category}")
    assert response.status_code == 200, response.content
    state = response.json()
    game_id = state["game_id"]
    assert module.store.get(game_id).catalog_id == board._catalog_id
    secrets = {board._catalog_id, board._source_id}
    assert not secrets & _strings(state)
    assert "score" not in state and "solution" not in state
    if game == "intrusul":
        assert board.payload["group_label"] not in _strings(state)
        state = client.post(f"{root}/{game_id}/guess", {"id": board.payload["intruder"]},
                            content_type="application/json").json()
    else:
        hidden = {pair["group_label"] for pair in board.payload["pairs"]}
        assert not hidden & _strings(state)
        for pair in board.payload["pairs"]:
            state = client.post(f"{root}/{game_id}/match", {"ids": list(pair["members"])},
                                content_type="application/json").json()
            hidden.discard(pair["group_label"])
            assert not hidden & _strings(state)
    assert state["won"] and state["score"] == 1000
    assert not secrets & _strings(state)
    saved = client.get(f"{root}/{game_id}").json()
    assert saved["won"] and saved["score"] == 1000


@pytest.mark.parametrize("corruption", ["missing", "changed_bytes", "oversized"])
def test_corrupt_supplement_fails_both_apis_without_falling_back_to_core(
    corruption, tmp_path, monkeypatch,
):
    path = tmp_path / "quick.json"
    if corruption == "changed_bytes":
        path.write_bytes(Q.CATALOG_PATH.read_bytes() + b" ")
    elif corruption == "oversized":
        path.write_bytes(b"x" * (Q.MAX_BYTES + 1))
    monkeypatch.setattr(Q, "CATALOG_PATH", path)
    for game in ("intrusul", "perechi"):
        response = Client().post(f"/api/wordgames/{game}/games?seed=38")
        assert response.status_code == 503
        assert "game_id" not in response.json()


@pytest.mark.parametrize("source", [
    "DEFAULT_PACK", "DEFAULT_FIXTURE", "DEFAULT_RUBRIC", "DEFAULT_DERIVED_CATALOG",
])
def test_unchanged_supplement_rejects_current_source_drift(source, core, tmp_path, monkeypatch):
    path = tmp_path / "changed-source"
    path.write_bytes(getattr(Q, source).read_bytes() + b"\n")
    monkeypatch.setattr(Q, source, path)
    with pytest.raises(ValueError, match="source drift"):
        Q.extend_catalog(core)


@pytest.mark.parametrize("field,value", [
    ("source", "https://example.org/forged-provenance"),
    ("redistributable", True),
    ("aliases", ["unreviewed identity"]),
])
def test_record_provenance_cannot_be_changed_under_valid_ratings(catalog, core, field, value):
    node = next(node for node in catalog["nodes"].values() if node[field] != value)
    node[field] = value
    with pytest.raises(ValueError, match="concept provenance drift"):
        Q.validate_catalog(catalog, core)


@pytest.mark.parametrize("malformation", ["three_pairs", "repeated_tile", "nontext_member"])
def test_perechi_payload_cannot_drop_a_pair_or_replace_a_displayed_identity(
    catalog, core, malformation,
):
    row = next(row for row in catalog["authored"] if row["game"] == "perechi")
    pairs = row["payload"]["pairs"]
    if malformation == "three_pairs":
        pairs.pop()
    elif malformation == "repeated_tile":
        pairs[1]["members"][0] = pairs[0]["members"][0]
    else:
        pairs[0]["members"][0] = {"id": pairs[0]["members"][0]}
    with pytest.raises(ValueError):
        Q.validate_catalog(catalog, core)


@pytest.mark.parametrize("change", ["alternative_match", "weak_intended", "zero_intruder_link"])
def test_live_graph_rejects_new_matching_ambiguity_and_even_a_zero_strength_intruder_link(
    catalog, core, change,
):
    kg = json.loads(Q.DEFAULT_FIXTURE.read_bytes())
    game = "intrusul" if change == "zero_intruder_link" else "perechi"
    row = next(row for row in catalog["authored"] if row["game"] == game)
    if change == "zero_intruder_link":
        left, right = row["payload"]["members"][0], row["payload"]["intruder"]
        strength = 0.0
    elif change == "weak_intended":
        left, right = row["payload"]["pairs"][0]["members"]
        strength = 0.59
        kg["kg_edges"] = [edge for edge in kg["kg_edges"]
                          if {edge["src_id"], edge["dst_id"]} != {left, right}]
    else:
        left = row["payload"]["pairs"][0]["members"][0]
        right = row["payload"]["pairs"][1]["members"][0]
        strength = 0.60
    edge = copy.deepcopy(kg["kg_edges"][0])
    edge.update(id="test_quick_added_link", src_id=left, dst_id=right,
                strength=strength, is_distractor=False)
    kg["kg_edges"].append(edge)
    changed = WordGameService(Graph.from_records(kg["kg_nodes"], kg["kg_edges"]))
    message = "intruder has an inlier link" if game == "intrusul" else "ambiguous or weak"
    with pytest.raises(ValueError, match=message):
        Q.validate_catalog(catalog, core, changed)


def test_loaded_payloads_cannot_mutate_the_shared_board_collection(catalog, core):
    added = Q.validate_catalog(catalog, core)
    for board in added:
        with pytest.raises(TypeError):
            board.payload["injected"] = True
        if board.game == "perechi":
            with pytest.raises(TypeError):
                board.payload["pairs"][0]["members"][0] = "changed"
    snapshots = {board._source_id: board for board in added}
    raw = next(row for row in catalog["authored"] if row["game"] == "perechi")
    original = snapshots[raw["source_id"]].payload["pairs"][0]["members"]
    raw["payload"]["pairs"][0]["members"][0] = "changed"
    assert snapshots[raw["source_id"]].payload["pairs"][0]["members"] == original


def test_perechi_shipped_pairs_have_one_strong_perfect_matching(catalog):
    strengths = Q.graph_strengths(get_service())

    def count_matchings(nodes):
        if not nodes:
            return 1
        first, *rest = nodes
        return sum(count_matchings([node for node in rest if node != partner])
                   for partner in rest
                   if strengths.get(frozenset((first, partner)), 0) >= 0.60)

    for row in catalog["authored"]:
        if row["game"] != "perechi":
            continue
        nodes = list(itertools.chain.from_iterable(
            pair["members"] for pair in row["payload"]["pairs"]
        ))
        assert len(nodes) == len(set(nodes)) == 8
        assert count_matchings(nodes) == 1, row["id"]
