#!/usr/bin/env python3
"""Export the public mobile app-pack contract snapshot.

Usage:
    python scripts/export_mobile_app_pack.py [output.json]

With no output path the JSON is printed to stdout. The snapshot is deterministic
and contains only fields roedu-mobile is allowed to store/render.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cat_de_roman_esti.data import mobile_app_pack_snapshot


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("usage: python scripts/export_mobile_app_pack.py [output.json]", file=sys.stderr)
        return 2

    payload = mobile_app_pack_snapshot()
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if args:
        Path(args[0]).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
