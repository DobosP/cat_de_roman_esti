# ADR-0234 — Anonymous daily board place, off by default

Date: 2026-11-16
Status: accepted and qualified on local product `abda879a`
Amends: [ADR-0061](0061-device-local-progress-and-upload-only-private-backup.md)

Paul's decision: “Build it, switched off”. This adds an optional comparison to
the result of one curated daily board in one game. Counts represent rounds.
Paul owns activation, publication, deployment and final privacy wording.

## Decision

The server groups anonymous rounds by rules version, sealed content digest,
Bucharest calendar date, game and curated board ID. Only that day's and the
previous day's dates are eligible. The server records a session's first
eligible terminal outcome once, based on the game engine's terminal
transition. Account progress runs through its existing path. The enabled
Lanț help action sends a one-time terminal give-up for eligible rounds.
The client keeps its local give-up flow whenever the server omits support.

Each board keeps a bounded histogram of steps for wins and separate totals
for losses and give-ups. The response on eligible daily wins includes
`place {better_than_pct, tier, rounds}` when at least 100 completed rounds
exist. The percentage is the floor of 100 times the fraction with strictly
more steps or a loss or give-up. Ties remain outside the numerator. The four
tiers are Perfect (zero steps), Top 10% (90 or higher), Prima jumătate (50 or
higher) and Ai reușit. The result hides place on a replay.

The server processes at most 20 eligible terminal samples in a ten-minute
window per forwarded client address from the trusted Caddy ingress. The
rate-limit keys live only in memory. Snapshot files carry only board keys,
histograms and aggregate totals. Guesses, addresses, session IDs, account
IDs and browser identifiers are excluded from the snapshots.

An unset `CAT_BOARD_STATS_DIR` disables the feature and omits `place`.
When explicitly enabled, one process holds an exclusive directory lock.
It flushes changed per-day snapshots in batches and at shutdown using a
temporary file and atomic rename. It loads valid snapshots at startup,
reports and skips corrupt ones, and retains 14 Bucharest calendar days.
The optional storage mount allows UID 10001 to write while the application
root stays read-only.

## Qualification

The exact unit and full gate commands, SHA-256 receipts and budgets are in the
[acceptance record](../reviews/redesign-v2-m2/acceptance.json). A temporary
snapshot read error withholds placement and keeps the existing bytes available
for later reads. Invalid snapshots are reported and skipped. The request
observer attempts each terminal sample once.

## Privacy wording for Paul

„Când comparația zilnică este activată, păstrăm timp de 14 zile totalurile
rundelor finalizate și distribuția numărului de pași la victorie. Adresa de
rețea este folosită temporar, în memorie, pentru a limita abuzul.”

## Amendment 2026-11-17

### B1 — bounded network prefixes

The limiter shares 20 samples per ten minutes within an IPv6 /64. IPv4 and
IPv4-mapped IPv6 share one full-address key. Each IPv6 /48 can occupy at most
64 of the 4,096 active buckets. A new bucket at the global capacity evicts
the least recently active bucket. Keys and prefix counts expire in memory.
Before activation, verify that Docker preserves real IPv6 client addresses
through the Caddy ingress as described in [DEPLOY](../DEPLOY.md).

### B2 — Advisory replay exclusion

Daily creates accept the optional boolean query parameter `replay=true`. The
client sends it when opening another session for a daily already marked as
started. The flag is fixed in the bounded server session before publication.
Replays receive no place and never contribute a sample. This is advisory, and
a client may omit it. The in-memory limiter remains the abuse bound.

### B3 — Placement requires an admitted sample

The session's terminal observer keeps the first outcome and whether its sample
was actually recorded. A refused rate-limit, snapshot read or capacity attempt
omits place on both the terminal response and later reads. An accepted sample
can show updated aggregate placement without adding a second sample.

### B6 — One terminal observation path and reachable tiers

All six services use the response observer inside the action's existing
transaction. The separate test-only terminal accessors are removed. Cald sau
Rece has three displayed podium tiers because its rules do not award Perfect.

### B4 — clock jumps and recorded retention

A calendar reading more than two days ahead of the last trusted reading
withholds samples and placement, reports the anomaly once, and leaves the
trusted date and snapshots intact. Normal periodic checks can advance the
trusted date during idle time. Retention advances only with a successfully
recorded round or a validated snapshot, keeping 14 calendar dates ending at
the newest recorded date. Idle snapshots can therefore outlive 14 wall-clock
days. Startup reads existing data before pruning and establishes a fresh
clock guard, allowing a service restarted after a long gap to resume.

### B5 — reserved final flush time

HTTP shutdown drains for at most seven seconds and closes remaining network
connections on timeout. The aggregate store then receives an independent
three-second close budget, including after a serving error. The optional
stats Compose profile grants a 20-second stop grace. A failed or timed-out
final flush is reported. A hung handler regression verifies that pending
data reaches its snapshot and the directory lock is released after the
HTTP deadline expires.

### Privacy draft correction

The 2026-11-16 privacy draft above predates the requested recorded-date
retention rule. The retained window comprises 14 board dates relative to the
latest date with recorded data. During a period with no new recorded date,
snapshot files may remain longer than 14 elapsed days. Final privacy wording
must describe that retention before Paul activates the feature.
