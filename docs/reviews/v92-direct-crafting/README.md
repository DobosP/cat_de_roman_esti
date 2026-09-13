# V92 — Direct crafting

Valid until: a later change to this candidate's source or serving artifacts — then treat as history.

On 2026-09-13 the owner clarified that the first V92 GUI candidate still required too
many buttons and actions. This revision continues the same V92 branch from
`e609de69ee0bfc6456d3de644a59ca7d4150cc1b`. It focuses on the repeated play sequence.
Current state: [STATUS](../../STATUS.md). Decision: [ADR-0142](../../adr/0142-direct-alchimie-crafting.md).

## Reference interfaces and adaptation

The official [Infinite Craft](https://neal.fun/infinite-craft/) interface was exercised:
dragging Fire onto Water creates Steam directly, and Steam remains in the workspace.
The official [Little Alchemy 2](https://littlealchemy2.com/) interface likewise centers
the workspace and library, with utilities at the edge rather than a combination form.
Its help documents [double-tap duplication](https://help.littlealchemy2.com/general/duplicating-items)
and [long-press information](https://help.littlealchemy2.com/general/item-info).

Alchimie's two-tap input is an accessible adaptation of direct combination, not a claim
that those games use that exact touch sequence. Desktop dragging is also supported.
The server continues to accept only distinct owned ingredients and decides every result.

## Player-visible changes

- First word selects; second word immediately combines. There is no Combine button,
  two-slot form or mandatory use-result action. Same-word tapping cancels the anchor.
- A sole useful discovery becomes the next ingredient automatically. If more than one
  useful word is discovered, the player chooses which to use rather than receiving an
  arbitrary selection. A confirmed empty attempt keeps the first word for a one-tap retry.
- Exit, search and options are the only three initial controls outside the word tiles.
  Filters, search input, history, explanations and round actions begin collapsed. Intro
  difficulty/category choices are optional. Available hints show the existing cost.
- Hint/resume adoption never triggers a combination. Paid pair hints anchor one word,
  highlight both and wait for player input. Lost-action recovery retains its GET-only path.
- Native keyboard input has the same play behavior. When a submitting word disappears,
  lost focus follows the carried word or inventory panel; deliberate focus moves are
  respected. Carried selection is announced. Native drag uses the same mutation guard.

## Measured interaction and layout

Real BFF seed 38, easy Sport board, 390×844 Chromium mobile emulation with actual
touchscreen taps. Fonts and finite animations settle before geometry capture.

| Measurement | First V92 candidate | Direct crafting |
|---|---:|---:|
| Actions for the two-combination win | 6 | 3 word taps |
| Combine POSTs | 2 | 2 |
| First word top | 613.75px | 367.91px |
| Fully visible starting words | 6 | 6 |

The direct journey creates Handbal feminin, carries it automatically, then wins on
the next word tap at two combinations and 1000 points. Search, options and history are
never opened during that journey. These measurements do not establish human enjoyment
or physical-device acceptance.

Evidence: [interaction receipt](interaction.json), [phone](mobile.png),
[desktop](desktop.png), [carried discovery](carried-result.png).
The [content delta](content-delta.json) records zero changes to concepts, connections,
forms, puzzles, rounds, approvals, declared eligibility and frozen derived boards.

## Verification and limits

The updated [browser acceptance suite](../../../frontend/e2e/alchimie-workbench.spec.mjs)
uses real server sessions for direct input, retries, duplicate blocking, drag/drop,
keyboard, focus, hint resume, narrow layouts, text zoom and network ownership. Existing
game helpers and recovery checks were adapted to the changed input sequence without
removing the network/ownership assertions. [Final verification](verification.json)
records exact commands, results and artifact fingerprints.

The initial focused run found a duplicated replay-failure notice; the standalone notice
now only belongs to live play and ResultCard owns terminal errors. A subsequent complete
browser run passed before independent review discovered keyboard focus loss. Dedicated
tests now cover focus following a carried discovery and respecting another focused control.
Earlier runs are historical evidence and are not described as the final gate.

Backend, API wrappers and content files have no diff from `e609de6`. Its full Python and
content-validator evidence is retained as baseline rather than rerun for an unchanged
backend. This revision's real browser tests exercise the same serving contracts.
The work remains local, with no production deployment or recurring version loop.
