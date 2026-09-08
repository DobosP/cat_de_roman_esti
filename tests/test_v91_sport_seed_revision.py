"""The V91 approved-stock repair accepts one exact reviewed seed delta only."""

from __future__ import annotations

import copy
import json
import shutil

import pytest

from scripts import apply_sport_seed_revision_v91 as migration


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


@pytest.fixture
def isolated(tmp_path):
    """Reconstruct frozen V90 bytes after V91 as well; never mutate served fixtures."""
    for relative in {*migration.SOURCE_BINDINGS, *map(str, migration.KG_PATHS)}:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(migration.ROOT / relative, destination)
    review_dir = tmp_path / migration.REVIEW_DIR
    review_dir.mkdir(parents=True)
    for name in (*migration.INPUT_SHA256, "quality-review.json", "factual-review.json"):
        shutil.copyfile(migration.ROOT / migration.REVIEW_DIR / name, review_dir / name)
    proposal = json.loads((review_dir / "replacement-proposal.json").read_bytes())
    pack = json.loads((tmp_path / migration.PACK_PATHS[0]).read_bytes())
    for index, row in enumerate(pack["alchimie"]):
        if row["id"] == migration.ITEM_ID:
            assert row in (proposal["before"], proposal["after"])
            pack["alchimie"][index] = proposal["before"]
    for relative in migration.PACK_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _write(path, pack)
    assert migration._sha((tmp_path / migration.PACK_PATHS[0]).read_bytes()) == (
        migration.SOURCE_BINDINGS[str(migration.PACK_PATHS[0])]
    )
    return tmp_path


def _snapshot(root):
    return {relative: (root / relative).read_bytes() for relative in migration.PACK_PATHS}


def _reject_unchanged(root, match, error=ValueError):
    before = _snapshot(root)
    with pytest.raises(error, match=match):
        migration.apply_revision(root=root, write=True)
    assert _snapshot(root) == before


def test_default_dry_run_rebuilds_exact_live_review_without_writes(isolated, capsys):
    before = _snapshot(isolated)
    migration.apply_revision(root=isolated)
    assert _snapshot(isolated) == before
    assert "dry run, no writes" in capsys.readouterr().out


def test_validated_write_changes_only_seeds_in_one_record_and_rejects_reapplication(isolated):
    before = json.loads((isolated / migration.PACK_PATHS[0]).read_bytes())
    proposal = json.loads(
        (isolated / migration.REVIEW_DIR / "replacement-proposal.json").read_bytes()
    )
    migration.apply_revision(root=isolated, write=True)
    mirrors = _snapshot(isolated)
    assert len(set(mirrors.values())) == 1
    after = json.loads(next(iter(mirrors.values())))
    expected = copy.deepcopy(before)
    changed = []
    for old, new in zip(before["alchimie"], after["alchimie"], strict=True):
        if old != new:
            changed.append(old["id"])
            assert old == proposal["before"] and new == proposal["after"]
            assert {key for key in old if old[key] != new[key]} == {"seeds"}
    assert changed == [migration.ITEM_ID]
    for row in expected["alchimie"]:
        if row["id"] == migration.ITEM_ID:
            row["seeds"] = proposal["after"]["seeds"]
    assert after == expected
    _reject_unchanged(isolated, "stale source")


@pytest.mark.parametrize("name", ["quality-review.json", "factual-review.json"])
def test_missing_independent_review_rejects_before_writing(isolated, name):
    (isolated / migration.REVIEW_DIR / name).unlink()
    _reject_unchanged(isolated, name, FileNotFoundError)


@pytest.mark.parametrize("field,value", [
    ("kind", "author-proposal"), ("verdict", "fix"), ("verdict", "reject"),
    ("proposal", "keep"), ("item_id", "al_sport_082"),
    ("review_binding", "sha256:" + "0" * 64), ("before_record_sha256", "0" * 64),
    ("after_record_sha256", "0" * 64), ("source_bindings", {}), ("input_sha256", {}),
    ("reviewer", " "),
])
def test_unaccepted_or_unbound_review_cannot_write(isolated, field, value):
    path = isolated / migration.REVIEW_DIR / "factual-review.json"
    review = json.loads(path.read_bytes())
    review[field] = value
    _write(path, review)
    _reject_unchanged(isolated, "verdict|binding|identity")


