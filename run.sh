#!/usr/bin/env bash
# Default Go anonymous arcade launcher; Python remains an offline content/test tool.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
STATIC_INDEX="$SCRIPT_DIR/cat_de_roman_esti/web/static/index.html"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
native_port="${PORT:-8000}"
native_host="${HOST:-127.0.0.1}"
native_build_dir="$HOME/work/_temp/adhoc-cat-native-$(date +%Y%m%d)"
native_repository_key="$(printf '%s' "$SCRIPT_DIR" | cksum)"
native_repository_key="${native_repository_key%% *}"
native_binary="$native_build_dir/cat-server-$native_repository_key"

log() { printf '[run] %s\n' "$*"; }
die() { printf '[run] %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

validate_address() {
  [[ "$native_port" =~ ^[0-9]{1,5}$ ]] || die "PORT must be an integer from 1 to 65535"
  (( 10#$native_port >= 1 && 10#$native_port <= 65535 )) || die "PORT must be from 1 to 65535"
  [ -n "$native_host" ] || die "HOST must not be empty"
  if [[ "$native_host" == *:* && "$native_host" != \[*\] ]]; then
    native_address="[$native_host]:$native_port"
  else
    native_address="$native_host:$native_port"
  fi
}

build_frontend() {
  have npm || die "npm not found; install Node 24 to build the SPA"
  (cd "$FRONTEND_DIR" && npm ci && npm run build)
  [ -f "$STATIC_INDEX" ] || die "SPA build did not produce index.html"
}

ensure_frontend() {
  [ -f "$STATIC_INDEX" ] || build_frontend
}

build_backend() {
  have go || die "Go not found; install the qualified Go 1.27.1 toolchain"
  mkdir -p "$native_build_dir/go-cache" "$native_build_dir/go-tmp"
  log "building Go backend (incremental cache in workspace scratch)"
  (cd "$SCRIPT_DIR/go-backend"
    CGO_ENABLED=0 GOCACHE="$native_build_dir/go-cache" GOTMPDIR="$native_build_dir/go-tmp" \
      go build -trimpath -ldflags="-s -w" -o "$native_binary.$$" ./cmd/cat-server)
  mv "$native_binary.$$" "$native_binary"
}

cmd_run() {
  validate_address
  ensure_frontend
  build_backend
  log "Go anonymous arcade: http://$native_address (Ctrl-C to stop)"
  exec "$native_binary" -listen "$native_address"
}

cmd_dev() {
  validate_address
  have npm || die "npm not found; install Node 24 for frontend development"
  [ "$native_host" = "127.0.0.1" ] && [ "$native_port" = "8000" ] \
    || die "Vite's checked-in API proxy requires HOST=127.0.0.1 PORT=8000"
  build_backend
  "$native_binary" -listen "$native_address" &
  native_api_pid=$!
  cleanup() { kill "$native_api_pid" 2>/dev/null || true; wait "$native_api_pid" 2>/dev/null || true; }
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  log "Go API: http://$native_address; Vite UI: http://localhost:5173"
  log "Restart this command after backend source changes; Vite reloads frontend changes."
  (cd "$FRONTEND_DIR"
    [ -d node_modules ] || npm ci
    npm run dev)
}

cmd_docker() {
  validate_address
  have docker || die "Docker not found"
  docker build -t cat-de-roman-esti:latest "$SCRIPT_DIR"
  log "Go container: http://$native_address (Ctrl-C to stop)"
  exec docker run --rm -it --read-only --cap-drop ALL --security-opt no-new-privileges \
    -p "$native_address:8000" -e CAT_ACCOUNTS_ENABLED=0 cat-de-roman-esti:latest
}

usage() {
  cat <<'HELP'
Cât de român ești? — Go anonymous arcade

  ./run.sh [run]   Build Go (and SPA if missing), then serve on localhost:8000.
  ./run.sh dev     Go API + Vite frontend development server; rerun after Go edits.
  ./run.sh docker  Build and run the canonical Go image; no Python serving runtime.
  ./run.sh build   Rebuild the SPA and Go executable, then exit.
  ./run.sh help    Show this help.

PORT defaults to 8000; HOST defaults to 127.0.0.1. A busy port fails explicitly.
Gameplay uses the reviewed embedded content. Accounts remain unsupported.
Generated Go binaries/caches live under ~/work/_temp/adhoc-cat-native-YYYYMMDD/.
HELP
}

case "${1:-run}" in
  run|"") cmd_run ;;
  dev) cmd_dev ;;
  docker) cmd_docker ;;
  build) build_frontend; build_backend ;;
  help|-h|--help) usage ;;
  *) usage; exit 2 ;;
esac
