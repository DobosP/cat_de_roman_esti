#!/usr/bin/env python3
"""Apply a re-review verdict set to the curated games pack (promote/reject pending items).

Reads `<dir>/<game>_verdicts.json` files of the shape
`{"game": "...", "verdicts": {"<item_id>": "promote|reject|keep", ...}}` and applies them
to BOTH bundled pack copies:

* `promote` → the pending item's `status` becomes `approved` (now served);
* `reject`  → the item is removed from the pack entirely;
* `keep` / absent → left untouched (still `pending`).

Only items currently `status: pending` are eligible — an `approved` item is never touched,
so a stray verdict can't silently unpublish shipped content. Refreshes `meta.counts`, runs
the full pack validator, and ROLLS BACK both copies on any failure (the densify idiom).

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

import validate_games_pack  # noqa: E402
from import_candidates import GAME_KINDS  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="dir holding <game>_verdicts.json files")
    args = parser.parse_args(argv[1:])
    vdir = Path(args.dir)

    verdicts: dict[str, str] = {}
    for game in GAME_KINDS:
        vpath = vdir / f"{game}_verdicts.json"
        if not vpath.exists():
            continue
        data = json.loads(vpath.read_text(encoding="utf-8"))
        for iid, verdict in (data.get("verdicts") or {}).items():
            verdicts[str(iid)] = str(verdict)
    if not verdicts:
        raise SystemExit(f"no verdicts found under {vdir}")

    originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    stats = Counter()
    for copy in PACK_COPIES:
        pack = json.loads(originals[copy].decode("utf-8"))
        for game in GAME_KINDS:
            kept = []
            for item in pack.get(game, []):
                verdict = verdicts.get(str(item.get("id")))
                # Only pending items are eligible; approved/rejected untouched.
                if item.get("status") != "pending" or verdict in (None, "keep"):
                    kept.append(item)
                    continue
                if verdict == "promote":
                    item = {**item, "status": "approved"}
                    kept.append(item)
                    stats["promote"] += 1
                elif verdict == "reject":
                    stats["reject"] += 1  # dropped
                else:
                    kept.append(item)
                    stats["unknown_verdict"] += 1
            pack[game] = kept
        pack["meta"]["counts"] = {g: len(pack[g]) for g in GAME_KINDS}
        copy.write_text(json.dumps(pack, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # stats double-counted across the two identical copies — halve for the report.
    applied = {k: v // 2 for k, v in stats.items()}

    if validate_games_pack.main(["validate_games_pack.py"]) != 0:
        for copy, blob in originals.items():
            copy.write_bytes(blob)
        raise SystemExit("pack validation failed — ROLLED BACK both copies")

    final = json.loads(PACK_COPIES[0].read_text(encoding="utf-8"))["meta"]["counts"]
    print(f"apply_rereview: {dict(applied)}")
    print(f"pack counts now: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
