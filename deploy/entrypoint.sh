#!/bin/sh
# Production container entrypoint (used by docker-compose.prod.yml).
#
# When accounts are enabled, apply DB migrations before serving. Then exec the same single
# uvicorn process the image ships (game sessions are in-memory, so the server MUST stay
# single-process — do NOT add workers; move SessionStore to Redis first if you ever need to).
set -eu

if [ "${CAT_ACCOUNTS_ENABLED:-0}" = "1" ]; then
  echo "[entrypoint] applying migrations…"
  python -m django migrate --noinput
fi

exec python -m cat_de_roman_esti.web --host 0.0.0.0 --port "${PORT:-8000}"
