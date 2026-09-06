# V76 Romanian input senses

Valid until: the reviewed input boundary or relevant vocabulary changes — then treat as history.

## Hypothesis and acceptance

The V75 food review exposed an input error: accent folding made `Paște` and `Paștele`
play the pasta concept. Preventing that interpretation should avoid misleading feedback,
charged attempts and false Lanț wins while preserving ordinary Romanian typing support.
The bounded decision is [ADR-0107](../../adr/0107-preserve-reviewed-romanian-input-senses.md).

Acceptance covers exact/fuzzy/advisory lookup, Contexto projection fallback, Lanț's visible
choices and local homonyms, case/space/NFD/legacy-cedilla forms, target privacy, unchanged
game state after rejection, and a subsequent valid pasta guess or hop. All 13,177 unique
existing labels, IDs and aliases retain the same resolution fingerprint.

## Before and after

| Probe | V75 baseline | V76 |
|---|---|---|
| `Paște`, `Paștele` in Contexto | Played `Paste`; charged an attempt or won a pasta target | Unknown; no attempt, guess, confirmation, suggestion or state change |
| Same forms in Lanț with a legal pasta hop | Took the hop, including a false win | Unknown; no move or state change, including a visible-label shortcut |
| `paste`, `pastele`, `paste făinoase`, longer compounds | Existing exact interpretation | Preserved |
| Unicode composition/case/cedilla variants | Same wrong sense after folding | Same bounded rejection |
| Existing food ingredient distances | Făină→Cozonac/Pâine/Clătite: 4/4/6 hops | Unchanged; outside this input fix |

The regression suite was first run against `d127abb`: **16 failed, 1 passed**. After the
fix, **17 passed**; the combined alias/Contexto/Lanț suite passed **137 tests**. An independent
review reran the 17 cases and found no actionable implementation issues. Full gate results
are maintained in [STATUS](../../STATUS.md).

Direct browser check: on an easy Gastronomie Contexto round, `Paște` and then `Paștele`
both left the visible attempt count at zero with the existing unknown-concept message.
`paste` was then accepted as `Paste`, rank 192, with one attempt; its history survived reload.
This verifies rendered behavior in the local browser, not human enjoyment or real-device coverage.

## Independent evidence and artifact preservation

- [Linguistic review](LINGUISTIC_REVIEW.md) and `review.json`: session_refactor's finite
  sense review using source-specific DOOM 3/DEX entries; independent agent judgment.
- `current-behavior.json`: baseline resolver/projection/local-neighbor probes against clean
  V75 main. True decomposed Unicode is recorded by its codepoints.
- `reproduce.py.txt`: original baseline probe source, archived as text. Its original scratch
  output path and runtime context are historical; current reproducible regression coverage
  is in `tests/test_v76_romanian_input_senses.py`.
- [Ingredient probe](INGREDIENT_PROBE.md): wave_audit's separate read-only graph diagnosis.
- `baseline.json`: exact content-artifact pins, pre-change surface fingerprint, initial
  failing-test evidence and raw linguistic-artifact digests. No generated artifact changes.

Root authored the implementation; resume_refactor independently reviewed the resolver,
all game bypasses, compatibility coverage and privacy/nonmutation tests. The linguistic
and code reviewers were separate from the implementation author.

## Remaining work

This wave adds **zero playable records and zero aliases**. It does not make the three
rejected V75 candidates eligible for promotion, add a holiday concept, or guess the
meaning of unaccented `paste`. The next content hypothesis is a separately reviewed
ingredient→dish batch for the three missing flour associations. Its graph and selection
effects, provenance, game quality and any later pending promotions require their own gates.
