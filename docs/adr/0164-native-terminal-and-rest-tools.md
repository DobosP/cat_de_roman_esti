# ADR-0164 — Native terminal, REST and mobile tools

Date: 2026-10-05
Status: accepted; broader native content-toolchain qualification remains in progress
Amends: ADR-0163's offline terminal/client boundary; serving and activation gates remain unchanged.

## Decision

The owner requested native tests, build tools and content operators in addition to Go
serving. This first independently qualified stage ports the original terminal semantic-hop
engine/client, bounded read-only RO-EDU REST smoke/export, and public mobile projection.
The Python implementations remain independent history/reference until the complete
source-build and review-operator migration passes its own qualification.

`cat-hop` preserves easy/hard distractor views, strongest-edge deterministic option order,
immediate-next-step hints, undo, 1000-point scoring and the 100-point finished-game floor.
Explicit online failures refuse play; operators can select the offline fixture explicitly.
`cat-roedu` retains all legal/provenance fields and page snapshot/release identities. It
refuses unavailable/torn/changing snapshots, duplicate IDs/cursors, redirects, unknown
legal permissions and byte/page/record cap overruns before any output commit. Fixture
export needs an explicit output path; smoke cannot report success by skipping infrastructure.
No real import or credential-backed provider was used for qualification.

`cat-mobile-pack` projects only public nodes, edges and puzzle endpoints/difficulty. It
reproduces the independent mobile hash contract, with no solution paths or hints. The
local Alchimie reviewer accessor returns a detached copy of the exact live bounded
projection/extension rail; it adds no HTTP route and cannot modify memoized game content.

## Evidence and limits

Go 1.27.1 race tests pass for terminal, REST and mobile packages; all 180 independently
stored terminal puzzle paths solve at exact optimal/par hops. Negative REST fixtures
exercise cursor/snapshot/cap/refusal/redirect/legal gates; public mobile output matches
the independent contract fixture. Focused vet passes. Full native content/export/review
and browser qualification is still required before retiring any legacy required path.
Commands and current receipts: [native tooling guide](../NATIVE_TOOLCHAIN.md) and
[STATUS](../STATUS.md). Accounts/proposals remain off in production; no deploy or push.

## Compatibility qualification amendment — 2026-10-05

ADR-0165 records the independent review follow-up: the original health-only offline
fallback is retained; a healthy server's subsequent content/provenance refusal remains
an error. Empty categories retain original selection behavior without a panic. Literal
Unicode line/paragraph separators use the independent mobile UTF-8 hash contract; literal
backslash escape text remains exact. New independent vectors cover these corrections.
