#!/usr/bin/env python3
"""Apply V81 walnut links through the rollback-safe graph transaction."""

from __future__ import annotations

import sys

from apply_common_words_v24 import main as apply_wave_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    return apply_wave_main(["--data-module", "nuca_feedback_v81_data", *args])


if __name__ == "__main__":
    raise SystemExit(main())
