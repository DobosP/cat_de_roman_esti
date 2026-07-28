# ADR-0062: Refine bounded recovery and player-state clarity

Date: 2026-07-28
Status: accepted

## Decision

Make stuck states easier to read without opening the six games' answer space.

- Alchimie unlocks its paid progressive hint after two consecutive distinct barren
  experiments. From the fourth total barren experiment onward, an otherwise empty combine
  may append one of three deterministic, generic strategy whispers. Whispers are free,
  rotate by the bounded experiment count, and name no recipe, undiscovered concept, or target.
- Conexiuni permits at most two redacted label-pattern clues. They unlock at two and three
  accepted mistakes; each keeps the existing 100-point penalty. The second clue moves to
  another unsolved category deterministically when possible, while category identity and
  membership remain server-only.
- Cald sau Rece splits the old cold tail with `Foarte rece`: rank percentiles are
  `Fierbinte` through 0.5%, `Cald` through 3%, `Călduț` through 10%, `Rece` through 40%,
  `Foarte rece` through 70%, then `Înghețat`; a reachable distance-one non-target remains
  `Fierbinte` regardless of percentile. A confident fuzzy correction to a non-target concept
  first returns a per-game confirmation handle and mutates no attempt state. Echoing that
  handle with the same resolution plays it. Exact labels, aliases, diacritic-insensitive
  matches, and a fuzzy correction that is itself the target keep their direct behavior.
- Lanț returns automatic coarse progress on `usor` and `normal`; `greu` omits that progress
  object but retains voluntary help and automatic dead-end recovery. Its three-stage
  voluntary-help counter is capped for the whole session and survives moves and undo, while
  every hint recomputes its content from the current position. The automatic two-move undo
  recommendation remains `usor`-only.

Keep all additions inside the existing 7,200-second, 1,000-session-per-game stores. Preserve
deterministic selection, bounded histories, score authorship, operationIds, and the hidden
answer boundary. Client-only clarity may add a fresh-board action, terminal loss summaries,
starter labels, and compact disclosures without creating new answer fields.

## Context / why

The V41 pilot surface still made a valid but unproductive action feel like failure. Alchimie
waited too long before help, Conexiuni offered no recovery after its first redacted clue,
Contexto silently spent a typo as a guess, and normal Lanț withheld the same coarse direction
that beginners already understood on easy. Exact recipes, category membership, routes, or
distances were rejected because they turn discovery into following an answer.

A confirmation round-trip is worthwhile only for a non-target fuzzy interpretation: accepting
a confidently corrected target remains evidence that the player knew the answer. Session-wide
Lanț escalation avoids reteaching the first hint stage after every exploratory move while
retaining a single capped integer.

## Consequences

Clients must accept seven Contexto temperature strings and the additive confirmation fields.
Conexiuni state can carry two redacted clues and `clues_used` can reach two. Lanț normal moves
can carry the existing `progress` object. Alchimie sessions add one integer bounded by the
existing 496 distinct-pair memory; Conexiuni retains at most two clue/category entries; Lanț's
help counter remains capped at three. Tests pin no-mutation confirmation, target secrecy,
redacted clues, deterministic rotation, hard-mode progress omission, and state bounds.
