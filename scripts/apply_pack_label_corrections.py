#!/usr/bin/env python3
"""Apply exact reviewed source-label repairs to both pack mirrors atomically.

Read-only by default; use --write after reviewing the checked-in corrections.
Then run the established ranking and derived-catalog generators for the release.
No status, member, order, selection or graph field is editable through this path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from cat_de_roman_esti.wordgames.label_corrections import CORRECTIONS, corrected_pack  # noqa: E402
from scripts import validate_games_pack  # noqa: E402
from scripts.content_file_transaction import atomic_write, file_transaction  # noqa: E402

PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    with file_transaction(PACK_COPIES) as originals:
        if len(set(originals.values())) != 1:
            raise ValueError("label correction requires byte-identical pack mirrors")
        candidate = corrected_pack(json.loads(originals[PACK_COPIES[0]]))
        blob = (json.dumps(candidate, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        count = sum(len(correction.groups) for correction in CORRECTIONS)
        if not args.write:
            print(f"label corrections: {count} labels verified; dry run, no writes")
            return 0
        for path in PACK_COPIES:
            atomic_write(path, blob)
        if validate_games_pack.main(["validate_games_pack.py"]) != 0:
            raise ValueError("label correction pack validation failed; rolling back")
    print(f"label corrections GREEN: {count} labels applied to both mirrors")
    print("Regenerate board_rankings_v37 and derived_catalog_v38 before release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
