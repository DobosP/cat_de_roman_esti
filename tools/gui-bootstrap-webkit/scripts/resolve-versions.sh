#!/usr/bin/env bash
set -euo pipefail
exec node web-kit/scripts/resolve-versions.mjs "$@"
