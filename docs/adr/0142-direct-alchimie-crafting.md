# ADR-0142: Make Alchimie crafting direct and reduce repeated actions

- Status: accepted
- Date: 2026-09-13

## Context and authority

The owner corrected the initial V92 rebuild: the frustrating part was the number of
buttons and actions required to play, and requested comparison with popular similar
games followed by a simpler, more intuitive refactor. Numbered ingredient slots and
immediate reuse buttons in [ADR-0141](0141-rebuild-alchimie-workbench.md) still required
selecting ingredients, submitting a combination and explicitly reusing its result.

This correction continues the authorized V92 work on `feat/v92-alchimie-gui`. It does
not start V93, a scheduler or the recurring version loop stopped by
[ADR-0137](0137-finish-v91-and-stop-iteration-loop.md). This ADR replaces ADR-0141's
explicit Combine interaction and default controls/layout, including selection and
result-reuse steps attached to that interaction. Its GUI-only scope, server authority,
privacy, bounded state and recovery safeguards remain in force.

## Primary-source interface observations

The official interfaces and help were inspected on 2026-09-13:

- [Infinite Craft](https://neal.fun/infinite-craft/): the initial desktop interface
  presents a canvas and element palette, with a short drag instruction and small edge
  utilities. Clicking Water placed it on the canvas; dragging Fire onto Water produced
  Steam without a separate submit action. Steam remained at that location and entered
  the inventory. A phone-width browser resize moved the palette below the canvas.
  That resize establishes responsive layout only, not native touch behavior.
- [Little Alchemy 2](https://littlealchemy2.com/): after Play, the interface presents
  a workspace and right-side element library, with cleanup, settings, encyclopedia
  and hints at the left edge. There is no ingredient form or Combine button.
- Little Alchemy 2's official help documents
  [double-tap duplication](https://help.littlealchemy2.com/general/duplicating-items)
  within the workspace, reducing returns to the library, and
  [long-press item details](https://help.littlealchemy2.com/general/item-info).
  Its [encyclopedia](https://help.littlealchemy2.com/encyclopedia/using-the-encyclopedia)
  contains item categories, histories and statistics outside the normal mixing loop.

These observations support removing repeated submission and reuse steps. The two-tap
interaction below is an Alchimie adaptation for pointer, touch and keyboard access;
it is not a claim that either reference game implements the same tap sequence.

## Decision

The normal loop is: tap one word, tap a different word, see the server result. The
second word immediately submits that pair through the existing owned action handler.
There is no persistent Combine button and no numbered slot-management workflow.
The first selected word remains visible in a compact workspace with short contextual
guidance. Tapping that same word again cancels selection: Alchimie requires two distinct
concepts, so this gesture must never submit a self-combination.

After a successful response, automatically carry the sole useful newly earned result
as the next first ingredient. Eligibility comes from the returned inventory's public
usefulness/depletion metadata; the browser does not inspect or infer a private recipe
or target route. If there is no single eligible new result, do not arbitrarily choose
one. A terminal win ends the interaction normally. Earned results remain available as
word choices, without a separate mandatory reuse action.

After a confirmed empty combination, retain the first ingredient and clear the second.
A different partner can therefore be tried in one tap. Keep feedback beside the active
ingredient; do not require acknowledgment or a cleanup action. Preserve free duplicate
memory and prevent an unchanged failed pair from becoming an accidental repeated POST.
The distinct-word cancellation rule also applies after an automatic result carry.

The initial playable board exposes three controls outside the word tiles: exit,
options and search. Keep the target, active ingredient, inline feedback and word
library in the main play area. Library filters, discovery history, explanations and
round options start collapsed in secondary content. Contextual selection cancellation,
earned-result choices and recovery controls appear only when their state requires
them. An available hint appears in the workbench, with its cost visible before a
request and the earned cue retained afterward. No information drawer needs to open
for an ordinary combination.

Word controls are semantic keyboard buttons. Enter or Space invokes the same selection
and automatic second-word submission as a pointer tap. When a discovery removes the
initiating focused word, restore lost focus to the carried word or inventory panel;
preserve deliberate navigation to another control while the response was pending.
Announce when a discovered word remains selected. Winning-result focus retains its
existing owner. Optional HTML5 desktop dragging
combines one owned word with a different owned word through the same guarded action
path; it is an additional affordance, not a requirement or a promise of native mobile
drag support. Reject same-word, stale, foreign and unavailable drag inputs. Keep labels
readable, controls reachable and scrolling available at narrow widths, larger text
and short viewport heights.

## Boundaries and recovery

No backend, private graph, recipe, concept, game-pack, ranking, eligibility, difficulty
or scoring changes are authorized by this interface correction. Discoveries, usefulness,
depletion, hint eligibility and target revelation remain server-authored. No private
solution values enter the browser or generated assets. Session TTL, capacity, locks,
request bounds and reaction-history bounds remain unchanged. Other games are outside
the refactor.

[ADR-0136](0136-reconcile-uncertain-alchimie-actions.md) continues to govern mutations:
use the synchronous owner guard, allow at most one verifying GET after a failed action,
never automatically replay a POST and reject stale responses after ownership changes.
While the server state is uncertain, word taps, dragging, hints and reset must not
start another mutation. Keep explicit read-only recovery available. A verifying GET
adopts authoritative state with neutral feedback; it cannot invent the missing transient
combine verdict or assume which result belongs to that request. Paid hints, reset,
terminal scoring and saved-game ownership retain their existing recovery guarantees.

## Acceptance and verification

Use real deterministic BFF rounds to measure the interaction, including a two-move
winning route whose first response contains exactly one useful new result. That route
must need three word taps from an empty selection, compared with the initial V92
sequence's six ingredient-selection/reuse/submission actions. This count is specific
to the eligible route; the returned state determines whether result carry is possible.
Do not turn an input-count example into a claim about all boards.

Check automatic second-word submission, sole-result carry, same-word cancellation,
one-tap changed-partner retries, repeated-pair guarding and both keyboard and desktop
dragging paths. Confirm the initial control count, collapsed secondary tools, retained
search/filter behavior and usable geometry on desktop, phone-width, long-label,
200%-text and short-height views. Exercise uncertain committed actions, failed GET
recovery, rapid repeated input, cross-tab ownership changes and recovered terminal wins.

Run the frontend native tests, lint, build and bundle gate, relevant real-browser
journeys and required repository checks; regenerate served assets from source. Exact
commands, results and evidence belong in [STATUS](../STATUS.md) and the
[V92 review](../reviews/v92-alchimie-gui/README.md). This decision records acceptance
criteria, not passed-test counts or completed human/physical-device playtesting.
