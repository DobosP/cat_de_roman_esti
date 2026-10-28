# ADR-0222: Simplified Alchimie collection interface

- Status: accepted; implementation qualification pending; native TMPDIR paragraph superseded by [ADR-0223](0223-hermetic-relocation-test-filesystem.md)
- Date: 2026-10-28
- Partially supersedes: ADR-0142 for the library controls and discovery presentation,
  and ADR-0149 for collapsed search/filter and progress presentation. Their gameplay,
  bounded feedback, ownership and recovery safeguards remain accepted.

## Authority and outcome

Paul approved the simplified interactive mockup and requested implementation in both
Alchimie modes, responsive on narrow and wide layouts, without per-word icons or a
separate recent-discoveries panel. This is an interface change in Cat only.

## Decision

The normal play area contains the current ingredient, the last earned reaction,
visible search and one collection of plain word buttons. New acquisitions appear
first while the relative order of existing words remains stable. Every owned concept
remains listed; server-provided inactive/depleted state still prevents crafting.
Selection has a quiet visual state without visible New/Selected/Collected badges.

Rețete/Cuvinte switches the same library area between words and earned recipes.
Exploration retains its independent word/recipe searches, descriptions, sources and
local replayable save. Challenge keeps its round-scoped earned links and bounded
12-reaction journal, including after victory. Search survives crafting. Result actions
only select the next ingredient; they never submit a combination by themselves.

Keep actual returned parents/results visible and distinguish automatically supplied
concepts from crafted outputs. Never manufacture hidden challenge recipe outputs.
Optional goals, help, hints and round options remain accessible as secondary actions.
Hint costs, score recording, copy/replay, uncertain-action reconciliation, concurrent
ownership, server authority, session bounds and existing save formats remain unchanged.

The collection follows the workbench in narrow layouts; wider layouts put them side
by side. Labels wrap, search text remains readable, and controls retain 44px targets.
The existing bounded exploration feedback pin and focus-restoration safeguards remain.
There is no physical-device checkpoint under ADR-0199; no device testing is requested.

## Verification

Qualification and commands are recorded in STATUS and the task review record. Existing
browser checks for game behavior, owned recovery, earned lineage, touch geometry and
keyboard access are retained. Assertions about removed disclosures, filter badges and
nested journal layout are replaced by assertions for the explicitly approved interface;
original inventory keys, frozen bundles, baselines and budgets stay intact.

The native unit runner uses a private temporary directory on the checkout filesystem.
This makes the existing parent-relocation test execute inside the container instead of
skipping on cross-filesystem rename. The gate still rejects unexpected skips; no
assertion, skip exception or numerical acceptance limit is changed.
