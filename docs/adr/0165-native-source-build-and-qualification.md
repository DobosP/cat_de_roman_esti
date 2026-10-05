# ADR-0165 — Native source build and independent qualification

Date: 2026-10-05
Status: accepted; full qualification completed by ADR-0168; CI reference routing pending
Amends: ADR-0162's Python content-build and mandatory HTTP/browser helper boundary.

## Decision

The owner requested native build, tests and operators in addition to Go serving. The
private source exporter and qualification paths now run in Go. Python/Django and Rust
implementations and their historical evidence remain available as independent references;
no required legacy path is retired before its native contracts pass qualification.

The exporter assembles all mutable game data from eight bounded reviewed source files.
It rebuilds graph records/defaults, labels/index/captions, reviewed ranking/selection and
reserve scopes, frozen quick/catalog identities, world mechanics/history, recipe extension
identities, metadata and the manifest. The separate authored policy input contains frozen
Unicode 15 tables, category/feedback/caption rules, OpenAPI and legal templates, with origin
hashes. Current Go Unicode tables and the private generated bundle are not source inputs.
The complete rebuilt bundle and digest pin match the independent baseline byte-for-byte.
Future policy/review-authority versions require explicit reviewed input and pin changes.

The unchanged 32-case request corpus lives in neutral `testdata/http/`; Go tests no longer
parse Rust implementation source. Private offline browser planning uses local Go services
and reviewed content, with no HTTP solution/debug route. Independent HTTP parity replays
the frozen 1207-response Django corpus with session aliases and all eight source bindings.
Digest/count/source drift refuses before requests. Generic capture/replay reports its
reference independence as unverified and cannot label candidate output independent parity.
HTTP tools cap requests/responses/calls/deadlines and refuse redirects, credential-bearing
origins and cookie forwarding. Native smoke covers six scored games, exploration restore,
and 28 static/cache/HEAD/ETag proofs. Benchmarks report measured local fixtures only.

All nine archived world books also have an independent neutral mechanics trace; every one
of its 1009 saved prefixes retains earned concepts and craft order under native restoration.
The terminal/mobile follow-up preserves the original health-only offline fallback without
swallowing content/legal refusal, and the public hash handles literal Unicode separators.
Native document checks port the independent fleet term/verb corpus and mandatory budgets.

## Qualification and retention

Focused Go 1.27.1 race/vet, exact source freshness, unchanged neutral corpora, native
compiled HTTP parity, synthetic smoke/capture/replay and bounded benchmark checks pass.
The complete fresh-checkout Go/Node/browser/disposable-PG gate is still an integration
requirement. Source operators and content builders require their separate prospective,
review/provenance/version and rollback tests before full retirement of required Python
operator/reference gates. Production accounts/proposals remain off; no live import,
promotion, provider activation, push or deployment occurs in this worker lane.

[Native tooling](../NATIVE_TOOLCHAIN.md), [proof record](../reviews/go-native-toolchain/README.md),
[STATUS](../STATUS.md) retain exact current verification and remaining boundaries.
