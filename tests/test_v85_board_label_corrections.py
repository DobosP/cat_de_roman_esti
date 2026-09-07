"""Reviewed label edits preserve exact source choices, frozen IDs and answer custody."""

from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import derived_catalog, intrusul
from cat_de_roman_esti.wordgames.label_corrections import (
    CORRECTIONS,
    corrected_pack,
    correction_state,
    identity_payload,
    record_sha256,
)
from cat_de_roman_esti.wordgames.packs import normalized_text_sha256
from scripts import apply_pack_label_corrections as APPLY
from scripts import build_derived_catalog_v38 as BUILD
from tests.content_history import before_v85_pack

SOURCE = "cx_gastronomie_171"
BOARD = "vi_1535ff1ac283061d41a1"
OLD_LABEL = "Alb, sărat, din zona laptelui"
NEW_LABEL = "Produse lactate"


def _before_pack() -> dict:
    return before_v85_pack(json.loads(BUILD.DEFAULT_PACK.read_text(encoding="utf-8")))


def _source(pack: dict) -> dict:
    return next(row for row in pack["conexiuni"] if row["id"] == SOURCE)


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def catalog_pair() -> tuple[dict, dict]:
    baseline = _before_pack()
    corrected = corrected_pack(baseline)
    original_load = BUILD.critique_pack.load_all
    _, svc, kg, nodes = original_load(
        BUILD.critique_pack.PACKAGE_PACK, BUILD.critique_pack.PACKAGE_KG,
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(BUILD.critique_pack, "load_all", lambda *_: (baseline, svc, kg, nodes))
        before = BUILD.generate_catalog()
        patch.setattr(BUILD.critique_pack, "load_all", lambda *_: (corrected, svc, kg, nodes))
        after = BUILD.generate_catalog()
    return before, after


def test_pack_delta_is_exactly_two_labels_with_the_full_source_bound() -> None:
    before = _before_pack()
    original = deepcopy(before)
    after = corrected_pack(before)
    assert before == original
    source = _source(before)
    assert record_sha256(source) == CORRECTIONS[0].before_sha256
    assert correction_state(source, CORRECTIONS[0]) == "before"
    assert correction_state(_source(after), CORRECTIONS[0]) == "after"
    assert _source(after)["group_labels"]["g1"] == "Denumiri cu trimitere geografică"
    assert _source(after)["group_labels"]["g3"] == NEW_LABEL
    restored = deepcopy(after)
    _source(restored)["group_labels"] = deepcopy(source["group_labels"])
    assert restored == before


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("missing", "missing label correction source"),
        ("duplicate", "duplicate Conexiuni source"),
        ("status", "requires approved source"),
        ("members", "member drift"),
        ("order", "source record drift"),
        ("label", "label drift"),
        ("partial", "partial label correction"),
        ("already", "already applied"),
    ],
)
def test_stale_partial_and_repeated_corrections_fail_before_mutation(change, message) -> None:
    pack = _before_pack()
    source = _source(pack)
    if change == "missing":
        pack["conexiuni"].remove(source)
    elif change == "duplicate":
        pack["conexiuni"].append(deepcopy(source))
    elif change == "status":
        source["status"] = "pending"
    elif change == "members":
        source["groups"]["g3"].reverse()
    elif change == "order":
        source["order"].reverse()
    elif change == "label":
        source["group_labels"]["g3"] = "Aproape lactate"
    elif change == "partial":
        source["group_labels"]["g3"] = NEW_LABEL
    else:
        pack = corrected_pack(pack)
    original = deepcopy(pack)
    with pytest.raises(ValueError, match=message):
        corrected_pack(pack)
    assert pack == original


def test_generator_changes_one_display_label_and_no_frozen_choice(catalog_pair) -> None:
    before, after = catalog_pair
    expected = deepcopy(before)
    row = next(row for row in expected["boards"] if row["id"] == BOARD)
    assert row["payload"]["group_label"] == OLD_LABEL
    row["payload"]["group_label"] = NEW_LABEL
    assert after == expected
    source_rows = [row for row in after["boards"] if row["source_id"] == SOURCE]
    assert len(source_rows) == 3
    assert all(row["game"] == "intrusul" for row in source_rows)
    assert all(
        row["id"] == derived_catalog._candidate_id(row["game"], row["source_id"], row["payload"])
        for row in after["boards"]
    )


def test_identity_fold_requires_exact_source_members_label_and_game(catalog_pair) -> None:
    _, after = catalog_pair
    payload = deepcopy(next(row for row in after["boards"] if row["id"] == BOARD)["payload"])
    expected = deepcopy(payload)
    expected["group_label"] = OLD_LABEL
    assert identity_payload("intrusul", SOURCE, payload) == expected
    assert payload["group_label"] == NEW_LABEL
    assert identity_payload("intrusul", "another_source", payload) == payload
    assert identity_payload("another_game", SOURCE, payload) == payload
    for mutated in (
        {**payload, "group_label": "Lactate"},
        {**payload, "members": [*payload["members"][:2], "n_gas_covrigi_buzau"]},
        {**payload, "members": [payload["members"][0]] * 3},
        {**payload, "members": payload["members"][:2]},
    ):
        assert identity_payload("intrusul", SOURCE, mutated) == mutated


def _load_corrected_catalog(tmp_path, monkeypatch, document, pack):
    pack_path = tmp_path / "pack.json"
    catalog_path = tmp_path / "catalog.json"
    _write(pack_path, pack)
    document = deepcopy(document)
    document["meta"]["pack_sha256"] = normalized_text_sha256(pack_path)
    _write(catalog_path, document)
    monkeypatch.setattr(derived_catalog, "DEFAULT_PACK", pack_path)
    return derived_catalog.load_derived_catalog(
        catalog_path, expected_sha256=normalized_text_sha256(catalog_path),
    )


