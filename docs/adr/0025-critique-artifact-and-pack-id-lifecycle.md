# ADR-0025: Bind critique artifacts to content and reserve pack IDs monotonically

Date: 2026-07-16
Status: accepted

## Decision

Require every gate judgment to carry a `review_binding`: SHA-256 over the canonical
judge dossier plus the current critique-rubric digest. Both critic and verifier must
echo it, and `apply_rereview.py` must rebuild the exact-batch dossiers and match every
binding before mutation. Persist a per-game `meta.id_high_water` in both pack copies;
all import and reject paths preserve it, and new IDs allocate strictly above it.

## Context / why

ID-only version-2 artifacts could survive an edit to a pending item, allowing an old
subjective judgment to approve different content. Deterministic lint does not replace
that review because WARN/editorial quality remains judge-owned. Likewise, allocating
from surviving IDs prevents same-run collisions but can reuse the maximum after a later
run retires it. Pack IDs live in player progress and editorial archives, so reuse is not
safe. ID-only binding and observed-maximum allocation were rejected for these lifecycle
gaps.

## Consequences

Any dossier-visible pack/KG change or rubric edit invalidates old gate artifacts and
requires re-review. Legacy or partially verified artifacts fail closed. Pack metadata
gains four small monotonic counters; deleting an item no longer frees its identifier.
Runtime selection, game/session behavior, and served item counts are unchanged.
