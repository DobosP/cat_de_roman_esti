"""Behavioral coverage for the portable two-reviewer V2 artifact builder."""

from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import build_review_artifact  # noqa: E402
import critique_pack  # noqa: E402

IDS = ("ct_meme_net_238", "ct_societate_257", "lt_literatura_210")


def _fresh_dossiers(path: Path, ids: tuple[str, ...] = IDS) -> dict[str, dict]:
    path.mkdir()
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG
    )
    _, _, selected = critique_pack.run(
        pack, svc, strong, regions, list(build_review_artifact.GAME_KINDS),
        {"pending"}, set(ids),
    )
    dossiers = {}
    for game, record, findings in selected:
        dossier = critique_pack.build_dossier(
            record, game, svc, strong, findings, regions
        )
        dossiers[record["id"]] = dossier
        (path / f"{record['id']}.json").write_text(
            json.dumps(dossier, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
    assert set(dossiers) == set(ids)
    return dossiers


def _review(role: str, dossiers: dict[str, dict]) -> dict:
    verdicts = {
        "analyst": ("promote", "promote", "keep"),
        "verifier": ("promote", "keep", "reject"),
    }[role]
    return {
        "reviewer": f"independent-{role}-01",
        "role": role,
        "input_ids": list(IDS),
        "items": [
            {
                "id": item_id,
                "game": dossiers[item_id]["game"],
                "verdict": verdict,
                "review_binding": dossiers[item_id]["review_binding"],
                "rationale": f"Raționament independent pentru {item_id}.",
                "sources": (
                    [f"https://example.org/review/{item_id}"]
                    if role == "verifier" else []
                ),
            }
            for item_id, verdict in zip(IDS, verdicts, strict=True)
        ],
    }


def _write(path: Path, data: dict) -> bytes:
    blob = (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode()
    path.write_bytes(blob)
    return blob


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, dict, dict, dict]:
    dossier_dir = tmp_path / "dossiers"
    dossiers = _fresh_dossiers(dossier_dir)
    analyst = _review("analyst", dossiers)
    verifier = _review("verifier", dossiers)
    analyst_path = tmp_path / "analyst.json"
    verifier_path = tmp_path / "verifier.json"
    _write(analyst_path, analyst)
    _write(verifier_path, verifier)
    return (
        analyst_path,
        verifier_path,
        dossier_dir,
        tmp_path / "out",
        dossiers,
        analyst,
        verifier,
    )


def _run(analyst: Path, verifier: Path, dossiers: Path, out: Path) -> int:
    return build_review_artifact.main([
        "--analyst", str(analyst),
        "--verifier", str(verifier),
        "--dossiers", str(dossiers),
        "--out", str(out),
    ])


def test_builds_conservative_v2_artifacts_accepted_by_applier(tmp_path: Path) -> None:
    analyst_path, verifier_path, dossier_dir, out, dossiers, _, _ = _inputs(tmp_path)
    analyst_blob = analyst_path.read_bytes()
    verifier_blob = verifier_path.read_bytes()

    assert _run(analyst_path, verifier_path, dossier_dir, out) == 0
    expected = {
        "contexto": {
            "ct_meme_net_238": "promote",
            "ct_societate_257": "keep",
        },
        "lant": {"lt_literatura_210": "reject"},
    }
    for game, verdicts in expected.items():
        path = out / f"{game}_verdicts.json"
        artifact = json.loads(path.read_text(encoding="utf-8"))
        accepted, batch, bindings = apply_rereview.validated_artifact(
            artifact, game, path
        )
        assert accepted == verdicts
        assert batch["input_ids"] == list(IDS)
        assert bindings == {
            item_id: dossiers[item_id]["review_binding"] for item_id in verdicts
        }
        assert artifact["provenance"]["analyst"]["sha256"] == (
            "sha256:" + hashlib.sha256(analyst_blob).hexdigest()
        )
        assert artifact["provenance"]["verifier"]["sha256"] == (
            "sha256:" + hashlib.sha256(verifier_blob).hexdigest()
        )
        for row in artifact["perItem"]:
            assert row["analyst_review"]["rationale"]
            assert row["verifier_review"]["sources"]
            assert row["verified"] is True
            assert row["verifier_lost"] is False

    assert {path.stem for path in (out / "dossiers").glob("*.json")} == set(IDS)
    assert not list(tmp_path.glob(".out.review-artifact-*"))


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("same-reviewer", "distinct reviewer IDs"),
        ("wrong-role", "invalid verifier review contract"),
        ("different-batch", "batches differ"),
        ("duplicate-id", "invalid verifier review contract"),
        ("blank-rationale", "invalid verifier judgment"),
        ("missing-source", "invalid verifier judgment"),
        ("unknown-game", "invalid verifier judgment"),
        ("stale-binding", "does not match dossier"),
    ],
)
def test_invalid_reviews_fail_before_overwriting_output(
    tmp_path: Path, case: str, message: str
) -> None:
    analyst_path, verifier_path, dossier_dir, out, _, analyst, verifier = _inputs(tmp_path)
    changed = deepcopy(verifier)
    if case == "same-reviewer":
        changed["reviewer"] = analyst["reviewer"]
    elif case == "wrong-role":
        changed["role"] = "analyst"
    elif case == "different-batch":
        changed["input_ids"] = changed["input_ids"][:-1]
        changed["items"] = changed["items"][:-1]
    elif case == "duplicate-id":
        changed["input_ids"][1] = changed["input_ids"][0]
    elif case == "blank-rationale":
        changed["items"][0]["rationale"] = "  "
    elif case == "missing-source":
        changed["items"][0]["sources"] = []
    elif case == "unknown-game":
        changed["items"][0]["game"] = "necunoscut"
    elif case == "stale-binding":
        changed["items"][0]["review_binding"] = "sha256:" + "0" * 64
    _write(verifier_path, changed)

    out.mkdir()
    target = out / "contexto_verdicts.json"
    sentinel = b"existing artifact\n"
    target.write_bytes(sentinel)
    with pytest.raises(SystemExit, match=message):
        _run(analyst_path, verifier_path, dossier_dir, out)
    assert target.read_bytes() == sentinel
    assert not (out / "lant_verdicts.json").exists()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


