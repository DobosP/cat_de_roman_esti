#!/usr/bin/env python3
"""Apply a re-review verdict set to the curated games pack (promote/reject pending items).

Reads version-2 `<dir>/<game>_verdicts.json` artifacts emitted under the workflow's
`artifacts` key. Each artifact binds the exact cross-game batch, both independent
judgments, per-item verifier coverage, and conservative synthesized verdicts; legacy,
non-unanimous promotions, or hand-combined verdict maps fail closed. Applies the
verified verdicts to BOTH bundled pack copies:

* `promote` → the pending item's `status` becomes `approved` (now served);
* `reject`  → the item is removed from the pack entirely;
* `keep` / absent → left untouched (still `pending`).

Only items currently `status: pending` are eligible. Batch identity, full verifier
coverage, filename/game scope, verdict enum, item ownership and status are validated
before mutation. Every ``promote`` ID is re-run through the strict deterministic checks
against the untouched inventory, including same-batch rejects as novelty debt; rejected
Conexiuni boards and Lanț directed pairs are then tombstoned. The full pack validator runs
and every mutated file ROLLS BACK on a red return or exception.

    python scripts/apply_rereview.py --dir <verdicts_dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import critique_pack  # noqa: E402
import validate_games_pack  # noqa: E402
from content_file_transaction import atomic_write, file_transaction  # noqa: E402
from import_candidates import GAME_KINDS, item_high_water  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)
GATE_ARTIFACT_VERSION = 2
GATE_VERDICTS = frozenset({"promote", "reject", "keep"})
ALCHIMIE_PROJECTION_AUDIT = "projection-audit.json"
ALCHIMIE_PROJECTION_SCHEMA = "alchimie-live-projection-audit-v1"
ALCHIMIE_RUNTIME_SOURCES = (
    _REPO_ROOT / "cat_de_roman_esti/wordgames/alchimie.py",
    _REPO_ROOT / "cat_de_roman_esti/wordgames/packs.py",
)
ALCHIMIE_AUDIT_GENERATOR = _REPO_ROOT / "scripts/audit_alchimie_projections.py"


def synthesized_gate_verdict(analyst: object, verifier: object) -> str | None:
    """Return the conservative two-reviewer outcome, or ``None`` for bad input."""
    if analyst not in GATE_VERDICTS or verifier not in GATE_VERDICTS:
        return None
    if analyst == verifier == "promote":
        return "promote"
    if "reject" in {analyst, verifier}:
        return "reject"
    return "keep"


def fully_verified_gate_row(
    row: dict, item_id: str, game: str, verdict: object,
) -> bool:
    """Require both raw judgments and their fail-closed synthesized outcome."""
    analyst = row.get("analyst", row.get("proposed"))
    verifier = row.get("verifier")
    if (
        "analyst" in row
        and "proposed" in row
        and row["analyst"] != row["proposed"]
    ):
        return False
    return (
        row.get("id") == item_id
        and row.get("game") == game
        and row.get("final") == verdict
        and synthesized_gate_verdict(analyst, verifier) == verdict
        and row.get("verified") is True
        and row.get("verifier_lost") is False
        and isinstance(row.get("review_binding"), str)
        and row["review_binding"].startswith("sha256:")
    )


def validate_alchimie_projection_evidence(
    data: dict, batch: dict, rows: dict[str, dict], path: Path,
) -> None:
    """Require every Alchimie reviewer to bind the exact live recipe projection."""
    digest = batch.get("projection_audit_sha256")
    valid_digest = (
        isinstance(digest, str)
        and len(digest) == 64
        and all(char in "0123456789abcdef" for char in digest)
    )
    audit_path = path.parent / ALCHIMIE_PROJECTION_AUDIT
    if not valid_digest or not audit_path.is_file():
        raise SystemExit(f"missing Alchimie live-projection evidence: {path}")
    audit_bytes = audit_path.read_bytes()
    if hashlib.sha256(audit_bytes).hexdigest() != digest:
        raise SystemExit(f"stale Alchimie live-projection evidence: {path}")
    try:
        audit = json.loads(audit_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"invalid Alchimie live-projection evidence: {audit_path}"
        ) from exc
    raw_audit_rows = audit.get("items")
    if not isinstance(raw_audit_rows, list):
        raise SystemExit(f"unbound Alchimie live-projection evidence: {path}")
    audit_rows = {
        row.get("id"): row
        for row in raw_audit_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    expected_ids = batch["input_ids"]
    id_blob = ("\n".join(expected_ids) + "\n").encode()
    expected_runtime_sources = [
        {
            "path": str(source.relative_to(_REPO_ROOT)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        for source in ALCHIMIE_RUNTIME_SOURCES
    ]
    runtime_manifest = hashlib.sha256(
        json.dumps(
            expected_runtime_sources,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    expected_generator = {
        "path": str(ALCHIMIE_AUDIT_GENERATOR.relative_to(_REPO_ROOT)),
        "sha256": hashlib.sha256(ALCHIMIE_AUDIT_GENERATOR.read_bytes()).hexdigest(),
    }
    fully_bound = (
        audit.get("schema") == ALCHIMIE_PROJECTION_SCHEMA
        and audit.get("game") == "alchimie"
        and audit.get("mode") == "gate"
        and audit.get("status") == "pending"
        and audit.get("input_ids") == expected_ids
        and expected_ids == sorted(expected_ids)
        and audit.get("input_ids_sha256") == hashlib.sha256(id_blob).hexdigest()
        and isinstance(audit.get("pack_sha256"), str)
        and len(audit["pack_sha256"]) == 64
        and all(char in "0123456789abcdef" for char in audit["pack_sha256"])
        and audit.get("kg_sha256") == critique_pack.kg_sha256()
        and audit.get("rubric_sha256") == critique_pack.rubric_sha256()
        and audit.get("runtime_sources") == expected_runtime_sources
        and audit.get("runtime_source_manifest_sha256") == runtime_manifest
        and audit.get("generator") == expected_generator
        and len(raw_audit_rows) == len(expected_ids)
        and len(audit_rows) == len(expected_ids)
        and set(audit_rows) == set(expected_ids) == set(rows)
        and all(
            rows[item_id].get("analyst_projection_audit_sha256") == digest
            and rows[item_id].get("verifier_projection_audit_sha256") == digest
            and audit_rows[item_id].get("review_binding")
            == rows[item_id].get("review_binding")
            and isinstance(audit_rows[item_id].get("source_record"), dict)
            and audit_rows[item_id]["source_record"].get("id") == item_id
            and audit_rows[item_id]["source_record"].get("status") == "pending"
            and audit_rows[item_id].get("record_sha256")
            == critique_pack.canonical_json_sha256(
                audit_rows[item_id]["source_record"]
            )
            for item_id in expected_ids
        )
    )
    if not fully_bound:
        raise SystemExit(f"unbound Alchimie live-projection evidence: {path}")

    import audit_alchimie_projections

    rebuilt = audit_alchimie_projections.rebuild_archived_artifact(
        audit,
        path.parent / "dossiers",
    )
    if rebuilt != audit:
        raise SystemExit(f"unreproducible Alchimie live-projection evidence: {path}")


def validate_live_alchimie_projection_source(batch: dict, path: Path) -> None:
    """Require archived Alchimie evidence to match the live pre-apply source pack."""
    audit_path = path.parent / ALCHIMIE_PROJECTION_AUDIT
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    current_pack_raw = critique_pack.PACKAGE_PACK.read_bytes()
    current_pack = json.loads(current_pack_raw.decode("utf-8"))
    current_records = {
        str(record["id"]): record for record in current_pack["alchimie"]
    }
    audit_rows = {row["id"]: row for row in audit["items"]}
    expected_ids = batch["input_ids"]
    live = (
        audit.get("pack_sha256") == hashlib.sha256(current_pack_raw).hexdigest()
        and all(
            item_id in current_records
            and current_records[item_id].get("status") == "pending"
            and audit_rows[item_id].get("source_record") == current_records[item_id]
            for item_id in expected_ids
        )
    )
    if not live:
        raise SystemExit(f"stale Alchimie live-projection source: {path}")


def critique_promotions(
    item_ids: set[str], rejected_ids: set[str] | None = None,
) -> int:
    '''Gate promotions while retaining rejected rows as novelty tombstones.

    Review bindings are validated against the untouched batch first. Same-batch
    rejects remain in the comparison inventory, preventing a promoted Conexiuni row
    from recycling an exact group, a 3-of-4 group, or half of a rejected board. The
    full untouched pending inventory likewise supplies same-batch rejects, keeps,
    unrelated rows, and co-promotions to the Lanț exact-pair census. ``rejected_ids``
    remains in the caller contract for compatibility; the census needs no verdict labels.
    '''
    if not item_ids:
        return 0
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG,
    )
    items, _, selected = critique_pack.run(
        pack, svc, strong, regions, list(GAME_KINDS), {'pending'}, item_ids,
    )
    errors = critique_pack.selection_errors(
        pack, list(GAME_KINDS), {'pending'}, item_ids, selected,
    )
    if errors:
        for error in errors:
            print(f'apply_rereview: ERROR: {error}', file=sys.stderr)
        return 2
    failures = [
        (str(rec['id']), finding)
        for _, rec, findings in selected
        for finding in findings
        if finding.get('level') == 'FAIL'
    ]
    print(
        f'apply_rereview: prospective critique checked {len(selected)} '
        f'promotion(s), {len(failures)} FAIL finding(s)'
    )
    for item_id, finding in failures:
        print(
            f"  FAIL {item_id}: [{finding.get('check')}] "
            f"{finding.get('detail')}"
        )
    return int(bool(failures))


def updated_rejection_tombstones(
    original: bytes,
    rejected_records: list[dict],
    review_bindings: dict[str, str],
    gate_digests: dict[str, str],
) -> bytes:
    """Append exact rejected Conexiuni records without permitting ID drift."""
    data = json.loads(original.decode("utf-8"))
    critique_pack.validate_rejection_tombstones(data)
    items = data["items"]
    for rec in sorted(rejected_records, key=lambda row: str(row["id"])):
        item_id = str(rec["id"])
        groups = canonical_rejection_groups(rec)
        entry = {
            "record_sha256": critique_pack.canonical_json_sha256(rec),
            "groups_sha256": critique_pack.canonical_json_sha256(groups),
            "review_binding": review_bindings[item_id],
            "source_gate_sha256": gate_digests[item_id],
            "groups": groups,
        }
        existing = items.get(item_id)
        if existing is not None and existing != entry:
            raise SystemExit(
                f"rejection tombstone conflict for revised item: {item_id}"
            )
        items[item_id] = entry
    data["meta"]["count"] = len(items)
    data["meta"]["group_count"] = len(items) * 4
    critique_pack.validate_rejection_tombstones(data)
    return (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def updated_lant_rejection_tombstones(
    original: bytes,
    rejected_records: list[dict],
    review_bindings: dict[str, str],
    gate_digests: dict[str, str],
) -> bytes:
    """Append exact rejected Lanț pairs without permitting ID drift."""
    data = json.loads(original.decode("utf-8"))
    critique_pack.validate_lant_rejection_tombstones(data)
    items = data["items"]
    for rec in sorted(rejected_records, key=lambda row: str(row["id"])):
        item_id = str(rec["id"])
        pair = {"start": str(rec["start"]), "target": str(rec["target"])}
        entry = {
            "record_sha256": critique_pack.canonical_json_sha256(rec),
            "pair_sha256": critique_pack.canonical_json_sha256(pair),
            "review_binding": review_bindings[item_id],
            "source_gate_sha256": gate_digests[item_id],
            **pair,
        }
        existing = items.get(item_id)
        if existing is not None and existing != entry:
            raise SystemExit(
                f"Lanț rejection tombstone conflict for revised item: {item_id}"
            )
        items[item_id] = entry
    data["meta"]["count"] = len(items)
    critique_pack.validate_lant_rejection_tombstones(data)
    return (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def canonical_rejection_groups(record: dict) -> dict[str, list[str]]:
    """Normalize legacy named group keys to the durable ``g1``–``g4`` schema."""
    raw = record.get("groups")
    if (
        not isinstance(raw, dict)
        or len(raw) != 4
        or not all(isinstance(key, str) and key for key in raw)
    ):
        raise ValueError(f"invalid Conexiuni groups for {record.get('id')}")
    canonical_keys = {"g1", "g2", "g3", "g4"}
    source_keys = sorted(raw) if set(raw) != canonical_keys else ["g1", "g2", "g3", "g4"]
    return {
        f"g{index}": list(raw[source_key])
        for index, source_key in enumerate(source_keys, start=1)
    }


def current_review_bindings(item_ids: set[str]) -> dict[str, str]:
    '''Rebuild exact-batch dossiers so stale judgments cannot mutate revised content.'''
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG,
    )
    _, _, selected = critique_pack.run(
        pack, svc, strong, regions, list(GAME_KINDS), {'pending'}, item_ids,
    )
    errors = critique_pack.selection_errors(
        pack, list(GAME_KINDS), {'pending'}, item_ids, selected,
    )
    if errors:
        raise SystemExit('cannot rebuild gate dossiers: ' + '; '.join(errors))
    return {
        str(rec['id']): critique_pack.build_dossier(
            rec, game, svc, strong, findings, regions,
        )['review_binding']
        for game, rec, findings in selected
    }


def validated_artifact(
    data: object, game: str, path: Path,
) -> tuple[dict[str, str], dict, dict[str, str]]:
    '''Validate one workflow artifact and return its verdict map and shared batch.'''
    if not isinstance(data, dict):
        raise SystemExit(f'invalid verdict contract in {path}')
    verdicts = data.get('verdicts')
    per_item = data.get('perItem')
    coverage = data.get('coverage')
    batch = data.get('batch')
    valid_batch = (
        isinstance(batch, dict)
        and batch.get('version') == GATE_ARTIFACT_VERSION
        and batch.get('mode') == 'gate'
        and isinstance(batch.get('input_ids'), list)
        and all(isinstance(iid, str) and iid for iid in batch['input_ids'])
        and len(set(batch['input_ids'])) == len(batch['input_ids'])
    )
    if (
        data.get('game') != game
        or data.get('mode') != 'gate'
        or not isinstance(verdicts, dict)
        or not isinstance(per_item, list)
        or not isinstance(coverage, dict)
        or not valid_batch
    ):
        raise SystemExit(f'invalid verdict contract in {path}')

    rows: dict[str, dict] = {}
    for row in per_item:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise SystemExit(f'invalid per-item verifier record in {path}')
        iid = row['id']
        if iid in rows:
            raise SystemExit(f'duplicate per-item verifier id: {iid}')
        rows[iid] = row

    ids = set(verdicts)
    coverage_values = {
        key: coverage.get(key) for key in
        ('total', 'verified', 'unverifiedClean', 'verifiersLost', 'lost')
    }
    fully_verified = (
        set(rows) == ids
        and coverage_values == {
            'total': len(ids), 'verified': len(ids), 'unverifiedClean': 0,
            'verifiersLost': 0, 'lost': 0,
        }
        and all(
            fully_verified_gate_row(row, iid, game, verdicts[iid])
            for iid, row in rows.items()
        )
    )
    if not fully_verified:
        raise SystemExit(f'gate artifact is not fully verified: {path}')
    if game == "alchimie":
        validate_alchimie_projection_evidence(data, batch, rows, path)
    return (
        {str(iid): str(verdict) for iid, verdict in verdicts.items()},
        batch,
        {iid: row['review_binding'] for iid, row in rows.items()},
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="dir holding <game>_verdicts.json files")
    args = parser.parse_args(argv[1:])
    vdir = Path(args.dir)

    baseline = json.loads(PACK_COPIES[0].read_text(encoding='utf-8'))
    high_water = item_high_water(baseline)
    locations = {
        str(item.get('id')): (game, str(item.get('status')))
        for game in GAME_KINDS for item in baseline.get(game, [])
    }

    verdicts: dict[str, str] = {}
    review_bindings: dict[str, str] = {}
    gate_digests: dict[str, str] = {}
    batches: list[dict] = []
    for game in GAME_KINDS:
        vpath = vdir / f"{game}_verdicts.json"
        if not vpath.exists():
            continue
        artifact_bytes = vpath.read_bytes()
        data = json.loads(artifact_bytes.decode("utf-8"))
        artifact_digest = hashlib.sha256(artifact_bytes).hexdigest()
        artifact_verdicts, batch, artifact_bindings = validated_artifact(data, game, vpath)
        if game == "alchimie":
            validate_live_alchimie_projection_source(batch, vpath)
        batches.append(batch)
        for iid, verdict in artifact_verdicts.items():
            iid, verdict = str(iid), str(verdict)
            if verdict not in GATE_VERDICTS:
                raise SystemExit(f'invalid verdict for {iid}: {verdict}')
            if iid in verdicts:
                raise SystemExit(f'duplicate verdict id: {iid}')
            if iid not in locations:
                raise SystemExit(f'unknown verdict id: {iid}')
            item_game, status = locations[iid]
            if item_game != game or status != 'pending':
                raise SystemExit(
                    f'{iid} is {item_game}/{status}, expected {game}/pending'
                )
            verdicts[iid] = verdict
            review_bindings[iid] = artifact_bindings[iid]
            gate_digests[iid] = artifact_digest
    if not verdicts:
        raise SystemExit(f"no verdicts found under {vdir}")
    if any(batch != batches[0] for batch in batches[1:]):
        raise SystemExit('verdict files do not belong to the same gate batch')
    batch_ids = set(batches[0]['input_ids'])
    if batch_ids != set(verdicts):
        raise SystemExit('gate batch IDs do not exactly match the supplied verdicts')
    current_bindings = current_review_bindings(batch_ids)
    stale = sorted(
        iid for iid in batch_ids
        if review_bindings.get(iid) != current_bindings.get(iid)
    )
    if stale:
        raise SystemExit('stale gate artifact for revised content: ' + ', '.join(stale))
    promotions = {iid for iid, verdict in verdicts.items() if verdict == 'promote'}
    rejections = {iid for iid, verdict in verdicts.items() if verdict == 'reject'}
    if critique_promotions(promotions, rejections) != 0:
        raise SystemExit('promotion blocked by ADR-0023 deterministic critique gate')
    rejected_conexiuni = [
        rec
        for rec in baseline["conexiuni"]
        if str(rec.get("id")) in rejections
    ]
    rejected_lant = [
        rec
        for rec in baseline["lant"]
        if str(rec.get("id")) in rejections
    ]

    stats = Counter()
    transaction_paths = [
        *PACK_COPIES,
        *(
            [critique_pack.REJECTION_TOMBSTONES]
            if rejected_conexiuni
            else []
        ),
        *(
            [critique_pack.LANT_REJECTION_TOMBSTONES]
            if rejected_lant
            else []
        ),
    ]
    with file_transaction(transaction_paths) as originals:
        for copy in PACK_COPIES:
            pack = json.loads(originals[copy].decode('utf-8'))
            for game in GAME_KINDS:
                kept = []
                for item in pack.get(game, []):
                    verdict = verdicts.get(str(item.get('id')))
                    if item.get('status') != 'pending' or verdict in (None, 'keep'):
                        kept.append(item)
                    elif verdict == 'promote':
                        kept.append({**item, 'status': 'approved'})
                        stats['promote'] += 1
                    elif verdict == 'reject':
                        stats['reject'] += 1
                pack[game] = kept
            pack['meta']['counts'] = {g: len(pack[g]) for g in GAME_KINDS}
            pack['meta']['id_high_water'] = high_water
            atomic_write(
                copy,
                (json.dumps(pack, ensure_ascii=False, indent=1) + '\n').encode(
                    'utf-8'
                ),
            )
        if rejected_conexiuni:
            atomic_write(
                critique_pack.REJECTION_TOMBSTONES,
                updated_rejection_tombstones(
                    originals[critique_pack.REJECTION_TOMBSTONES],
                    rejected_conexiuni,
                    review_bindings,
                    gate_digests,
                ),
            )
        if rejected_lant:
            atomic_write(
                critique_pack.LANT_REJECTION_TOMBSTONES,
                updated_lant_rejection_tombstones(
                    originals[critique_pack.LANT_REJECTION_TOMBSTONES],
                    rejected_lant,
                    review_bindings,
                    gate_digests,
                ),
            )
        if validate_games_pack.main(['validate_games_pack.py']) != 0:
            raise SystemExit("pack validation failed — rolling back both copies")
        final = json.loads(PACK_COPIES[0].read_text(encoding="utf-8"))["meta"]["counts"]

    # Stats are accumulated once for each identical mirror.
    applied = {key: value // len(PACK_COPIES) for key, value in stats.items()}
    print(f"apply_rereview: {dict(applied)}")
    if rejected_conexiuni:
        print(
            "rejection tombstones now: "
            f"{len(critique_pack.load_rejection_tombstones())}"
        )
    if rejected_lant:
        print(
            "Lanț rejection tombstones now: "
            f"{len(critique_pack.load_lant_rejection_tombstones())}"
        )
    print(f"pack counts now: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
