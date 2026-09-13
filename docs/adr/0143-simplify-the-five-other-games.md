# ADR-0143: Simplify the five other game interfaces

- Status: accepted
- Date: 2026-09-13
- Extends: [ADR-0142](0142-direct-alchimie-crafting.md) for authorized game scope only.

## Context and authority

After the Alchimie correction, the owner asked to review the other games against
popular similar interfaces and improve their usability. This explicitly expands the
V92 task to Intrusul, Perechi, Conexiuni, Cald sau Rece and Lanțul Cuvintelor.
ADR-0142's exclusion of other games is replaced by this scope extension; its Alchimie
interaction and safety decisions remain accepted and unchanged. Work continues on
`feat/v92-alchimie-gui`, with no V93 or restart of the automatic loop stopped by
[ADR-0137](0137-finish-v91-and-stop-iteration-loop.md).

The objective is easier play with fewer competing controls and unnecessary actions.
An existing efficient interaction should be retained. Reducing controls must preserve
meaningful decisions, paid-hint consent, visible feedback and keyboard access.

## Primary-source observations

The following references were inspected on 2026-09-13. These are interface references,
not measurements of comparative popularity or proof of improved human performance.

- [Wordwall Quiz](https://wordwall.zendesk.com/hc/en-gb/articles/360015811938--How-to-create-a-Quiz-activity)
  documents choosing an answer by tapping, immediate marking and options below the
  activity. [Sporcle's official formats](https://support.sporcle.com/hc/en-us/articles/33897795822989-Understanding-different-quiz-types-and-formats)
  also describe direct clickable answers. These support retaining Intrusul's one-tap answer.
- [Wordwall Matching Pairs](https://wordwall.zendesk.com/hc/en-gb/articles/360015775077--How-to-create-a-Matching-Pairs-activity)
  documents selecting one tile and then its partner, automatically processing matches
  and optionally removing matched tiles. It is a memory game with hidden tiles; Perechi
  keeps its words visible and its existing semantic matching rules. The transferable
  pattern is direct selection with immediate feedback and fewer items left to scan.
- [NYT Connections help](https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections)
  documents 16 words, groups of four, limited mistakes and submitting guesses. The live
  NYT page loaded only partially during inspection; no completed reference round is
  claimed. The help supports retaining an explicit submission step while making our
  board and its controls easier to reach.
- The [official Contexto interface](https://contexto.me/en/daily) was inspected in a
  browser: Enter submitted a guess, focus stayed ready for typing, guesses appeared in
  ranked rows, and Hint, Give Up and Settings were in a menu. Its text-only web response
  requires JavaScript. The adaptation below keeps an available paid hint visible while
  moving other occasional actions into options.
- [EPFL's Wikispeedia](https://dlab.epfl.ch/wikispeedia/play/) explains navigation from a
  starting article to a target by following links. It supports Lanț's visible current
  position, target and directly selectable next steps. The Wiki Game could not be
  inspected past its consent screen and supplies no claimed gameplay evidence here.

## Decision

The main play area contains the current task, answer controls and meaningful feedback.
Use concise contextual instructions in place of repeated teaching panels. Optional
rules and round tools live in a closed native `GameOptions` disclosure; configurable
intro extras live in closed `GameSetupOptions`. Opening either must not submit a move,
request a hint, change a score or replace a round.

Intrusul continues to submit an answer in one tap. Perechi continues to check a pair
on the second word; retapping the selected word cancels it. Remove the redundant
Perechi Golește action, name the selected word in the compact instruction and put
solved pairs below the remaining board. Both use two columns on narrow phones and
four on desktop. Locked hints are explanatory text. An available hint has an explicit
button and visible 150-point cost; earned clue information remains visible afterward.

Conexiuni keeps a four-column board on phones, including the 390px layout. Place
Amestecă, Golește and Verifică together below the board. The fourth selection does not
submit automatically: mistakes are limited and the player can revise the group before
committing. Shuffle and clear remain free local actions. Keep mistakes available,
selection count, one-away feedback and earned clues readable. Available hints explicitly
show their existing 100-point cost; unavailable hints explain their unlock state.
The header, instruction and action rows do not form stacked sticky panels.

Cald sau Rece centers play on one guess field and ranked feedback. A visible inline
guide explains that a smaller number is closer and #1 is the target. Keep the field
ready for repeated keyboard guesses without stealing deliberate focus from other
controls. Round settings, answer reveal and best/recent ordering live in options;
revealing the answer still requires explicit confirmation. That confirmation focuses
the safe cancel button and stays reachable on short, enlarged-text screens. The action
that leaves the current round is named “Începe alt joc”, distinct from opening options.
Available clues remain
deliberate actions with the existing 120-point cost visible before the request.

Lanț places current word, target and directly selectable next words before optional
history and metadata. A server-earned exact hint or concrete alternative takes one
tap through the existing guarded submission handler. Direction-only hints never cause
an automatic move. Uncertain spelling suggestions only fill the editable field and
require a subsequent deliberate submission. Keep relationship labels, progress,
backtracking and typed input available. The original-start optimal benchmark belongs
in round details; it must not be presented as distance remaining after a detour. Any
remaining-distance statement still comes from the server hint for the current node.
Lanț's scoring and hint behavior otherwise remain unchanged.

An owned direct action retains keyboard context. If a consumed hint button disappears,
restore lost focus to an enabled answer/next-word choice after the action completes.
Keep deliberate navigation to another control while a response is pending. Passive
hint restoration does not initiate a move, request or focus transfer. Initial Lanț
typing focus occurs once on fine-pointer devices rather than after every state change.

## Boundaries and recovery

This is a local V92 interface candidate. It does not authorize pushing or deploying.
Alchimie runtime, API wrappers, backend services, public contracts and all content
artifacts remain unchanged. Server-authored solutions, eligibility, difficulty, score,
hint costs and disclosure boundaries remain authoritative. Session TTL, capacity,
locking, ownership, request bounds and stored histories retain their existing limits.

The action-recovery decisions in [ADR-0126](0126-reconcile-uncertain-contexto-actions.md),
[ADR-0128](0128-reconcile-uncertain-lant-actions.md),
[ADR-0132](0132-reconcile-uncertain-conexiuni-actions.md) and
[ADR-0138](0138-owned-intrusul-perechi-recovery.md) remain in force. Preserve synchronous
guards, departure invalidation, saved-game ownership, GET-only recovery after uncertain
actions, paid-cue persistence and exactly-once terminal score recording. Layout changes
must not create automatic POST retries, paid actions or hidden answer inference.

## Acceptance and verification

Exercise real deterministic BFF rounds with desktop keyboard and phone touch input.
Intrusul must retain one-tap answers and Perechi two-tap matching with retap cancellation.
Show every initial quick-game tile at 320px without horizontal overflow. Check the
complete Conexiuni board and submission row at 390px, explicit submit after four choices,
free rearrangement and selection clearing. Verify readable labels and reachable controls
at narrow widths, long labels and 200% text, with touch targets of at least 44px.

Verify repeated Contexto guesses and deliberate focus handling, optional result ordering,
cancelable reveal confirmation, single-tap exact Lanț hint moves and edit-only uncertain
suggestions. Opening options or rules must preserve the round and selected words.
Check visible costs, no automatic paid hints, persistent earned feedback, failed reads,
rapid input, cross-tab ownership changes, departure and terminal score ownership.

Run frontend native tests, lint, typecheck/build and bundle budget, browser journeys and
required repository checks. Regenerate served assets from source. Exact commands,
completed results and observed limitations belong in [STATUS](../STATUS.md) and review
evidence. This ADR defines criteria and does not claim completed player acceptance or
physical-device testing.
