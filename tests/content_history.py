"""Reverse reviewed deltas when checking earlier content-wave history."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v80-clatite-target/artifact-delta.json"
)
_V81_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v81-nuca-feedback/artifact-delta.json"
)
_V82_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v82-playable-content-batch/artifact-delta.json"
)
_V83_REVIEW = Path(__file__).resolve().parents[1] / "docs/reviews/v83-food-input-and-feedback"
_V84_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v84-six-game-graph-quality/artifact-delta.json"
)
_V85_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v85-ingredient-feedback-and-board-clarity/artifact-delta.json"
)
_V86_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v86-preparation-and-route-quality/artifact-delta.json"
)
_V87_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v87-snack-and-action-quality/artifact-delta.json"
)
_V88_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v88-cross-game-quality/artifact-delta.json"
)

_V89_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v89-feedback-and-conexiuni-recovery/artifact-delta.json"
)

_V90_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v90-household-discovery-and-critique-gates/artifact-delta.json"
)

_V91_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v91-recovery-and-mobile-clarity/artifact-delta.json"
)

_V92_ENTRY_SESSION_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v92-entry-creation-and-gui/artifact-delta.json"
)
# Pin the generated receipt as well as complete artifacts on both sides of its delta.
_V92_ENTRY_SESSION_RECEIPT_SHA256 = (
    "9133bcdef3ad91679208a9b60ef690aaa6df58b0333242ac65a70b8af16f732b"
)
_V92_ENTRY_SESSION_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_368"},
    "contexto": {"ct_geografie_365", "ct_muzica_366", "ct_personalitati_367"},
    "lant": {"lt_literatura_236"},
    "alchimie": set(),
}

_V92_SESSION03_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v92-session03-vocabulary-and-interface/artifact-delta.json"
)
# Pin the complete final receipt independently of every before/after artifact hash.
_V92_SESSION03_RECEIPT_SHA256 = (
    "8c990bc5645400e83b18bda92157dddeef45a18f9d66f1648c1ece7a9b29fd6c"
)
_V92_SESSION03_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "9c0a8fde33742ad5230d1697fe7617eabfc8a257a6409562e3b0357c0b8fc77b",
    "board_rankings_v37.json": "cdc148bfc95c9791b8b941b7c537a04b72d8d21398e1b258cf8e743ac9bdbde5",
    "derived_catalog_v38.json": "931278ac590aa1d4904e15d4a30990a349fe82af09cbbb1b9c1a3e3c1461671a",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V92_SESSION03_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_369"},
    "contexto": {"ct_istorie_368", "ct_literatura_369"},
    "lant": {"lt_arta_cultura_237", "lt_istorie_238"},
    "alchimie": set(),
}



_V93_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v93-words-and-game-quality/artifact-delta.json"
)
_V93_RECEIPT_SHA256 = "4fad0ef7db0131ed1e74bd881506dc2b9d86e6b09bc5c6832ba19f29292518f5"
_V93_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "02b966eacaa851a9b20c4f36e0ee50c217e49670553da462313b16830b2c13e6",
    "board_rankings_v37.json": "e467823999d6b20bd0abeb6a41ceb239faaf7c600afe7d9df3adfc65daad3b12",
    "derived_catalog_v38.json": "de2f46a72c23e5ecbd496d3a4314a48f0d4f636b71aa5ba4662bccc837298449",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V93_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_370"},
    "contexto": {"ct_gastronomie_370", "ct_gastronomie_371"},
    "lant": {"lt_geografie_239", "lt_literatura_240"},
    "alchimie": set(),
}

_V94_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v94-words-and-clearer-connections/artifact-delta.json"
)
_V94_RECEIPT_SHA256 = "803fd0860796c54159df54fd486c80c16d4e78f5133ee151162745c8569202a1"
_V94_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "573e921cbe54cb482535584a22e55183c4b7add9b0a9a92a1400f9dae4fd01d8",
    "board_rankings_v37.json": "5e29e48a7d684d23d5532f38d80fb996c92d3474744b20a0159111ac7b41bc76",
    "derived_catalog_v38.json": "46360ac6a77fff6cdab2f86500dcadc348243f71bab71eea01111e76bf80f2c4",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V94_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_371"},
    "contexto": {"ct_gastronomie_372", "ct_viata_de_roman_373"},
    "lant": {"lt_gastronomie_241"},
    "alchimie": set(),
}
_V94_LEDGER_SHA256 = "01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_V94_REJECTED_LANT = {
    "record_sha256": "a23970fe742c5674a07bc3b5c3eda183f9f3e61355974d3a231daa31168af5b5",
    "pair_sha256": "2b3185659e407d75fd4940708cf77460138141b9a67c952caf3e6ba6bf067401",
    "review_binding": "sha256:31c5fd57edeb74888ae689ebcfc430d8dc4150d6bdb975dc7e9ec5719007adb3",
    "source_gate_sha256": "bf30221d7d4f87c090d1f7c60c2d2e34dff2cabc3dde747e83c014c95f65047a",
    "start": "n_v17geo_sfinxul_bucegi",
    "target": "n_v20geo_crucea_caraiman",
}

_V95_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v95-discovery-and-game-quality/artifact-delta.json"
)
_V95_RECEIPT_SHA256 = "7672de9ef287a7808a12d77d11183b0b3741f6d969998ec026de9367f7fe47e1"
_V95_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "7d28b9df887fe561150bc582f390df0dde4f8c292e5550055bbe84e9e8d90990",
    "board_rankings_v37.json": "82f128edb3ccdd8208d41c43b7eb77df1e8d528d2aaea1fed5972712047255ed",
    "derived_catalog_v38.json": "4088402b80b78946e6f9cb7ee5379c9c3f32438801611008f266101625bb428d",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V95_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_372"},
    "contexto": {"ct_viata_de_roman_374", "ct_viata_de_roman_375"},
    "lant": {"lt_gastronomie_243", "lt_gastronomie_244"},
    "alchimie": set(),
}


_V96_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v96-words-and-input-clarity/artifact-delta.json"
)
_V96_RECEIPT_SHA256 = "703f7da7adb78213c2958eb45f4769122a8bb3020312bf45d5f89708b6305666"
_V96_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "27b1dba81a2e02d1e2616a1ad4e6eceefe12d189a86a0913c3655adee99bb3cf",
    "board_rankings_v37.json": "b4c32d0ff65e024e4bd2e292c03e5382f0927c7c388367bf1f80bd7a3c09a831",
    "derived_catalog_v38.json": "5e27495fcc34980ced41a7bbd5c0b61d703c459489d08d6b7322dac197fd7e96",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V96_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_373"},
    "contexto": {"ct_viata_de_roman_376"},
    "lant": {"lt_gastronomie_245"},
    "alchimie": set(),
}


_V97_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v97-discovery-continuity-and-new-words/artifact-delta.json"
)
_V97_RECEIPT_SHA256 = "b7e6a500524eb31c78b0b8a9fd05ed60bcb990657d7fd2af73e91b3ef64683ec"
_V97_BASELINE = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "f2538a91726da87a519f8efac5d3a9993a8a23445879af817f08bdabd478e307",
    "board_rankings_v37.json": "bee608938a113922842ec987bf44269ae086f45aaeb9c54f68e39c8f160bd9d3",
    "derived_catalog_v38.json": "9c46598b19acd30e82cf7bf542c82b8fcfe5039f607bc689ef27a98e78e3d76c",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V97_ADDED_IDS = {
    "conexiuni": {"cx_viata_de_roman_374"},
    "contexto": {"ct_viata_de_roman_377"},
    "lant": {"lt_gastronomie_246"},
    "alchimie": set(),
}


# The V92 expansion adds exactly 4 Conexiuni, 8 Contexto and 13 Lanț records.
# Pin complete current bytes before peeling it; never replace historical wave hashes.
_V92_ARTIFACT_HASHES = {
    "kg_sample.json": "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109",
    "games_pack.json": "62c1eaaa7bb72674cf59a66f9b543d911749d52973155f6b201d796d97d6ea4a",
    "board_rankings_v37.json": "6f2662615b686a492b41f2d689a7ba6b380b62d7b8cecc5e7a3c9788d1dce641",
    "derived_catalog_v38.json": "09e6b1caa3ed586264a85d3d9807f0173384c02c80102dae072d14665432f2aa",
    "cat_mobile_app_pack_contract.json": (
        "5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f"
    ),
}
_V92_ADDED_IDS = {
    "conexiuni": (
        "cx_limba_364",
        "cx_viata_de_roman_365",
        "cx_viata_de_roman_366",
        "cx_viata_de_roman_367",
    ),
    "contexto": (
        "ct_film_tv_357",
        "ct_film_tv_358",
        "ct_film_tv_359",
        "ct_gastronomie_360",
        "ct_gastronomie_361",
        "ct_sport_362",
        "ct_viata_de_roman_363",
        "ct_viata_de_roman_364",
    ),
    "lant": (
        "lt_film_tv_223",
        "lt_gastronomie_224",
        "lt_geografie_225",
        "lt_geografie_226",
        "lt_geografie_227",
        "lt_geografie_228",
        "lt_istorie_229",
        "lt_literatura_230",
        "lt_literatura_231",
        "lt_sport_232",
        "lt_sport_233",
        "lt_sport_234",
        "lt_stiinta_235",
    ),
    "alchimie": (),
}
# Exact (V91 weight, V92 weight) transitions caused by the larger ranked shelves.
_V92_WEIGHT_CHANGES = {
    "ct_gastronomie_131": (3, 2),
    "ct_gastronomie_132": (3, 2),
    "ct_geografie_028": (3, 2),
    "ct_limba_046": (2, 1),
    "ct_limba_223": (5, 4),
    "ct_literatura_230": (2, 1),
    "ct_muzica_241": (4, 3),
    "ct_muzica_244": (4, 3),
    "ct_personalitati_075": (4, 3),
    "cx_gastronomie_173": (5, 4),
    "cx_gastronomie_297": (5, 4),
    "cx_gastronomie_301": (5, 4),
    "cx_istorie_034": (3, 2),
    "cx_istorie_117": (2, 1),
    "cx_istorie_118": (4, 3),
    "cx_literatura_128": (3, 2),
    "cx_meme_net_045": (4, 3),
    "cx_meme_net_267": (4, 3),
    "cx_viata_de_roman_313": (5, 4),
    "lt_arta_cultura_003": (2, 1),
    "lt_arta_cultura_092": (3, 2),
    "lt_film_tv_011": (3, 2),
    "lt_film_tv_098": (4, 3),
    "lt_gastronomie_221": (5, 4),
    "lt_istorie_171": (4, 3),
    "lt_muzica_055": (3, 2),
    "lt_muzica_137": (5, 4),
    "lt_muzica_141": (4, 3),
    "lt_personalitati_067": (3, 2),
    "lt_personalitati_143": (5, 4),
    "lt_personalitati_149": (2, 1),
    "lt_societate_150": (4, 3),
    "lt_sport_080": (3, 2),
    "lt_stiinta_203": (2, 1),
    "lt_viata_de_roman_089": (4, 3),
}


def before_v92_artifact(current: dict, filename: str) -> dict:
    """Peel the exact reviewed V92 delta and reproduce complete 75584bf artifact bytes."""
    current = before_v92_entry_session_artifact(current, filename)
    indent = 2 if filename == "kg_sample.json" else 1

    def digest(value):
        blob = (json.dumps(value, ensure_ascii=False, indent=indent) + "\n").encode()
        return hashlib.sha256(blob).hexdigest()

    assert filename in _V92_ARTIFACT_HASHES
    assert digest(current) == _V92_ARTIFACT_HASHES[filename]
    restored = deepcopy(current)
    previous = json.loads(_V91_RECEIPT.read_bytes())["files"][filename]
    if filename == "games_pack.json":
        assert sum(len(ids) for ids in _V92_ADDED_IDS.values()) == 25
        for game, added in _V92_ADDED_IDS.items():
            rows = restored[game]
            assert {row["id"] for row in rows if row["id"] in added} == set(added)
            assert all(row["status"] == "approved" for row in rows if row["id"] in added)
            restored[game] = [row for row in rows if row["id"] not in added]
    elif filename == "board_rankings_v37.json":
        added = {item_id for ids in _V92_ADDED_IDS.values() for item_id in ids}
        rows = restored["boards"]
        assert {row["id"] for row in rows if row["id"] in added} == added
        restored["boards"] = [row for row in rows if row["id"] not in added]
        ranks: Counter[str] = Counter()
        changed = set()
        for row in restored["boards"]:
            ranks[row["game"]] += 1
            row["rank"] = ranks[row["game"]]
            if row["id"] in _V92_WEIGHT_CHANGES:
                before, after = _V92_WEIGHT_CHANGES[row["id"]]
                assert row["selection_weight"] == after
                row["selection_weight"] = before
                changed.add(row["id"])
        assert changed == set(_V92_WEIGHT_CHANGES)
    # The core derived board payloads, shared KG and mobile rows are not rewritten.
    # Their only potential inverse is the exact historical non-table metadata.
    head = {key for key, value in restored.items() if not isinstance(value, list)}
    assert head == set(previous["head_after"])
    restored.update(deepcopy(previous["head_after"]))
    assert digest(restored) == previous["after_sha256"]
    return restored


def _reverse_reviewed_delta(current: dict, filename: str, receipt_path: Path) -> dict:
    """Peel only exact reviewed additions/corrections before checking old wave pins."""
    receipt = json.loads(receipt_path.read_bytes())["files"][filename]
    restored = deepcopy(current)
    head = {key: value for key, value in restored.items() if not isinstance(value, list)}
    assert head == receipt["head_after"]
    for table, changes in receipt["tables"].items():
        rows = restored[table]
        assert isinstance(rows, list)
        for added in changes["added"]:
            assert rows.count(added) == 1
            rows.remove(added)
        by_id = {row["id"]: row for row in rows}
        assert len(by_id) == len(rows)
        for row_id, change in changes["changed"].items():
            assert by_id[row_id] == change["after"]
            by_id[row_id] = change["before"]
        rows = [by_id[row["id"]] for row in rows]
        for removal in sorted(changes["removed"], key=lambda record: record["index"]):
            row = removal["row"]
            assert row["id"] not in by_id
            assert 0 <= removal["index"] <= len(rows)
            rows.insert(removal["index"], row)
            by_id[row["id"]] = row
        if (order := changes["baseline_order"]) is not None:
            assert len(order) == len(set(order)) == len(rows)
            assert set(order) == set(by_id)
            rows = [by_id[row_id] for row_id in order]
        restored[table] = rows
    for key in head:
        if key not in receipt["head_before"]:
            del restored[key]
    restored.update(receipt["head_before"])
    return restored


def _reverse_bound_delta(current: dict, filename: str, receipt_path: Path) -> dict:
    """Check complete canonical artifact bytes on both sides of an exact delta."""
    receipt = json.loads(receipt_path.read_bytes())["files"][filename]
    indent = 2 if filename == "kg_sample.json" else 1

    def digest(value):
        blob = (json.dumps(value, ensure_ascii=False, indent=indent) + "\n").encode()
        return hashlib.sha256(blob).hexdigest()

    assert digest(current) == receipt["after_sha256"]
    restored = _reverse_reviewed_delta(current, filename, receipt_path)
    assert digest(restored) == receipt["baseline_sha256"]
    return restored


def before_v92_entry_session_artifact(current: dict, filename: str) -> dict:
    """Restore complete c0ead5e bytes, rejecting drift before removing new records."""
    current = before_v92_session03_artifact(current, filename)
    receipt_blob = _V92_ENTRY_SESSION_RECEIPT.read_bytes()
    assert hashlib.sha256(receipt_blob).hexdigest() == _V92_ENTRY_SESSION_RECEIPT_SHA256
    files = json.loads(receipt_blob)["files"]
    assert set(files) == set(_V92_ARTIFACT_HASHES)
    assert filename in _V92_ARTIFACT_HASHES
    receipt = files[filename]
    assert receipt["baseline_sha256"] == _V92_ARTIFACT_HASHES[filename]
    expected_ids = {item_id for ids in _V92_ENTRY_SESSION_ADDED_IDS.values()
                    for item_id in ids}
    assert len(expected_ids) == 5
    for table, changes in receipt["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V92_ENTRY_SESSION_ADDED_IDS
            added = changes["added"]
            assert {row["id"] for row in added} == _V92_ENTRY_SESSION_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in added)
            assert not changes["changed"]
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V92_ENTRY_SESSION_RECEIPT)


def before_v92_session03_artifact(current: dict, filename: str) -> dict:
    """Restore exact 0b51e03 bytes before any older content inverse runs."""
    current = before_v93_artifact(current, filename)
    receipt_blob = _V92_SESSION03_RECEIPT.read_bytes()
    assert hashlib.sha256(receipt_blob).hexdigest() == _V92_SESSION03_RECEIPT_SHA256
    receipt = json.loads(receipt_blob)
    assert receipt["baseline_commit"] == "0b51e03c983bcbfc042807b4eb97e59a8a9e7781"
    files = receipt["files"]
    assert set(files) == set(_V92_SESSION03_BASELINE)
    assert filename in _V92_SESSION03_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V92_SESSION03_BASELINE[filename]
    expected_ids = set().union(*_V92_SESSION03_ADDED_IDS.values())
    assert len(expected_ids) == 5
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V92_SESSION03_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V92_SESSION03_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V92_SESSION03_RECEIPT)


def before_v93_artifact(current: dict, filename: str) -> dict:
    """Restore exact bf9d814 bytes before any historical content inverse runs."""
    receipt_blob = _V93_RECEIPT.read_bytes()
    assert hashlib.sha256(receipt_blob).hexdigest() == _V93_RECEIPT_SHA256
    current = before_v94_artifact(current, filename)
    receipt = json.loads(receipt_blob)
    assert receipt["baseline_commit"] == "bf9d8145f2797b7e1ea125531f81a98d2ff6098c"
    files = receipt["files"]
    assert set(files) == set(_V93_BASELINE)
    assert filename in _V93_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V93_BASELINE[filename]
    expected_ids = set().union(*_V93_ADDED_IDS.values())
    assert len(expected_ids) == 5
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V93_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V93_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V93_RECEIPT)


def before_v94_artifact(current: dict, filename: str) -> dict:
    """Restore exact c971846 content before evaluating any earlier wave."""
    current = before_v95_artifact(current, filename)
    blob = _V94_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V94_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "c971846feac31e73c3a2a2593c66265f29603e58"
    files = receipt["files"]
    assert set(files) == set(_V94_BASELINE) and filename in _V94_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V94_BASELINE[filename]
    expected_ids = set().union(*_V94_ADDED_IDS.values())
    assert len(expected_ids) == 4
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V94_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V94_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 242
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V94_RECEIPT)


def before_v95_artifact(current: dict, filename: str) -> dict:
    """Restore complete cf6b28b bytes before evaluating the original V94 transition."""
    current = before_v96_artifact(current, filename)
    blob = _V95_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V95_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "cf6b28bc0d247be33e494be1395ca7d676a9f4b4"
    files = receipt["files"]
    assert set(files) == set(_V95_BASELINE) and filename in _V95_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V95_BASELINE[filename]
    expected_ids = set().union(*_V95_ADDED_IDS.values())
    assert len(expected_ids) == 5
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V95_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V95_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 244
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V95_RECEIPT)


def before_v96_artifact(current: dict, filename: str) -> dict:
    """Restore complete 1457786 bytes before evaluating the original V95 transition."""
    current = before_v97_artifact(current, filename)
    blob = _V96_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V96_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "14577863038378c734c7b2e0e8b33ea8158f318b"
    files = receipt["files"]
    assert set(files) == set(_V96_BASELINE) and filename in _V96_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V96_BASELINE[filename]
    expected_ids = set().union(*_V96_ADDED_IDS.values())
    assert len(expected_ids) == 3
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V96_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V96_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 245
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V96_RECEIPT)


def before_v97_artifact(current: dict, filename: str) -> dict:
    """Restore complete fd3ca7c bytes before evaluating the original V96 transition."""
    blob = _V97_RECEIPT.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == _V97_RECEIPT_SHA256
    receipt = json.loads(blob)
    assert receipt["baseline_commit"] == "fd3ca7c78b6bee774c283d873d400abf4a8e7d65"
    files = receipt["files"]
    assert set(files) == set(_V97_BASELINE) and filename in _V97_BASELINE
    artifact = files[filename]
    assert artifact["baseline_sha256"] == _V97_BASELINE[filename]
    expected_ids = set().union(*_V97_ADDED_IDS.values())
    assert len(expected_ids) == 3
    for table, changes in artifact["tables"].items():
        assert not changes["removed"]
        if filename == "games_pack.json":
            assert table in _V97_ADDED_IDS
            assert {row["id"] for row in changes["added"]} == _V97_ADDED_IDS[table]
            assert all(row["status"] == "approved" for row in changes["added"])
            assert not changes["changed"]
            assert current["meta"]["id_high_water"]["lant"] == 246
            assert all(row["id"] != "lt_geografie_242" for row in current["lant"])
        elif filename == "board_rankings_v37.json":
            assert table == "boards"
            assert {row["id"] for row in changes["added"]} == expected_ids
            for change in changes["changed"].values():
                before, after = change["before"], change["after"]
                assert set(before) == set(after)
                assert {key for key in before if before[key] != after[key]} <= {
                    "rank", "selection_weight",
                }
        else:
            assert not changes["added"] and not changes["changed"]
    return _reverse_bound_delta(current, filename, _V97_RECEIPT)


def before_v94_lant_ledger(current: dict) -> dict:
    """Remove only the exact V94 rejection and retain every original V49 byte."""
    def digest(value):
        blob = (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()
        return hashlib.sha256(blob).hexdigest()

    assert digest(current) == _V94_LEDGER_SHA256
    assert current["meta"]["count"] == len(current["items"]) == 105
    assert current["items"]["lt_geografie_242"] == _V94_REJECTED_LANT
    restored = deepcopy(current)
    del restored["items"]["lt_geografie_242"]
    restored["meta"]["count"] = 104
    assert digest(restored) == _V49_LEDGER_SHA256
    return restored


def v49_lant_ledger_bytes(path: Path) -> bytes:
    """Historical tests consume a strictly verified reconstruction of their ledger."""
    value = before_v94_lant_ledger(json.loads(path.read_bytes()))
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def before_v91_artifact(current: dict, filename: str) -> dict:
    """Restore exact V90 content before checking earlier historical receipts."""
    previous = before_v92_artifact(current, filename)
    return _reverse_bound_delta(previous, filename, _V91_RECEIPT)


def _before_v90(current: dict, filename: str) -> dict:
    previous = before_v91_artifact(current, filename)
    return _reverse_bound_delta(previous, filename, _V90_RECEIPT)


def before_v90_fixture(current: dict) -> dict:
    return _before_v90(current, "kg_sample.json")


def before_v90_pack(current: dict) -> dict:
    return _before_v90(current, "games_pack.json")


def before_v90_rankings(current: dict) -> dict:
    return _before_v90(current, "board_rankings_v37.json")


def before_v90_derived(current: dict) -> dict:
    return _before_v90(current, "derived_catalog_v38.json")


def before_v90_mobile(current: dict) -> dict:
    return _before_v90(current, "cat_mobile_app_pack_contract.json")


def _before_v89(current: dict, filename: str) -> dict:
    previous = _before_v90(current, filename)
    return _reverse_bound_delta(previous, filename, _V89_RECEIPT)


def before_v89_fixture(current: dict) -> dict:
    return _before_v89(current, "kg_sample.json")


def before_v89_pack(current: dict) -> dict:
    return _before_v89(current, "games_pack.json")


def before_v89_rankings(current: dict) -> dict:
    return _before_v89(current, "board_rankings_v37.json")


def before_v89_derived(current: dict) -> dict:
    return _before_v89(current, "derived_catalog_v38.json")


def _before_v88(current: dict, filename: str) -> dict:
    previous = _before_v89(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V88_RECEIPT)


def before_v88_fixture(current: dict) -> dict:
    return _before_v88(current, "kg_sample.json")


def before_v88_pack(current: dict) -> dict:
    return _before_v88(current, "games_pack.json")


def before_v88_rankings(current: dict) -> dict:
    return _before_v88(current, "board_rankings_v37.json")


def before_v88_derived(current: dict) -> dict:
    return _before_v88(current, "derived_catalog_v38.json")


def _before_v87(current: dict, filename: str) -> dict:
    previous = _before_v88(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V87_RECEIPT)


def before_v87_fixture(current: dict) -> dict:
    return _before_v87(current, "kg_sample.json")


def before_v87_pack(current: dict) -> dict:
    return _before_v87(current, "games_pack.json")


def before_v87_rankings(current: dict) -> dict:
    return _before_v87(current, "board_rankings_v37.json")


def before_v87_derived(current: dict) -> dict:
    return _before_v87(current, "derived_catalog_v38.json")


def _before_v86(current: dict, filename: str) -> dict:
    previous = _before_v87(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V86_RECEIPT)


def before_v86_fixture(current: dict) -> dict:
    return _before_v86(current, "kg_sample.json")


def before_v86_pack(current: dict) -> dict:
    return _before_v86(current, "games_pack.json")


def before_v86_rankings(current: dict) -> dict:
    return _before_v86(current, "board_rankings_v37.json")


def before_v86_derived(current: dict) -> dict:
    return _before_v86(current, "derived_catalog_v38.json")


def before_v85_fixture(current: dict) -> dict:
    return _before_v85(current, "kg_sample.json")


def before_v85_pack(current: dict) -> dict:
    return _before_v85(current, "games_pack.json")


def before_v85_rankings(current: dict) -> dict:
    return _before_v85(current, "board_rankings_v37.json")


def before_v85_derived(current: dict) -> dict:
    return _before_v85(current, "derived_catalog_v38.json")


def _before_v85(current: dict, filename: str) -> dict:
    previous = _before_v86(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V85_RECEIPT)


def _before_v84(current: dict, filename: str) -> dict:
    previous = _before_v85(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V84_RECEIPT)


def before_v84_fixture(current: dict) -> dict:
    return _before_v84(current, "kg_sample.json")


def before_v84_pack(current: dict) -> dict:
    return _before_v84(current, "games_pack.json")


def before_v84_rankings(current: dict) -> dict:
    return _before_v84(current, "board_rankings_v37.json")


def before_v84_derived(current: dict) -> dict:
    return _before_v84(current, "derived_catalog_v38.json")


def before_v84_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact retired Drojdie row from the committed V83 module."""
    restored = before_v85_projection_rows(current)
    assert not any(row[0] == "drojdie" for row in restored)
    index = next(i for i, row in enumerate(restored) if row[0] == "gem")
    restored.insert(index, (
        "drojdie", "n_v4gas_mancare", "ingrediente", 1, "domain_fallback",
        "ctxp_3218ea40b036e40101f5",
    ))
    return restored


