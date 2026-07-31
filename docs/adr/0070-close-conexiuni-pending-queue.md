# ADR-0070: Close the Conexiuni pending queue without quota promotions

- Status: accepted
- Date: 2026-07-31

## Context

ADR-0065 left 79 Conexiuni records pending because its partial V42 review covered only 77
outcomes and became stale before apply. ADR-0067 later made the full approved, pending,
demoted, and rejected inventory part of every novelty check, added durable rejection
tombstones, and required exact-byte unanimous promotion. V46 rebuilt the missing exact
batch rather than trusting the archived judgments or filling ten empty shelves by quota.

The fresh deterministic review found 438 failures across 76 records. Seventy-four reuse
an exact/near group, at least half of another board, or already overused members; two more
fail tile fairness. The remaining three use common, recognizable words but admit alternate
partitions or worksheet-style leftover solves. No record clears both independent reviews.

Applying the result also exposed one legacy Conexiuni record whose named group keys could
not enter the newer `g1`–`g4` tombstone schema. The content transaction rolled back before
any partial mutation.

## Decision

1. Bind the fresh v2 gate to all 79 V45-era pending Conexiuni records. Reuse no V42
   judgment. Continue to require two independent `promote` judgments to ship; either
   `reject` rejects; otherwise synthesize `keep`.
2. Apply the resulting zero-promotion outcome: remove all 79 records and leave no pending
   Conexiuni queue. Preserve the Conexiuni ID high-water mark at 361 and do not fill an
   empty shelf with a failed board.
3. Append every removed record to the durable rejection ledger. Normalize legacy named
   group keys deterministically to `g1`–`g4` only inside the ledger representation; retain
   the original record digest, exact dossier binding, source-gate digest, and four member
   partitions.
4. Regenerate rankings and derived metadata. Preserve the frozen Intrusul/Perechi boards
   payload, shared KG/graph, frontend, scoring, hidden-answer boundary, and session
   behavior. Do not deploy V46 as part of this content gate.
5. Cross-bind the exact batch, dossiers, final artifact, tombstones, pack counts,
   rankings, and frozen derived payload in a committed regression test.

This resolves ADR-0065's deferred Conexiuni apply. Its other authored-wave and
derived-freeze clauses remain in force.

## Consequences

Conexiuni becomes 232 records = 232 approved + 0 pending, with 74 runtime-eligible. The
original-game pack becomes 645 records = 608 approved + 37 pending; runtime eligibility
stays 447 because no served board changed. The rejection ledger becomes 122 boards / 488
groups, making future authoring stricter without exposing rejected content at runtime.

The derived catalog remains 336 boards (183 Intrusul / 153 Perechi), and its frozen
`boards` payload SHA-256 remains
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
Future Conexiuni work must author materially new candidates and pass a new exact gate;
empty shelves are product evidence, not a promotion mandate.
