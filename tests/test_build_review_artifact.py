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
import audit_alchimie_projections  # noqa: E402
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


def _run(
    analyst: Path, verifier: Path, dossiers: Path, out: Path,
    projection: Path | None = None,
) -> int:
    args = [
        "--analyst", str(analyst),
        "--verifier", str(verifier),
        "--dossiers", str(dossiers),
        "--out", str(out),
    ]
    if projection is not None:
        args.extend(["--projection-audit", str(projection)])
    return build_review_artifact.main(args)


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

    with pytest.raises(SystemExit, match="invalid analyst item schema"):
        _run(analyst_path, verifier_path, dossier_dir, out)
    assert not out.exists()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


@pytest.fixture(scope="module")
def alchimie_evidence(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict, dict]:
    dossier_dir = tmp_path_factory.mktemp("alchimie-source") / "dossiers"
    dossiers = _fresh_dossiers(dossier_dir, ("al_gastronomie_026",))
    audit = audit_alchimie_projections.build_artifact(sorted(dossiers), dossier_dir)
    return dossiers, audit


def _alchimie_inputs(
    tmp_path: Path, evidence: tuple[dict, dict],
) -> tuple[Path, Path, Path, Path, Path, dict, dict]:
    dossiers, audit = deepcopy(evidence)
    dossier_dir = tmp_path / "dossiers"
    dossier_dir.mkdir()
    for item_id, dossier in dossiers.items():
        _write(dossier_dir / f"{item_id}.json", dossier)
    audit_path = tmp_path / "source-projection.json"
    # Deliberately noncanonical whitespace must survive publication unchanged.
    audit_path.write_bytes(json.dumps(audit, ensure_ascii=False, indent=3).encode() + b"\n\n")
    digest = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    reviews = []
    paths = []
    for role in ("analyst", "verifier"):
        review = {
            "reviewer": f"independent-{role}-alchimie",
            "role": role,
            "input_ids": sorted(dossiers),
            "items": [{
                "id": item_id,
                "game": "alchimie",
                "verdict": "keep",
                "review_binding": dossier["review_binding"],
                "rationale": "Proiecția și traseele sunt verificate; lotul rămâne pending.",
                "sources": ["https://example.org/alchimie"] if role == "verifier" else [],
                "projection_audit_sha256": digest,
            } for item_id, dossier in dossiers.items()],
        }
        path = tmp_path / f"{role}.json"
        _write(path, review)
        paths.append(path)
        reviews.append(review)
    return (*paths, dossier_dir, tmp_path / "out", audit_path, *reviews)


def test_alchimie_preserves_independently_bound_audit_and_raw_judgments(
    tmp_path: Path, alchimie_evidence: tuple[dict, dict],
) -> None:
    analyst, verifier, dossiers, out, audit, left, right = _alchimie_inputs(
        tmp_path, alchimie_evidence,
    )
    assert _run(analyst, verifier, dossiers, out, audit) == 0
    assert (out / "projection-audit.json").read_bytes() == audit.read_bytes()
    path = out / "alchimie_verdicts.json"
    artifact = json.loads(path.read_bytes())
    verdicts, batch, bindings = apply_rereview.validated_artifact(artifact, "alchimie", path)
    apply_rereview.validate_live_alchimie_projection_source(batch, path)
    assert verdicts == {"al_gastronomie_026": "keep"}
    assert bindings == {
        "al_gastronomie_026": alchimie_evidence[0]["al_gastronomie_026"]["review_binding"],
    }
    assert artifact["perItem"][0]["analyst_review"] == left["items"][0]
    assert artifact["perItem"][0]["verifier_review"] == right["items"][0]
    assert batch["projection_audit_sha256"] == hashlib.sha256(audit.read_bytes()).hexdigest()
    assert not list(tmp_path.glob(".out.review-artifact-*"))


