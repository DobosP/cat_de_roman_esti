# V92 — Alchimie GUI rebuild

Valid until: a later change to the V92 source or serving artifacts — then treat as history.

The owner requested this version on 2026-09-13 because Alchimie's interface was confusing
and frustrating. Baseline: `6208eae22429d9b976a7c88477913010997eb3de` (V91).
Decision and scope: [ADR-0141](../../adr/0141-rebuild-alchimie-workbench.md).
Current integration and production state: [STATUS](../../STATUS.md).

## Player outcomes

- A visible target and one workbench put choosing and combining together. Numbered slots
  and full word labels replace ambiguous compact chips; instructions change with selection.
- A third selection preserves both chosen ingredients and explains how to replace one.
  Removing or clearing ingredients dismisses the old message and restores usable focus.
- Discoveries preserve the chosen filter. The workbench displays feedback and direct
  use buttons; the journal still exposes the server-authored associations.
- Search has an explicit way back, and choosing a filter clears the search. Inventory
  text explains that a marked word has some suitable partner, without revealing recipes.
- Available hints show their existing 150-point penalty before use. Lost replies retain
  the existing read-only recovery, session ownership and paid-cue behavior.

## Before and after

Real BFF seed 38, easy difficulty, Romanian locale, reduced motion, 390×844 browser
viewport. Both versions use the same unchanged approved Sport board. Measurements wait
for fonts and finite animations; no scrolling precedes capture.

| Measurement | V91 | V92 |
|---|---:|---:|
| First ingredient top | 744px | 613.75px |
| First ingredient bottom | 788px | 679.75px |
| Entire inventory bottom | 892px | 829.75px |
| Fully visible starting ingredients | 4 | 6 |

Evidence: [geometry](geometry.json), [V91 phone](v91-mobile.png),
[V92 phone](v92-mobile.png), [V92 desktop](v92-desktop.png).
The images document layout rather than human enjoyment or physical-device acceptance.

## Scope and evidence

[Content delta](content-delta.json) reports zero added, removed or revised concepts,
connections, forms, puzzles, curated rounds, approvals, declared eligibility and frozen
derived boards. No recipes, difficulty, scoring or server contracts changed.

The browser acceptance file is
[`alchimie-workbench.spec.mjs`](../../../frontend/e2e/alchimie-workbench.spec.mjs).
It uses real BFF sessions; the existing solution helper executes only in the test
process. It covers desktop/mobile play, stable selections, quick results, filter/search,
warning dismissal, long Romanian labels, 320px width, 200% text and a short viewport.
Existing suites cover all six games, accessibility, resume, action recovery and replay.
Exact final check results are recorded in STATUS and the [verification receipt](verification.json).

Initial development runs exposed a misplaced test selector for the clear-search button,
action-row overflow at 200% text and header overflow with long stressed labels. These
are tracked as development failures, not passing evidence. Subsequent checks cover the
corrected behavior. Four native source-contract tests changed to match intentional copy,
help placement, readiness explanations and focus fallback; their behavioral boundaries remain.

V92 is a local review candidate. It does not restart automatic versions or claim a
production deployment. Owner playtesting is still required to judge the play feel.
