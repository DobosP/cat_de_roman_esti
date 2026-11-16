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
- [x] Build the Go rules and independently implement the Python oracle. Record and replay the source- and rules-bound corpus, regenerate mechanics and OpenAPI goldens, and update the mobile contract.
- [x] Build the Home, entry, game screens, help, result and history UI. Measure the route and CSS budgets from the pinned build during implementation.
- [x] Migrate the browser journeys, retain superseded assertions with their replacements and capture the new GUI lock in a dedicated gate-change commit.
- [x] Rebase on content main. Run exact-SHA unit and full and get independent review of that SHA and baseline re-capture.
- [x] Walk through the managed build at 390 × 844 in both themes, locally fast-forward main, record receipts and clean up the verified-merged worktree.

Exact gate operator: `agent:codex` (PROGRAM E8). Qualified SHA `8b6679afae886cd0014e0b0bd98f0c2a6f30e1e1`. [Canonical commands, result hashes, browser counts and budgets](../reviews/redesign-v2-m1/acceptance.json).

## Independent review

- Rules and interface review found repeated/member hint disclosures, retargeting of an earned
  hint after a group or pair was solved, and races around loading or saving a round from two
  tabs. Those findings were fixed and the affected rules, save/retry and focus journeys were
  rechecked.
- The first full candidate at `ffab22be5869d7984148c539b4a74bdf9d6e795c` failed 114 browser
  cases. The fixes removed obsolete setup selectors, kept the newest saved round after a
  concurrent create, and restored visible controls at 320 px with doubled text and in the
  Alchimie inventory. The next full found two copies of one stale Intrusul
  1280 px expectation. The corrected four layout cases passed in the pinned browser.
- The exact `a71e147e5e65fd294c8156699626e8ab01194098` renderer review gave GO. The captured
  images preserved 390 × 844 and the nine screens in each theme. All 18 recaptured PNGs matched
  byte for byte. The separate recapture passed all 28 checks, including zero Axe findings,
  the live Home semantics, and original LCP and INP bounds.
- The managed in-app walkthrough used `1db0266d16d38c034c8f511a22344e93b4a4846f`. It
  covered both themes at 390 × 844, theme persistence, daily and free entry, saved resume,
  each hint ladder, win, loss, give-up and Help focus. The final SHA includes later saved
  round handling and reduced-motion fixes.

The exact broad Django rerun reproduced the 474 historical failed nodes and 188 setup errors from main. No candidate-only red node matched the comparison. Superseded raw pytest and browser output trees were pruned after compact receipts were retained.

## Milestone 2

The daily sample window uses the current and preceding Bucharest dates. The opt-in Lanț terminal receipt counts an explicit give-up in that window. The inherited local action applies whenever the capability is absent. The client copy refers to rounds pending Paul's final wording.

- [x] Start `feat/board-place` from landed Milestone 1 and record [ADR-0234](../adr/0234-anonymous-daily-board-place.md).
- [x] Implement the bounded anonymous histograms, single-writer snapshots, trusted-proxy rate limiter, optional response and result podium.
- [x] Update optional deployment storage and draft the privacy line for Paul.
- [x] Run the final exact-SHA unit and full gates and independent review, verify enabled and disabled behavior, locally fast-forward and clean up.

### Milestone 2 evidence

The local 390 × 844 walkthrough used the exact compiled app in dark mode. The
enabled Intrusul result displayed Perfect and 99% across 101 finished rounds.
The saved snapshot contained 76 wins and 25 losses for Intrusul, and one
Lanț give-up. The default-off instance showed the normal win with zero podiums.

Independent Codex reviewers checked the immutable terminal result, storage and
limiter, date wording and accessible tier list, same-round navigation and
give-up recovery. A snapshot read error now preserves the previous snapshot
for later recovery. The approved capture and the independent recapture both kept
all 18 default-off PNGs byte for byte with zero Axe findings.

The two broad Python runs had identical failing test IDs (474 failures and 188 setup errors).

Exact gate operator `agent:codex` (PROGRAM E8). Product SHA `abda879a3675c5a5424a5f18866b70856104adde`. [Commands, receipt hashes, browser and parity counts, and gzip measurements](../reviews/redesign-v2-m2/acceptance.json). Superseded raw test output was pruned after the compact evidence was retained.
