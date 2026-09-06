# ADR-0107: Preserve reviewed Romanian input senses

Date: 2026-09-06
Status: accepted

## Decision

Treat the complete accented spellings `Paște` and `Paștele` as unresolved until their
actual senses are supported by a separately reviewed content change. Check this finite
set before accent folding, confident correction, projection fallback or advisory suggestions.
Membership preserves accents while normalizing NFKC, case, whitespace and legacy Romanian
cedilla characters. The original accent-insensitive resolver remains in place for other inputs.

Apply the boundary to the shared exact/fuzzy/suggestion service and Contexto's projection
fallback, and before Lanț's visible-choice and local-homonym shortcuts. Rejection uses the
existing unknown-concept response without an attempt, move, score, confirmation or suggestion.
Do not reinterpret a holiday as `Masa de Paște` or add a graph owner through this fix.

Preserve `paste`, `pastele`, qualified compounds, every authored label/ID/alias mapping,
Moldova homonym handling and the earlier `intrigii`/`intrigilor` fuzzy-deny policy. This is
a narrow exception to the accent-folding/typo contracts of ADRs 0012/0022/0062, not a
replacement for them or a general rule that accentless Romanian input is ambiguous.

## Evidence

V75's rejected Cozonac candidate exposed the collision. The current implementation folded
`Paște` to the `Paste` label and `Paștele` to the `pastele` alias. Both counted as pasta
guesses in Contexto and could win a legal Brânză→Paste Lanț round.

The [DOOM 3 holiday entry](https://dexonline.ro/definitie/pa%C8%99te/1258487) distinguishes
these spellings from the plural recorded in the [pastă entry](https://dexonline.ro/definitie/past%C4%83/1280847).
An independent linguistic/safety review approved the bounded exclusion; an independent
implementation review checked every bypass and the public nonmutation behavior.
These are agent reviews, not human subject-expert approval. Full evidence and limits:
[V76 review](../reviews/v76-romanian-input-senses/README.md).

## Consequences

The game stops silently assigning this unsupported sense to an unrelated concept. It still
does not recognize a standalone Easter holiday. Accentless `paste`/`pastele` retain their
existing food interpretation; this wave does not infer intent when the distinguishing
diacritic is absent. Any expansion of the exclusion set requires new evidence and review.

No node, edge, alias, puzzle, pack row, ranking, derived board, frontend asset or mobile
artifact changes. Selection/daily determinism, hidden answers, session TTL/cap/locking,
request limits and bounded caches/history remain unchanged. Missing flour associations and
holiday/oven vocabulary are separate content work, requiring fresh review before promotion.
