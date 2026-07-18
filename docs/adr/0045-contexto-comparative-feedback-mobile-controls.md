# ADR-0045: Keep Contexto comparison and recovery controls bounded

Date: 2026-07-19
Status: accepted

## Decision

Assign every distinct accepted Contexto guess a stable one-based `attempt_number`, while
retaining the existing best-first public guess order. Return one server-authored `feedback`
object with a bounded `kind` of `first`, `new-best`, `warmer`, `colder`, `same`, `repeat`, or
`found`, a short Romanian message, and an optional rank delta. Classify only against ranks
already public in the session: compare a new strict best with the prior public best and other
new guesses with the prior chronological guess. Keep repeats free and preserve their original
attempt number. Never consult or serialize a target id, projection anchor, path, or category
to produce this feedback.

In the browser, use the stable ordinal for a `Recente` view and retain server rank order for
`Bune`. Show only the latest accepted comparison. Keep the guess form and a compact 44 px
clue/reveal/options action row together at the top of the scrolling play area, including a
visible countdown until the first clue unlocks. Require an inline second tap before calling
the give-up endpoint; clear an armed confirmation on text edits, suggestion/clue fills,
guesses, clues, options, escape, and game lifecycle changes.

Preserve the 444-term projection, target selection, scoring and clue limits, hidden-answer
boundary, two-hour sliding TTL, and 1,000-session cap.

## Context / why

The existing best-first list made a player's latest guess move unpredictably, so beginners
could not reliably tell whether they were improving. Recomputing comparisons in the browser
was rejected because resumed sessions, ties, repeats, and later client versions could disagree
with authoritative history. Shipping anchors, paths, or wider neighbourhoods was also rejected
because it would enlarge the hidden search space and weaken the target boundary.

Hint, reveal, and options controls inside the scrolling HUD were easy to lose on a phone. A
single-tap reveal beside ordinary recovery actions was especially easy to trigger by mistake.
A modal was rejected because the choice needs only one short local confirmation and should not
interrupt guessing.

## Consequences

Guess payloads add one integer and accepted-guess responses add one small feedback object.
Older clients may ignore both. Browser history can now offer chronological and best-first views
without reordering ambiguity, while all semantic classification remains deterministic and
server-authoritative. Feedback wording or kinds are API surface and require contract updates.
The first reveal tap never reaches the API, and resuming any guess/clue flow disarms it.
