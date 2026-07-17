# ADR-0035: Retain empty Alchimie pairs for immediate correction

Date: 2026-07-17
Status: accepted

## Decision

After an authoritative nonterminal Alchimie response returns no discoveries, retain the
exact submitted pair and one local canonical key for that pair. Disable `Combină`, the
Enter shortcut, and the action handler while the selected pair is unchanged; explain
that one ingredient must change in the existing nonterminal status and `ACUM` guide.
Make each occupied bench slot a 44 px remove button so the player chooses which concept
to replace. Any selection edit or clear dismisses the retry block. Clear it on discovery,
win, hint, reset, new game, and resume, and use a synchronous in-flight guard so rapid
activation cannot send a second request before the busy state renders.

## Context / why

An accepted empty combination spends a move and contributes to the three-attempt hint
threshold, while the static graph guarantees that its unordered pair cannot discover a
new concept on an immediate retry. Clearing both ingredients discarded useful input;
retaining only one would choose the correction direction for the player. Nielsen Norman
Group's [error-message guidance](https://www.nngroup.com/articles/error-message-guidelines/)
recommends preserving original input for correction, and GOV.UK's
[button guidance](https://design-system.service.gov.uk/components/button/) documents
duplicate activation while feedback is pending. Native remove buttons also preserve
cancel-on-release behavior described by
[WCAG pointer cancellation](https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation.html).

A persistent tried-pair set would add client history, drift across resume, and alter the
effective hint loop. Automatic resubmission would spend moves without fresh intent.
Keeping only the latest immediate block is bounded, reversible, and compatible with the
server contract.

## Consequences

An empty move still counts and its server-authored message remains the sole nonterminal
live announcement; the result card remains the terminal owner. Players can replace
either ingredient directly, while an unchanged or double-clicked pair cannot spend a
second move. Re-forming a pair after an explicit selection edit remains valid, so current
hint progression is preserved. No response fields or persistence are added. Target-ID
secrecy, scoring, category scoping, deterministic discovery, two-hour sliding TTL, and
the 1,000-session LRU cap are unchanged. Manual Romanian playtesting at 320–390 px
remains required when the in-app browser is available.
