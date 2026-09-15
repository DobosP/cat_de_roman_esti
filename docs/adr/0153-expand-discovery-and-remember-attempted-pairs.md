# ADR-0153: Expand discovery and remember attempted Alchimie pairs

- Status: accepted
- Date: 2026-09-15
- Extends [ADR-0152](0152-expand-reviewed-rounds-and-explain-lant-connections.md).

## Decision

The owner authorized landing V94 and starting V95. V94 is published on main at
`cf6b28b`; V95 develops separately from that baseline with the existing content gates.

Add independently reviewed content across all six games while preserving the shared
KG, earlier game records and earned Alchimie progress. Five new Alchimie preparations
have two recipes each. Their explanations name omitted ingredients and preparation
steps; game pairs are starting points, not complete cooking instructions. Keep the
256-concept ceiling, starter supplies, tiers and optional goals unchanged. Independent
factual and quality review, plus final live audits, gate catalog installation.

Alchimie remembers at most 128 unique unsuccessful pairs in the current server session.
Only an authoritative empty combine result can add an observation. Pairs are unordered,
oldest observations leave first, and compatible recipe-book changes clear this memory.
GET and goal changes retain observations; portable saves and restored/new sessions do
not import them. Recipe data and untried outcomes remain private.

After choosing an ingredient, visibly mark its previously tried partners. Keep them
selectable and acknowledge immediate repeated attempts locally with pair-specific text,
without another request or save write. Local acknowledgment is valid only for 30 seconds
since the last authoritative state; it does not refresh itself. Later attempts contact
the server so added recipes become available. Existing save ownership, request locking,
transport recovery and keyboard-focus checks also apply to local acknowledgments.
Local acknowledgments keep their already focused button and center it synchronously;
they do not queue a deferred focus reference that could survive an identical message.

A final natural-selection audit found that the width-three beginner preference made
reviewed width-two Lanț rounds unreachable for anonymous players. In casual easy games,
keep an initially selected eligible narrower round with probability one in four; otherwise
apply the existing wider-pool preference. Daily selection is unchanged. This is a
conditional chance, not a promise that a quarter of all rounds will be narrow. Preserve
the strict two-route content floor, ranking, exclusions and thin-pool fallback. Seeded
selection remains deterministic. This partially supersedes [ADR-0043](0043-lant-visible-route-corridors.md)
only for casual beginner sampling.

## Consequences and verification

The interface removes avoidable waiting and gives players a visible memory of failed
experiments without adding controls. Marks describe observations rather than promises
that a pair can never work. Browser review covers narrow screens, keyboard/drag use,
reloads, lost responses, expiry and the bounded freshness window. Backend checks cover
unordered deduplication, capacity, rejection of forged save fields and recipe upgrades.

Content evidence and integration results live in the
[V95 review](../reviews/v95-discovery-and-game-quality/README.md) and
[STATUS](../STATUS.md). Agent/browser judgments do not establish human enjoyment or
physical-device acceptance. Production deployment remains separate from this session.
