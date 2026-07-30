# ADR-0069: Fail closed and clear the Lanț pending queue

- Status: accepted
- Date: 2026-07-31

## Context

ADR-0065 left 107 Lanț records pending because its partial V42 review became stale before
apply. V45 rebuilt the exact batch and found that the critique command reported zero
FAILs even though the runtime payload validator rejected 91 records for forced openings
or width-one shortest-path layers. The remaining 16 were structurally valid but still
needed D1–D5 gameplay and freshness review. Empty shelves were not a release quota.

## Decision

1. Add the runtime Lanț payload errors to `critique_pack.py` as fail-closed
   `lant_playability` findings. Exact dossiers must expose distance, difficulty, first-hop,
   and shortest-layer failures before subjective review.
2. Bind a fresh gate to all 107 V44-era pending records. Do not reuse incomplete or stale
   V42 judgments. Require two independent `promote` judgments to ship; either `reject`
   rejects; otherwise synthesize `keep`.
3. Apply the resulting zero-promotion outcome: remove 104 rejected records and retain only
   `lt_literatura_210`, `lt_stiinta_216`, and `lt_viata_de_roman_211` as pending repair
   holds. Preserve the Lanț ID high-water mark at 219.
4. Keep the shared graph, KG/mobile contract, session behavior, frontend, and approved
   Lanț pool unchanged. Regenerate rankings and derived metadata, while requiring the
   frozen Intrusul/Perechi `boards` payload to remain byte-identical.
5. Preserve all 107 dossiers and the complete gate artifact as rejection provenance.
   A future generic Lanț rejection ledger may harden imports, but rejected stock must not
   remain in the pack merely because that ledger is not yet implemented.

This resolves ADR-0065's deferred Lanț apply. Its authored-wave, derived-freeze, and other
owner-decision clauses remain in force.

## Consequences

Lanț becomes 97 records = 94 approved/selectable + 3 pending. The original-game pack
becomes 724 records = 608 approved + 116 pending; runtime eligibility remains 447 because
no pending board was promoted and no approved board was removed.

The three holds each carry a concrete blocker: comparative route-family review for
`lt_literatura_210`, shortest-hop opening-menu visibility for `lt_viata_de_roman_211`,
and semantic edge labels for `lt_stiinta_216`. None can ship without a fresh exact
dossier after its blocker changes.

The corrected gate reports 91 failing records and 177 deterministic Lanț playability
findings. The derived catalog remains 336 boards (183 Intrusul / 153 Perechi) with frozen
payload SHA-256
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
