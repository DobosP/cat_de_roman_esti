# ADR-0154: Expand V96 content and clarify input recovery

- Status: accepted
- Date: 2026-09-17
- Extends [ADR-0153](0153-expand-discovery-and-remember-attempted-pairs.md).

## Decision

Complete V96's independently reviewed content and input/focus improvements before the
owner-authorized landing, then begin V97 from landed main. Add the accepted three pack
entries, two quick boards and two Alchimie preparations/five recipes through the existing
raw, allocated and final live-audit gates. Preserve the KG, previous game payloads and
scores, and all eight compatible saved-book generations. No capacity is raised.

For unsupported Cald sau Rece guesses, state clearly that the word is outside the game's
vocabulary and that no attempt was spent. Keep authoritative attempts, scoring, clues,
exact resolution, reviewed projections and confident correction unchanged. Apply a
normalized displayed-label check only to advisory suggestions: retain one substitution,
an adjacent transposition, a complete label with one/two extra trailing keystrokes, or
similarity of at least 0.82. An alias match alone must not offer an unrelated visible label.
Existing target/proxy privacy filtering still applies before suggestions are displayed.
The client labels these as spelling variants and still only fills/focuses the input.

After a lost Alchimie combine response is reconciled through authoritative GET, restore
the activated usable word or deliberate collection fallback. Queue that focus only after
successful state adoption, respect focus moved elsewhere while waiting, and keep generation
and save-ownership checks. Never replay the mutation. Cached no-request acknowledgments
keep V95's synchronous centering and do not leave a deferred focus reference.

## Consequences and verification

The new message separates unsupported vocabulary from a wrong guess. The advisory filter
may withhold a useful alias-based suggestion; it cannot change accepted meanings or ranks.
Regression checks retain close typo help and hidden-answer protection. Keyboard browser
checks cover committed/uncommitted responses, deliberate focus movement, depleted inputs,
320px doubled text and repeated cached attempts. Existing Lanț captions remain unchanged;
more specific earned explanations are a separate review queue for the next session.

Evidence and exact integration results: [V96 review](../reviews/v96-words-and-input-clarity/README.md)
and [STATUS](../STATUS.md). Browser and agent reviews do not replace owner playtesting.
