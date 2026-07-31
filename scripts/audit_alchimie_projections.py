#!/usr/bin/env python3
"""Bind Alchimie review dossiers to the sparse recipes players actually receive.

The generic critique dossier intentionally describes the source graph. Alchimie serves a
smaller private recipe projection, so a pending-board gate also needs exact evidence for
that live choice space. This command rebuilds those projections from the current runtime,
cross-binds them to fresh critique dossiers, and emits deterministic reviewer evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from itertools import combinations
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

import django  # noqa: E402

django.setup()

import critique_pack  # noqa: E402
from content_file_transaction import atomic_write  # noqa: E402

from cat_de_roman_esti.wordgames import alchimie, packs  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402

SCHEMA = "alchimie-live-projection-audit-v1"
RUNTIME_SOURCES = (
    _ROOT / "cat_de_roman_esti/wordgames/alchimie.py",
    _ROOT / "cat_de_roman_esti/wordgames/packs.py",
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _concept(svc, node_id: str) -> dict[str, str]:
    node = svc.node(node_id)
    if node is None:
        raise SystemExit(f"unknown projection node: {node_id}")
    return {"id": node_id, "label": node.label_ro}


def _route_row(svc, route) -> dict:
    steps = []
    strengths: list[float] = []
    for pair, outputs in route:
        step_strengths = []
        for parent in pair:
            for output in outputs:
                edge = svc.link(parent, output)
                strength = edge.strength if edge is not None else 0.0
                strengths.append(strength)
                step_strengths.append(strength)
        steps.append({
            "left": _concept(svc, pair[0]),
            "right": _concept(svc, pair[1]),
            "results": [_concept(svc, output) for output in outputs],
            "minimum_edge_strength": round(min(step_strengths), 4),
        })
    return {
        "actions": len(route),
        "minimum_edge_strength": round(min(strengths), 4),
        "mean_edge_strength": round(sum(strengths) / len(strengths), 4),
        "steps": steps,
    }


def _runtime_source_manifest() -> tuple[list[dict[str, str]], str]:
    entries = [
        {
            "path": str(path.relative_to(_ROOT)),
            "sha256": _sha256(path.read_bytes()),
        }
        for path in RUNTIME_SOURCES
    ]
    return entries, _sha256(_canonical_json(entries))


def _dossier_manifest(
    ids: list[str], dossier_dir: Path, records: dict[str, dict],
) -> tuple[dict[str, str], str]:
    actual_ids = sorted(path.stem for path in dossier_dir.glob("*.json"))
    if actual_ids != ids:
        raise SystemExit("dossier directory does not exactly match the requested ids")
    bindings = {}
    for item_id in ids:
        path = dossier_dir / f"{item_id}.json"
        if not path.is_file():
            raise SystemExit(f"missing dossier: {path}")
        dossier = json.loads(path.read_text(encoding="utf-8"))
        record_sha256 = critique_pack.canonical_json_sha256(records[item_id])
        if (
            dossier.get("id") != item_id
            or dossier.get("game") != "alchimie"
            or dossier.get("record_sha256") != record_sha256
            or dossier.get("kg_sha256") != critique_pack.kg_sha256()
            or critique_pack.dossier_review_binding(dossier)
            != dossier.get("review_binding")
        ):
            raise SystemExit(f"stale or invalid dossier: {path}")
        bindings[item_id] = str(dossier["review_binding"])
    manifest = "".join(f"{item_id}\t{bindings[item_id]}\n" for item_id in ids).encode()
    return bindings, _sha256(manifest)


def build_artifact(
    ids: list[str],
    dossier_dir: Path,
    *,
    status: str = "pending",
    source_records: dict[str, dict] | None = None,
    source_pack_sha256: str | None = None,
) -> dict:
    """Return deterministic live-projection evidence for one exact Alchimie batch."""
    if not ids or ids != sorted(ids) or len(ids) != len(set(ids)):
        raise SystemExit("--ids must be a non-empty, unique, sorted list")

    if source_records is None:
        pack_raw = critique_pack.PACKAGE_PACK.read_bytes()
        pack = json.loads(pack_raw.decode("utf-8"))
        all_records = {str(row["id"]): row for row in pack["alchimie"]}
        pack_sha256 = _sha256(pack_raw)
    else:
        all_records = source_records
        if (
            not isinstance(source_pack_sha256, str)
            or len(source_pack_sha256) != 64
            or any(char not in "0123456789abcdef" for char in source_pack_sha256)
        ):
            raise SystemExit("archive rebuild requires its bound source pack SHA-256")
        pack_sha256 = source_pack_sha256
    missing = [item_id for item_id in ids if item_id not in all_records]
    wrong_status = [
        item_id for item_id in ids
        if item_id in all_records and all_records[item_id].get("status") != status
    ]
    if missing:
        raise SystemExit("unknown Alchimie ids: " + ", ".join(missing))
    if wrong_status:
        raise SystemExit(
            f"Alchimie ids are not {status}: " + ", ".join(wrong_status)
        )

    bindings, dossier_manifest_sha256 = _dossier_manifest(
        ids, dossier_dir, all_records,
    )
    runtime_sources, runtime_source_manifest_sha256 = _runtime_source_manifest()
    svc = get_service()
    rows = []
    for item_id in ids:
        record = all_records[item_id]
        payload_errors = packs.validate_payload(record, "alchimie", svc)
        if payload_errors:
            raise SystemExit(
                f"invalid Alchimie payload for {item_id}: " + "; ".join(payload_errors)
            )
        seeds = [str(seed) for seed in record["seeds"]]
        target = str(record["target"])
        category = str(record.get("category") or "") or None
        projection = alchimie._build_recipe_projection(seeds, target, category)
        if projection is None:
            raise SystemExit(f"runtime cannot project Alchimie record: {item_id}")
        exact_par = packs.minimum_alchimie_actions(svc, seeds, target, category)
        if exact_par is None:
            raise SystemExit(f"runtime cannot certify Alchimie par: {item_id}")

        owned = set(seeds)
        openings = []
        for left, right in combinations(sorted(seeds), 2):
            outputs = [
                output
                for output in projection.recipes.get(alchimie._pair_key(left, right), ())
                if output not in owned
            ]
            if outputs:
                openings.append({
                    "left": _concept(svc, left),
                    "right": _concept(svc, right),
                    "results": [_concept(svc, output) for output in outputs],
                })

        structural_projection = {
            "par": projection.par,
            "recipes": [
                {"pair": list(pair), "results": list(outputs)}
                for pair, outputs in sorted(projection.recipes.items())
            ],
            "routes": [
                [
                    {"pair": list(pair), "results": list(outputs)}
                    for pair, outputs in route
                ]
                for route in projection.routes
            ],
        }
        projected_nodes = set(seeds)
        for pair, outputs in projection.recipes.items():
            projected_nodes.update(pair)
            projected_nodes.update(outputs)
        max_outputs = max(map(len, projection.recipes.values()), default=0)
        bounds = {
            "declared_par_matches_exact": record["target_depth"] == exact_par,
            "projection_par_matches_exact": projection.par == exact_par,
            "route_limit": len(projection.routes) <= alchimie.MAX_TARGET_ROUTES,
            "recipe_pair_limit": len(projection.recipes) <= alchimie.MAX_RECIPE_PAIRS,
            "projected_concept_limit": len(projected_nodes) <= alchimie.MAX_PROJECTED_CONCEPTS,
            "result_per_pair_limit": max_outputs <= alchimie.MAX_RESULTS_PER_RECIPE,
            "e2_live_opening_floor": len(openings) >= alchimie.MIN_OPENING_PAIRS,
        }
        rows.append({
            "id": item_id,
            "review_binding": bindings[item_id],
            "record_sha256": critique_pack.canonical_json_sha256(record),
            "source_record": record,
            "category": record.get("category"),
            "difficulty": record.get("difficulty"),
            "seeds": [_concept(svc, seed) for seed in seeds],
            "target": _concept(svc, target),
            "declared_target_depth": record["target_depth"],
            "exact_action_par": exact_par,
            "projection_par": projection.par,
            "projection_sha256": _sha256(_canonical_json(structural_projection)),
            "projected_opening_pair_count": len(openings),
            "projected_opening_pairs": openings,
            "route_count": len(projection.routes),
            "recipe_pair_count": len(projection.recipes),
            "projected_concept_count": len(projected_nodes),
            "max_results_per_pair": max_outputs,
            "routes": [_route_row(svc, route) for route in projection.routes],
            "bounds": bounds,
        })

    id_blob = ("\n".join(ids) + "\n").encode()
    return {
        "schema": SCHEMA,
        "game": "alchimie",
        "mode": "gate",
        "status": status,
        "input_ids": ids,
        "input_ids_sha256": _sha256(id_blob),
        "pack_sha256": pack_sha256,
        "kg_sha256": critique_pack.kg_sha256(),
        "rubric_sha256": critique_pack.rubric_sha256(),
        "dossier_manifest_sha256": dossier_manifest_sha256,
        "runtime_sources": runtime_sources,
        "runtime_source_manifest_sha256": runtime_source_manifest_sha256,
        "generator": {
            "path": str(Path(__file__).resolve().relative_to(_ROOT)),
            "sha256": _sha256(Path(__file__).read_bytes()),
        },
        "summary": {
            "records": len(rows),
            "live_opening_floor_failures": sum(
                not row["bounds"]["e2_live_opening_floor"] for row in rows
            ),
        },
        "items": rows,
    }


def rebuild_archived_artifact(artifact: dict, dossier_dir: Path) -> dict:
    """Rebuild checked-in evidence after its source rows leave the live pack."""
    ids = artifact.get("input_ids")
    rows = artifact.get("items")
    if (
        artifact.get("schema") != SCHEMA
        or artifact.get("game") != "alchimie"
        or artifact.get("mode") != "gate"
        or not isinstance(ids, list)
        or not isinstance(rows, list)
    ):
        raise SystemExit("invalid archived Alchimie projection artifact")
    source_records = {
        row.get("id"): row.get("source_record")
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("id"), str)
        and isinstance(row.get("source_record"), dict)
    }
    if set(source_records) != set(ids) or len(source_records) != len(ids):
        raise SystemExit("archived Alchimie projection source rows are incomplete")
    return build_artifact(
        ids,
        dossier_dir,
        status=str(artifact.get("status")),
        source_records=source_records,
        source_pack_sha256=artifact.get("pack_sha256"),
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", required=True, help="sorted comma-separated exact ids")
    parser.add_argument("--dossier", required=True, help="fresh dossier directory")
    parser.add_argument("--status", default="pending")
    parser.add_argument("--json", required=True, help="output artifact")
    args = parser.parse_args(argv[1:])
    ids = [part.strip() for part in args.ids.split(",") if part.strip()]
    artifact = build_artifact(ids, Path(args.dossier), status=args.status)
    raw = (json.dumps(artifact, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    atomic_write(Path(args.json), raw)
    print(
        f"audit_alchimie_projections: {len(ids)} item(s), "
        f"{artifact['summary']['live_opening_floor_failures']} live E2 failure(s)"
    )
    print(f"report -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
