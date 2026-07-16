#!/usr/bin/env python3
"""Apply a re-review verdict set to the curated games pack (promote/reject pending items).

Reads version-2 `<dir>/<game>_verdicts.json` artifacts emitted under the workflow's
`artifacts` key. Each artifact binds the exact cross-game batch, per-item verifier
coverage, and final verdicts; legacy or hand-combined verdict maps fail closed. Applies
the verified verdicts to BOTH bundled pack copies:

* `promote` → the pending item's `status` becomes `approved` (now served);
* `reject`  → the item is removed from the pack entirely;
* `keep` / absent → left untouched (still `pending`).

Only items currently `status: pending` are eligible. Batch identity, full verifier
coverage, filename/game scope, verdict enum, item ownership and status are validated
before mutation. Every ``promote`` ID is re-run through ``critique_pack.py --strict``;
then the full pack validator runs and both copies ROLL BACK on a red return or exception.

    python scripts/apply_rereview.py --dir <verdicts_dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import critique_pack  # noqa: E402
import validate_games_pack  # noqa: E402
from import_candidates import GAME_KINDS, item_high_water  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)
GATE_ARTIFACT_VERSION = 2


def critique_promotions(item_ids: set[str]) -> int:
    '''Run ADR-0023's deterministic gate over the exact pending promotion set.'''
    if not item_ids:
        return 0
    return critique_pack.main([
        'critique_pack.py',
        '--status', 'pending',
        '--ids', ','.join(sorted(item_ids)),
        '--strict',
    ])


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
            row.get('game') == game
            and row.get('final') == verdicts[iid]
            and row.get('verified') is True
            and row.get('verifier_lost') is False
            and isinstance(row.get('review_binding'), str)
            and row['review_binding'].startswith('sha256:')
            for iid, row in rows.items()
        )
    )
    if not fully_verified:
        raise SystemExit(f'gate artifact is not fully verified: {path}')
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
    batches: list[dict] = []
    for game in GAME_KINDS:
        vpath = vdir / f"{game}_verdicts.json"
        if not vpath.exists():
            continue
        data = json.loads(vpath.read_text(encoding="utf-8"))
        artifact_verdicts, batch, artifact_bindings = validated_artifact(data, game, vpath)
        batches.append(batch)
        for iid, verdict in artifact_verdicts.items():
            iid, verdict = str(iid), str(verdict)
            if verdict not in {'promote', 'reject', 'keep'}:
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
    if critique_promotions(promotions) != 0:
        raise SystemExit('promotion blocked by ADR-0023 deterministic critique gate')

    originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    stats = Counter()
    try:
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
            copy.write_text(
                json.dumps(pack, ensure_ascii=False, indent=1) + '\n', encoding='utf-8'
            )
        validation_rc = validate_games_pack.main(['validate_games_pack.py'])
    except BaseException:
        for copy, blob in originals.items():
            copy.write_bytes(blob)
        raise

    # stats double-counted across the two identical copies — halve for the report.
    applied = {k: v // 2 for k, v in stats.items()}

    if validation_rc != 0:
        for copy, blob in originals.items():
            copy.write_bytes(blob)
        raise SystemExit("pack validation failed — ROLLED BACK both copies")

    final = json.loads(PACK_COPIES[0].read_text(encoding="utf-8"))["meta"]["counts"]
    print(f"apply_rereview: {dict(applied)}")
    print(f"pack counts now: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