def test_missing_or_extra_dossiers_fail_without_creating_output(tmp_path: Path) -> None:
    analyst_path, verifier_path, dossier_dir, out, _, _, _ = _inputs(tmp_path)
    (dossier_dir / f"{IDS[-1]}.json").unlink()
    (dossier_dir / "unknown.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit, match="dossier batch mismatch"):
        _run(analyst_path, verifier_path, dossier_dir, out)
    assert not out.exists()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


def test_self_consistent_but_outdated_dossier_fails_before_output(tmp_path: Path) -> None:
    analyst_path, verifier_path, dossier_dir, out, dossiers, analyst, verifier = _inputs(tmp_path)
    item_id = IDS[0]
    stale = deepcopy(dossiers[item_id])
    stale["category"] = "categorie-schimbată"
    stale["review_binding"] = critique_pack.dossier_review_binding(stale)
    _write(dossier_dir / f"{item_id}.json", stale)
    for review, path in ((analyst, analyst_path), (verifier, verifier_path)):
        next(item for item in review["items"] if item["id"] == item_id)[
            "review_binding"
        ] = stale["review_binding"]
        _write(path, review)

    with pytest.raises(SystemExit, match="stale dossiers for current pending content"):
        _run(analyst_path, verifier_path, dossier_dir, out)
    assert not out.exists()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


def test_valid_batch_does_not_mix_with_stale_output_artifacts(tmp_path: Path) -> None:
    analyst_path, verifier_path, dossier_dir, out, _, _, _ = _inputs(tmp_path)
    out.mkdir()
    stale = out / "conexiuni_verdicts.json"
    stale.write_bytes(b"old batch\n")

    with pytest.raises(SystemExit, match="stale game artifacts"):
        _run(analyst_path, verifier_path, dossier_dir, out)
    assert stale.read_bytes() == b"old batch\n"
    assert not (out / "contexto_verdicts.json").exists()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


def test_alchimie_input_fails_without_fabricating_projection_evidence(
    tmp_path: Path,
) -> None:
    item_id = "al_gastronomie_026"
    dossier_dir = tmp_path / "dossiers"
    dossiers = _fresh_dossiers(dossier_dir, (item_id,))
    analyst_path = tmp_path / "analyst.json"
    verifier_path = tmp_path / "verifier.json"
    for role, path in (("analyst", analyst_path), ("verifier", verifier_path)):
        _write(path, {
            "reviewer": f"independent-{role}-alchimie",
            "role": role,
            "input_ids": [item_id],
            "items": [{
                "id": item_id,
                "game": "alchimie",
                "verdict": "keep",
                "review_binding": dossiers[item_id]["review_binding"],
                "rationale": "Judecata nu pretinde verificarea proiecției private.",
                "sources": ["https://example.org/alchimie"] if role == "verifier" else [],
            }],
        })
    out = tmp_path / "out"

    with pytest.raises(SystemExit, match="do not support Alchimie projection evidence"):
        _run(analyst_path, verifier_path, dossier_dir, out)
    assert not out.exists()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


def test_validation_stage_uses_output_parent_and_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    analyst_path, verifier_path, dossier_dir, out, _, _, _ = _inputs(tmp_path)
    real_mkdtemp = build_review_artifact.tempfile.mkdtemp
    seen = []

    def observed_mkdtemp(*, prefix: str, dir: Path) -> str:
        seen.append((prefix, Path(dir)))
        return real_mkdtemp(prefix=prefix, dir=dir)

    monkeypatch.setattr(build_review_artifact.tempfile, "mkdtemp", observed_mkdtemp)
    assert _run(analyst_path, verifier_path, dossier_dir, out) == 0
    assert seen == [(".out.review-artifact-", tmp_path)]
    assert not list(tmp_path.glob(".out.review-artifact-*"))
