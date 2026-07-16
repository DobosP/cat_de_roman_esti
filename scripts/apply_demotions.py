#!/usr/bin/env python3
"""Apply owner-approved demotions to the curated games pack (approved -> pending).

The critique gate's sweep mode (ADR-0023/0024) emits demotion *proposals* for served
content; once the owner approves a batch, this script applies it. Reads
`<dir>/<game>_demotions.json` files of the shape
`{"game": "...", "verdicts": {"<item_id>": "demote|keep", ...}}` and applies them to
BOTH bundled pack copies:

* `demote` → the approved item's `status` becomes `pending` (withdrawn from serving,
  content preserved for revision — the ADR-0019 reversibility rule; never deletes);
* `keep` / absent → left untouched.

Only items currently `status: approved` are eligible — the mirror image of
`apply_rereview.py`. Filename/game scope, verdict enum, item ownership and status are
validated before mutation. The full pack validator then runs and both copies ROLL BACK
on a red return or exception.

    python scripts/apply_demotions.py --dir <verdicts_dir>
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

import validate_games_pack  # noqa: E402
from import_candidates import GAME_KINDS  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)


def apply(pack: dict, verdicts: dict[str, str]) -> tuple[dict, Counter]:
    """Pure demotion pass over one in-memory pack. Returns (new_pack, stats)."""
    stats: Counter = Counter()
    out = {**pack}
    for game in GAME_KINDS:
        items = []
        for item in pack.get(game, []):
            verdict = verdicts.get(str(item.get("id")))
            # Only approved items are eligible; pending/rejected untouched.
            if item.get("status") != "approved" or verdict in (None, "keep"):
                items.append(item)
                continue
            if verdict == "demote":
                items.append({**item, "status": "pending"})
                stats["demote"] += 1
            else:
                items.append(item)
                stats["unknown_verdict"] += 1
        out[game] = items
    out["meta"] = {**pack["meta"], "counts": {g: len(out[g]) for g in GAME_KINDS}}
    return out, stats


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="dir holding <game>_demotions.json files")
    args = parser.parse_args(argv[1:])
    vdir = Path(args.dir)

    baseline = json.loads(PACK_COPIES[0].read_text(encoding='utf-8'))
    locations = {
        str(item.get('id')): (game, str(item.get('status')))
        for game in GAME_KINDS for item in baseline.get(game, [])
    }

    verdicts: dict[str, str] = {}
    for game in GAME_KINDS:
        vpath = vdir / f"{game}_demotions.json"
        if not vpath.exists():
            continue
        data = json.loads(vpath.read_text(encoding="utf-8"))
        if data.get('game') != game or not isinstance(data.get('verdicts'), dict):
            raise SystemExit(f'invalid demotion contract in {vpath}')
        for iid, verdict in data['verdicts'].items():
            iid, verdict = str(iid), str(verdict)
            if verdict not in {'demote', 'keep'}:
                raise SystemExit(f'invalid verdict for {iid}: {verdict}')
            if iid in verdicts:
                raise SystemExit(f'duplicate verdict id: {iid}')
            if iid not in locations:
                raise SystemExit(f'unknown verdict id: {iid}')
            item_game, status = locations[iid]
            if item_game != game or status != 'approved':
                raise SystemExit(
                    f'{iid} is {item_game}/{status}, expected {game}/approved'
                )
            verdicts[iid] = verdict
    if not verdicts:
        raise SystemExit(f"no demotion verdicts found under {vdir}")

    originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    stats: Counter = Counter()
    try:
        for copy in PACK_COPIES:
            pack = json.loads(originals[copy].decode('utf-8'))
            pack, copy_stats = apply(pack, verdicts)
            stats.update(copy_stats)
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

    final = json.loads(PACK_COPIES[0].read_text(encoding="utf-8"))
    approved = {
        g: sum(1 for it in final[g] if it.get("status") == "approved")
        for g in GAME_KINDS
    }
    print(f"apply_demotions: {dict(applied)}")
    print(f"approved now: {approved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
