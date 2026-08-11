# ADR-0073: Retain durable Lanț rejection debt

Date: 2026-08-11
Status: accepted

## Decision

Retain each rejected Lanț record as digest-bound, non-runtime novelty debt in
`lant_rejection_tombstones.json`. Seed the ledger with exactly the 104 V45 rejections,
recovered from pre-apply commit `246e857` and cross-bound to the V45 dossiers and complete
two-reviewer gate; exclude the three V45 repair holds.

Treat the exact directed `start` → `target` pair as the automated identity. A pending
promotion fails when that pair occurs in either the complete current Lanț inventory or
the rejection ledger. The reverse direction and merely similar routes remain distinct
inputs for ordinary A1–A7 and D1–D5 review rather than inferred rejections.

Validate the ledger before import, critique, and apply. Candidate import checks the
post-alias pair before any mutation. Review apply checks the untouched full inventory,
then appends every newly rejected Lanț row in the same pack/ledger transaction; binding,
digest, conflict, validation, or pack failure rolls the complete transaction back. Keep
the existing rubric bytes and generated ranking/catalog artifacts unchanged: this is a
fail-closed implementation of A6 freshness, not a retrospective rewrite of V45–V48
review evidence.

## Context / why

ADR-0069 removed 104 rejected Lanț records while preserving their V45 archive, but left
the generic import-time ledger as explicit follow-up work. A removed pair could therefore
return under a new ID, through an alias, or beside a same-batch rejection. STATUS required
that gap to close before another large import.

Why not re-gate the remaining three Lanț rows: their named blockers have not changed, so
ADR-0069 still requires fresh repaired evidence. Why not infer corridor similarity: no
reviewed threshold exists, direction can materially change play, and D1–D5 already owns
semantic route quality. Why not edit the rubric now: changing its digest would make
historical V45/V48 bindings appear stale without changing their reviewed content.

## Consequences

The ledger begins at 104 records and 104 unique directed pairs. It is never loaded by the
game runtime. Pack counts remain 618 = 610 approved + 8 pending, ranked eligibility remains
449, the KG and gameplay records remain byte-identical, and the frozen 336-board derived
payload remains unchanged.

Exact ledger reuse fails deterministic authored-content preflight. Current-pack reuse is
culled by authored review and definitively fails pending critique before promotion. Future
Lanț rejections grow the ledger transactionally. The V49 regression pins the exact initial
104-row seed; the next genuine append must evolve the versioned contract while retaining
that seed as an immutable subset. Broader route-family novelty still needs human evidence,
and the three V45 holds still need their named repair plus a fresh exact gate. V49 changes
no session TTL/cap, hidden-answer boundary, frontend, account setting, score, or deployed
production version.
