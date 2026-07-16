# ADR-0031: Teach each game through the next visible action

Date: 2026-07-16
Status: accepted

## Decision

Make `Ușor` the initial free-play selection in all four browser games. Keep the explicit
start screen, but replace each rules paragraph with one short sentence and a shared,
semantic three-step strip. During play, show one compact `ACUM` cue derived only from
already-visible client state: what to select or type next, the selection count, and the
existing server-authored result. Do not infer a hint, answer, path, group, or recipe.

Design mobile first: give coarse-pointer controls a 44 px minimum target; keep header
status and category choices in horizontal rails; keep Alchimie's two-item bench and
Conexiuni's count-plus-verify coach reachable; let long Lanț paths scroll horizontally;
and render Conexiuni in two readable columns below 481 px and four columns above it.
Pair every colour signal with text or an icon, expose Contexto rank direction visibly,
announce important inline feedback politely, and prevent global Enter shortcuts from
hijacking focused controls. On wider screens, retain the same loop in a focused 760 px
play column instead of adding more simultaneous UI.

## Context / why

The existing screens already had strong delight beats—fresh-discovery glow, temperature
feedback, group locking, one-away retention, sound, and reduced motion—but presented the
rules before the action. Mobile headers wrapped into several rows, category chips formed a
setup wall, important actions could scroll away, and Contexto's `#1` convention was only
available in hover text.

Current English-language analogues converge on the same hierarchy. NYT Connections keeps
the 16-word board, four-item selection, brief near-miss feedback, and post-game stats as the
main loop (https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections).
Semantle puts one guess input and semantic-proximity feedback first, with hints secondary
(https://semantle.com/faq/). Infinite Craft starts from a tiny inventory and makes each new
combination the reward (https://neal.fun/infinite-craft/). Wikispeedia keeps source, target,
and the current route legible while explaining the loop in two bullets
(https://dlab.epfl.ch/wikispeedia/play/). Apple recommends reachable game controls, while
WCAG requires colour-independent meaning and reduced animation
(https://developer.apple.com/design/human-interface-guidelines/game-controls,
https://www.w3.org/WAI/WCAG22/Understanding/use-of-color,
https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions).

Why not auto-create an easy session on route entry: that would allocate server sessions for
visitors who only browse and would hide the free-play versus daily choice. Why not a tutorial
modal: it delays the first useful action and repeats information the live state can explain.
Why not copy an analogue's colours, dimensions, or wording: the interaction hierarchy is the
useful pattern; this game's Romanian identity and existing accessible accent system remain
its own.

## Consequences

Beginners see the recommended setting and full loop before starting, then get a short next
action instead of a repeated rules paragraph. Mobile selection and input controls stay
reachable, long Romanian labels remain readable, and keyboard activation no longer risks a
second combine, submit, or replay. The lobby blurbs are one sentence each, while history and
advanced actions remain available below the game choices.

The change is frontend-only. Game generation, daily seeds, scoring, clues, typo suggestions,
hidden-answer boundaries, two-hour sliding TTL, and the 1,000-session per-game caps are
unchanged and server-authoritative. Source-contract tests pin the shared guide, easy default,
responsive rails/grid, touch targets, visible rank legend, live feedback, and shortcut guards.
The initial JS/CSS bundle is 116.11 KiB gzip under the 120 KiB budget. Playtests should measure
first-action time, first-round completion, hint use, accidental taps, and abandonment at 320–
390 px before considering removal of the explicit start step.
