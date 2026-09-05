# ADR-0099: Consolidate session endpoint transactions

Date: 2026-09-06
Status: accepted

## Decision

Route every existing-session endpoint for all six word games through one internal
`atomic_session` decorator factory. Keep the store and missing-session message as explicit
per-game configuration. Resolve the module-level store for every request so bounded-store
replacement in tests and runtime wiring still reaches the current store.

Keep ADR-0049's `SessionStore.transaction()` boundary unchanged: it pins the entry and holds
its per-entry lock from session lookup through public response construction. Do not move game
validation, mutation, serialization, request parsing, or selection into the shared helper.

## Context / why

Each game carried a private copy of the same transaction decorator. The six copies made a
security and concurrency boundary easy to change unevenly, while their sole intentional
contract difference was Alchimie's trailing period in the Romanian 404 detail. Capturing a
store object at decoration time was rejected because existing tests replace module stores to
exercise capacity and isolation behavior.

## Consequences

The transaction boundary now has one implementation and six small configurations. Cross-game
endpoint tests pin exact missing-session responses, actual same-session serialization through
the real routes, dynamic store replacement, and the production store defaults. Game mechanics,
query parsing, deterministic seed/daily selection, public payloads, private answers, 64 KiB
request limit, 7,200-second sliding TTL, 1,000-entry per-game cap, and `SessionStore` itself do
not change.
