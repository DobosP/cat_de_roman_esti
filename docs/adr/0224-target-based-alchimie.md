# ADR-0224 — Target-based Alchimie

- Date: 2026-11-08
- Status: accepted design; release qualification pending
- Supersedes the two-mode current GUI in [ADR-0222](0222-simplified-alchimie-collection-interface.md).

Alchimie opens directly to target-based rounds. The old mode query URLs resolve to
the same round entry. Daily, theme and difficulty controls and saved rounds stay
available. The current application does not read or rewrite old Exploration saves.
The Exploration API and frozen rollback bundle retain their existing contracts.

The active workbench places the target, combination count, two ingredient slots
and earned result together. A player can reuse a result explicitly. The word
inventory keeps acquisition order, a count, readable inactive words and visible
search. Earned recipes share the inventory area and can return the player to
crafting with the result selected. A completed round displays its winning recipe
from earned inventory even on resume. No changes to recipe or scoring rules.

The historical introduction screenshots and their hashes remain preserved. The
current gate checks the two former mode links against the same target-only
introduction and still runs the remaining exact screenshot, axe and vitals
checks. The historical Explore browser journeys are reproducible on the
previous qualified product, `2cacc8783641acf908cc8bfa572687e13cb2fc30`.
