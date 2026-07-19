"""V37 digest-bound rankings and deterministic fun-first curated selection."""

from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from cat_de_roman_esti.data import DEFAULT_FIXTURE
from cat_de_roman_esti.wordgames.packs import (
    DEFAULT_PACK,
    DEFAULT_RUBRIC,
    GAME_KINDS,
    CuratedItem,
    GamesPack,
    load_pack,
    normalized_text_sha256,
)


def _item(
    item_id: str,
    *,
    weight: int = 1,
    eligible: bool = True,
    category: str = "istorie",
    difficulty: str = "normal",
) -> CuratedItem:
    return CuratedItem(
        id=item_id,
        game="contexto",
        category=category,
        difficulty=difficulty,
        source="ai",
        status="approved",
        payload={"target": "n_dacia"},
        _pilot_eligible=eligible,
        _selection_weight=weight,
    )


def _ranking_document() -> dict:
    pack = json.loads(DEFAULT_PACK.read_text(encoding="utf-8"))
    boards = []
    for game in GAME_KINDS:
        for rank, rec in enumerate(pack[game], 1):
            approved = rec["status"] == "approved"
            boards.append(
                {
                    "id": rec["id"],
                    "game": game,
                    "status": rec["status"],
                    "romanian_familiarity": 80 if rank == 1 else 50,
                    "play_quality": 75 if rank == 1 else 50,
                    "pilot_score": 78 if rank == 1 else 50,
                    "rank": rank,
                    "pilot_eligible": approved,
                    "selection_weight": 5 if rank == 1 and approved else 1,
                }
            )
    by_game = {game: len(pack[game]) for game in GAME_KINDS}
    eligible_by_game = {
        game: sum(entry["pilot_eligible"] for entry in boards if entry["game"] == game)
        for game in GAME_KINDS
    }
    counts = {
        "total": sum(by_game.values()),
        "approved": sum(entry["status"] == "approved" for entry in boards),
        "pilot_eligible": sum(eligible_by_game.values()),
        "by_game": by_game,
        "eligible_by_game": eligible_by_game,
    }
    return {
        "meta": {
            "schema_version": 1,
            "pack_sha256": normalized_text_sha256(DEFAULT_PACK),
            "kg_sha256": normalized_text_sha256(DEFAULT_FIXTURE),
            "rubric_sha256": normalized_text_sha256(DEFAULT_RUBRIC),
            "counts": counts,
        },
        "boards": boards,
    }


