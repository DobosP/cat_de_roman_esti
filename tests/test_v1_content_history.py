"""V1 reconstructs exact pre-release history while retaining verified live counts."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history as history
from tests.content_history import before_v1_artifact
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "4162c8db2205ac4f250e29e6e94ec1e0212036d6c38de5660991a8bd010204de",
    "board_rankings_v37.json": "23421501b0e4bc391a62d25a577ed9d08c935a9eb48a550ab0e5b2f0e8367acb",
    "derived_catalog_v38.json": "fe88e7265c68a79884eabb257912630722980dccd7238f3a834c6796aa65b400",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
GAMES = ("conexiuni", "contexto", "lant", "alchimie")


def current(filename: str) -> dict:
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    return json.loads((ROOT / directory / filename).read_bytes())


def canonical(value: dict, filename: str) -> bytes:
    return (json.dumps(value, ensure_ascii=False,
                       indent=2 if filename == "kg_sample.json" else 1) + "\n").encode()


def digest(value: dict, filename: str) -> str:
    return hashlib.sha256(canonical(value, filename)).hexdigest()


@pytest.mark.parametrize("filename", BASELINE)
def test_v1_inverse_reconstructs_complete_cc0a6a4_bytes_without_mutation(filename: str) -> None:
    latest = current(filename)
    untouched = deepcopy(latest)
    restored = before_v1_artifact(latest, filename)
    assert digest(restored, filename) == BASELINE[filename]
    assert latest == untouched
    assert restored is not latest


@pytest.mark.parametrize("filename", BASELINE)
@pytest.mark.parametrize("part", ["head", "row"])
def test_v1_inverse_rejects_modified_current_record(filename: str, part: str) -> None:
    latest = current(filename)
    if part == "head":
        latest["manifest" if filename.startswith("cat_mobile") else "meta"]["forged"] = True
    else:
        table = next(key for key, value in latest.items() if isinstance(value, list))
        latest[table][0]["forged"] = True
    with pytest.raises(AssertionError):
        before_v1_artifact(latest, filename)


@pytest.mark.parametrize("repin_receipt", [False, True])
def test_v1_inverse_rejects_forged_receipt_and_rebound_after_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repin_receipt: bool,
) -> None:
    filename = "games_pack.json"
    latest = current(filename)
    latest["lant"][0]["status"] = "pending"
    receipt = json.loads(history._V1_RECEIPT.read_bytes())
    receipt["files"][filename]["after_sha256"] = digest(latest, filename)
    path = tmp_path / "forged.json"
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_RECEIPT", path)
    if repin_receipt:
        monkeypatch.setattr(history, "_V1_RECEIPT_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(AssertionError):
        before_v1_artifact(latest, filename)


def test_v1_inverse_rejects_forged_baseline_even_with_new_receipt_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = json.loads(history._V1_RECEIPT.read_bytes())
    receipt["files"]["kg_sample.json"]["baseline_sha256"] = "0" * 64
    path = tmp_path / "forged-before.json"
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_RECEIPT", path)
    monkeypatch.setattr(history, "_V1_RECEIPT_SHA256", hashlib.sha256(blob).hexdigest())
    with pytest.raises(AssertionError):
        before_v1_artifact(current("kg_sample.json"), "kg_sample.json")


def test_v1_delta_is_only_the_independently_reviewed_graph_and_status_change() -> None:
    kg = current("kg_sample.json")
    old = before_v1_artifact(kg, "kg_sample.json")
    before_nodes = {r["id"]: r for r in old["kg_nodes"]}
    after_nodes = {r["id"]: r for r in kg["kg_nodes"]}
    changed = {key: {field for field in before_nodes[key]
                     if before_nodes[key][field] != after_nodes[key][field]}
               for key in before_nodes if before_nodes[key] != after_nodes[key]}
    assert changed == {
        "n_v20geo_crucea_caraiman": {"description"}, "n_ateneul_roman": {"description"},
        "n_v17art_muzeul_satului": {"description"}, "n_ftv_dem_radulescu": {"degree"},
        "n_ftv_operatiunea_monstrul": {"degree"},
    }
    before_edges = {r["id"]: r for r in old["kg_edges"]}
    after_edges = {r["id"]: r for r in kg["kg_edges"]}
    assert set(before_edges) - set(after_edges) == {"de427"}
    assert not set(after_edges) - set(before_edges)
    assert {key for key in after_edges if after_edges[key] != before_edges[key]} == {
        "de1218", "de2664", "de2665",
    }
    assert old["kg_puzzles"] == kg["kg_puzzles"]
    pack = current("games_pack.json")
    previous = before_v1_artifact(pack, "games_pack.json")
    changed_ids = []
    for game in GAMES:
        assert [r["id"] for r in pack[game]] == [r["id"] for r in previous[game]]
        for before, after in zip(previous[game], pack[game], strict=True):
            if before != after:
                changed_ids.append(after["id"])
                assert before == {**after, "status": "pending"}
                assert after["status"] == "approved"
    assert changed_ids == ["lt_viata_de_roman_211"]


def test_v1_current_snapshot_pins_final_artifacts_and_stored_selectable_counts() -> None:
    from cat_de_roman_esti.wordgames.derived_catalog import get_derived_catalog
    from cat_de_roman_esti.wordgames.packs import load_pack

    for relative, expected in CURRENT_CONTENT.artifact_sha256.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    raw = current("games_pack.json")
    assert Counter(r["status"] for game in GAMES for r in raw[game]) == (
        CURRENT_CONTENT.status_counts
    )
    assert current("board_rankings_v37.json")["meta"]["counts"] == (
        CURRENT_CONTENT.ranking_counts
    )
    pack = load_pack()
    assert {game: pack.selectable_count(game) for game in GAMES} == (
        CURRENT_CONTENT.ranking_counts["eligible_by_game"]
    )
    quick = get_derived_catalog()
    assert quick.counts() == CURRENT_CONTENT.quick_counts["by_game"]
    available = {game: len(quick.pool(game)) for game in quick.counts()}
    assert available == CURRENT_CONTENT.quick_selectable_counts["by_game"]
    assert sum(available.values()) == CURRENT_CONTENT.quick_selectable_counts["total"]
    assert {game: sum(b._standard_score >= 55 for b in quick.pool(game))
            for game in quick.counts()} == CURRENT_CONTENT.quick_selectable_counts[
                "preferred_by_game"
            ]
