# ADR-0157: Start V99 with reviewed route explanations and a discovery pool

- Status: accepted
- Date: 2026-09-23
- Extends [ADR-0156](0156-two-track-content-growth.md) and
  [ADR-0155](0155-preserve-discovery-history-and-explain-food-links.md).

## Context

The owner requested a pull from origin and V99 startup using the repository content skill.
Origin already contains verified V97 and an unimplemented V98 kickoff. Reconciliation
preserves those published commits and the local skill. The skill ADR, previously numbered
0155 only locally, moves to 0156; published origin ADR-0155 is unchanged.

## Decision

Start a finite first batch with two related tracks: refine understandable existing play,
and research recognizable everyday words for later adoption. Bind the batch to reconciled
baseline `af5981a580ab629ec8de29fd50657a9850404085` and fetched origin `b25c949`.
The V98 drafts are inputs to fresh review, not inherited approval or a V98 completion claim.

Install four independently fact-checked and quality-reviewed Lanț relationship captions
for the existing Cacao→Înghețată→Lapte and Cacao→Chec→Lapte routes. Preserve all 113 prior
captions, full edge-snapshot guards, five allowed directions and three absent reverses.
The current hint selector may return a direction hint because the opening now has a
meaningful visible explanation; it reveals no additional continuation. No graph or
selection algorithm change is needed for this refinement.

Keep twelve experimental shared-concept proposals in the everyday-spaces pool. Eight
are researched and four held; none crosses the readiness or installation boundary.
Preserve specific senses and normalized-form ownership, including Masă as a meal and
ac as the existing AC alias. Selective school-olympiad evidence supports exposure only,
not population-wide familiarity. Prototype pairing/route hypotheses remain unapproved.

The [review archive](../reviews/v99-refinement-and-discovery/README.md) binds proposals,
independent judgments, historical source, installed behavior, research audit and gates.
Version-specific text evidence uses LF checkout attributes so byte-digest bindings survive
Windows and Linux checkouts; binary screenshots and other version archives are unaffected.
Historical V97 registry assertions use its byte-pinned source snapshot while still
requiring every old entry to remain live; V99 separately asserts exactly four additions.

## Consequences and scope

The first batch improves explanations while retaining all existing concepts, forms,
links, recipes, rounds, rankings and capacity limits. Research can feed a later small
refinement selection only through the existing graph and downstream game review rails.
Broad V99 expansion, human playtesting and physical-device acceptance remain open.
This request starts no recurring automation and grants no push or deployment authority.
Existing ADRs retain their status; this decision adds a bounded application of ADR-0156.

Current inventory and completed verification belong in [STATUS](../STATUS.md).
