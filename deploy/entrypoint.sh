#!/bin/sh
# Retained Python reference/rollback entrypoint (docker-compose.python-reference.yml).
#
# This reference-only path applies legacy Django migrations and starts its Python server.
# Canonical Go profiles invoke cat-server directly; native accounts use explicit -migrate.
# Reference game sessions remain single-process. This script is not the Go entrypoint.
set -eu

if [ "${CAT_ACCOUNTS_ENABLED:-0}" = "1" ]; then
  echo "[entrypoint] applying migrations…"
  python -m django migrate --noinput
fi

exec python -m cat_de_roman_esti.web --host 0.0.0.0 --port "${PORT:-8000}"
