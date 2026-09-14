"""Preserve V90 history and the exact reviewed Sport seed revision."""

from __future__ import annotations

import dataclasses
import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from cat_de_roman_esti.wordgames import alchimie
from cat_de_roman_esti.wordgames.service import get_service
from tests.content_history import (
    before_v91_artifact,
    before_v92_artifact,
    before_v92_entry_session_artifact,
)
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v91-recovery-and-mobile-clarity"
BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "e32139529aacc88e2f453ac1cee1d8cd9a2cd1b16f3ee0551a5a76779192391e",
    "board_rankings_v37.json": "b5beb978b911c952ef2632cb2d93bc695be19f226b4a4661d77e26b335413fab",
    "derived_catalog_v38.json": "6ac090bc2186bf00209913d1123ba3f54de9f7b02f9fa2a781f2dfcccbbf58a9",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
V92_SESSION_ONE = {
    **BASELINE,
    "games_pack.json": "62c1eaaa7bb72674cf59a66f9b543d911749d52973155f6b201d796d97d6ea4a",
    "board_rankings_v37.json": "6f2662615b686a492b41f2d689a7ba6b380b62d7b8cecc5e7a3c9788d1dce641",
    "derived_catalog_v38.json": "09e6b1caa3ed586264a85d3d9807f0173384c02c80102dae072d14665432f2aa",
}


def read(path):
    return json.loads(path.read_bytes())


@pytest.mark.parametrize("filename", BASELINE)
def test_exact_v90_artifact_inverse_rejects_unreviewed_changes(filename):
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    path = ROOT / directory / filename
    blob = path.read_bytes()
    current = json.loads(blob)
    restored = before_v91_artifact(current, filename)
    indent = 2 if filename == "kg_sample.json" else 1
    restored_blob = (json.dumps(restored, ensure_ascii=False, indent=indent) + "\n").encode()
    assert hashlib.sha256(restored_blob).hexdigest() == BASELINE[filename]
    assert hashlib.sha256(blob).hexdigest() == CURRENT_CONTENT.artifact_sha256[
        str(path.relative_to(ROOT))
    ]
    assert current == json.loads(blob)
    assert blob == (ROOT / "tests/fixtures" / filename).read_bytes()
    for kind in ("head", "row"):
        modified = deepcopy(current)
        if kind == "head":
            head = "manifest" if filename.startswith("cat_mobile") else "meta"
            modified[head]["unreviewed"] = True
        else:
            table = next(key for key, value in modified.items() if isinstance(value, list))
            modified[table][0]["unreviewed"] = True
        with pytest.raises(AssertionError):
            before_v91_artifact(modified, filename)


def test_only_reviewed_sport_seeds_change_and_all_other660_records_remain_exact():
    live = read(ROOT / "cat_de_roman_esti/fixtures/games_pack.json")
    current = before_v92_artifact(live, "games_pack.json")
    previous = before_v91_artifact(live, "games_pack.json")
    proposal = read(REVIEW / "content/replacement-proposal.json")
    changed = []
    total = 0
    for game in ("conexiuni", "contexto", "lant", "alchimie"):
        assert len(current[game]) == len(previous[game])
        for before, after in zip(previous[game], current[game], strict=True):
            total += 1
            assert before["id"] == after["id"]
            if before != after:
                changed.append(after["id"])
                assert before == proposal["before"] and after == proposal["after"]
                assert {key for key in before if before[key] != after[key]} == {"seeds"}
    assert total == 661 and changed == ["al_sport_083"]
    assert current["meta"] == previous["meta"]


def test_live83_recipe_books_match_exact_reviewed_candidate():
    expected = json.loads(gzip.decompress(
        (REVIEW / "content/all-83-books-candidate.json.gz").read_bytes(),
    ))
    pack = read(ROOT / "cat_de_roman_esti/fixtures/games_pack.json")
    svc = get_service()

    def recipe(step):
        pair, outputs = step
        return {
            "pair": list(pair), "pair_labels": [svc.label(n) for n in pair],
            "outputs": list(outputs), "output_labels": [svc.label(n) for n in outputs],
            "actual_edges": [dataclasses.asdict(svc.link(parent, output))
                             for parent in pair for output in outputs],
        }

    actual = {}
    for record in pack["alchimie"]:
        projection = alchimie._build_recipe_projection(
            record["seeds"], record["target"], record["category"],
        )
        actual[record["id"]] = None if projection is None else {
            "par": projection.par,
            "recipes": [recipe(step) for step in projection.recipes.items()],
            "routes": [[recipe(step) for step in route] for route in projection.routes],
            "candidate_quality": projection.candidate_quality,
        }
    assert len(actual) == 83
    assert json.loads(json.dumps(actual)) == expected


