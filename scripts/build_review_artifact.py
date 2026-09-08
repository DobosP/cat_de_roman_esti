#!/usr/bin/env python3
"""Build fail-closed V2 gate artifacts from two independent review files.

The command validates already-authored analyst and verifier judgments against the exact
current pending dossiers. It never creates or changes a judgment::

    python scripts/build_review_artifact.py \
      --analyst analyst.json --verifier verifier.json \
      --dossiers wave-dossiers --out wave-verdicts
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import apply_rereview  # noqa: E402
import critique_pack  # noqa: E402
from content_file_transaction import atomic_write  # noqa: E402
from import_candidates import GAME_KINDS  # noqa: E402

ROOT_KEYS = frozenset({"reviewer", "role", "input_ids", "items"})
ITEM_KEYS = frozenset(
    {"id", "game", "verdict", "review_binding", "rationale", "sources"}
)
ALCHIMIE_ITEM_KEYS = ITEM_KEYS | {"projection_audit_sha256"}
ROLES = frozenset({"analyst", "verifier"})


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256_uri(blob: bytes) -> str:
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def valid_projection_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def valid_url(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def read_review(path: Path, expected_role: str) -> tuple[dict, bytes]:
    try:
        blob = path.read_bytes()
        data = json.loads(blob.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read {expected_role} review {path}: {exc}")
    if not isinstance(data, dict) or set(data) != ROOT_KEYS:
        fail(f"invalid {expected_role} review schema: {path}")
    reviewer = data.get("reviewer")
    role = data.get("role")
    input_ids = data.get("input_ids")
    items = data.get("items")
    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
        or reviewer != reviewer.strip()
        or role != expected_role
        or role not in ROLES
        or not isinstance(input_ids, list)
        or not input_ids
        or not all(isinstance(item_id, str) and item_id for item_id in input_ids)
        or len(set(input_ids)) != len(input_ids)
        or not isinstance(items, list)
    ):
        fail(f"invalid {expected_role} review contract: {path}")

    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            fail(f"invalid {expected_role} item schema: {path}")
        keys = ALCHIMIE_ITEM_KEYS if item.get("game") == "alchimie" else ITEM_KEYS
        if set(item) != keys:
            fail(f"invalid {expected_role} item schema: {path}")
        item_id = item.get("id")
        game = item.get("game")
        verdict = item.get("verdict")
        binding = item.get("review_binding")
        rationale = item.get("rationale")
        sources = item.get("sources")
        valid_sources = isinstance(sources, list) and all(valid_url(url) for url in sources)
        if (
            not isinstance(item_id, str)
            or not item_id
            or item_id in seen
            or game not in GAME_KINDS
            or verdict not in apply_rereview.GATE_VERDICTS
            or not isinstance(binding, str)
            or not binding.startswith("sha256:")
            or not isinstance(rationale, str)
            or not rationale.strip()
            or not valid_sources
            or (expected_role == "verifier" and not sources)
            or (
                game == "alchimie"
                and not valid_projection_digest(item["projection_audit_sha256"])
            )
        ):
            fail(f"invalid {expected_role} judgment for {item_id!r}: {path}")
        seen.add(item_id)
    if seen != set(input_ids) or len(items) != len(input_ids):
        fail(f"incomplete {expected_role} item coverage: {path}")
    return data, blob


def read_projection_audit(path: Path | None) -> bytes | None:
    if path is None:
        return None
    try:
        blob = path.read_bytes()
        data = json.loads(blob.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read Alchimie projection audit {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"invalid Alchimie projection audit: {path}")
    return blob


def read_dossiers(dossier_dir: Path, input_ids: list[str]) -> dict[str, dict]:
    if not dossier_dir.is_dir():
        fail(f"dossier directory does not exist: {dossier_dir}")
    paths = {path.stem: path for path in dossier_dir.glob("*.json")}
    expected = set(input_ids)
    if set(paths) != expected:
        missing = sorted(expected - set(paths))
        extra = sorted(set(paths) - expected)
        fail(f"dossier batch mismatch; missing={missing}, extra={extra}")

    dossiers: dict[str, dict] = {}
    for item_id in input_ids:
        path = paths[item_id]
        try:
            dossier = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            fail(f"cannot read dossier {path}: {exc}")
        if (
            not isinstance(dossier, dict)
            or dossier.get("id") != item_id
            or dossier.get("game") not in GAME_KINDS
            or dossier.get("status") != "pending"
            or not isinstance(dossier.get("review_binding"), str)
        ):
            fail(f"invalid dossier identity for {item_id}: {path}")
        try:
            rebuilt = critique_pack.dossier_review_binding(dossier)
        except (TypeError, ValueError) as exc:
            fail(f"invalid dossier binding for {item_id}: {exc}")
        if dossier["review_binding"] != rebuilt:
            fail(f"stale or invalid dossier binding for {item_id}")
        dossiers[item_id] = dossier

    current = apply_rereview.current_review_bindings(expected)
    stale = sorted(
        item_id
        for item_id in input_ids
        if dossiers[item_id]["review_binding"] != current.get(item_id)
    )
    if stale:
        fail("stale dossiers for current pending content: " + ", ".join(stale))
    return dossiers


def indexed_items(review: dict) -> dict[str, dict]:
    return {item["id"]: item for item in review["items"]}


def policy(analyst: str, verifier: str, final: str) -> str:
    if final == "promote":
        return "unanimous-promote"
    if final == "reject":
        return "reject-wins"
    if analyst == verifier == "keep":
        return "unanimous-keep"
    return "conservative-keep"


def build_artifacts(
    analyst: dict,
    verifier: dict,
    analyst_path: Path,
    verifier_path: Path,
    analyst_blob: bytes,
    verifier_blob: bytes,
    dossiers: dict[str, dict],
    projection_blob: bytes | None = None,
) -> dict[str, dict]:
    input_ids = analyst["input_ids"]
    if verifier["input_ids"] != input_ids:
        fail("analyst and verifier batches differ")
    if analyst["reviewer"].casefold() == verifier["reviewer"].casefold():
        fail("analyst and verifier must have distinct reviewer IDs")

    analyst_items = indexed_items(analyst)
    verifier_items = indexed_items(verifier)
    for item_id in input_ids:
        left = analyst_items[item_id]
        right = verifier_items[item_id]
        dossier = dossiers[item_id]
        expected_identity = (dossier["game"], dossier["review_binding"])
        if (left["game"], left["review_binding"]) != expected_identity:
            fail(f"analyst judgment does not match dossier for {item_id}")
        if (right["game"], right["review_binding"]) != expected_identity:
            fail(f"verifier judgment does not match dossier for {item_id}")

    batch_games = {dossiers[item_id]["game"] for item_id in input_ids}
    if "alchimie" in batch_games:
        if batch_games != {"alchimie"} or input_ids != sorted(input_ids):
            fail("Alchimie projection evidence requires a sorted Alchimie-only batch")
        if projection_blob is None:
            fail("Alchimie reviews require --projection-audit")
        projection_digest = hashlib.sha256(projection_blob).hexdigest()
        for item_id in input_ids:
            for role, items in (("analyst", analyst_items), ("verifier", verifier_items)):
                if items[item_id]["projection_audit_sha256"] != projection_digest:
                    fail(f"{role} projection audit does not match supplied bytes for {item_id}")
    elif projection_blob is not None:
        fail("projection audit supplied without an Alchimie batch")

    provenance = {
        "analyst": {
            "path": str(analyst_path),
            "sha256": sha256_uri(analyst_blob),
            "reviewer": analyst["reviewer"],
            "role": analyst["role"],
        },
        "verifier": {
            "path": str(verifier_path),
            "sha256": sha256_uri(verifier_blob),
            "reviewer": verifier["reviewer"],
            "role": verifier["role"],
        },
    }
    artifacts: dict[str, dict] = {}
    for game in GAME_KINDS:
        game_ids = [item_id for item_id in input_ids if dossiers[item_id]["game"] == game]
        if not game_ids:
            continue
        verdicts = {
            item_id: apply_rereview.synthesized_gate_verdict(
                analyst_items[item_id]["verdict"], verifier_items[item_id]["verdict"]
            )
            for item_id in game_ids
        }
        if any(verdict is None for verdict in verdicts.values()):
            fail(f"cannot synthesize {game} verdicts")
        batch = {
            "version": apply_rereview.GATE_ARTIFACT_VERSION,
            "mode": "gate",
            "input_ids": input_ids,
        }
        if game == "alchimie":
            batch["projection_audit_sha256"] = projection_digest
        rows = []
        for item_id in game_ids:
            left = analyst_items[item_id]
            right = verifier_items[item_id]
            final = verdicts[item_id]
            row = {
                "id": item_id,
                "game": game,
                "final": final,
                "analyst": left["verdict"],
                "verifier": right["verdict"],
                "verified": True,
                "verifier_lost": False,
                "review_binding": dossiers[item_id]["review_binding"],
                "policy": policy(left["verdict"], right["verdict"], final),
                "analyst_review": dict(left),
                "verifier_review": dict(right),
            }
            if game == "alchimie":
                row["analyst_projection_audit_sha256"] = left["projection_audit_sha256"]
                row["verifier_projection_audit_sha256"] = right["projection_audit_sha256"]
            rows.append(row)
        artifacts[game] = {
            "game": game,
            "mode": "gate",
            "batch": batch,
            "verdicts": verdicts,
            "perItem": rows,
            "coverage": {
                "total": len(game_ids),
                "verified": len(game_ids),
                "unverifiedClean": 0,
                "verifiersLost": 0,
                "lost": 0,
            },
            "provenance": provenance,
        }
    return artifacts


def validated_staging(
    artifacts: dict[str, dict],
    dossiers: dict[str, dict],
    staging_parent: Path,
    output_name: str,
    projection_blob: bytes | None = None,
) -> Path:
    if not staging_parent.is_dir():
        fail(f"output parent directory does not exist: {staging_parent}")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{output_name}.review-artifact-",
        dir=staging_parent,
    ))
    try:
        if projection_blob is not None:
            (staging / apply_rereview.ALCHIMIE_PROJECTION_AUDIT).write_bytes(projection_blob)
        dossier_out = staging / "dossiers"
        dossier_out.mkdir()
        for item_id, dossier in dossiers.items():
            (dossier_out / f"{item_id}.json").write_text(
                json.dumps(dossier, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8",
            )
        for game, artifact in artifacts.items():
            path = staging / f"{game}_verdicts.json"
            path.write_text(
                json.dumps(artifact, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8",
            )
            _, batch, _ = apply_rereview.validated_artifact(artifact, game, path)
            if game == "alchimie":
                apply_rereview.validate_live_alchimie_projection_source(batch, path)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return staging


def write_outputs(staging: Path, out_dir: Path, games: set[str]) -> None:
    existing = {
        game
        for game in GAME_KINDS
        if (out_dir / f"{game}_verdicts.json").exists()
    }
    stale = sorted(existing - games)
    if stale:
        fail("output directory contains stale game artifacts: " + ", ".join(stale))
    expected_dossiers = {
        path.stem for path in (staging / "dossiers").glob("*.json")
    }
    existing_dossiers = {
        path.stem for path in (out_dir / "dossiers").glob("*.json")
    }
    stale_dossiers = sorted(existing_dossiers - expected_dossiers)
    if stale_dossiers:
        fail("output directory contains stale dossiers: " + ", ".join(stale_dossiers))
    audit_name = apply_rereview.ALCHIMIE_PROJECTION_AUDIT
    if (out_dir / audit_name).exists() and not (staging / audit_name).is_file():
        fail("output directory contains a stale projection audit")
    out_dir.mkdir(parents=True, exist_ok=True)
    if (staging / audit_name).is_file():
        atomic_write(out_dir / audit_name, (staging / audit_name).read_bytes())
    for path in sorted(staging.glob("*_verdicts.json")):
        atomic_write(out_dir / path.name, path.read_bytes())
    source_dossiers = staging / "dossiers"
    target_dossiers = out_dir / "dossiers"
    target_dossiers.mkdir(exist_ok=True)
    for path in sorted(source_dossiers.glob("*.json")):
        atomic_write(target_dossiers / path.name, path.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyst", required=True, type=Path)
    parser.add_argument("--verifier", required=True, type=Path)
    parser.add_argument("--dossiers", required=True, type=Path)
    parser.add_argument(
        "--projection-audit", type=Path,
        help="exact reviewer-bound live projection audit for an Alchimie-only batch",
    )
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    analyst, analyst_blob = read_review(args.analyst, "analyst")
    verifier, verifier_blob = read_review(args.verifier, "verifier")
    if verifier["input_ids"] != analyst["input_ids"]:
        fail("analyst and verifier batches differ")
    dossiers = read_dossiers(args.dossiers, analyst["input_ids"])
    projection_blob = read_projection_audit(args.projection_audit)
    artifacts = build_artifacts(
        analyst,
        verifier,
        args.analyst,
        args.verifier,
        analyst_blob,
        verifier_blob,
        dossiers,
        projection_blob,
    )
    staging = validated_staging(
        artifacts,
        dossiers,
        args.out.parent,
        args.out.name,
        projection_blob,
    )
    try:
        write_outputs(staging, args.out, set(artifacts))
    finally:
        shutil.rmtree(staging)
    print(
        f"built {len(artifacts)} V2 gate artifact(s) for "
        f"{len(analyst['input_ids'])} independently reviewed item(s) in {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
