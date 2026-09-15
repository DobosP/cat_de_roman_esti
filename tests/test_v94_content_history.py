"""V94 additions preserve exact reviewed V93 content and reject forged inverses."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history
from tests.content_history import before_v94_artifact, before_v94_lant_ledger, before_v95_artifact

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "573e921cbe54cb482535584a22e55183c4b7add9b0a9a92a1400f9dae4fd01d8",
    "board_rankings_v37.json": "5e29e48a7d684d23d5532f38d80fb996c92d3474744b20a0159111ac7b41bc76",
    "derived_catalog_v38.json": "46360ac6a77fff6cdab2f86500dcadc348243f71bab71eea01111e76bf80f2c4",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
ADDED = {
    "conexiuni": {"cx_viata_de_roman_371"},
    "contexto": {"ct_gastronomie_372", "ct_viata_de_roman_373"},
    "lant": {"lt_gastronomie_241"},
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
def test_v94_inverse_restores_complete_c971846_bytes_without_mutating_input(filename):
    latest = read_current(filename)
    untouched = deepcopy(latest)
    previous = before_v94_artifact(latest, filename)
    # Preserve the original V94 transition after verifying the complete V95 delta.
    current = before_v95_artifact(latest, filename)
    assert digest(previous, filename) == BASELINE[filename]
    assert latest == untouched
    if filename == "games_pack.json":
        assert sum(len(previous[g]) for g in ADDED) == 701
        for game, added in ADDED.items():
            old = {row["id"]: row for row in previous[game]}
            new = {row["id"]: row for row in current[game]}
            assert set(new) - set(old) == added
            assert all(new[item_id]["status"] == "approved" for item_id in added)
            assert all(new[item_id] == row for item_id, row in old.items())
    elif filename == "board_rankings_v37.json":
        old = {row["id"]: row for row in previous["boards"]}
        new = {row["id"]: row for row in current["boards"]}
        assert len(old) == 701 and set(new) - set(old) == set().union(*ADDED.values())
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
def test_v94_inverse_rejects_unreviewed_artifact_bytes(filename, part):
    current = read_current(filename)
    if part == "head":
        head = "manifest" if filename.startswith("cat_mobile") else "meta"
        current[head]["unreviewed"] = True
    else:
        table = next(key for key, value in current.items() if isinstance(value, list))
        current[table][0]["unreviewed"] = True
    with pytest.raises(AssertionError):
        before_v94_artifact(current, filename)


@pytest.mark.parametrize("change", ["remove_added", "modify_added", "extra_row", "rank_weight"])
def test_v94_inverse_checks_additions_and_rank_changes_before_stripping(change):
    filename = "board_rankings_v37.json" if change == "rank_weight" else "games_pack.json"
    current = read_current(filename)
    if change == "remove_added":
        current["conexiuni"] = [r for r in current["conexiuni"]
                                if r["id"] != "cx_viata_de_roman_371"]
    elif change == "modify_added":
        row = next(r for r in current["lant"] if r["id"] == "lt_gastronomie_241")
        row["start"] = "n_unreviewed"
    elif change == "extra_row":
        current["contexto"].append({**current["contexto"][-1], "id": "ct_unreviewed_999"})
    else:
        current["boards"][0]["selection_weight"] += 1
    with pytest.raises(AssertionError):
        before_v94_artifact(current, filename)


def test_v94_receipt_cannot_be_rebound_to_tampered_content(tmp_path, monkeypatch):
    filename = "games_pack.json"
    current = read_current(filename)
    current["meta"]["unreviewed"] = True
    receipt = json.loads(content_history._V94_RECEIPT.read_bytes())
    receipt["files"][filename]["after_sha256"] = digest(current, filename)
    receipt["files"][filename]["head_after"]["meta"]["unreviewed"] = True
    path = tmp_path / "forged-v94-receipt.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    monkeypatch.setattr(content_history, "_V94_RECEIPT", path)
    with pytest.raises(AssertionError):
        before_v94_artifact(current, filename)


def test_v94_rejected_level_reserves_id_and_extends_the_exact_old_ledger():
    from scripts import critique_pack

    path = ROOT / "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json"
    live = json.loads(path.read_bytes())
    untouched = deepcopy(live)
    previous = before_v94_lant_ledger(live)
    assert live == untouched
    assert previous["meta"]["count"] == len(previous["items"]) == 104
    assert live["meta"]["count"] == len(live["items"]) == 105
    assert set(live["items"]) - set(previous["items"]) == {"lt_geografie_242"}
    assert all(live["items"][key] == value for key, value in previous["items"].items())
    assert hashlib.sha256(
        (json.dumps(previous, ensure_ascii=False, indent=1) + "\n").encode(),
    ).hexdigest() == "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
    review = ROOT / "docs/reviews/v94-words-and-clearer-connections/pack"
    dossier = json.loads((review / "dossiers/lt_geografie_242.json").read_bytes())
    gate_path = review / "verdicts/lant_verdicts.json"
    gate = json.loads(gate_path.read_bytes())
    tombstone = live["items"]["lt_geografie_242"]
    assert tombstone["source_gate_sha256"] == hashlib.sha256(gate_path.read_bytes()).hexdigest()
    assert tombstone["record_sha256"] == dossier["record_sha256"]
    assert tombstone["review_binding"] == dossier["review_binding"]
    pair = {"start": dossier["start"]["id"], "target": dossier["target"]["id"]}
    assert tombstone["pair_sha256"] == critique_pack.canonical_json_sha256(pair)
    assert {key: tombstone[key] for key in pair} == pair
    assert gate["verdicts"]["lt_geografie_242"] == "reject"
    assert {row["id"] for row in critique_pack.load_lant_rejection_tombstones()} == set(
        live["items"],
    )
    pack = before_v95_artifact(read_current("games_pack.json"), "games_pack.json")
    assert pack["meta"]["id_high_water"]["lant"] == 242
    assert "lt_geografie_242" not in {row["id"] for row in pack["lant"]}
    assert pair not in [{"start": row["start"], "target": row["target"]}
                        for row in pack["lant"]]


@pytest.mark.parametrize("change", ["old_record", "new_record", "remove", "metadata"])
def test_v94_ledger_inverse_rejects_drift_before_removing_the_new_rejection(change):
    path = ROOT / "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json"
    value = json.loads(path.read_bytes())
    if change == "old_record":
        first = next(key for key in value["items"] if key != "lt_geografie_242")
        value["items"][first]["source_gate_sha256"] = "0" * 64
    elif change == "new_record":
        value["items"]["lt_geografie_242"]["target"] = "n_unreviewed"
    elif change == "remove":
        del value["items"]["lt_geografie_242"]
    else:
        value["meta"]["unreviewed"] = True
    with pytest.raises(AssertionError):
        before_v94_lant_ledger(value)


def test_v94_rejected_visible_description_cannot_return_under_a_new_pack_id(tmp_path):
    from scripts import import_candidates

    directory = tmp_path / "geografie"
    directory.mkdir()
    proposal = {kind: [] for kind in ("nodes", "edges", *ADDED)}
    proposal["lant"] = [{
        "start": "n_v17geo_sfinxul_bucegi", "target": "n_v20geo_crucea_caraiman",
        "difficulty": "usor",
    }]
    blob = (json.dumps(proposal, ensure_ascii=False, indent=2) + "\n").encode()
    binding = "sha256:" + hashlib.sha256(blob).hexdigest()
    (directory / "candidates.json").write_bytes(blob)
    factual = {
        "category": "geografie", "candidate_sha256": binding,
        "reviewed_refs": ["lant[0]"], "issues": [], "coverage_note": "Test fixture only.",
    }
    quality = {
        "category": "geografie", "candidate_sha256": binding,
        "instances": [{"ref": "lant[0]", "verdict": "keep", "note": "Test fixture only."}],
        "coverage_note": "Test fixture only.",
    }
    (directory / "verify_factual.json").write_text(json.dumps(factual))
    (directory / "verify_quality.json").write_text(json.dumps(quality))
    with pytest.raises(SystemExit, match="reuses rejected directed start/target pair"):
        import_candidates.preflight_candidates(tmp_path)
