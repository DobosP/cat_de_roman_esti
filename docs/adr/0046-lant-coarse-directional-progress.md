# ADR-0046: Easy Lanț gives coarse directional progress

Date: 2026-07-19
Status: accepted

## Decision

After every successful easy-mode hop, compare the previous and current concepts with
the existing directed distance-to-target map and return exactly one coarse progress
kind: `closer`, `lateral`, `farther`, `dead_end`, or `won`. Pair it with one
short Romanian message. Never expose either distance, the comparison inputs, corridor
membership, or a route marker. Normal and hard games retain their existing move
responses without this automatic progress.

Keep only a capped scalar count of consecutive easy hops that are lateral, farther, or
dead ends. Cap it at two; reset it after a closer hop, victory, or free undo. Serialize
only `backtrack_recommended: boolean`, never the count. The browser renders the coarse
result with an icon and short text and gives the existing free undo control a visible,
textual recommendation after two non-improving hops. Keep local choices, unrestricted
legal typing, staged voluntary hints, score, and route secrecy unchanged.

Make the beginner loop tap-first with “Alege o legătură”. After the first hint stage,
rename the repeated action “Mai clar”. Recovery and hint chips may fill the text input,
but may focus it only for a fine pointer so a tap never summons a phone keyboard.

## Context / why

The V34 local menu reduced the whole graph to a readable choice, but a beginner still
could not tell whether an exploratory legal hop helped. Exact remaining distance would
turn play into greedy route following, while marking corridor choices would reveal
which branches are authored as productive. No feedback leaves two harmless detours
feeling identical to being lost.

A five-state comparison communicates direction without revealing topology. Two
consecutive non-improving hops are enough to surface the already-free recovery action;
retaining every comparison or chain position would grow session state for no gameplay
benefit. Easy mode receives the automatic aid because normal and hard deliberately
preserve more uncertainty.

## Consequences

Easy move responses add a bounded `progress: {kind, message}` object and every state
adds the boolean `backtrack_recommended`. The existing target-distance traversal used
for dead-end detection supplies the comparison, so successful moves add no graph pass.
The session adds one integer capped at two; the two-hour sliding TTL and 1,000-session
LRU cap are unchanged.

Tests pin all five progress kinds, directed comparison, cap/reset behavior, the absence
of exact distance/corridor fields, normal-mode omission, focus safety, undo emphasis,
tap-first copy, and the repeated-hint label. Mobile clients may ignore both additive
fields until they adopt this beginner presentation.
