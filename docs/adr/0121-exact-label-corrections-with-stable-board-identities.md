# ADR-0121: Correct exact reviewed labels without reshuffling derived puzzles

- Status: accepted
- Date: 2026-09-07

## Context

Source `cx_gastronomie_171` describes Urdă as inherently salty and calls regions localities.
Its frozen Intrusul variant exposes the first error to players. Rehashing corrected labels
naively could change the diversity cap's tie order and select different puzzles.

## Decision

Replace only the two bound source labels: g1 becomes “Denumiri cu trimitere geografică”
and g3 becomes “Produse lactate”. Bind the entire approved source record and exact ordered
group members. Reject duplicate, absent, stale or partially corrected source states.
Apply only this label delta to both pack mirrors using the verified file transaction.
Keep status, membership, order, eligibility, source set and all gameplay bounds unchanged.

The derived builder and runtime share one narrow identity policy: for this exact source,
member subset and corrected label, hash the historical label while rendering the corrected
one. Validate the complete before/after source record before relying on that compatibility
mapping. This is not a generic label alias or a bypass for custom or tampered sources.
The normal source/payload validation and artifact digest gates remain active.

This is a bounded label-only exception to ADR-0054's frozen payload policy, not an expansion
of its catalog or source set. Exactly one served Intrusul label changes; all 336 IDs,
partitions, choices, scores and ordering remain exact. The approved Conexiuni source is
not currently pilot-eligible, so its stored correction is not claimed as a newly served
Conexiuni round. No Perechi display change or new board is implied.

## Consequences

The factual wording improves without changing daily identity or replay choices. New label
corrections need fresh exact data and independent review. The historical inverse restores
both source labels and the one derived label before checking earlier artifact hashes.
