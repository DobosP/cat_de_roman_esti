# Native Go backend and anonymous Rust reference

The native implementation and its qualification are tracked in [STATUS](STATUS.md).
The comparison decision is [ADR-0161](adr/0161-complete-anonymous-native-backends.md);
Go production selection is [ADR-0162](adr/0162-select-go-production-backend.md).
Canonical local/production launch uses Go via `run.sh` and the root Dockerfile.
The runtime is Python-free; Python content/reference tools run outside it.

Both `go-backend/cmd/cat-server` and `rust-backend` serve the six anonymous games,
Alchimie exploration, the existing compiled SPA, category/manifest/OpenAPI responses
and the anonymous legal pages. Gameplay runs without a Python server or upstream.
Python remains the content producer and the reference used by development tests.

Go now includes optional PostgreSQL-backed password/Google/Facebook accounts, consent,
private score copies, server-verified ranking, curated history and bounded pending
submissions. [ADR-0163](adr/0163-complete-native-go-accounts.md) records that completion.
Rust remains the anonymous reference; Python remains offline content/reference tooling.
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
PYTHONPATH=. python scripts/export_go_content.py --check
(cd go-backend && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" \
  -o "$native_build_dir/cat-server" ./cmd/cat-server)
CARGO_TARGET_DIR="$native_build_dir/rust-target" \
  cargo +1.98.1 build --manifest-path rust-backend/Cargo.toml --locked --release
```

The content exporter requires **Python 3.12 / Unicode 15.0.0** so normalization,
letter classification, redacted label patterns and private source pins match the
qualified reference. Run content regeneration and `--check` with that interpreter.
Other supported Python versions still test the Python application; they do not
regenerate this native export.

Start either executable from the repository root so it finds the compiled SPA:

```bash
"$native_build_dir/cat-server" -listen 127.0.0.1:8081
"$native_build_dir/rust-target/release/cat-rust-server" --listen 127.0.0.1:8082
```

Open the matching loopback address. Every game and exploration request is native.
`/api/health` reports the same content version and six-game inventory. The private
embedded content export must never be copied into the public static directory.

## Containers

Build with the **repository root** as Docker context. The runtime stages contain
the executable, its operating-system dependencies and the tracked compiled SPA.
They run as UID/GID **10001**, listen on container port **8080**, support a read-only
filesystem and have an HTTP health check. Python and the language compilers remain
outside the runtime images.

```bash
docker build -f go-backend/Dockerfile -t cat-native-go:local .
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
(cd rust-backend && cargo +1.98.1 fmt --all -- --check \
  && cargo +1.98.1 clippy --locked --all-targets -- -D warnings \
  && cargo +1.98.1 test --locked)

PYTHONPATH=. python scripts/check_go_parity.py --binary "$native_build_dir/cat-server"
PYTHONPATH=. python scripts/check_go_parity.py --runtime rust \
  --binary "$native_build_dir/rust-target/release/cat-rust-server"
```

The checked-in browser configurations are `frontend/playwright.go.config.mjs` and
`frontend/playwright.rust.config.mjs`. Their default executable locations are
`build/cat-server` and `rust-backend/target/release/cat-rust-server`, respectively,
matching the ephemeral CI checkout. For local scratch builds, a temporary config
can import `nativeConfig(runtime, absoluteBinaryPath)` from
`frontend/playwright.native.config.mjs`. The factory preserves the existing test
directory, project/browser settings, locale and time zone. It starts only the native
executable. Python calls in test helpers provide offline fixture answers.

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
`docker-compose.accounts.yml`, with production activation gated in DEPLOY.md.

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
