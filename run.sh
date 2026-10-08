#!/usr/bin/env bash
# Local managed build/run entry points; qualification remains owner-controlled.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"
die() { printf '[run] %s\n' "$*" >&2; exit 1; }

qualified_checkout() {
  [[ "${GATE_SHA:-}" =~ ^[0-9a-f]{40}$ && "$GATE_SHA" != 0000000000000000000000000000000000000000 ]] \
    || die "GATE_SHA must be the explicit owner-qualified source SHA"
  [[ "${GATE_TREE_SHA256:-}" =~ ^[0-9a-f]{64}$ && "$GATE_TREE_SHA256" != 0000000000000000000000000000000000000000000000000000000000000000 ]] \
    || die "GATE_TREE_SHA256 must be the explicit owner-qualified source tree"
  [ "$(git rev-parse --show-toplevel)" = "$SCRIPT_DIR" ] || die "Run from the real repository root"
  [ "$(git rev-parse HEAD)" = "$GATE_SHA" ] || die "Owner-qualified source SHA does not equal checkout HEAD"
  [ -z "$(git status --porcelain --untracked-files=normal)" ] || die "Owner-qualified launch requires a clean checkout"
}

cmd_docker() {
  qualified_checkout
  command -v docker >/dev/null || die "Docker is required"
  local port="${PORT:-8000}" host="${HOST:-127.0.0.1}" address iid_root iid_dir iid_file image
  [[ "$port" =~ ^[0-9]{1,5}$ ]] && (( 10#$port >= 1 && 10#$port <= 65535 )) || die "PORT must be from 1 to 65535"
  [ -n "$host" ] || die "HOST must not be empty"
  if [[ "$host" == *:* && "$host" != \[*\] ]]; then address="[$host]:$port"; else address="$host:$port"; fi
  iid_root="$HOME/work/_temp/adhoc-cat-local-docker-$(date +%Y%m%d)"
  [ "$(realpath -m -- "$iid_root")" = "$iid_root" ] || die "IID scratch path alias refused"
  (umask 077; mkdir -p -- "$iid_root")
  iid_dir="$(mktemp -d "$iid_root/build-XXXXXXXX")"
  iid_file="$iid_dir/image.iid"
  cleanup_iid() { rm -f -- "$iid_file"; rmdir -- "$iid_dir"; }
  trap cleanup_iid EXIT
  # Consume the owner's qualified pair; this does not create qualification.
  docker build --iidfile "$iid_file" --build-arg "GATE_SHA=$GATE_SHA" --build-arg "GATE_TREE_SHA256=$GATE_TREE_SHA256" "$SCRIPT_DIR"
  [ -f "$iid_file" ] && [ ! -L "$iid_file" ] || die "Docker did not produce a regular image IID"
  image="$(cat -- "$iid_file")"
  [[ "$image" =~ ^sha256:[0-9a-f]{64}$ ]] || die "Docker image IID is malformed"
  cleanup_iid
  trap - EXIT
  exec docker run --pull=never --rm -it --read-only --cap-drop ALL --security-opt no-new-privileges \
    -p "$address:8000" -e CAT_ACCOUNTS_ENABLED=0 "$image"
}

usage() {
  cat <<'HELP'
Cât de român ești? — managed local arcade

  ./run.sh [run]   Fresh owning-wrapper build, verify its receipt, serve on :8000.
  ./run.sh build   Fresh owning-wrapper build and verify its actual binary, then exit.
  ./run.sh dev     Same managed preparation; pinned-container API + Vite HMR on :5173.
  ./run.sh docker  Canonical Docker build/run alternative for an ordinary clean checkout.
  ./run.sh help    Show this help.

All modes require explicit GATE_SHA/GATE_TREE_SHA256 from the owner's same-source
qualification; there are no identity defaults. run/build/dev require the actual
fleet task worktree and its trusted gate setup, Docker and Python 3. Compilation
and installs use the owning pinned wrapper or the canonical Docker recipe.
The wrapper's real source/tree and binary receipt must match before local execution.
Accounts and submissions stay off. run accepts HOST/PORT (127.0.0.1:8000 by default).
dev requires those defaults and publishes only loopback :8000 and :5173. src/index
changes hot-reload; restart after backend, configuration or dependency changes.
HMR edits are development only and do not create a new qualified GUI identity.
HELP
}

case "${1:-run}" in
  run|build|dev)
    [ $# -le 1 ] || die "Unexpected launcher arguments"
    qualified_checkout
    exec python3 -I "$SCRIPT_DIR/scripts/gui-local-runner.py" "${1:-run}"
    ;;
  docker) [ $# -eq 1 ] || die "Unexpected launcher arguments"; cmd_docker ;;
  help|-h|--help) usage ;;
  *) usage; exit 2 ;;
esac