@pytest.mark.parametrize("filename", BASELINE)
def test_v92_inverse_restores_exact_reviewed_v91_after_artifact(filename):
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    live = read(ROOT / directory / filename)
    untouched = deepcopy(live)
    current = before_v92_entry_session_artifact(live, filename)
    restored = before_v92_artifact(live, filename)
    receipt = read(REVIEW / "artifact-delta.json")["files"][filename]
    indent = 2 if filename == "kg_sample.json" else 1
    blob = (json.dumps(restored, ensure_ascii=False, indent=indent) + "\n").encode()
    assert hashlib.sha256(blob).hexdigest() == receipt["after_sha256"]
    assert live == untouched
    if filename == "games_pack.json":
        assert {game: len(current[game]) - len(restored[game])
                for game in ("conexiuni", "contexto", "lant", "alchimie")} == {
                    "conexiuni": 4, "contexto": 8, "lant": 13, "alchimie": 0,
                }
        for game in ("conexiuni", "contexto", "lant", "alchimie"):
            live_rows = {row["id"]: row for row in current[game]}
            assert all(row == live_rows[row["id"]] for row in restored[game])
    elif filename == "board_rankings_v37.json":
        assert len(current["boards"]) - len(restored["boards"]) == 25
        live_rows = {row["id"]: row for row in current["boards"]}
        assert sum(row["selection_weight"] != live_rows[row["id"]]["selection_weight"]
                   for row in restored["boards"]) == 35
        for row in restored["boards"]:
            assert {k: v for k, v in row.items() if k not in {"rank", "selection_weight"}} == {
                k: v for k, v in live_rows[row["id"]].items()
                if k not in {"rank", "selection_weight"}
            }
    elif filename == "derived_catalog_v38.json":
        assert current["boards"] == restored["boards"]
        assert len(restored["boards"]) == 336
    else:
        assert current == restored


@pytest.mark.parametrize("change", ["added_row", "missing_added", "rank_weight", "extra_row"])
def test_v92_inverse_rejects_tampering_before_stripping_new_content(change):
    filename = "board_rankings_v37.json" if change == "rank_weight" else "games_pack.json"
    current = read(ROOT / "cat_de_roman_esti/fixtures" / filename)
    if change == "added_row":
        row = next(row for row in current["lant"] if row["id"] == "lt_film_tv_223")
        row["start"] = "n_unreviewed"
    elif change == "missing_added":
        current["conexiuni"] = [r for r in current["conexiuni"] if r["id"] != "cx_limba_364"]
    elif change == "rank_weight":
        row = next(row for row in current["boards"] if row["id"] == "cx_gastronomie_173")
        row["selection_weight"] = 5
    else:
        current["contexto"].append({**current["contexto"][-1], "id": "ct_unreviewed_999"})
    with pytest.raises(AssertionError):
        before_v92_artifact(current, filename)


@pytest.mark.parametrize("filename", V92_SESSION_ONE)
def test_session_two_inverse_restores_complete_c0ead5e_bytes(filename):
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    current = read(ROOT / directory / filename)
    untouched = deepcopy(current)
    restored = before_v92_entry_session_artifact(current, filename)
    indent = 2 if filename == "kg_sample.json" else 1
    blob = (json.dumps(restored, ensure_ascii=False, indent=indent) + "\n").encode()
    assert hashlib.sha256(blob).hexdigest() == V92_SESSION_ONE[filename]
    assert current == untouched
    if filename == "games_pack.json":
        expected = {
            "conexiuni": {"cx_viata_de_roman_368"},
            "contexto": {"ct_geografie_365", "ct_muzica_366", "ct_personalitati_367"},
            "lant": {"lt_literatura_236"},
            "alchimie": set(),
        }
        for game, added in expected.items():
            before = {row["id"]: row for row in restored[game]}
            after = {row["id"]: row for row in current[game]}
            assert set(after) - set(before) == added
            assert all(after[item_id]["status"] == "approved" for item_id in added)
            assert all(row == after[item_id] for item_id, row in before.items())
    elif filename == "board_rankings_v37.json":
        assert len(current["boards"]) - len(restored["boards"]) == 5
    elif filename == "derived_catalog_v38.json":
        assert current["boards"] == restored["boards"]
    else:
        assert current == restored


@pytest.mark.parametrize("change", [
    "new_row", "missing_new_row", "old_row", "rank_weight", "extra_row",
])
def test_session_two_inverse_checks_current_bytes_before_removing_additions(change):
    filename = "board_rankings_v37.json" if change == "rank_weight" else "games_pack.json"
    current = read(ROOT / "cat_de_roman_esti/fixtures" / filename)
    if change == "new_row":
        row = next(row for row in current["lant"] if row["id"] == "lt_literatura_236")
        row["start"] = "n_unreviewed"
    elif change == "missing_new_row":
        current["conexiuni"] = [
            row for row in current["conexiuni"] if row["id"] != "cx_viata_de_roman_368"
        ]
    elif change == "old_row":
        current["alchimie"][0]["unreviewed"] = True
    elif change == "rank_weight":
        current["boards"][0]["selection_weight"] += 1
    else:
        current["contexto"].append({**current["contexto"][-1], "id": "ct_unreviewed_999"})
    with pytest.raises(AssertionError):
        before_v92_entry_session_artifact(current, filename)


def test_session_two_receipt_cannot_be_rebound_to_modified_current_bytes(tmp_path, monkeypatch):
    from tests import content_history

    filename = "games_pack.json"
    current = read(ROOT / "cat_de_roman_esti/fixtures" / filename)
    current["meta"]["unreviewed"] = True
    receipt = read(content_history._V92_ENTRY_SESSION_RECEIPT)
    blob = (json.dumps(current, ensure_ascii=False, indent=1) + "\n").encode()
    receipt["files"][filename]["after_sha256"] = hashlib.sha256(blob).hexdigest()
    receipt["files"][filename]["head_after"]["meta"]["unreviewed"] = True
    path = tmp_path / "modified-receipt.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    monkeypatch.setattr(content_history, "_V92_ENTRY_SESSION_RECEIPT", path)
    with pytest.raises(AssertionError):
        before_v92_entry_session_artifact(current, filename)
