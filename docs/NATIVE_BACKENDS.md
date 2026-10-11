# Native Go backend and anonymous Rust reference

The native implementation and its qualification are tracked in [STATUS](STATUS.md).
The comparison decision is [ADR-0161](adr/0161-complete-anonymous-native-backends.md);
Go production selection is [ADR-0162](adr/0162-select-go-production-backend.md).
Canonical local/production launch uses Go via `run.sh` and the root Dockerfile.
Native source/build/tooling boundaries are recorded in
[ADR-0165](adr/0165-native-source-build-and-qualification.md) and
[ADR-0166](adr/0166-native-content-operators-and-builder-rails.md).

Both `go-backend/cmd/cat-server` and `rust-backend` serve the six anonymous games,
Alchimie exploration, the existing compiled SPA, category/manifest/OpenAPI responses
and the anonymous legal pages. Gameplay runs without a Python server or upstream.
The source builder and operators run natively; retained Python and Rust provide
optional independent history/reference qualification.

Go now includes optional PostgreSQL-backed password/Google/Facebook accounts, consent,
private score copies, server-verified ranking, curated history and bounded pending
submissions. [ADR-0163](adr/0163-complete-native-go-accounts.md) records that completion.
Rust remains the anonymous reference; Python sources and tests remain available offline.
Production account activation still requires the [DEPLOY](DEPLOY.md) go-live checklist.

## Build locally

The Go module and qualified compiler are **Go 1.27.1**. The Rust
package minimum is 1.98; the qualified compiler is **Rust 1.98.1**. Rust dependencies
are resolved by the checked-in `Cargo.lock`. The Go serving layer uses the standard library, pgx and the shared authentication core.

Run from the repository root. This example keeps generated artifacts in the task's
workspace scratch directory:

```bash
native_build_dir="$HOME/work/_temp/go-backend-pilot/native-release"
mkdir -p "$native_build_dir"
go -C go-backend run ./cmd/cat-content export --root .. --check
(cd go-backend && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" \
  -o "$native_build_dir/cat-server" ./cmd/cat-server)
```

The native exporter uses pinned Unicode 15 tables and private authored policy inputs.
It rebuilds all eight mutable source artifacts and checks exact private bytes/pins.
Native operator/build/audit commands: [tooling guide](NATIVE_TOOLCHAIN.md).
The retained legacy exporter can independently reproduce the historical build with
Python 3.12/Unicode 15; it is preserved as an optional oracle.

Start the selected executable from the repository root so it finds the compiled SPA:

```bash
"$native_build_dir/cat-server" -listen 127.0.0.1:8081
```

Open the matching loopback address. Every game and exploration request is native.
`/api/health` reports the same content version and six-game inventory. The private
embedded content export must never be copied into the public static directory.

## Canonical Go container

Build the root Dockerfile for local, anonymous-production and optional native-account
profiles. It builds frontend JavaScript with Node and the server with Go, serves on
container port 8000, and contains no Python interpreter. Anonymous publication and
account activation are described in [DEPLOY](DEPLOY.md).
Root/standalone Go builds require explicit owner-qualified `GATE_SHA` (40 lowercase
hex) and `GATE_TREE_SHA256` (64 lowercase hex), from the actual same-source pinned
wrapper evidence. Supply these only as build arguments; do not invent a Git-tree
hash or set runtime identity overrides. Container/source changes still need actual
qualification; these commands do not authorize deployment.

```bash
[[ ${GATE_SHA:-} =~ ^[0-9a-f]{40}$ ]] && [[ ${GATE_TREE_SHA256:-} =~ ^[0-9a-f]{64}$ ]] || exit 2
docker build --build-arg "GATE_SHA=$GATE_SHA" --build-arg "GATE_TREE_SHA256=$GATE_TREE_SHA256" \
  -t cat-de-roman-esti:local .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:8000:8000 -e CAT_ACCOUNTS_ENABLED=0 cat-de-roman-esti:local
```

## Retained native comparison containers

The following Go/Rust comparison images are separate from canonical Compose.
Build with the **repository root** as Docker context. The runtime stages contain
the executable, its operating-system dependencies and a fresh managed SPA.
They run as UID/GID **10001**, listen on container port **8080**, support a read-only
filesystem and have an HTTP health check. Python and the language compilers remain
outside the runtime images.

```bash
[[ ${GATE_SHA:-} =~ ^[0-9a-f]{40}$ ]] && [[ ${GATE_TREE_SHA256:-} =~ ^[0-9a-f]{64}$ ]] || exit 2
docker build -f go-backend/Dockerfile --build-arg "GATE_SHA=$GATE_SHA" \
  --build-arg "GATE_TREE_SHA256=$GATE_TREE_SHA256" -t cat-native-go:local .
docker build -f rust-backend/Dockerfile -t cat-native-rust:local .

docker run --rm --name cat-native-go --read-only --cap-drop ALL \
  --security-opt no-new-privileges -p 127.0.0.1:8081:8080 cat-native-go:local
docker run --rm --name cat-native-rust --read-only --cap-drop ALL \
  --security-opt no-new-privileges -p 127.0.0.1:8082:8080 cat-native-rust:local
```

The two images are independent alternatives. These commands create local test
containers; production Compose/Caddy files continue using the existing deployment.
Port publishing changes the host port while keeping the container listener and
health check on 8080. The frontend source/release-bundle convention remains
[ADR-0020](adr/0020-bound-launch-runtime-and-first-load.md).

