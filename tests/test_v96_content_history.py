"""V96 additions preserve exact reviewed V95 content and reject forged inverses."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history
from tests.content_history import before_v96_artifact, before_v97_artifact

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "27b1dba81a2e02d1e2616a1ad4e6eceefe12d189a86a0913c3655adee99bb3cf",
    "board_rankings_v37.json": "b4c32d0ff65e024e4bd2e292c03e5382f0927c7c388367bf1f80bd7a3c09a831",
    "derived_catalog_v38.json": "5e27495fcc34980ced41a7bbd5c0b61d703c459489d08d6b7322dac197fd7e96",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
ADDED = {
    "conexiuni": {"cx_viata_de_roman_373"},
    "contexto": {"ct_viata_de_roman_376"},
    "lant": {"lt_gastronomie_245"},
    "alchimie": set(),
}


def read_current(filename):
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    return json.loads((ROOT / directory / filename).read_bytes())


def digest(value, filename):
    blob = (json.dumps(value, ensure_ascii=False,
                       indent=2 if filename == "kg_sample.json" else 1) + "\n").encode()
    return hashlib.sha256(blob).hexdigest()


@pytest.mark.parametrize("filename", BASELINE)
def test_v96_inverse_restores_complete_1457786_bytes_without_mutating_input(filename):
    latest = read_current(filename)
    untouched = deepcopy(latest)
    previous = before_v96_artifact(latest, filename)
    current = before_v97_artifact(latest, filename)
    assert digest(previous, filename) == BASELINE[filename]
    assert latest == untouched
    if filename == "games_pack.json":
        assert sum(len(previous[g]) for g in ADDED) == 710
        for game, added in ADDED.items():
            old = {row["id"]: row for row in previous[game]}
            new = {row["id"]: row for row in current[game]}
            assert set(new) - set(old) == added
            assert all(new[item_id]["status"] == "approved" for item_id in added)
            assert all(new[item_id] == row for item_id, row in old.items())
    elif filename == "board_rankings_v37.json":
        old = {row["id"]: row for row in previous["boards"]}
        new = {row["id"]: row for row in current["boards"]}
        assert len(old) == 710 and set(new) - set(old) == set().union(*ADDED.values())
        for item_id, row in old.items():
            assert {k: v for k, v in row.items() if k not in {"rank", "selection_weight"}} == {
                k: v for k, v in new[item_id].items() if k not in {"rank", "selection_weight"}
            }
    elif filename == "derived_catalog_v38.json":
        assert current["boards"] == previous["boards"] and len(previous["boards"]) == 336
    else:
        assert current == previous


@pytest.mark.parametrize("filename", BASELINE)
@pytest.mark.parametrize("part", ["head", "row"])
def test_v96_inverse_rejects_unreviewed_artifact_bytes(filename, part):
    current = read_current(filename)
    if part == "head":
        head = "manifest" if filename.startswith("cat_mobile") else "meta"
        current[head]["unreviewed"] = True
    else:
        table = next(key for key, value in current.items() if isinstance(value, list))
        current[table][0]["unreviewed"] = True
    with pytest.raises(AssertionError):
        before_v96_artifact(current, filename)


@pytest.mark.parametrize("change", ["remove_added", "modify_added", "extra_row", "rank_weight"])
def test_v96_inverse_checks_additions_and_rank_changes_before_stripping(change):
    filename = "board_rankings_v37.json" if change == "rank_weight" else "games_pack.json"
    current = read_current(filename)
    if change == "remove_added":
        current["conexiuni"] = [r for r in current["conexiuni"]
                                if r["id"] != "cx_viata_de_roman_373"]
    elif change == "modify_added":
        row = next(r for r in current["lant"] if r["id"] == "lt_gastronomie_245")
        row["start"] = "n_unreviewed"
    elif change == "extra_row":
        current["contexto"].append({**current["contexto"][-1], "id": "ct_unreviewed_999"})
    else:
        current["boards"][0]["selection_weight"] += 1
    with pytest.raises(AssertionError):
        before_v96_artifact(current, filename)


def test_v96_receipt_cannot_be_rebound_to_tampered_content(tmp_path, monkeypatch):
    filename = "games_pack.json"
    current = read_current(filename)
    current["meta"]["unreviewed"] = True
    receipt = json.loads(content_history._V96_RECEIPT.read_bytes())
    receipt["files"][filename]["after_sha256"] = digest(current, filename)
    receipt["files"][filename]["head_after"]["meta"]["unreviewed"] = True
    path = tmp_path / "forged-v96-receipt.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    monkeypatch.setattr(content_history, "_V96_RECEIPT", path)
    with pytest.raises(AssertionError):
        before_v96_artifact(current, filename)


def test_v96_keeps_v94_rejection_ledger_exact_and_caraiman_absent():
    path = ROOT / "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json"
    blob = path.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == (
        "01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d"
    )
    ledger = json.loads(blob)
    assert ledger["meta"]["count"] == len(ledger["items"]) == 105
    assert "lt_geografie_242" in ledger["items"]
    pack = before_v97_artifact(read_current("games_pack.json"), "games_pack.json")
    assert pack["meta"]["id_high_water"]["lant"] == 245
    assert "lt_geografie_242" not in {row["id"] for row in pack["lant"]}
    pair = {key: ledger["items"]["lt_geografie_242"][key] for key in ("start", "target")}
    assert pair not in [{key: row[key] for key in ("start", "target")} for row in pack["lant"]]