def before_v85_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore only V85's two native replacements to their exact V84 positions."""
    restored = before_v86_projection_rows(current)
    for index, successor, row in (
        (29, "piper", (
            "scorțișoară", "n_v4gas_mancare", "ingrediente", 1, "domain_fallback",
            "ctxp_ed454bb254e529d7508c",
        )),
        (38, "cappuccino", (
            "cacao", "n_v3gas_cafea", "băuturi", 1, "explicit",
            "ctxp_73226150ba2fe847d20e",
        )),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == successor
        restored.insert(index, row)
    return restored


def before_v86_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact Congelator projection retired by its V86 native concept."""
    restored = before_v87_projection_rows(current)
    assert not any(row[0] == "congelator" for row in restored)
    assert restored[86][0] == "hotă de bucătărie"
    restored.insert(86, (
        "congelator", "n_v24_home_appliances_frigider", "ustensile de bucătărie",
        0, "explicit", "ctxp_ab9722a1b626f7b1d9ca",
    ))
    return restored


def before_v87_projection_rows(current: list[tuple]) -> list[tuple]:
    """Remove the reviewed Tort cue and restore the two exact V86 pastry rows."""
    restored = before_v88_projection_rows(current)
    added = (
        "tort", "n_v4gas_prajitura", "mâncare gătită", 1, "explicit",
        "ctxp_7de7b40dd74b4b0f44bf",
    )
    assert restored.count(added) == 1
    restored.remove(added)
    for index, row in (
        (14, ("brioșă", "n_v4gas_paine", "mâncare gătită", 1, "explicit",
              "ctxp_48dbb31871219f323569")),
        (15, ("chec", "n_v4gas_paine", "mâncare gătită", 1, "explicit",
              "ctxp_2e50eafd1e160b7bc25a")),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == "chiflă"
        restored.insert(index, row)
    return restored


def before_v90_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact retired dust row and the complete 465-row V89 fingerprint."""
    restored = list(current)
    assert not any(row[0] == "praf" for row in restored)
    assert restored[314][0] == "scoică"
    restored.insert(314, (
        "praf", "n_v24_nature_world_pamant", "peisaj", 1, "explicit",
        "ctxp_81703160cad7893fa1c9",
    ))
    assert len(restored) == 465
    assert hashlib.sha256(json.dumps(
        restored, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest() == (
        "2c47be5276ba580036413db1308075a5ec44db27e8af8146c5c37aca4f597320"
    )
    return restored


def before_v88_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the two exact V87 household cues replaced by native V88 owners."""
    restored = before_v90_projection_rows(current)
    for index, successor, row in (
        (59, "birou de acasă", (
            "taburet", "n_v4soc_casa", "mobilier și casă", 1, "domain_fallback",
            "ctxp_cd04babfc1ac9193f9cf",
        )),
        (106, "cârpă de praf", (
            "mătură", "n_v31_cleaning_floor_aspirator", "curățenie", 1, "explicit",
            "ctxp_14422411a52f6dbbfe68",
        )),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == successor
        restored.insert(index, row)
    return restored


def before_v89_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only the reviewed Diplomat-to-whipped-cream native cue."""
    added = frozenset({("n_v87_food_tort_diplomat", "n_v86_food_frisca")})
    assert added <= current
    return current - added


def before_v88_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only V88's independently reviewed native bread-family cue."""
    current = before_v89_feedback_pairs(current)
    added = frozenset({("n_v87_food_briosa", "n_v4gas_paine")})
    assert added <= current
    return current - added


def before_v87_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only the three reviewed V87 native exact-target additions."""
    current = before_v88_feedback_pairs(current)
    added = frozenset({
        ("n_v87_food_pandispan", "n_v87_food_chec"),
        ("n_v24_food_snack_biscuit", "n_v87_food_piscot"),
        ("n_v4gas_prajitura", "n_v87_food_cremsnit"),
    })
    assert added <= current
    return current - added


def before_v90_projection_neighborhoods(current: dict) -> dict:
    """Restore V89's retired dust policy before older exact-scope checks."""
    from cat_de_roman_esti.wordgames.contexto_projection import ProjectionNeighborhood

    assert set(current) == {"gem", "burta", "tort", "ciocolata calda"}
    return {
        "praf": ProjectionNeighborhood(
            "n_v24_nature_world_pamant", 0.60, include_direct_neighbors=False,
            exact_target_ids=frozenset({
                "n_v31_cleaning_floor_faras", "n_v31_cleaning_floor_mop",
                "n_v31_cleaning_floor_aspirator",
            }),
        ),
        **current,
    }


def before_v89_projection_neighborhoods(current: dict) -> dict:
    """Restore the exact V88 policies after validating the three closed dust scopes."""
    restored = before_v90_projection_neighborhoods(current)
    policy = restored.pop("praf")
    assert (policy.anchor_id, policy.min_strength, policy.include_direct_neighbors,
            policy.exact_target_ids) == (
        "n_v24_nature_world_pamant", 0.60, False, frozenset({
            "n_v31_cleaning_floor_faras", "n_v31_cleaning_floor_mop",
            "n_v31_cleaning_floor_aspirator",
        }),
    )
    return restored


def before_v87_projection_neighborhoods(current: dict) -> dict:
    """Retain exact older policies while checking the two closed V87 cue policies."""
    restored = before_v89_projection_neighborhoods(current)
    for key, anchor, target in (
        ("tort", "n_v4gas_prajitura", "n_v87_food_tort_diplomat"),
        ("ciocolata calda", "n_v24_food_snack_ceai", "n_v85_food_ciocolata"),
    ):
        policy = restored.pop(key)
        assert (policy.anchor_id, policy.min_strength, policy.include_direct_neighbors,
                policy.exact_target_ids) == (anchor, 0.60, False, frozenset({target}))
    return restored


def v83_added_forms() -> set[str]:
    receipt = json.loads((_V83_REVIEW / "morphology-delta.json").read_bytes())
    return {
        form for change in receipt["alias_changes"].values()
        for form in change["after"] if form not in change["before"]
    }


def before_v83_fixture(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "morphology-delta.json").read_bytes())
    restored = before_v84_fixture(current)
    assert restored["meta"] == receipt["after_kg_meta"]
    for row in restored["kg_nodes"]:
        change = receipt["alias_changes"].get(row["id"])
        if change is not None:
            assert row["aliases"] == change["after"]
            row["aliases"] = change["before"]
    restored["meta"] = receipt["baseline_kg_meta"]
    return restored


def before_v83_pack(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_pack(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v83_rankings(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    added = {row["id"] for row in receipt["new_records"]}
    assert added <= {row["id"] for row in restored["boards"]}
    restored["boards"] = [row for row in restored["boards"] if row["id"] not in added]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v83_derived(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v82_pack(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_pack(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v82_rankings(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    new_ids = {row["id"] for row in receipt["new_records"]}
    assert new_ids <= {row["id"] for row in restored["boards"]}
    restored["boards"] = [row for row in restored["boards"] if row["id"] not in new_ids]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v82_derived(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_fixture(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v83_fixture(current)
    assert restored["meta"] == receipt["after_kg_meta"]
    new_node = receipt["new_node"]
    assert new_node in restored["kg_nodes"]
    nodes = []
    for row in restored["kg_nodes"]:
        if row["id"] == new_node["id"]:
            continue
        change = receipt["changed_nodes"].get(row["id"])
        if change:
            assert row == change["after"]
            row = change["before"]
        nodes.append(row)
    restored["kg_nodes"] = nodes
    for edge in receipt["new_edges"]:
        assert edge in restored["kg_edges"]
        restored["kg_edges"].remove(edge)
    for idx, row in enumerate(restored["kg_puzzles"]):
        change = receipt["changed_puzzles"].get(row["id"])
        if change:
            assert row == change["after"]
            restored["kg_puzzles"][idx] = change["before"]
    restored["meta"] = receipt["baseline_kg_meta"]
    return restored


def before_v81_rankings(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v82_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    rows = {row["id"]: row for row in restored["boards"]}
    assert len(rows) == len(restored["boards"])
    assert set(rows) == set(receipt["baseline_ranking_order"])
    for item_id, change in receipt["changed_ranking_rows"].items():
        assert rows[item_id] == change["after"]
        rows[item_id] = change["before"]
    restored["boards"] = [rows[item_id] for item_id in receipt["baseline_ranking_order"]]
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v81_derived(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v82_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the one retired synthetic row for the V79 history fingerprint."""

    restored = before_v84_projection_rows(current)
    assert not any(row[0] == "nucă" for row in restored)
    index = next(i for i, row in enumerate(restored) if row[0] == "alună")
    restored.insert(index, (
        "nucă", "n_v24_food_breakfast_miere", "ingrediente", 1, "explicit",
        "ctxp_92113401f76976ac37f7",
    ))
    return restored


def before_v80_pack(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = before_v82_pack(current)
    restored["contexto"] = [
        row for row in restored["contexto"] if row["id"] not in receipt["new_ids"]
    ]
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v80_rankings(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = before_v81_rankings(current)
    restored["boards"] = [
        row for row in restored["boards"] if row["id"] not in receipt["new_ids"]
    ]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_ranking_meta"]
    return restored


def before_v80_derived(current: dict) -> dict:
    restored = before_v81_derived(current)
    restored["meta"] = json.loads(_RECEIPT.read_bytes())["baseline_derived_meta"]
    return restored
