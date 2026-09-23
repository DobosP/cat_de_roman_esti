# ADR-0156: Refine playable content and maintain an experimental discovery pool

- Status: accepted
- Date: 2026-09-22
- Extends [ADR-0113](0113-outcome-based-version-batches.md) and
  [ADR-0148](0148-expand-all-game-content-with-independent-review.md).

## Context

The owner requested two complementary directions: refine the current games, and explore
more broadly for new concepts that can feed the reliable direction. The requested artifact
is a reusable skill stored with the game. Existing authoring, factual review, critique,
ranking, runtime and saved-progress gates already define how content becomes playable.

## Decision

Keep the workflow in the repository-local
[romanian-game-content skill](../../.agents/skills/romanian-game-content/SKILL.md).
Refinement is the delivery track: it improves existing content and independently selects
promising research. Discovery explores broader themes, meanings and relationships in
isolated prototypes, recording hypotheses, sources, uncertainty and counterexamples.
Risk changes what is investigated; it does not weaken the acceptance standard.

Preserve useful research in theme-scoped `docs/content-pool/<theme>/pool.json` ledgers,
created only when records exist. Their editorial states and identifiers are separate from
runtime approval and canonical game IDs. The skill's
[pool contract](../../.agents/skills/romanian-game-content/references/candidate-pool.md)
defines durable provenance, revisions, negative results and the handoff to refinement.
This is a workflow convention, not a new importer or enforced application schema.

The handoff binds selected revisions, baseline, evidence, destination rail and expected
player benefit. Refinement can reject, narrow or hold any selection. Shared KG changes,
pack-only rounds, authored quick-game supplements and Alchimie exploration retain their
respective existing independent reviews, digest bindings, generators and live audits.
Experimental pool records never become served fixtures directly. Preserve current owner
holds, rejected-record evidence, frozen content and earned collections.

Use finite batches without a required track ratio or shipment quota. Track vocabulary,
per-game exposure, rounds, approvals and actual selection separately. Automated quality
estimates remain distinct from human playtesting. Existing resource and compatibility
bounds stay in force; read current STATUS before adopting Alchimie recipes or concepts.

## Consequences and scope

The skill can run either track alone or both, with research and refinement delegated
independently when available. Durable rejection reasons and source evidence can inform
later waves. Exact installation reviews remain necessary, even for promising research.

This change adds instructions, UI metadata and the pool reference only. It starts no
content wave, creates no research records, changes no game or fixture, and adds no recurring
run. It does not grant publication, deployment or new resource-limit authority. Existing
ADRs remain accepted; this decision adds a research-to-refinement workflow around them.

Verification and current inventory remain in [STATUS](../STATUS.md).
