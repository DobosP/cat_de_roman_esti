# ADR-0160 — Begin the Go backend with a native Intrusul migration pilot

Date: 2026-10-01
Status: accepted

## Decision

The owner requested beginning the Go backend port after considering long-term
resource efficiency and inexpensive scaling. The first complete game is anonymous
Intrusul. Its Go HTTP API, selector and bounded session store live in `go-backend/`.
The React application, Python content tools and deployed Django release remain.

The pilot has no external Go dependencies. It preserves the reviewed catalog's
weighted source/category selection, preferred and starter shelves, source rotation,
daily BLAKE2b rendezvous, Python integer-seeded MT19937 shuffle, scoring and privacy
rules. Request integer parsing targets the deployed Python 3.12 Unicode 15 tables.
Python remains the validation authority for content: a deterministic private export
includes reviewed selectable boards, exact display labels, manifest and source
digests. A separate generated SHA-256 pin binds the embedded export; CI checks both
against the current Python loader. No new content is generated or approved.

The default listener is loopback. Standalone mode exposes the native game and a
limited truthful metadata surface; it is not the six-game SPA server. Opt-in gateway
mode delegates other routes to a numeric-loopback anonymous Python upstream after
checking accounts are off and its manifest matches the embedded graph. Native
Intrusul never calls Python. Unknown-length bodies are bounded before dispatch;
session mutations and input validation retain one pinned transaction.

## Verification and rollout

Golden selection/RNG vectors and real Django/Go HTTP differential journeys are
required alongside Go race tests, vet, content freshness, and existing backend
gates. Random session IDs are the only normalized response field. Tests use replay
without sockets or production data. Current receipts and commands are in
[the migration guide](../GO_BACKEND.md) and [STATUS](../STATUS.md).

No production replacement, accounts activation or remote publication follows from
this pilot. All six current Python games remain the deployment baseline. A later
native game adds its own contract/golden journeys before taking ownership of its
route. The fleet hosting decision remains outside this repository's mutation scope.

## Rust evaluation

The first game is mostly selection, HTTP and bounded session work. It establishes a
Go baseline, not evidence that every game has the same cost. Evaluate Rust for the
graph/recipe computation when Contexto or Alchimie is ported: compare identical
inputs and whole-session CPU, retained memory, concurrency and p95 latency. Prefer
Go alone unless a native Rust kernel or complete game backend demonstrates a
material benefit after including transport, duplicated data and build complexity.

## Consequences

- Sessions stay process-local with 7200-second sliding TTL, 1000 entries and LRU
  eviction; the migration does not claim horizontal scaling or session persistence.
- Python-generated source pins and labels must be regenerated through the exporter
  after reviewed content changes; the private artifact never belongs in static assets.
- A Go+Python gateway temporarily retains both runtimes. Intrusul-only measurements
  cannot be advertised as full-arcade savings, production capacity or a cheaper bill.
- Accounts, custom source overrides and non-default request-size configuration are
  unsupported by this pilot and fail closed rather than silently diverging.
