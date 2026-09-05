# ADR-0105: Deduplicate local terminal score receipts across tabs

Date: 2026-09-06
Status: accepted

## Decision

Record each server-terminal game ID into local score history once. The completion recorder
uses one same-origin Web Lock for the entire score store because every score update rewrites
the whole board. A local-only receipt ledger retains opaque game IDs for 24 hours, prunes
malformed and future rows, and keeps at most 1,000 receipts per game.

The six terminal effects await the recorder and ignore late UI callbacks after cleanup.
Strict Mode setups reuse the same in-component promise. Contexto giveup continues to clear
its resume pointer without recording a score.

Keep receipts out of score rows, history export/import, and account score transport. Clearing
local score history also clears the receipt ledger. If storage or Web Locks are unavailable,
play continues; the ledger still deduplicates sequential calls when storage works, but
concurrent-tab deduplication is best-effort without Web Locks.

## Context

ADR-0101 made all six games adopt a saved terminal session so normal result and score effects
run after recovery. Two tabs could both adopt the same terminal response before either effect
removed the resume pointer. Their component-local guards then appended two history rows and
incremented `played` twice for one server session.

## Consequences

Tabs supporting Web Locks serialize receipt lookup, whole-board score mutation, and receipt
write. Repeated recovery of the same still-live terminal ID does not add another row, while
distinct IDs and simultaneous completions in different games remain distinct.

The receipt ledger contains no answers, content source IDs, score details, or account data.
Its 24-hour horizon is twelve times the untouched server-session TTL and bounds stale local
identifiers; a terminal session deliberately kept alive and revisited after that horizon can
record again. The 1,000-per-game cap matches the server's bounded per-game session population.
