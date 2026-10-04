# ADR-0163 — Complete native Go accounts and serving

Date: 2026-10-04
Status: accepted implementation direction; offline terminal/client boundary amended by ADR-0164; production accounts remain gated
Amends: ADR-0162's anonymous runtime boundary; Go selection remains unchanged.

## Decision

The owner requested the whole serving implementation in Go for the arcade and Social
Activities app. Optional native PostgreSQL accounts now complement the six game engines,
exploration, metadata, legal/static serving and bounded pending proposals. The release
image executes no Python/Django server, proxy or worker. Offline content validators,
Python differential oracles and manual Rust comparison remain available.

`shared-go/authcore` is the canonical MIT-licensed native identity module. It provides
password login/signup, Google/Facebook authorization-code adapters and revocable opaque
sessions, browser-bound CSRF/state/nonce/PKCE and bounded password verification. Login
never grants age/consent/public-listing status. Existing supported password/provider IDs
are migrated once without resetting users; previous Django sessions retire.

The application owns sticky minor holds, current privacy/terms acceptance, private progress,
explicit public nicknames, private score-copy retention, server-authored verified bests,
curated played-key history and erasure. Client-uploaded scores never become public bests.
Private game ownership prevents one completed game from crediting multiple accounts;
first claims are serialized, and erasure seals ownership until the bounded session expiry.
Anonymous gameplay remains independently available. Engine state stays process-local and
replicas require affinity; durable account state is database-backed.

All four proposal handlers validate reviewed content against the native startup snapshot
and append to bounded, private pending queues. They do not publish/promote content.
Production accounts and submissions remain disabled until their go-live gates are met.

## Consequences and qualification

The Go account module depends on pgx and the canonical shared identity core; consumer
apps carry reviewed hash-pinned portable copies with no production checkout dependency.
Credentials deploy by registered names through the fleet SOPS path, never source/docs/logs.
Actual registered OAuth callbacks remain an integration gate beyond local mock-provider tests.

Release qualification includes race/vet, explicit disposable PostgreSQL account and
combined HTTP gameplay proofs, migrations/erasure/concurrency/adversarial ownership,
independent Python proposal/content/HTTP goldens, frontend/browser contracts and a
Python-free nonroot read-only release image. Exact results belong in STATUS/WORKLOG.
The authorized anonymous rollout keeps account/proposal flags off and preserves rollback.