## Qualification

The CI workflow has separate Go and Rust jobs for content freshness, formatting,
native tests, release builds, differential HTTP journeys and container checks.
Native browser jobs download those qualified executables and run the existing
desktop and mobile Playwright suite against each standalone server. The original
Python and frontend jobs remain.

```bash
(cd go-backend && go test -race ./... && go vet ./...)
go -C go-backend run ./cmd/cat-qualify parity --binary "$native_build_dir/cat-server"
```

The checked-in browser configurations are `frontend/playwright.go.config.mjs` and
`frontend/playwright.rust.config.mjs`. Their default executable locations are
`build/cat-server` and `rust-backend/target/release/cat-rust-server`, respectively,
matching the ephemeral CI checkout. For local scratch builds, a temporary config
can import `nativeConfig(runtime, absoluteBinaryPath)` from
`frontend/playwright.native.config.mjs`. The factory preserves the existing test
directory, project/browser settings, locale and time zone. It starts only the native
executable. Private `cat-browser-plan` helpers derive local fixture answers in Go.
Use `CDR_NATIVE_BINARY`, `CDR_BROWSER_PLAN_BINARY` and `CDR_E2E_OUTPUT_DIR` for
existing scratch binaries/receipts without a temporary browser configuration.

## Operating bounds

Each process keeps game sessions in memory with the default 7200-second sliding TTL,
1000-session bound per store and independent session transactions. Restarts discard
ordinary live games; validated exploration checkpoints remain restorable. Multiple
instances need session affinity until an external session store is introduced.
`CAT_SESSION_TTL_SECONDS` and `CAT_MAX_SESSIONS_PER_GAME` support positive values
(the defaults are 7200/1000); invalid settings fail startup. Source overrides and
non-default `CAT_MAX_REQUEST_BYTES` are refused. Static compression belongs in the
front proxy; packaged assets have no precompressed variants.

Resource measurements and capacity limits depend on the workload. The HTTP benchmark
in `scripts/benchmark_native_http.py` separates backend CPU/RSS from client costs and
compares fresh processes on identical CPU affinity. Its fixed-load throughput does
not establish a hosting-plan capacity or percentage hosting saving.

## Optional native accounts and pending proposals

Supply the registered `CAT_DATABASE_URL` through the secret bundle and set
`CAT_ACCOUNTS_ENABLED=1` only in an approved development/test or go-live environment.
Run `cat-server -migrate -listen 127.0.0.1:8000` against the explicit database;
anonymous mode requires no database. The optional Compose override is
`docker-compose.accounts.yml` layered on `docker-compose.yml`; `docker-compose.prod.yml`
is the standalone native account/Caddy/PostgreSQL profile. Production activation is
gated in [DEPLOY](DEPLOY.md); the public anonymous deployment enables neither.

The CLI exposes `-listen`, `-migrate` and offline `-replay` JSON-lines HTTP requests;
`-migrate` applies the native account schema only when accounts are enabled, then serves.
There is no Python management-command dependency or automatic account activation.
Anonymous mode needs no database or migration. PostgreSQL uses a bounded four-connection
pool and statement deadlines; credentials are supplied externally, never in documented
command arguments.

Native account details and migration/rollback expectations:
[accounts README](../go-backend/internal/accounts/README.md), [shared identity](../shared-go/authcore/README.md).
Registered callback paths remain `/accounts/google/login/callback/` and the Facebook
analogue. Actual provider app acceptance is a separate integration gate. Authenticated
game writes require same-origin CSRF; the existing client sends that proof and credentials.
Games bound to an account cannot be read/modified/credited by other accounts. An anonymous
session can be claimed once through an authenticated guarded action; erasure removes
identity/progress and leaves a bounded owner-free seal until expiry.

`CAT_SUBMISSIONS_DIR` enables only bounded validated private pending JSONL proposals:
no publication/promotion, no symlink-following, bounded body/file/quota and whitelisted
reviewed-content payloads. Production leaves this unset and accounts off.

Release tests supply separate explicit PostgreSQL flags:
`go -C go-backend test -race ./internal/accounts -accounts.database <disposable-dsn>`
and `go -C go-backend test -race ./internal/httpapi -arcade.database <disposable-dsn>`.
Default race runs skip database contracts and cannot substitute for these gates.

## Retained independent reference commands

The manual Rust reference preserves its complete build/test comparison:

```bash
CARGO_TARGET_DIR="$native_build_dir/rust-target" \
  cargo +1.98.1 build --manifest-path rust-backend/Cargo.toml --locked --release
(cd rust-backend && cargo +1.98.1 fmt --all -- --check \
  && cargo +1.98.1 clippy --locked --all-targets -- -D warnings \
  && cargo +1.98.1 test --locked)
PYTHONPATH=. python scripts/check_go_parity.py --runtime rust \
  --binary "$native_build_dir/rust-target/release/cat-rust-server"
```

Native fixed-workload benchmark: `cat-qualify benchmark --url <synthetic-origin>`.
The original Python benchmark is a retained historical comparison tool. Required native
commands use an executable allowlist. The active Python reference CI job still runs
automatically; making it manual is an exact policy proposal awaiting human approval
after automatic approval review rejected that change (ADR-0168).
