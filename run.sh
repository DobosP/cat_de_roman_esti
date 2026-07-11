#!/usr/bin/env bash
#
# run.sh — one-command launcher for the cat_de_roman_esti web app.
#
#   ./run.sh            (or ./run.sh run)  build SPA if missing, then serve the BFF
#   ./run.sh dev                           vite dev + uvicorn --reload (hot-reload)
#   ./run.sh docker                        docker build + run the image
#   ./run.sh build                         just build the SPA into web/static
#   ./run.sh help
#
# Offline by default (bundled fixture). To use a live ro_data_server, export
# ROEDU_API_URL (and optionally ROEDU_API_KEY) before running — the BFF reads them.
#
# Notes for THIS host: there is no usable venv here, so we run python via the
# romania_scraper venv with PYTHONPATH pointed at this repo. Override with
# CDR_PYTHON / CDR_PYTHONPATH if your layout differs.

set -euo pipefail

# --- Resolve paths (work regardless of the caller's cwd) ---------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Python interpreter + import path. Defaults match this host's documented layout; both
# are overridable via env so the script is portable.
CDR_PYTHON="${CDR_PYTHON:-/home/dobo/work/romania_scraper/.venv/bin/python}"
CDR_PYTHONPATH="${CDR_PYTHONPATH:-$SCRIPT_DIR}"

STATIC_INDEX="$SCRIPT_DIR/cat_de_roman_esti/web/static/index.html"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

DEFAULT_PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

# --- Small helpers -----------------------------------------------------------
log()  { printf '\033[1;36m[run]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[run]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[run]\033[0m %s\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# Pick the interpreter: prefer the configured venv python, else fall back to any
# python3 that can import django/uvicorn (so `./run.sh` still works elsewhere).
resolve_python() {
  if [ -x "$CDR_PYTHON" ]; then
    echo "$CDR_PYTHON"; return 0
  fi
  if have python3; then
    echo "python3"; return 0
  fi
  die "no python interpreter found (set CDR_PYTHON to a python with django+uvicorn)"
}

# Is a TCP port free on $HOST? Uses python's socket so we need no extra tools.
port_free() {
  local port="$1" py
  py="$(resolve_python)"
  PYTHONPATH="$CDR_PYTHONPATH" "$py" - "$HOST" "$port" <<'PY'
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.5)
try:
    s.bind((host, port))
    s.close()
    sys.exit(0)        # free
except OSError:
    sys.exit(1)        # busy
PY
}

# Find a free port starting at $1, scanning up to 20 candidates.
pick_port() {
  local start="$1" p
  for p in $(seq "$start" "$((start + 20))"); do
    if port_free "$p"; then echo "$p"; return 0; fi
  done
  die "no free port in range $start..$((start + 20))"
}

# Build the SPA into cat_de_roman_esti/web/static.
build_frontend() {
  have npm || die "npm not found — install Node 24 LTS to build the frontend"
  log "building SPA (npm) -> cat_de_roman_esti/web/static ..."
  ( cd "$FRONTEND_DIR"
    if [ -f package-lock.json ]; then npm ci; else npm install; fi
    npm run build )
  [ -f "$STATIC_INDEX" ] || die "build finished but $STATIC_INDEX is missing"
  log "SPA build OK."
}

ensure_frontend() {
  if [ -f "$STATIC_INDEX" ]; then
    log "SPA build present ($STATIC_INDEX)."
  else
    warn "no SPA build found — building it now."
    build_frontend
  fi
}

# --- Subcommands -------------------------------------------------------------

cmd_run() {
  ensure_frontend
  local py port
  py="$(resolve_python)"
  port="$(pick_port "$DEFAULT_PORT")"
  if [ "$port" != "$DEFAULT_PORT" ]; then
    warn "port $DEFAULT_PORT busy — using $port instead."
  fi

  if [ -n "${ROEDU_API_URL:-}" ]; then
    log "data source: LIVE ($ROEDU_API_URL)  [fail-soft to offline fixture]"
  else
    log "data source: OFFLINE bundled fixture (set ROEDU_API_URL for live)."
  fi

  log "starting BFF at http://$HOST:$port  (Ctrl-C to stop)"
  # ROEDU_API_URL / ROEDU_API_KEY pass through the environment to the app.
  PYTHONPATH="$CDR_PYTHONPATH" exec "$py" -m cat_de_roman_esti.web \
    --host "$HOST" --port "$port"
}

cmd_dev() {
  have npm || die "npm not found — install Node 24 LTS for dev mode"
  local py port
  py="$(resolve_python)"
  # uvicorn on the BFF port (vite proxies /api here — see vite.config.ts default 8000).
  port="$(pick_port "$DEFAULT_PORT")"

  log "dev mode: vite (hot SPA) + uvicorn --reload (hot API) ..."
  log "  API   : http://$HOST:$port"
  log "  vite  : http://localhost:5173  (open THIS for the live UI)"
  warn "vite.config.ts proxies /api -> http://127.0.0.1:8000; if API port != 8000,"
  warn "edit the proxy target or run with PORT=8000."

  # Start uvicorn --reload in the background; kill the whole group on exit.
  PYTHONPATH="$CDR_PYTHONPATH" "$py" -m cat_de_roman_esti.web \
    --host "$HOST" --port "$port" --reload &
  local api_pid=$!
  cleanup() { kill "$api_pid" 2>/dev/null || true; }
  trap cleanup EXIT INT TERM

  ( cd "$FRONTEND_DIR"
    [ -d node_modules ] || { if [ -f package-lock.json ]; then npm ci; else npm install; fi; }
    npm run dev )
}

cmd_docker() {
  have docker || die "docker not found — install Docker to use ./run.sh docker"
  local port="${PORT:-8000}"
  log "building image cat-de-roman-esti:latest ..."
  docker build -t cat-de-roman-esti:latest "$SCRIPT_DIR"
  log "running container on http://localhost:$port  (Ctrl-C to stop)"
  # Forward live-server env if set; otherwise the container plays offline.
  exec docker run --rm -it \
    -p "$port:8000" \
    -e "PORT=8000" \
    ${ROEDU_API_URL:+-e "ROEDU_API_URL=$ROEDU_API_URL"} \
    ${ROEDU_API_KEY:+-e "ROEDU_API_KEY=$ROEDU_API_KEY"} \
    cat-de-roman-esti:latest
}

usage() {
  cat <<'EOF'
cat_de_roman_esti launcher

  ./run.sh [run]    build the SPA if missing, then serve the BFF (default :8000,
                    auto-falls-back to the next free port). Offline by default.
  ./run.sh dev      vite dev server + uvicorn --reload for hot-reload development.
  ./run.sh docker   docker build + run the production image.
  ./run.sh build    build the SPA into cat_de_roman_esti/web/static and exit.
  ./run.sh help     show this help.

Env:
  PORT            preferred port (default 8000).
  HOST            bind host (default 127.0.0.1).
  ROEDU_API_URL   point at a live ro_data_server (unset = offline fixture).
  ROEDU_API_KEY   API key for the live server (default cat-de-roman-dev).
  CDR_PYTHON      python interpreter (default: romania_scraper venv python).
  CDR_PYTHONPATH  import path (default: this repo root).
EOF
}

# --- Dispatch ----------------------------------------------------------------
case "${1:-run}" in
  run|"")  cmd_run ;;
  dev)     cmd_dev ;;
  docker)  cmd_docker ;;
  build)   build_frontend ;;
  help|-h|--help) usage ;;
  *) warn "unknown command: $1"; usage; exit 2 ;;
esac