def _write_rankings(path: Path, document: dict | None = None) -> Path:
    path.write_text(
        json.dumps(document or _ranking_document(), ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def test_digest_bound_sidecar_loads_private_ratings(tmp_path: Path):
    rankings = _write_rankings(tmp_path / "rankings.json")
    pack = load_pack(DEFAULT_PACK, rankings_path=rankings)

    first = min(pack.pool("conexiuni"), key=lambda item: item._pilot_rank or 10_000)
    assert first._romanian_familiarity == 80
    assert first._play_quality == 75
    assert first._pilot_score == 78
    assert first._pilot_rank == 1
    assert first._pilot_eligible is True
    assert first._selection_weight == 5


def test_custom_pack_without_sidecar_keeps_neutral_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("CAT_BOARD_RANKINGS", raising=False)
    custom = tmp_path / "games_pack.json"
    custom.write_text(DEFAULT_PACK.read_text(encoding="utf-8"), encoding="utf-8")
    pack = load_pack(custom)

    item = pack.pool("contexto")[0]
    assert item._pilot_eligible is False
    assert item._selection_weight == 1
    assert item._pilot_rank is None


def test_graph_override_neutralizes_bundled_rankings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("CAT_BOARD_RANKINGS", raising=False)
    rankings = _write_rankings(tmp_path / "rankings.json")
    custom_kg = tmp_path / "kg.json"
    custom_kg.write_text(DEFAULT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(
        "cat_de_roman_esti.wordgames.packs.DEFAULT_RANKINGS", rankings
    )
    monkeypatch.setenv("CAT_KG_FIXTURE", str(custom_kg))

    pack = load_pack(DEFAULT_PACK)
    assert pack.pool("contexto")[0]._pilot_rank is None


def test_explicit_rankings_validate_against_resolved_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    rankings = _write_rankings(tmp_path / "rankings.json")
    custom_kg = tmp_path / "kg.json"
    custom_kg.write_text(DEFAULT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("CAT_KG_FIXTURE", str(custom_kg))

    pack = load_pack(DEFAULT_PACK, rankings_path=rankings)
    assert any(item._pilot_rank is not None for item in pack.pool("contexto"))


def test_ranking_env_override_is_supported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    rankings = _write_rankings(tmp_path / "rankings.json")
    monkeypatch.setenv("CAT_BOARD_RANKINGS", str(rankings))

    pack = load_pack(DEFAULT_PACK)
    assert any(item._pilot_rank is not None for item in pack.pool("contexto"))


def test_rankings_digest_drift_fails_closed(tmp_path: Path):
    document = _ranking_document()
    document["meta"]["pack_sha256"] = "0" * 64
    rankings = _write_rankings(tmp_path / "rankings.json", document)

    with pytest.raises(ValueError, match="pack_sha256"):
        load_pack(DEFAULT_PACK, rankings_path=rankings)


def test_rankings_coverage_drift_fails_closed(tmp_path: Path):
    document = _ranking_document()
    document["boards"].pop()
    rankings = _write_rankings(tmp_path / "rankings.json", document)

    with pytest.raises(ValueError, match="coverage mismatch"):
        load_pack(DEFAULT_PACK, rankings_path=rankings)


def test_rankings_status_drift_fails_closed(tmp_path: Path):
    document = _ranking_document()
    document["boards"][0]["status"] = "pending"
    document["boards"][0]["pilot_eligible"] = False
    rankings = _write_rankings(tmp_path / "rankings.json", document)

    with pytest.raises(ValueError, match="identity/status drift"):
        load_pack(DEFAULT_PACK, rankings_path=rankings)


def test_ineligible_rankings_must_keep_neutral_weight(tmp_path: Path):
    document = _ranking_document()
    first_approved = next(
        entry for entry in document["boards"] if entry["pilot_eligible"] is True
    )
    first_approved["pilot_eligible"] = False
    first_approved["selection_weight"] = 5
    rankings = _write_rankings(tmp_path / "rankings.json", document)

    with pytest.raises(ValueError, match="ineligible item.*selection_weight 1"):
        load_pack(DEFAULT_PACK, rankings_path=rankings)


def test_rankings_meta_schema_is_exact(tmp_path: Path):
    document = _ranking_document()
    document["meta"]["extra"] = "not part of v37"
    rankings = _write_rankings(tmp_path / "rankings.json", document)

    with pytest.raises(ValueError, match="meta fields"):
        load_pack(DEFAULT_PACK, rankings_path=rankings)


def test_rankings_nested_counts_must_match_pack_and_rows(tmp_path: Path):
    document = _ranking_document()
    document["meta"]["counts"]["pilot_eligible"] -= 1
    rankings = _write_rankings(tmp_path / "rankings.json", document)

    with pytest.raises(ValueError, match="counts do not match"):
        load_pack(DEFAULT_PACK, rankings_path=rankings)


def test_neutral_seeded_selection_keeps_historical_choice_sequence():
    items = [
        _item("ct_c", eligible=False),
        _item("ct_a", eligible=False),
        _item("ct_b", eligible=False),
    ]
    pack = GamesPack(items)
    ordered = sorted(items, key=lambda item: item.id)

    for seed in range(100):
        expected = random.Random(seed).choice(ordered)
        assert pack.pick_seeded("contexto", random.Random(seed)).id == expected.id


def test_weighted_seeded_selection_is_deterministic_and_order_independent():
    items = [_item("ct_low", weight=1), _item("ct_high", weight=5)]
    forward = GamesPack(items)
    reverse = GamesPack(list(reversed(items)))

    for seed in range(100):
        left = forward.pick_seeded("contexto", random.Random(seed))
        right = reverse.pick_seeded("contexto", random.Random(seed))
        assert left is not None and right is not None and left.id == right.id


def test_weighted_seeded_selection_favors_high_score_but_keeps_low_reachable():
    pack = GamesPack([_item("ct_low", weight=1), _item("ct_high", weight=5)])
    counts = Counter(
        pack.pick_seeded("contexto", random.Random(seed)).id for seed in range(2_000)
    )

    assert counts["ct_high"] > counts["ct_low"] * 3
    assert counts["ct_low"] > 0


def test_pilot_preference_falls_back_after_filters_and_exclusions():
    preferred = _item("ct_preferred", weight=1, eligible=True)
    reserve = _item("ct_reserve", weight=5, eligible=False)
    other = _item(
        "ct_other", category="geografie", difficulty="greu", eligible=False
    )
    pack = GamesPack([preferred, reserve, other])

    assert {
        pack.pick_seeded("contexto", random.Random(seed)).id for seed in range(40)
    } == {"ct_preferred"}
    picked = pack.pick_seeded(
        "contexto", random.Random(1), exclude_ids={"ct_preferred"}
    )
    assert picked is not None and picked.id == "ct_reserve"
    filtered = pack.pick_seeded(
        "contexto", random.Random(1), category="geografie", difficulty="greu"
    )
    assert filtered is not None and filtered.id == "ct_other"
    assert pack.pick_seeded(
        "contexto", random.Random(1), category="geografie", difficulty="normal"
    ) is None


def test_weighted_daily_is_stable_order_independent_and_keeps_low_reachable():
    items = [_item("ct_low", weight=1), _item("ct_high", weight=5)]
    forward = GamesPack(items)
    reverse = GamesPack(list(reversed(items)))
    counts: Counter[str] = Counter()
    for day in range(2_000):
        key = f"v37-day-{day}"
        left = forward.pick_daily("contexto", key, min_pool=1)
        right = reverse.pick_daily("contexto", key, min_pool=1)
        assert left is not None and right is not None and left.id == right.id
        counts[left.id] += 1

    assert counts["ct_high"] > counts["ct_low"] * 3
    assert counts["ct_low"] > 0


def test_daily_pilot_preference_respects_shared_floor_and_category_minimum():
    preferred = [_item(f"ct_good_{index}") for index in range(8)]
    reserve = _item("ct_reserve", weight=5, eligible=False)

    thin_preferred = GamesPack([*preferred[:7], reserve])
    assert any(
        thin_preferred.pick_daily("contexto", f"thin-{day}").id == reserve.id
        for day in range(200)
    )

    full_preferred = GamesPack([*preferred, reserve])
    assert all(
        full_preferred.pick_daily("contexto", f"full-{day}").id != reserve.id
        for day in range(200)
    )
    assert GamesPack(preferred[:7]).pick_daily("contexto", "too-thin") is None

    themed = GamesPack([preferred[0], reserve])
    assert themed.pick_daily("contexto", "themed", category="istorie").id == preferred[0].id


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(map(str, value))
        for nested in value.values():
            keys |= _all_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            keys |= _all_keys(nested)
    return keys


@pytest.mark.parametrize("game", GAME_KINDS)
def test_private_ranking_fields_never_leak_from_create_responses(game: str, monkeypatch):
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames.packs import get_pack

    module = __import__(f"cat_de_roman_esti.wordgames.{game}", fromlist=[game])
    base = get_pack().pool(game, difficulty="normal")[0]
    ranked = replace(
        base,
        _romanian_familiarity=99,
        _play_quality=98,
        _pilot_score=97,
        _pilot_rank=1,
        _pilot_eligible=True,
        _selection_weight=5,
    )
    monkeypatch.setattr(module, "get_pack", lambda: GamesPack([ranked]))

    response = Client().post(f"/api/wordgames/{game}/games?seed=37&difficulty=normal")
    assert response.status_code == 200
    assert _all_keys(response.json()).isdisjoint(
        {
            "romanian_familiarity",
            "play_quality",
            "pilot_score",
            "rank",
            "pilot_eligible",
            "selection_weight",
            "_romanian_familiarity",
            "_play_quality",
            "_pilot_score",
            "_pilot_rank",
            "_pilot_eligible",
            "_selection_weight",
        }
    )