def test_copying_one_review_does_not_supply_two_independent_judgments(isolated):
    folder = isolated / migration.REVIEW_DIR
    review = json.loads((folder / "quality-review.json").read_bytes())
    review["reviewer"] = " " + review["reviewer"].upper() + " "
    _write(folder / "factual-review.json", review)
    _reject_unchanged(isolated, "two distinct")


@pytest.mark.parametrize("name", migration.INPUT_SHA256)
def test_tampered_review_input_cannot_be_rebound_by_editing_both_reviews(isolated, name):
    folder = isolated / migration.REVIEW_DIR
    path = folder / name
    path.write_bytes(path.read_bytes() + b"\n")
    for review_name in ("quality-review.json", "factual-review.json"):
        review_path = folder / review_name
        review = json.loads(review_path.read_bytes())
        review["input_sha256"][name] = migration._sha(path.read_bytes())
        _write(review_path, review)
    _reject_unchanged(isolated, "review input changed")


@pytest.mark.parametrize("field,value", [
    ("target", "n_spt_handbal_feminin"), ("status", "pending"),
    ("target_depth", 3), ("seeds", ["n_spt_cristina_neagu"]),
])
def test_proposal_cannot_expand_beyond_frozen_revision(isolated, field, value):
    path = isolated / migration.REVIEW_DIR / "replacement-proposal.json"
    proposal = json.loads(path.read_bytes())
    proposal["after"][field] = value
    proposal["after_record_sha256"] = migration.critique.canonical_json_sha256(proposal["after"])
    _write(path, proposal)
    _reject_unchanged(isolated, "review input changed")


@pytest.mark.parametrize("relative", migration.SOURCE_BINDINGS)
def test_source_or_before_pack_drift_rejects(isolated, relative):
    path = isolated / relative
    path.write_bytes(path.read_bytes() + b"\n")
    if relative == str(migration.PACK_PATHS[0]):
        (isolated / migration.PACK_PATHS[1]).write_bytes(path.read_bytes())
    _reject_unchanged(isolated, "stale source")


@pytest.mark.parametrize("relative,match", [
    (migration.PACK_PATHS[1], "pack mirrors"), (migration.KG_PATHS[1], "KG mirrors"),
])
def test_mirrored_inputs_must_match_exactly(isolated, relative, match):
    path = isolated / relative
    path.write_bytes(path.read_bytes() + b"\n")
    _reject_unchanged(isolated, match)


def test_actual_live_projection_must_keep_all_reviewed_openings(isolated, monkeypatch):
    from cat_de_roman_esti.wordgames import alchimie

    monkeypatch.setattr(alchimie, "_projected_opening_pair_count", lambda *_: 3)
    _reject_unchanged(isolated, "four productive opening pairs")


def test_dossier_is_rebuilt_instead_of_trusting_archived_metrics(isolated, monkeypatch):
    original = migration.critique.build_dossier

    def changed_dossier(*args):
        dossier = original(*args)
        dossier["craft_profile"]["closure_size"] += 1
        return dossier

    monkeypatch.setattr(migration.critique, "build_dossier", changed_dossier)
    _reject_unchanged(isolated, "live dossier differs")


@pytest.mark.parametrize("failure", ["validation", "second_write", "post_write_corruption"])
def test_failed_transaction_restores_both_original_mirrors(isolated, monkeypatch, failure):
    if failure == "validation":
        monkeypatch.setattr(migration.validator, "validate", lambda *_: ["injected failure"])
        match, error = "pack validation failed", ValueError
    elif failure == "second_write":
        original = migration.atomic_write

        def interrupted(path, blob):
            if path == isolated / migration.PACK_PATHS[1]:
                raise KeyboardInterrupt("injected interruption")
            original(path, blob)

        monkeypatch.setattr(migration, "atomic_write", interrupted)
        match, error = "injected interruption", KeyboardInterrupt
    else:
        def corrupt(path, _kg):
            path.write_bytes(path.read_bytes() + b"\n")
            return []

        monkeypatch.setattr(migration.validator, "validate", corrupt)
        match, error = "written pack bytes differ", ValueError
    _reject_unchanged(isolated, match, error)


def test_cli_requires_explicit_write_flag(monkeypatch):
    calls = []
    monkeypatch.setattr(migration, "apply_revision", lambda **kwargs: calls.append(kwargs))
    assert migration.main([]) == 0
    assert migration.main(["--write"]) == 0
    assert calls == [{"write": False}, {"write": True}]
