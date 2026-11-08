#!/usr/bin/env bash
set -euo pipefail
exec python3 -IB "$(dirname -- "${BASH_SOURCE[0]}")/run_4i.py" "$@"
