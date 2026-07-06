"""Diff two api_golden.py captures (old vs new backend) and report contract drift.

    python scripts/api_golden_diff.py golden-fastapi.json golden-django.json

Exit 0 = identical contract (modulo normalized volatiles), 1 = drift (printed).
"""

from __future__ import annotations

import json
import sys


def flatten(prefix: str, value: object, out: dict[str, object]) -> None:
    if isinstance(value, dict):
        for k in sorted(value):
            flatten(f"{prefix}.{k}", value[k], out)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            flatten(f"{prefix}[{i}]", item, out)
    else:
        out[prefix] = value


def main() -> int:
    old = json.load(open(sys.argv[1], encoding="utf-8"))
    new = json.load(open(sys.argv[2], encoding="utf-8"))
    drift = 0

    for flow in sorted(set(old) | set(new)):
        if flow not in old or flow not in new:
            print(f"[{flow}] present only in {'old' if flow in old else 'new'}")
            drift += 1
            continue
        a, b = {}, {}
        flatten("", old[flow], a)
        flatten("", new[flow], b)
        keys = sorted(set(a) | set(b))
        diffs = [
            f"  {k}: {a.get(k, '<absent>')!r} -> {b.get(k, '<absent>')!r}"
            for k in keys
            if a.get(k, "<absent>") != b.get(k, "<absent>")
        ]
        if diffs:
            print(f"[{flow}]")
            print("\n".join(diffs))
            drift += 1

    print(f"\n{'DRIFT in ' + str(drift) + ' flow(s)' if drift else 'contract identical'} "
          f"({len(set(old) | set(new))} flows compared)")
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
