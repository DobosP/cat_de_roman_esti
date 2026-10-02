# Anonymous native backend qualification

Valid until: a native implementation, shared export or compiled frontend changes — then requalify.

Scope and safeguards: [ADR-0161](../../adr/0161-complete-anonymous-native-backends.md).
Commands: [Native backends](../../NATIVE_BACKENDS.md). Current status: [STATUS](../../STATUS.md).

Both standalone servers implement the six games and their fallback generation,
Alchimie exploration/restores, metadata, legal notices and the tracked SPA. No Python
serving process is required. Dormant accounts and the optional submissions queue
remain outside this qualification. Production is unchanged.

## Contracts

- Each binary matched **1,207 real Django-reference HTTP responses**, normalizing
  only random `game_id` fields, including full wins for every game, game validation,
  metadata, exploration and malformed/Unicode query inputs.
- Shared frozen fixtures cover 1,269 seeded/235 daily derived-selection vectors,
  285 Perechi/Conexiuni responses, 2,595 Contexto/Lanț responses, directed graph/fuzzy
  resolver maps, all 80 Alchimie curated projections, mined difficulty cases, scored
  challenge journeys, 147 exploration crafts and all nine archived mechanics.
- Go race/vet passed across all packages. Rust formatting, strict Clippy and
  **55 tests** pass, including website compatibility and bounded session configuration.
- Python export freshness, both content validators, Ruff and the existing targeted
  Python HTTP/session gates pass. The deployed Python game algorithms were retained.

## Browser qualification and recovered race

The existing Chromium desktop/Pixel 7 suite passed 622/622 on Rust. Go passed 621/622
on its first full run; the failing mobile test concerned duplicate local scores
when two tabs adopted the same terminal Contexto session. Ten isolated repeats
passed, but source review identified a real shared frontend race: sampling time
before acquiring the Web Lock could discard another tab's newer receipt.

The fix samples the transaction clock after lock acquisition. A deterministic unit
regression reverses two queued lock callbacks and requires one score append. The
compiled frontend is regenerated with the same build process; affected browser
flows are requalified against both native servers. Final totals follow in the
verification receipt. Safari/WebKit and physical-device tests remain unqualified.

## Performance method

The reproducible Linux runner uses standalone release executables and the current
Python ASGI app, backend affinity on two distinct physical cores (logical CPUs 0/2),
client affinity on 4/6/8/10, persistent HTTP connections, fresh processes, rotating
target order and three repeats at concurrency 1/8/32. Backend
CPU and RSS exclude the client. Startup and warmup are excluded from measured CPU.
Every normalized response trace must match before results are accepted.

Two workloads are measured: six-request completed Intrusul sessions and an equal
mix of six-game puzzle creation, rotating seeds/difficulties/dailies. Results do
not establish maximum capacity, production traffic costs, TLS performance or the
worst case for sparse Alchimie fallback generation. Request latency can include
client/host scheduling. Peak RSS covers the specified retained session/cache load.

## Resource implementation

The first mixed run exposed a real allocation/search regression and timed out on
Go at concurrency 32. It is retained as a partial baseline, with that failure
explicitly marked. Indexed graph traversal/precomputed edge costs, shared dense
Contexto profiles, one quality calculation per recipe candidate and compact numeric
search inventories correct those costs without changing puzzles or RNG calls.
No Python-built projection cache was added: all cold native recipe searches and
fallback generators remain native. The finite LRU and original search bounds remain.

## Container qualification

The checked-in multi-stage recipes use the pinned official toolchains, nonroot UID
10001 and a read-only runtime containing the binary and tracked SPA. CI includes
container build, health and no-Python checks. Local registry downloads repeatedly
stalled, so container execution is **not locally qualified**. The standalone release
binaries and their actual HTTP/browser behavior are qualified locally; no production
container or deployment was changed.

## Final mixed creation result

Median of three repeats, 600 creates/run, equal six-game rotation, 8 concurrent
clients; backend CPU per created puzzle and sampled backend peak RSS.

| Runtime | CPU/create | Peak RSS | Request p95 |
|---|---:|---:|---:|
| Python | 16.25 ms | 327.7 MiB | 371.79 ms |
| Go | 4.82 ms | 165.7 MiB | 39.84 ms |
| Rust | 4.98 ms | 95.2 MiB | 128.93 ms |

Both native implementations use about **70% less CPU** than Python in this mix.
Go uses about **49% less peak RAM**, Rust about **71% less**. CPU medians are close;
Go has lower mixed-create latency while Rust has the smaller memory footprint.
The difference includes runtime scheduling, caching and allocation choices; it is
not an intrinsic-language comparison. Rust has two bounded blocking workers, which
can queue cheap requests behind expensive creates under this synthetic load.
A Go/Rust sidecar would duplicate data and add transport; these results support
choosing one complete backend for the workload rather than adding a hybrid.

[All concurrency levels and raw aggregate receipt](http-creates.json).
[Complete Intrusul journeys](http-journeys.json) use six requests/session and are a
separate workload; their CPU/session numbers must not be compared directly with
the single-request creation column. Actual hosting-plan bills are not measured.

Reproduce the final runs from the repository root (qualified release binaries):

```bash
PYTHONPATH=. python scripts/benchmark_native_http.py \
  --go-binary "$native_build_dir/cat-server" \
  --rust-binary "$native_build_dir/rust-target/release/cat-rust-server" \
  --python /path/to/production-reference-venv/bin/python \
  --report "$native_build_dir/creates.json" --workload creates \
  --flows 600 --repeats 3 --concurrency 1,8,32 --daily-every 5 \
  --cpus 0,2 --client-cpus 4,6,8,10
```

Select allowed CPUs from the host topology; the listed cores belong to this receipt's
machine. Repeat with `--workload journeys --flows 1000` for the completed-session
experiment. Earlier selected Go runs remain historical diagnostics; the final
three-target reports above were repeated with final binaries after browser testing
stopped, and every run's normalized trace and binary SHA-256 were checked.
