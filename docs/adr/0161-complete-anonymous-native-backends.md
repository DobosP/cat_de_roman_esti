# ADR-0161 — Complete anonymous Go and Rust backends for comparison

Date: 2026-10-02
Status: partially superseded by ADR-0162 (Go production selection; comparative implementation/evidence retained)

## Decision

The owner requested continuing the Rust performance experiment and finishing both
implementations of Cât de român ești?. Provide two alternative standalone servers:
`go-backend/` and `rust-backend/`. Each owns all six anonymous game APIs, Alchimie
exploration and restore, metadata/OpenAPI, legal pages and the existing compiled
React site. Neither requires Python to serve these paths. The existing Python
application remains the production baseline and content-validation authority.

This supersedes ADR-0160's Intrusul-only native boundary. Its reviewed content,
privacy, bounded requests and anonymous safeguards remain. The complete anonymous
release is the implementation scope; dormant accounts/OAuth, authenticated score
storage, public leaderboards and the optional submissions queue remain Python
features. Native startup refuses accounts activation; submissions remain disabled.
No deployment, remote publication, account activation or fleet-wide migration is
part of this decision.

## Compatibility

A single private schema-2 export is embedded by both binaries, pinning the complete
reviewed graph, ranked catalogs, projections, provenance, discovery histories and
Unicode 15 tables to the deployed Python 3.12 oracle. Rust reads the same Go artifact
and generated digest at build time. This avoids two independently generated data
copies. The exporter is explicitly qualified on Python 3.12 / Unicode 15; the
existing Python 3.14 test matrix remains, with export freshness checked on 3.12.

Native algorithms preserve Python integer-seeded RNG, BLAKE2b daily selection,
ordered directed BFS/Dijkstra, fuzzy text resolution, recipe projection and
floating-point ranking. CPython compensated sums and canonical sorted JSON are
reproduced where they affect selection and restore hashes. Curated puzzles and
on-demand mining remain native, with reference vectors for both. Indexed graph
traversal and shared numeric distance profiles avoid duplicate string maps;
recipe searches use compact temporary states and compute sort quality once per
candidate. These optimizations retain the same search bounds and output vectors;
no build-time recipe projection replaces the native computational engine.

Each game retains a process-local bounded sliding-TTL/LRU store. Session mutation,
validation and response generation hold one pinned transaction. Shared configuration
supports the existing TTL/cap names; defaults remain 7200 seconds and 1000 entries
per game. Requests remain capped at 65536 bytes. Content overrides and non-default
request budgets fail startup rather than silently changing the qualified contract.
Exploration restores all shipped historical formats. Its world is an immutable
startup snapshot; content changes require a rebuild and server restart.

## Qualification and measurement

Require full Go race/vet and Rust fmt/strict Clippy/tests, source freshness,
Python-reference semantic fixtures, real HTTP differential journeys for every game,
and the existing desktop/mobile browser suite on each standalone binary.

The browser gate also exposed an existing shared score-receipt race: capturing
clock time before a queued Web Lock could discard a newer receipt. Sample the
clock inside the transaction, preserving future-receipt rejection and the bounded
ledger; a reversed-lock-callback unit regression protects the correction.

Native Dockerfiles and CI jobs build/run both implementations without a Python runtime.
Local results and reproducible commands live in [STATUS](../STATUS.md),
[the native guide](../NATIVE_BACKENDS.md) and the verification receipts.

Measure release binaries against the existing ASGI application using persistent
HTTP connections, identical two-CPU affinity, fresh processes, rotating target order,
and equal request sequences. Compare complete Intrusul sessions plus a separate
six-game create workload. Compare normalized response hashes before interpreting
CPU/RSS/latency. Exclude client CPU and startup/warmup from measured backend CPU.
These fixed-load experiments are not maximum capacity, a production load trace,
heavy-fallback coverage or hosting-price promises.

## Consequences

- Either binary can serve the anonymous site alone; running Go and Rust together
  would duplicate the graph and session heaps without a demonstrated benefit.
- Python stays useful for authoring, validators, reference tests and dormant account
  features; this does not migrate the scraper or any other repository.
- Horizontal replicas require sticky sessions or a separately designed shared store;
  process-local games expire on restart, as in the current Python implementation.
- Rust adds a pinned dependency/toolchain surface; Go retains standard-library-only
  dependencies. Both ship the same public frontend and private data contracts.
- Selecting a deployment runtime remains a later operational decision based on
  workload and resource measurements, preserving the current production rollback.
