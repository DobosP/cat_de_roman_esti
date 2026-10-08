#!/usr/bin/env bash
# Complete native Go/Node/browser release qualification. No legacy interpreter.
set -euo pipefail
repository_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_dir"
: "${CDR_TOOLCHAIN_SCRATCH:?Set CDR_TOOLCHAIN_SCRATCH to the task workspace scratch directory}"
: "${CDR_NATIVE_TEST_DSN:?An explicit disposable PostgreSQL fixture is required}"
CDR_TOOLCHAIN_SCRATCH="$(realpath -m "$CDR_TOOLCHAIN_SCRATCH")"
case "$CDR_TOOLCHAIN_SCRATCH" in "$(realpath -m "$HOME/work/_temp")/"*) ;; *) printf 'Scratch must be under ~/work/_temp/\n' >&2; exit 2;; esac
if command -v python python3 python3.12 python3.14 rustc cargo; then printf 'Qualification requires Python/Rust absent from PATH\n' >&2; exit 2; fi
[ "$(go version)" = 'go version go1.27.1 linux/amd64' ] || { printf 'Qualified Go 1.27.1 linux/amd64 is required\n' >&2; exit 2; }
[[ "$(node --version)" == v26.10.0 ]] || { printf 'Selected Node 26.10.0 is required\n' >&2; exit 2; }
mkdir -p "$CDR_TOOLCHAIN_SCRATCH/bin" "$CDR_TOOLCHAIN_SCRATCH/go-cache" "$CDR_TOOLCHAIN_SCRATCH/go-tmp" "$CDR_TOOLCHAIN_SCRATCH/tmp" "$CDR_TOOLCHAIN_SCRATCH/receipts"
export GOMAXPROCS=2 GOFLAGS=-p=2 GOCACHE="$CDR_TOOLCHAIN_SCRATCH/go-cache" GOTMPDIR="$CDR_TOOLCHAIN_SCRATCH/go-tmp" TMPDIR="$CDR_TOOLCHAIN_SCRATCH/tmp"
[ -z "$(gofmt -l go-backend shared-go/authcore)" ]
go -C go-backend run ./cmd/cat-content validate --root ..
go -C go-backend run ./cmd/cat-content export --root .. --check
go -C go-backend run ./cmd/cat-mobile-pack --root .. --check
go -C go-backend run ./cmd/cat-content-ops rank --root .. --check
go -C go-backend run ./cmd/cat-content-ops derive --root .. --check
go -C go-backend run ./cmd/cat-content-rail all --root .. --check
go -C go-backend run ./cmd/cat-doc-check --root ..
go -C go-backend test -race ./...
go -C go-backend vet ./...
go -C shared-go/authcore test -race ./...
go -C shared-go/authcore vet ./...
go -C go-backend test -race ./internal/accounts -accounts.database "$CDR_NATIVE_TEST_DSN"
go -C go-backend test -race ./internal/httpapi -arcade.database "$CDR_NATIVE_TEST_DSN"
for native_command in cat-server cat-content cat-content-ops cat-content-rail cat-browser-plan cat-qualify cat-hop cat-roedu cat-mobile-pack cat-doc-check; do
  CGO_ENABLED=0 go -C go-backend build -trimpath -o "$CDR_TOOLCHAIN_SCRATCH/bin/$native_command" "./cmd/$native_command"
done
"$CDR_TOOLCHAIN_SCRATCH/bin/cat-qualify" parity --binary "$CDR_TOOLCHAIN_SCRATCH/bin/cat-server" --report "$CDR_TOOLCHAIN_SCRATCH/receipts/http-parity.json"

smoke_port="${CDR_SMOKE_PORT:-18143}"
[[ "$smoke_port" =~ ^[0-9]{4,5}$ ]] && ((10#$smoke_port>=1024 && 10#$smoke_port<=65535)) || { printf 'Invalid smoke port\n' >&2; exit 2; }
CAT_ACCOUNTS_ENABLED=0 CAT_SUBMISSIONS_ENABLED=0 CAT_LEGAL_OPERATOR=Synthetic-Fixture CAT_LEGAL_CONTACT_EMAIL=operator@example.invalid \
 "$CDR_TOOLCHAIN_SCRATCH/bin/cat-server" -listen "127.0.0.1:$smoke_port" > "$CDR_TOOLCHAIN_SCRATCH/receipts/smoke-server.log" 2>&1 &
smoke_pid=$!
trap 'kill "$smoke_pid" 2>/dev/null || true; wait "$smoke_pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 60); do
 if curl --max-time 1 --fail --silent --output /dev/null "http://127.0.0.1:$smoke_port/api/health"; then break; fi
 sleep 1
done
"$CDR_TOOLCHAIN_SCRATCH/bin/cat-qualify" smoke --url "http://127.0.0.1:$smoke_port" --static-root cat_de_roman_esti/web/static --report "$CDR_TOOLCHAIN_SCRATCH/receipts/smoke.json"
"$CDR_TOOLCHAIN_SCRATCH/bin/cat-qualify" benchmark --url "http://127.0.0.1:$smoke_port" --flows 24 --warmup-flows 6 --concurrency 4 --report "$CDR_TOOLCHAIN_SCRATCH/receipts/benchmark.json"
kill "$smoke_pid"; wait "$smoke_pid" || true
trap - EXIT
export CDR_NATIVE_BINARY="$CDR_TOOLCHAIN_SCRATCH/bin/cat-server" CDR_BROWSER_PLAN_BINARY="$CDR_TOOLCHAIN_SCRATCH/bin/cat-browser-plan" CDR_E2E_OUTPUT_DIR="$CDR_TOOLCHAIN_SCRATCH/receipts/browser"
(cd frontend
 npm ci --cache "$CDR_TOOLCHAIN_SCRATCH/npm-cache"
 npm test
 npm run lint
 npm run build
 npm run test:e2e)
git diff --check
printf 'Native Go/Node/browser/PostgreSQL qualification GREEN\n'
