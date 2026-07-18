#!/usr/bin/env python3
"""Apply the v31 basic-word wave through the shared safe transaction."""

from __future__ import annotations

import sys

from apply_common_words_v24 import main as apply_wave_main

DATA_MODULE = "basic_words_v31_data"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    return apply_wave_main(["--data-module", DATA_MODULE, *args])


if __name__ == "__main__":
    raise SystemExit(main())
