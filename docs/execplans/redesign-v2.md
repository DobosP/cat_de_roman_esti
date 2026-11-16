# Redesign v2

Valid until: both redesign milestones land locally — then treat as history.

## Scope

Build and locally land the six standalone game screens, steps and hint ladders, followed by anonymous board comparison. The rules and UI are defined in [ADR-0232](../adr/0232-steps-and-hint-ladder.md) and [ADR-0233](../adr/0233-redesign-v2-interface.md). Supporting implementation details and the approved canvas exports are in the redesign handoff.

## Decision Log

Paul's decisions of 2026-11-16 apply to both milestones.

- “Yes, re-lock” authorizes new screenshots, source hashes and axe expectations with the previous capture preserved as history. The CSS limit stays 16,093 B gzip and each game route JS limit stays 40,960 B gzip.
- “Keep current fonts” retains Fredoka and Inter.
- “Update the Python copy” requires independent Go and Python implementations with parity recorded from Python.
- “Build it, switched off” applies to Milestone 2 board comparison.
- “Undo free, jumps still count” governs Lanț. “Count every new pair” governs Alchimie.
- “Ușor” with no theme governs the daily boards for Conexiuni, Cald sau Rece, Lanț and Alchimie.
- “Yes, new count is fine” authorizes more than 1,206 parity cases.
- The six games stand alone. Home cards open games directly and show “Gata azi” after completion. The theme follows the device until the player uses the Home switch.
- Local landing follows ADR-0004 after the exact-SHA unit and full gates and independent review. Paul owns publication, deployment, and activating counts in production.

### Browser assertion replacements

The former frozen Help text has a new exact-copy pin and tests for each ladder and the step rules. The original assertions are retained under `frontend/historical-e2e/redesign-v2/`.

- The circuit, streak, diploma and pre-entry challenge actions are replaced by the Home card's one-tap daily/free decision, daily completion badge and dated resume tests. The pilot journey still checks same-document navigation and inert exiting frames.
- Home's starter chip, rankings, record totals and history wall are replaced by the isolated free starter request, single-purpose cards and the lazy Results dialog. The existing private account, source-closure and byte-identity assertions stay active.
- The intro focus, locked-hint countdown and point deductions are replaced by the game frame's entry and recovery focus, immediate hint buttons, enforced step increments and exhaustion tests. Intrusul, Perechi, Conexiuni, Cald, Lanț and Alchimie keep their keyboard and pending-reply journeys.
- The setup pickers, in-round disclosures and result “Schimbă opțiunile” are replaced by the labelled Help dialog with exact per-difficulty availability, input retention, focus return and next-free-round preference checks. Alchimie recipe views retain their browser witnesses.
- Score and best-record presentation assertions are replaced by result steps, score-free clipboard, Perfect for eligible wins and the terminal receipt checks.


- The archived Conexiuni visual test keeps the old numbers and life image. Its replacement checks the current coach copy, pressed tiles, visible attempts and non-overlap at both widths and text scales.

## Milestone 1

- [x] Record the approved decisions and claim their ADR numbers.
- [ ] Build the Go rules and independently implement the Python oracle. Record and replay the source- and rules-bound corpus, regenerate mechanics and OpenAPI goldens, and update the mobile contract.
- [ ] Build the Home, entry, game screens, help, result and history UI. Measure the route and CSS budgets from the pinned build during implementation.
- [ ] Migrate the browser journeys, retain superseded assertions with their replacements and capture the new GUI lock in a dedicated gate-change commit.
- [ ] Rebase on content main. Run exact-SHA unit and full and get independent review of that SHA and baseline re-capture.
- [ ] Walk through the managed build at 390 × 844 in both themes, locally fast-forward main, record receipts and clean up the verified-merged worktree.

## Milestone 2

- [ ] Start `feat/board-place` from landed Milestone 1 and record ADR-0234.
- [ ] Implement the bounded anonymous histograms, single-writer snapshots, trusted-proxy rate limiter, optional response and result podium.
- [ ] Update optional deployment storage and draft the privacy line for Paul.
- [ ] Run the final exact-SHA unit and full gates and independent review, verify enabled and disabled behavior, locally fast-forward and clean up.
