"""Finite V1 reserves protect bundled selection without deleting archives."""

from __future__ import annotations

import hashlib
import json
import random
import shutil
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from cat_de_roman_esti.wordgames import release_reserve as reserve
from cat_de_roman_esti.wordgames.derived_catalog import (
    DerivedBoard,
    DerivedCatalog,
    get_derived_catalog,
)
from cat_de_roman_esti.wordgames.packs import DEFAULT_PACK, GAME_KINDS, load_pack
from scripts import build_release_reserve_v1 as builder
from scripts import rank_games_pack as ranking
from tests.current_content import CURRENT_CONTENT

CONTROL = "vi_71e487036cbba4014f67"


def _board(record: dict) -> DerivedBoard:
    return DerivedBoard(**{
        (key if key in {"game", "category", "difficulty", "payload"} else
         "_catalog_id" if key == "id" else "_" + key): value
        for key, value in record.items()
    })


@pytest.fixture(scope="module")
def frozen_boards() -> dict[str, DerivedBoard]:
    raw = json.loads((builder.FIXTURES / "derived_catalog_v38.json").read_bytes())
    return {r["id"]: _board(r) for r in raw["boards"]}


def test_reviewed_manifest_is_reproducible_and_mirrored() -> None:
    blob = builder.render_manifest(builder.build_manifest())
    assert hashlib.sha256(blob).hexdigest() == reserve.MANIFEST_SHA256
    assert all(path.read_bytes().replace(b"\r\n", b"\n") == blob for path in builder.COPIES)
    review = json.loads(builder.QUALITY_REVIEW.read_bytes())
    loaded = reserve.load_reserve()
    assert len(loaded.pack) == 20 and len(loaded.quick) == 3
    assert {r[0] for r in (*loaded.pack, *loaded.quick)} == {
        r["id"] for r in review["items"]
    }
    assert review["reviewer"] != review["author_of_proposals"]


@pytest.mark.parametrize("failure", ["missing", "tampered", "oversized"])
def test_runtime_manifest_fails_closed(tmp_path: Path, failure: str) -> None:
    path = tmp_path / "reserve.json"
    if failure == "tampered":
        path.write_bytes(reserve.RESERVE_PATH.read_bytes() + b" ")
    elif failure == "oversized":
        path.write_bytes(b" " * (reserve.MAX_MANIFEST_BYTES + 1))
    with pytest.raises(ValueError, match="release reserve:"):
        reserve.load_reserve(path)


def test_runtime_manifest_is_self_contained_and_accepts_platform_newlines(tmp_path: Path) -> None:
    path = tmp_path / "reserve.json"
    path.write_bytes(reserve.RESERVE_PATH.read_bytes().replace(b"\r\n", b"\n")
                     .replace(b"\n", b"\r\n"))
    assert reserve.load_reserve(path) == reserve.load_reserve()


