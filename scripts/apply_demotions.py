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
`apply_rereview.py`, which only touches `pending`, so the two scripts can never fight
over the same item. Refreshes `meta.counts`, runs the full pack validator, and ROLLS
BACK both copies on any failure (the densify idiom).

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

    verdicts: dict[str, str] = {}
    for game in GAME_KINDS:
        vpath = vdir / f"{game}_demotions.json"
        if not vpath.exists():
            continue
        data = json.loads(vpath.read_text(encoding="utf-8"))
        for iid, verdict in (data.get("verdicts") or {}).items():
            verdicts[str(iid)] = str(verdict)
    if not verdicts:
        raise SystemExit(f"no demotion verdicts found under {vdir}")

    originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    stats: Counter = Counter()
    for copy in PACK_COPIES:
        pack = json.loads(originals[copy].decode("utf-8"))
        pack, copy_stats = apply(pack, verdicts)
        stats.update(copy_stats)
        copy.write_text(json.dumps(pack, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # stats double-counted across the two identical copies — halve for the report.
    applied = {k: v // 2 for k, v in stats.items()}

    if validate_games_pack.main(["validate_games_pack.py"]) != 0:
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
