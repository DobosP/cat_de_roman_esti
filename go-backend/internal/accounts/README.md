# Native account persistence

The native PostgreSQL adapter preserves the account API and consent gates used
by the SPA. Login identity comes from `shared-go/authcore`; this package controls
current policy acceptance, a sticky below-threshold age hold, private progress,
explicit public nicknames and erasure. Login never grants age or consent status.

The `CAT_ACCOUNTS_ENABLED=1` CLI path opens the explicitly configured PostgreSQL database.
With `-migrate`, it calls `Migrate` before `NewStore`, `authcore.New` and `New`; without
that flag the schema must already exist. Anonymous startup uses no database. Migration creates
`cat_native_*` tables and imports the existing `auth_user`, allauth provider IDs
and account records once under an advisory lock. Password hashes and numeric
user IDs remain usable. Existing Django sessions are retired; migrated users
sign in again. Legacy tables remain for reviewed rollback, and erasure deletes
their matching account copies as well as all native account rows. Import expects
the current Django account migration schema. A later dump cannot be imported
after the one-time marker is recorded: restore the legacy database before first
native initialization.

The adapter implements atomic database-backed OAuth state and attempt counters.
State expires after five minutes and at most 1,024 pending flows are retained.
Auth attempts expire after one minute with ten attempts per client digest and a
4,096-key bound. Sessions retain at most ten current tokens per user. All these
limits apply across replicas sharing the same database.

The private score copy retains the newest 500 arrivals per user. Client-provided
timestamps affect display order; they cannot pin retained rows. Browser score
uploads never populate the public leaderboard. `RecordVerifiedBest` is only for
server-authored terminal results and locks the same profile row as other account
writes before checking current consent. Equal leaderboard scores share
competition rank. Public responses expose explicit nicknames and verified scores
only; email, real name, avatar and puzzle identities are excluded.

`Finished` and `RecordPlayed` handle stable curated puzzle IDs. The game engine
must pass curated IDs only, never mined identity keys that could reveal answers.
Anonymous game actions remain available independently of account storage.

`Handle` dispatches account endpoints; `Register` mounts them on a `ServeMux`.
Mount the application-specific `Logout` separately if using the shared auth
registration, to preserve the existing `{\"ok\":true}` payload.

Integration tests use a disposable PostgreSQL database and isolated schemas:
`go test -race ./internal/accounts -args -accounts.database=<test-connection>`.
Ordinary runs report the database-required tests as skipped if no fixture is
provided. The release gate must supply the fixture and run those tests.

Native authenticated game ownership is private and transactional. Authenticated
creation binds the opaque game to that account before returning it. An anonymous
game stays anonymous until the first authenticated, CSRF-validated request claims
it; an ordinary unclaimed GET does not credit progress. Other accounts and logged-out
callers receive the same private 404 before reading or modifying an owned game.
Only the bound account's server-authored terminal result can enter verified bests
or the finished-curated-key ledger. Browser score uploads remain private receipts.
Ownership is retained as a game-capability digest with a user FK, a 6000-row hard cap,
and a startup-captured expiry at least twice the game TTL (four hours by default).
Account erasure drops the identity link and keeps a bounded anonymous seal until
expiry, so a live game cannot be transferred to a new account. No capability,
private puzzle key or account identifier is logged by this path.

The combined real HTTP fixture gate is
`go test -race ./internal/httpapi -args -arcade.database=<disposable-connection>`.
It covers native signup/login, consent/opt-in, terminal score provenance, independent
private-score JSON export, ownership/claim races, logout/re-login and erasure.

CLI/profile operations are documented in [NATIVE_BACKENDS](../../../docs/NATIVE_BACKENDS.md)
and [DEPLOY](../../../docs/DEPLOY.md). `CAT_DATABASE_URL` (or the compatibility
`DATABASE_URL`) is supplied externally; the pool is bounded to four connections.
`CAT_DOMAIN` selects the HTTPS account origin; only `CAT_DEBUG=1` permits a loopback
development origin without that domain. Google/Facebook adapters are conditional on
configured provider credentials and use the preserved `/accounts/<provider>/login/callback/`
paths. None of these flags activates production accounts without the go-live gates.