@pytest.mark.parametrize("failure", ["self_review", "rejected", "missing", "stale"])
def test_builder_rejects_invalid_independent_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    review = json.loads(builder.QUALITY_REVIEW.read_bytes())
    if failure == "self_review":
        review["reviewer"] = review["author_of_proposals"]
    elif failure == "rejected":
        review["items"][0]["verdict"] = "reject"
    elif failure == "missing":
        review["items"].pop()
    else:
        review["items"][0]["record_sha256"] = "0" * 64
    path = tmp_path / "quality.json"
    blob = builder.render_manifest(review)
    path.write_bytes(blob)
    # Even an intentionally rebound source must pass semantic quality gates.
    monkeypatch.setattr(builder, "QUALITY_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(ValueError, match="release reserve builder:"):
        builder.build_manifest(quality_path=path)


def test_builder_rejects_source_drift_before_writing(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.json"
    proposal.write_bytes(builder.PROPOSAL.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source drift"):
        builder.build_manifest(proposal_path=proposal)
    for name in ("games_pack.json", "derived_catalog_v38.json", "quick_games_v92.json"):
        shutil.copyfile(builder.FIXTURES / name, tmp_path / name)
    pack = json.loads((tmp_path / "games_pack.json").read_bytes())
    held_id, game, _ = reserve.load_reserve().pack[0]
    next(r for r in pack[game] if r["id"] == held_id)["difficulty"] = "hard"
    (tmp_path / "games_pack.json").write_bytes(builder.render_manifest(pack))
    with pytest.raises(ValueError, match="current archived record drift"):
        builder.build_manifest(fixtures=tmp_path)


@pytest.mark.parametrize("failure", ["missing", "duplicate", "changed"])
def test_ranking_gate_rejects_changed_reviewed_pack_record(failure: str) -> None:
    pack = json.loads(DEFAULT_PACK.read_bytes())
    held_id, game, _ = reserve.load_reserve().pack[0]
    record = next(r for r in pack[game] if r["id"] == held_id)
    if failure == "missing":
        pack[game].remove(record)
    elif failure == "duplicate":
        pack[game].append(deepcopy(record))
    else:
        record["difficulty"] = "changed"
    with pytest.raises(ValueError, match="reviewed pack record drift"):
        reserve.validate_pack_reserve(pack)


@pytest.mark.parametrize("previously_exists", [False, True])
def test_manifest_mirror_failure_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, previously_exists: bool,
) -> None:
    first, second = tmp_path / "package.json", tmp_path / "mirror.json"
    if previously_exists:
        first.write_bytes(b"old package")
        second.write_bytes(b"old mirror")
    original_write = builder.atomic_write
    failed = False

    def fail_second_once(path: Path, blob: bytes) -> None:
        nonlocal failed
        if path == second and not failed:
            failed = True
            raise OSError("simulated second-mirror failure")
        original_write(path, blob)

    monkeypatch.setattr(builder, "atomic_write", fail_second_once)
    with pytest.raises(OSError, match="second-mirror"):
        builder.write_copies(b"new", copies=(first, second))
    if previously_exists:
        assert first.read_bytes() == b"old package"
        assert second.read_bytes() == b"old mirror"
    else:
        assert not first.exists() and not second.exists()


@pytest.mark.parametrize("held_id", [row[0] for row in reserve.load_reserve().quick])
def test_every_quick_selection_path_excludes_exact_reviewed_board(
    frozen_boards: dict[str, DerivedBoard], held_id: str,
) -> None:
    held = replace(frozen_boards[held_id], _starter_eligible=True,
                   _starter_score=100, _standard_score=100)
    catalog = DerivedCatalog([held])
    assert catalog.counts()[held.game] == 1  # retained archive
    for filters in ({}, {"category": held.category}, {"difficulty": held.difficulty},
                    {"category": held.category, "difficulty": held.difficulty}):
        assert catalog.pool(held.game, **filters) == []
        assert catalog.pick_daily(held.game, "2026-09-23", **filters) is None
        for starter in (False, True):
            for balanced in (False, True):
                for history in (set(), {held._source_id}):
                    assert catalog.pick_seeded(
                        held.game, random.Random(1), **filters, starter=starter,
                        balance_categories=balanced, exclude_source_ids=history,
                    ) is None


def test_quick_negative_control_and_custom_id_reuse_survive(
    frozen_boards: dict[str, DerivedBoard],
) -> None:
    held = frozen_boards[reserve.load_reserve().quick[0][0]]
    control = frozen_boards[CONTROL]
    assert not reserve.quick_is_reserved(control)
    catalog = DerivedCatalog([
        control, *(frozen_boards[r[0]] for r in reserve.load_reserve().quick),
    ])
    assert catalog.pick_seeded("intrusul", random.Random(3))._catalog_id == CONTROL
    assert catalog.pick_daily("intrusul", "2026-09-23")._catalog_id == CONTROL
    custom = replace(held, payload={**held.payload, "group_label": "Custom distinct puzzle"})
    assert not reserve.quick_is_reserved(custom)
    assert DerivedCatalog([custom]).pick_seeded(custom.game, random.Random(2)) is custom


@pytest.mark.parametrize("game", ["intrusul", "perechi"])
def test_game_level_history_and_starter_fallback_cannot_resurrect_reserve(
    frozen_boards: dict[str, DerivedBoard], monkeypatch: pytest.MonkeyPatch, game: str,
) -> None:
    pytest.importorskip("django")
    from cat_de_roman_esti.wordgames import intrusul, perechi

    held = [replace(frozen_boards[r[0]], _starter_eligible=False)
            for r in reserve.load_reserve().quick if frozen_boards[r[0]].game == game]
    catalog = DerivedCatalog(held)
    sources = {b._source_id for b in held}
    if game == "intrusul":
        assert intrusul._pick_non_daily(
            catalog, random.Random(4), category=held[0].category,
            starter=True, excluded_sources=sources,
        ) is None
    else:
        monkeypatch.setattr(perechi, "get_derived_catalog", lambda: catalog)
        monkeypatch.setattr(perechi, "excluded_pack_ids", lambda *_args: sources)
        chosen, _ = perechi._pick_non_daily(
            object(), random.Random(4), category=held[0].category,
            starter=True, previous_game_id=None,
        )
        assert chosen is None


def test_combined_inventory_distinguishes_storage_from_selection() -> None:
    catalog = get_derived_catalog()
    assert catalog.counts() == CURRENT_CONTENT.quick_counts["by_game"]
    assert {game: len(catalog.pool(game)) for game in catalog.counts()} == (
        CURRENT_CONTENT.quick_selectable_counts["by_game"]
    )
    assert {game: sum(b._standard_score >= 55 for b in catalog.pool(game))
            for game in catalog.counts()} == (
        CURRENT_CONTENT.quick_selectable_counts["preferred_by_game"]
    )
    assert CONTROL in {b._catalog_id for b in catalog.pool("intrusul")}


def test_fresh_rankings_exclude_only_reviewed_pack_stock_on_all_paths(tmp_path: Path) -> None:
    document = ranking.generate_rankings()  # in-memory only; no bundled fixture writes
    expected = reserve.load_reserve().pack_ids
    assert expected <= ranking._owner_demotions()
    rows = {row["id"]: row for row in document["boards"]}
    assert all(rows[item_id]["status"] == "approved"
               and not rows[item_id]["pilot_eligible"] for item_id in expected)
    for item_id in ("al_istorie_035", "al_literatura_005", "al_societate_017"):
        assert rows[item_id]["pilot_eligible"]  # reviewed negative controls stay playable
    sidecar = tmp_path / "rankings.json"
    sidecar.write_bytes(ranking.render_rankings(document))
    pack = load_pack(DEFAULT_PACK, rankings_path=sidecar)
    archived = {item.id for game in GAME_KINDS for item in pack.pool(game)}
    assert expected <= archived
    for game in GAME_KINDS:
        shelves = {(None, None), *((item.category, item.difficulty)
                                  for item in pack.pool(game) if item.id in expected)}
        for category, difficulty in shelves:
            kwargs = {"category": category, "difficulty": difficulty}
            has_selection = pack.selectable_count(game, **kwargs) > 0
            for seed in range(20):
                for history in (set(), archived):
                    chosen = pack.pick_seeded(game, random.Random(seed), **kwargs,
                                              exclude_ids=history, filtered_shelf_weights=True)
                    assert (chosen is not None) == has_selection
                    assert chosen is None or chosen.id not in expected
                daily = pack.pick_daily(game, f"2026-v1-{seed}", **kwargs,
                                        min_pool=1, filtered_shelf_weights=True)
                assert (daily is not None) == has_selection
                assert daily is None or daily.id not in expected
