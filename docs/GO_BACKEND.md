# Go backend migration

The owner-authorized initial migration is [ADR-0160](adr/0160-start-go-backend-with-native-intrusul.md).
Current implementation and verification are in [STATUS](STATUS.md).

## Implemented boundary

`go-backend/cmd/cat-server` serves the complete anonymous Intrusul create/get/guess/hint
API. It preserves deterministic selection and shuffle, starter/category/daily
controls, recent-source rotation, score/share/messages, hidden-answer rules and
atomic bounded sessions. It embeds a private reviewed content export and needs no
Python process for native gameplay. The remaining five games, exploration, accounts,
submissions, legal pages, SPA/static assets and full OpenAPI stay in Python.

## Build and run

Go 1.26+ is the module minimum; the qualified toolchain is 1.27.1. No external Go
modules are required. Python content generation/validation remains a build step.
Run from the repository root with its documented Python environment:

```bash
PYTHONPATH=. python scripts/export_go_content.py --check
cd go-backend
go build -o ../build/cat-server ./cmd/cat-server
../build/cat-server -listen 127.0.0.1:8081
```

Create a native game with `POST /api/wordgames/intrusul/games?seed=17`, then use its
`game_id` with the existing API paths. Standalone `/api/health` advertises only
Intrusul and `runtime: go-pilot`; unsupported games return 503. This mode does not
serve the full frontend or OpenAPI and is not ready to replace production.

To use the current frontend and all games locally, start the existing anonymous
Python web runtime on port 8000, then start the gateway:

```bash
build/cat-server -listen 127.0.0.1:8081 -python-upstream http://127.0.0.1:8000
```

Open `http://127.0.0.1:8081`. Intrusul's requests are native; other routes and assets
are delegated. Startup refuses accounts-enabled or content-mismatched upstreams,
and non-loopback/credential-bearing upstream URLs. `CAT_ACCOUNTS_ENABLED` must be
off; only the default 65536-byte `CAT_MAX_REQUEST_BYTES` budget is supported.
Existing localhost development CORS behavior is retained. Nothing changes the
production Compose/Caddy configuration or the frontend bundle.

## Content and tests

After an approved source change, regenerate with `PYTHONPATH=. python
scripts/export_go_content.py`, then run `--check`. The exporter uses validated
selectable boards, preserving release-reserve exclusions. It refuses source
overrides. `go-backend/internal/content/bundled.json` and its generated `digest.go`
are private server build inputs; never expose them as browser/mobile artifacts.
Source digests normalize line endings consistently with Python content pins.

```bash
cd go-backend
go test -race ./...
go vet ./...
go build -o ../build/cat-server ./cmd/cat-server
cd ..
PYTHONPATH=. python scripts/check_go_parity.py --binary build/cat-server
```

The differential runner uses the real Django TestClient and Go HTTP recorder,
without a network listener. It compares deterministic seeds (including large,
negative and Unicode-decimal inputs), daily/category/starter games, recent-source
rotation, complete wins/losses, hints, repeated actions, methods and validation.
Go-specific tests cover body limits, CORS, proxying, manifest/account refusal,
artifact integrity, TTL/LRU, transaction pinning and concurrent operations.

## Measurements and continuation

The [initial verification receipt](reviews/go-backend-pilot/verification.json) records
2838 matched responses, 16.0 MiB native pilot peak RSS versus 100.9 MiB Python oracle,
and median/p95 harness timings of 61.8/114.2 µs Go versus 584.9/1011.9 µs Python.
The real local gateway served the SPA and all six game creates successfully.

Add `--benchmark --report <path>` to the differential command for local aggregate
timings and process peak RSS. Go request timing excludes replay serialization;
Python timing includes the TestClient machinery. Go has only Intrusul data, while
Python loads the shared full graph. This is a pilot footprint comparison, not a
full-port benchmark or traffic capacity estimate. Gateway mode retains both heaps.

Next native candidates are Perechi and Conexiuni, reusing the selector and session
store. Before Contexto/Alchimie, benchmark graph distances and recipe generation in
Go, then evaluate Rust only if whole-session CPU/memory justify another runtime or
FFI boundary. Other repositories and the Python producer/model services are outside
this initial task.
