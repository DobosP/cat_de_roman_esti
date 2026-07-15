# ADR-0024: Distinctive-association standard (A7) and the owner demote path

Date: 2026-07-15
Status: accepted

## Decision

Add rubric criterion **A7 Distinctive association** to the critique gate: any
connection the gameplay leans on must be true of the concept *specifically*, not of
the whole country or class ("Sarmale → Moldova" is true-but-generic — sarmale is
pan-Romanian; "Eminescu → Moldova" is biographic and fine). Deterministic detection in
`critique_pack.py`: `nondistinctive_region_link` (KG inventory — a node linked to ≥2
macro-regions, or a national-salience ≥0.70 concept with a generic `related_to` region
edge) and `generic_region_link` (item-level WARN when a board pairs region tiles with
generically-linked tiles, or a Contexto target is/is-polluted-by such a node); judges
settle flagged cases with a web distinctiveness check (rubric D7). And add the demote
path ADR-0023 left open: `scripts/apply_demotions.py` applies owner-approved sweep
verdicts `{"game": ..., "verdicts": {"<id>": "demote|keep"}}` by flipping `approved →
pending` (withdrawn from serving, content preserved — never deleted), touching ONLY
approved items (the mirror image of `apply_rereview.py`), with the same atomic
validate+rollback over both pack copies.

## Context / why

The owner played the shipped games and reported region connections that are "kind of
too generic … that can be said about all Romania" (Sarmale surfacing as connected to
Moldova, and to Transilvania) — the KG confirms `Sarmale→Moldova (0.52)` +
`Sarmale→Transilvania (0.50)`, plus the same disease on Mămăligă, Țuică, sat, mare,
Mănăstire (16 flagged nodes). In Cald sau Rece these edges make region guesses rank
warm arbitrarily; in Conexiuni they make regional groups read as fake-regional. The
prior rubric had no distinctiveness criterion, so judges scored such items as fine
(the pilot passed Sarmale as a control). Why not auto-remove the edges: several flags
are defensible (Ciorbă rădăuțeană→Bucovina is genuinely of Rădăuți; Mihai Viteazul→2
regions is his history) — only a web-grounded judge separates them, so the lint emits
WARN + inventory, never FAIL. Why a separate demote script instead of extending
apply_rereview: apply_rereview's documented safety property is that approved items are
never touched; keeping the two mutations in mirror-image scripts means neither can
fight the other over an item, and demotion (unlike rejection) preserves content per
the ADR-0019 reversibility rule. Owner approved applying demotions in-session
(2026-07-15): the ADR-0023 pilot's confirmed demote class plus A7-condemned items.

## Consequences

Approved counts drop as owner-approved sweep batches land; every category must retain
a healthy curated pool (verified this batch: all conexiuni categories keep ≥12
approved, no category×difficulty cell empties, daily-pool floor 8 unaffected).
Demoted items sit in `pending` where revision batches can fix-and-repromote them via
the ADR-0023 gate. The 16-node `nondistinctive_region_link` inventory is the queue
for a future KG edge-cleanup batch (weaken/retype generic region edges, then
re-derive); until then the runtime graph is unchanged and Cald sau Rece can still
rank region guesses warm on flagged targets that were not demoted. Thresholds
(REGION_FANOUT=2, NATIONAL_SALIENCE=0.70, region label list) live in
`critique_pack.py` and extend to county/city genericity only if a future ADR says so.
Unchanged: ADR-0023's gate flow and verdict contracts, ADR-0019's owner boundary,
serving order, playability floors, hidden-answer boundaries.