def test_loader_accepts_generated_repair_and_seed_daily_choices_stay_exact(
    catalog_pair, tmp_path, monkeypatch,
) -> None:
    before, after = catalog_pair
    baseline = _load_corrected_catalog(tmp_path, monkeypatch, before, _before_pack())
    corrected = _load_corrected_catalog(
        tmp_path, monkeypatch, after, corrected_pack(_before_pack()),
    )
    for game in ("intrusul", "perechi"):
        assert len(baseline.pool(game)) == len(corrected.pool(game))
        for seed in range(100):
            for category in (None, "gastronomie"):
                left = baseline.pick_seeded(game, random.Random(seed), category=category)
                right = corrected.pick_seeded(game, random.Random(seed), category=category)
                assert (left is None) == (right is None)
                if left is not None:
                    assert left._catalog_id == right._catalog_id
        for day in range(1, 31):
            daily = f"2026-09-{day:02d}"
            left = baseline.pick_daily(game, daily)
            right = corrected.pick_daily(game, daily)
            assert left._catalog_id == right._catalog_id


@pytest.mark.parametrize("change", ["partial", "custom", "derived_label"])
def test_loader_refuses_bound_but_unreviewed_source_or_payload_changes(
    change, catalog_pair, tmp_path, monkeypatch,
) -> None:
    _, document = catalog_pair
    pack = corrected_pack(_before_pack())
    document = deepcopy(document)
    if change == "partial":
        _source(pack)["group_labels"]["g1"] = CORRECTIONS[0].groups[0].before
        error = "partial label correction"
    elif change == "custom":
        _source(pack)["order"].reverse()
        error = "source record drift"
    else:
        row = next(row for row in document["boards"] if row["id"] == BOARD)
        row["payload"]["group_label"] = OLD_LABEL
        error = "group label drift"
    with pytest.raises(ValueError, match=error):
        _load_corrected_catalog(tmp_path, monkeypatch, document, pack)


@pytest.fixture
def pack_mirrors(tmp_path, monkeypatch):
    paths = (tmp_path / "package.json", tmp_path / "tests.json")
    for path in paths:
        _write(path, _before_pack())
    monkeypatch.setattr(APPLY, "PACK_COPIES", paths)
    return paths


def test_authoring_dry_run_is_read_only_and_success_writes_exact_mirrors(pack_mirrors, monkeypatch):
    before = pack_mirrors[0].read_bytes()
    assert APPLY.main([]) == 0
    assert all(path.read_bytes() == before for path in pack_mirrors)
    monkeypatch.setattr(APPLY.validate_games_pack, "main", lambda _: 0)
    assert APPLY.main(["--write"]) == 0
    assert pack_mirrors[0].read_bytes() == pack_mirrors[1].read_bytes()
    assert json.loads(pack_mirrors[0].read_bytes()) == corrected_pack(json.loads(before))


@pytest.mark.parametrize("failure", ["validation", "interrupted_write", "mirror_drift"])
def test_authoring_failures_restore_both_mirrors(pack_mirrors, monkeypatch, failure):
    if failure == "mirror_drift":
        pack_mirrors[1].write_bytes(pack_mirrors[1].read_bytes() + b"\n")
    before = {path: path.read_bytes() for path in pack_mirrors}
    if failure == "validation":
        monkeypatch.setattr(APPLY.validate_games_pack, "main", lambda _: 1)
        error = ValueError
    elif failure == "interrupted_write":
        original_write = APPLY.atomic_write

        def interrupt_second(path, blob):
            if path == pack_mirrors[1]:
                raise KeyboardInterrupt("interrupted mirror write")
            original_write(path, blob)

        monkeypatch.setattr(APPLY, "atomic_write", interrupt_second)
        error = KeyboardInterrupt
    else:
        error = ValueError
    with pytest.raises(error):
        APPLY.main(["--write"])
    assert {path: path.read_bytes() for path in pack_mirrors} == before


def test_corrected_intrusul_hint_and_win_expose_only_earned_label(
    catalog_pair, tmp_path, monkeypatch,
) -> None:
    _, after = catalog_pair
    catalog = _load_corrected_catalog(
        tmp_path, monkeypatch, after, corrected_pack(_before_pack()),
    )
    board = next(row for row in catalog.pool("intrusul") if row._catalog_id == BOARD)
    session = intrusul._build_session(
        board, random.Random(85), daily=None, requested_category="gastronomie", previous_ring=(),
    )
    game_id = intrusul.store.create(session)
    client = Client()
    url = f"/api/wordgames/intrusul/games/{game_id}"
    initial = client.get(url)
    assert initial.status_code == 200
    assert NEW_LABEL not in initial.content.decode()
    assert "solution" not in initial.json()
    wrong = client.post(f"{url}/guess", {"id": session.members[0]}, content_type="application/json")
    assert wrong.status_code == 200 and wrong.json()["mistakes"] == 1
    hinted = client.post(f"{url}/hint").json()
    assert hinted["clue"]["label"] == NEW_LABEL
    assert "solution" not in hinted
    won = client.post(
        f"{url}/guess", {"id": session.intruder}, content_type="application/json",
    ).json()
    assert won["won"] is True and won["score"] == 650
    assert won["solution"]["group"]["label"] == NEW_LABEL
    assert OLD_LABEL not in json.dumps(won, ensure_ascii=False)
    assert client.get(url).json()["solution"] == won["solution"]