@pytest.mark.parametrize("case", [
    "missing-audit", "missing-analyst-binding", "missing-verifier-binding",
    "invalid-digest", "analyst-different-audit", "verifier-different-audit",
    "changed-audit-bytes", "invalid-json", "nonobject-json", "same-reviewer",
    "changed-projection", "missing-row", "duplicate-row", "changed-batch",
    "changed-dossier-manifest", "changed-record", "stale-pack", "stale-kg",
    "stale-rubric", "stale-runtime", "stale-generator",
])
def test_alchimie_invalid_evidence_never_overwrites_output(
    tmp_path: Path, alchimie_evidence: tuple[dict, dict], case: str,
) -> None:
    analyst, verifier, dossiers, out, audit, left, right = _alchimie_inputs(
        tmp_path, alchimie_evidence,
    )
    data = json.loads(audit.read_bytes())
    if case == "missing-audit":
        audit = None
    elif case == "missing-analyst-binding":
        del left["items"][0]["projection_audit_sha256"]
    elif case == "missing-verifier-binding":
        del right["items"][0]["projection_audit_sha256"]
    elif case == "invalid-digest":
        right["items"][0]["projection_audit_sha256"] = "sha256:" + "0" * 64
    elif case == "analyst-different-audit":
        left["items"][0]["projection_audit_sha256"] = "0" * 64
    elif case == "verifier-different-audit":
        right["items"][0]["projection_audit_sha256"] = "0" * 64
    elif case == "changed-audit-bytes":
        audit.write_bytes(audit.read_bytes() + b"\n")
    elif case == "invalid-json":
        audit.write_bytes(b"{")
    elif case == "nonobject-json":
        audit.write_bytes(b"[]")
    elif case == "same-reviewer":
        right["reviewer"] = left["reviewer"]
    else:
        if case == "changed-projection":
            data["items"][0]["projected_opening_pair_count"] += 1
        elif case == "missing-row":
            data["items"] = []
        elif case == "duplicate-row":
            data["items"] *= 2
        elif case == "changed-batch":
            data["input_ids"] = ["al_invented_999"]
        elif case == "changed-dossier-manifest":
            data["dossier_manifest_sha256"] = "0" * 64
        elif case == "changed-record":
            data["items"][0]["source_record"]["difficulty"] = "greu"
            data["items"][0]["record_sha256"] = critique_pack.canonical_json_sha256(
                data["items"][0]["source_record"],
            )
        elif case == "stale-runtime":
            data["runtime_sources"][0]["sha256"] = "0" * 64
            data["runtime_source_manifest_sha256"] = hashlib.sha256(json.dumps(
                data["runtime_sources"], ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ).encode()).hexdigest()
        elif case == "stale-generator":
            data["generator"]["sha256"] = "0" * 64
        else:
            data[case.removeprefix("stale-") + "_sha256"] = "0" * 64
        # Even coordinated digest restamping cannot hide stale or altered evidence.
        digest = hashlib.sha256(_write(audit, data)).hexdigest()
        left["items"][0]["projection_audit_sha256"] = digest
        right["items"][0]["projection_audit_sha256"] = digest
    _write(analyst, left)
    _write(verifier, right)
    out.mkdir()
    (out / "dossiers").mkdir()
    for name in (
        "alchimie_verdicts.json", "projection-audit.json", "dossiers/al_gastronomie_026.json",
    ):
        (out / name).write_bytes(b"preexisting bytes\n")
    before = {
        str(path.relative_to(out)): path.read_bytes()
        for path in out.rglob("*") if path.is_file()
    }
    with pytest.raises(SystemExit):
        _run(analyst, verifier, dossiers, out, audit)
    after = {
        str(path.relative_to(out)): path.read_bytes()
        for path in out.rglob("*") if path.is_file()
    }
    assert after == before
    assert not list(tmp_path.glob(".out.review-artifact-*"))


def test_alchimie_mixed_game_batch_is_explicitly_rejected(
    tmp_path: Path, alchimie_evidence: tuple[dict, dict],
) -> None:
    analyst, verifier, dossiers, out, audit, left, right = _alchimie_inputs(
        tmp_path, alchimie_evidence,
    )
    extra_dir = tmp_path / "extra"
    extra = _fresh_dossiers(extra_dir, (IDS[0],))[IDS[0]]
    _write(dossiers / f"{IDS[0]}.json", extra)
    for path, review in ((analyst, left), (verifier, right)):
        review["input_ids"].append(IDS[0])
        review["items"].append({
            "id": IDS[0], "game": "contexto", "verdict": "keep",
            "review_binding": extra["review_binding"], "rationale": "Separat.",
            "sources": ["https://example.org/contexto"],
        })
        _write(path, review)
    with pytest.raises(SystemExit, match="sorted Alchimie-only batch"):
        _run(analyst, verifier, dossiers, out, audit)
    assert not out.exists()


def test_non_alchimie_batch_rejects_unused_or_stale_projection_audit(tmp_path: Path) -> None:
    analyst, verifier, dossiers, out, _, _, _ = _inputs(tmp_path)
    audit = tmp_path / "projection.json"
    _write(audit, {})
    with pytest.raises(SystemExit, match="without an Alchimie batch"):
        _run(analyst, verifier, dossiers, out, audit)
    assert not out.exists()
    out.mkdir()
    (out / "projection-audit.json").write_bytes(b"old audit\n")
    with pytest.raises(SystemExit, match="stale projection audit"):
        _run(analyst, verifier, dossiers, out)
    assert (out / "projection-audit.json").read_bytes() == b"old audit\n"
    assert not list(out.glob("*_verdicts.json"))


def test_alchimie_unsorted_batch_is_rejected_before_audit_output(tmp_path: Path) -> None:
    ids = ("al_gastronomie_030", "al_gastronomie_026")
    dossier_dir = tmp_path / "dossiers"
    dossiers = _fresh_dossiers(dossier_dir, ids)
    for role in ("analyst", "verifier"):
        _write(tmp_path / f"{role}.json", {
            "reviewer": f"independent-{role}", "role": role, "input_ids": list(ids),
            "items": [{
                "id": item_id, "game": "alchimie", "verdict": "keep",
                "review_binding": dossiers[item_id]["review_binding"],
                "rationale": "Ambele proiecții necesită verificare.",
                "sources": ["https://example.org/alchimie"],
                "projection_audit_sha256": "0" * 64,
            } for item_id in ids],
        })
    out = tmp_path / "out"
    with pytest.raises(SystemExit, match="sorted Alchimie-only batch"):
        _run(tmp_path / "analyst.json", tmp_path / "verifier.json", dossier_dir, out)
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
