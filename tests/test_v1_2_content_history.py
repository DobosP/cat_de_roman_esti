"""V1.2 reconstruction preserves full historical bytes and rejects repinned drift."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests import content_history as history

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "kg_sample.json": "1c74e5fe387b20ed196f76588d1ef96658743776817532c09a17ab9dd0a39b64",
    "games_pack.json": "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
    "board_rankings_v37.json": "bf7a88448ce7cb8d21d95defc745517d97c8542f582d66eadbfb92ef54bd4adc",
    "derived_catalog_v38.json": "bea0732aefeb0af59e99c926f893bc9f6bb54bae3bb371eace238872470ac2a4",
    "cat_mobile_app_pack_contract.json": (
        "82304733284ca62245e0d2ac0abb7b81c991ed1857ca904c990116c5bce280b4"
    ),
}
AFTER = {
    "kg_sample.json": "c9f23c4a9dab1281ad91baaf0e2c836a5b7ab9a6d5f2776799908d76e10f4b85",
    "games_pack.json": "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
    "board_rankings_v37.json": "96409c88927a60e9d6d379237af88a57aef6b40279520bf54f64214017b45806",
    "derived_catalog_v38.json": "1340147300b3d9d174e09d899ac8eaf91756ca0470d0550121af66751ea92d71",
    "cat_mobile_app_pack_contract.json": (
        "8735d304a7d9734a53c03307c034093c910c1a931e73c40df346ed25700f1438"
    ),
}


def current(filename: str) -> dict:
    directory = "tests/fixtures" if filename.startswith("cat_mobile") else (
        "cat_de_roman_esti/fixtures"
    )
    return json.loads((ROOT / directory / filename).read_bytes())


def digest(value: dict, filename: str) -> str:
    blob = (json.dumps(value, ensure_ascii=False,
                       indent=2 if filename == "kg_sample.json" else 1) + "\n").encode()
    return hashlib.sha256(blob).hexdigest()


def replace_receipt(
    receipt: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, repin: bool = True,
) -> None:
    path = tmp_path / "forged-v1-2.json"
    blob = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    path.write_bytes(blob)
    monkeypatch.setattr(history, "_V1_2_RECEIPT", path)
    if repin:
        monkeypatch.setattr(history, "_V1_2_RECEIPT_SHA256", hashlib.sha256(blob).hexdigest())


@pytest.mark.parametrize("filename", BASELINE)
def test_v1_2_inverse_restores_complete_baseline_bytes_without_mutation(filename: str) -> None:
    latest = current(filename)
    untouched = deepcopy(latest)
    restored = history.before_v1_2_artifact(latest, filename)
    assert digest(latest, filename) == AFTER[filename]
    assert digest(restored, filename) == BASELINE[filename]
    assert latest == untouched and restored is not latest


@pytest.mark.parametrize("filename", BASELINE)
def test_v1_2_exact_inverse_roundtrip_retains_rows_and_native_serialization(filename: str) -> None:
    latest = current(filename)
    restored = history.before_v1_2_artifact(latest, filename)
    receipt = json.loads(history._V1_2_RECEIPT.read_bytes())["files"][filename]
    forward = deepcopy(restored)
    for table, changes in receipt["tables"].items():
        rows = {r["id"]: r for r in forward[table]}
        for row_id, change in changes["changed"].items():
            assert rows[row_id] == change["before"]
            rows[row_id] = deepcopy(change["after"])
        forward[table] = [rows[r["id"]] for r in forward[table]]
        forward[table].extend(deepcopy(changes["added"]))
    forward.update(deepcopy(receipt["head_after"]))
    if filename.startswith("cat_mobile"):
        # Public product snapshots sort edges by ID; the KG source appends its new edge.
        forward["kg_edges"].sort(key=lambda row: row["id"])
    if filename in {"board_rankings_v37.json", "derived_catalog_v38.json"}:
        # Native output sorts dictionary keys; its semantic rows remain exact.
        forward = json.loads(json.dumps(forward, ensure_ascii=False, sort_keys=True))
        assert restored["boards"] == latest["boards"]
    assert forward == latest
    assert digest(forward, filename) == AFTER[filename]


@pytest.mark.parametrize("filename", BASELINE)
@pytest.mark.parametrize("part", ["head", "row"])
def test_v1_2_inverse_refuses_current_row_or_head_drift(filename: str, part: str) -> None:
    latest = current(filename)
    if part == "head":
        latest["manifest" if filename.startswith("cat_mobile") else "meta"]["forged"] = True
    else:
        table = next(k for k, value in latest.items() if isinstance(value, list))
        latest[table][0]["forged"] = True
    untouched = deepcopy(latest)
    with pytest.raises(AssertionError):
        history.before_v1_2_artifact(latest, filename)
    assert latest == untouched


@pytest.mark.parametrize("repin", [False, True])
def test_v1_2_inverse_refuses_forged_receipt_and_rebound_after_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repin: bool,
) -> None:
    latest = current("games_pack.json")
    latest["lant"][0]["status"] = "pending"
    receipt = json.loads(history._V1_2_RECEIPT.read_bytes())
    receipt["files"]["games_pack.json"]["after_sha256"] = digest(latest, "games_pack.json")
    replace_receipt(receipt, tmp_path, monkeypatch, repin=repin)
    with pytest.raises(AssertionError):
        history.before_v1_2_artifact(latest, "games_pack.json")


def test_v1_2_inverse_refuses_repinned_baseline_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = json.loads(history._V1_2_RECEIPT.read_bytes())
    receipt["files"]["kg_sample.json"]["baseline_sha256"] = "0" * 64
    replace_receipt(receipt, tmp_path, monkeypatch)
    with pytest.raises(AssertionError):
        history.before_v1_2_artifact(current("kg_sample.json"), "kg_sample.json")


@pytest.mark.parametrize("forgery", ["neutral-row", "neutral-order", "review", "scope"])
def test_v1_2_inverse_refuses_repinned_scope_even_with_unchanged_artifact_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, forgery: str,
) -> None:
    receipt = json.loads(history._V1_2_RECEIPT.read_bytes())
    latest = current("kg_sample.json")
    if forgery == "neutral-row":
        row = next(r for r in latest["kg_nodes"] if r["id"] == "n_ateneul_roman")
        receipt["files"]["kg_sample.json"]["tables"]["kg_nodes"]["changed"][row["id"]] = {
            "before": deepcopy(row), "after": deepcopy(row),
        }
    elif forgery == "neutral-order":
        receipt["files"]["kg_sample.json"]["tables"]["kg_puzzles"]["baseline_order"] = [
            r["id"] for r in latest["kg_puzzles"]
        ]
    elif forgery == "review":
        receipt["review_bindings"]["graph_quality_sha256"] = "0" * 64
    else:
        receipt["scope"] = "Unreviewed broader scope"
    replace_receipt(receipt, tmp_path, monkeypatch)
    with pytest.raises(AssertionError):
        history.before_v1_2_artifact(latest, "kg_sample.json")


def test_v1_2_inverse_rejects_duplicate_baseline_dictionary_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orders = deepcopy(history._V1_2_KEY_ORDERS)
    orders["board_rankings_v37.json"][""] = (("meta", "boards", "boards"),)
    monkeypatch.setattr(history, "_V1_2_KEY_ORDERS", orders)
    with pytest.raises(AssertionError):
        history.before_v1_2_artifact(current("board_rankings_v37.json"), "board_rankings_v37.json")


def test_v1_2_inverse_refuses_unknown_artifact() -> None:
    with pytest.raises(AssertionError):
        history.before_v1_2_artifact({}, "unknown.json")
