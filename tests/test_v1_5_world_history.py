"""V1.5 adds one world item while every historical catalogue stays exact."""

from __future__ import annotations

import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history as history

ROOT = Path(__file__).resolve().parents[1]
WORLD = "alchimie_discovery_world_v92.json"
SOURCE4_WORLD_SHA256 = "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"
SOURCE4_ARCHIVE_SHA256 = "76245d7d5fd3266981c92e3ad7a7e323395b8edd919a4208a56b01bf3bc5f5d3"
SOURCE4_BUNDLE_SHA256 = "d1d3f721525e06f247727d6998bd91a9e38bf26610bde9eba55406dabcfd54c2"


def current() -> dict:
    raw = history.historical_source5_bytes(WORLD)
    assert history._V1_5_WORLD_AFTER_SHA256 is not None, "Final V1.5 pin is required"
    assert hashlib.sha256(raw).hexdigest() == history._V1_5_WORLD_AFTER_SHA256
    return json.loads(raw)


def test_source4_complete_archive_and_original_world_are_immutable():
    raw = history._V1_5_WORLD_BEFORE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE4_WORLD_SHA256
    archive = (ROOT / "go-backend/internal/alchimie_explore/testdata/bundled-v1-4.json.gz")
    compressed = archive.read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == SOURCE4_ARCHIVE_SHA256
    bundle = gzip.decompress(compressed)
    assert len(bundle) <= 8 << 20
    assert hashlib.sha256(bundle).hexdigest() == SOURCE4_BUNDLE_SHA256
    assert json.loads(bundle)["sources"][WORLD] == SOURCE4_WORLD_SHA256


def test_v15_inverse_restores_every_source4_world_byte_without_input_mutation():
    latest = current()
    untouched = deepcopy(latest)
    previous = history.before_v1_5_world_catalog(latest, WORLD)
    assert len(latest["concepts"]) == 252 and len(latest["recipes"]) == 352
    assert len(latest["compatible_versions"]) == 10
    assert len(previous["concepts"]) == 251 and len(previous["recipes"]) == 351
    assert len(previous["compatible_versions"]) == 9
    assert history._v1_3_catalog_digest(previous) == SOURCE4_WORLD_SHA256
    assert latest == untouched and previous is not latest
    twice = history.before_v1_5_world_catalog(previous, WORLD)
    assert twice == previous and twice is not previous


@pytest.mark.parametrize("part", ["binding", "concept", "recipe", "history", "order", "duplicate"])
def test_v15_inverse_rejects_unreviewed_world_fields_order_and_duplicates(part):
    latest = current()
    if part == "binding":
        latest["bindings"]["editorial_source_sha256"] = "0" * 64
    elif part == "concept":
        latest["concepts"][0]["description"] += " forged"
    elif part == "recipe":
        latest["recipes"][0]["result"] = "alw_food_ciocolata_calda"
    elif part == "history":
        latest["compatible_versions"][-1]["source_sha256"] = "0" * 64
    elif part == "order":
        latest["recipes"][0], latest["recipes"][1] = latest["recipes"][1], latest["recipes"][0]
    else:
        latest["concepts"].append(deepcopy(latest["concepts"][0]))
    with pytest.raises(AssertionError):
        history.before_v1_5_world_catalog(latest, WORLD)


def test_v15_inverse_refuses_rebinding_to_a_forged_proposal(monkeypatch):
    latest = current()
    latest["concepts"][0]["description"] += " forged"
    monkeypatch.setattr(history, "_V1_5_WORLD_AFTER_SHA256", history._v1_3_catalog_digest(latest))
    with pytest.raises(AssertionError):
        history.before_v1_5_world_catalog(latest, WORLD)


def test_historical_loader_context_restores_current_path_and_cache(monkeypatch, tmp_path):
    from cat_de_roman_esti.wordgames import discovery_world as loader

    original = loader.CATALOG_PATH
    with history.historical_v1_4_world(monkeypatch, tmp_path / "source4") as world:
        assert loader.CATALOG_PATH == history._V1_5_WORLD_BEFORE
        assert len(world.concepts) == 251 and len(world.recipes) == 351
        assert len(world.catalog.compatible_versions) == 9
    assert loader.CATALOG_PATH == original
    assert loader._load_world.cache_info().currsize == 0
