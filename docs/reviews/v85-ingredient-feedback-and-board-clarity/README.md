# V85 — ingredient feedback and board clarity

Valid until: the reviewed content, source or validation bindings change — then treat as history.

Verified 2026-09-08 against local main `39b64cb15cf40bbcd2000b3b12770e616d7d357f`,
which includes landed V84 `eb4155c`. V85 is ready on
`feat/v85-ingredient-feedback-and-board-clarity`; no push or deployment occurred.

## Delivered changes

| Measure | V85 change | Final stock |
|---|---:|---:|
| Native concepts | +8 | 2,388 |
| Accepted forms | +25 | 8,542 |
| New graph connections | +40 | 9,319 |
| Existing relation descriptions corrected | 1 | 41 added IDs / 1 retired ID |
| Approved playable rounds | +5 | 635 approved / 8 pending |
| Cald sau Rece eligible rounds | +4 | 224 |
| Lanț eligible rounds | +1 | 96 |
| Derived boards | 0 new; 1 clue corrected | 336 |
| Legacy puzzles | unchanged | 180 |

The eight concepts are Scorțișoară, Cacao, Vanilie, Ciocolată, Stafide, Migdale,
Alune de pădure and Semințe de floarea-soarelui. Forms include accepted grammatical and
spelling variants; they are not counted as 25 synonyms. No separate synonym count is claimed.
The Mucenici/Moldova description now correctly names the baked Moldavian variant. Its
endpoints, strength and two existing directions are preserved. The 40 new connections
provide 45 newly legal directed journeys.

New rounds are Ecler (`ct_gastronomie_337`), Amandină (`338`), Halva (`339`), Înghețată
(`340`), and Stafide→Brânză (`lt_gastronomie_221`). The last has two two-hop routes through
Pască and Poale-n brâu. All five passed separate bound analyst/verifier judgments; four
salience warnings have explicit familiarity justifications. The eight historical holds remain.

Native cinnamon and cocoa replace approximate food/coffee projections. The audit now counts
at least 14 accepted words per domain, including four exact native migrations; the ingredient
projection itself has 13 synthetic entries. This deliberate policy change is documented in
[ADR-0120](../../adr/0120-native-ingredients-and-audited-vocabulary.md). All 469 retained
projection rows and 71 legacy proxies remain exact. The audit metadata does not affect scoring.

An exact correction policy repairs two labels in `cx_gastronomie_171`: “Denumiri cu trimitere
geografică” and “Produse lactate”. One served Intrusul board receives the dairy clue; its ID
`vi_1535ff1ac283061d41a1`, choices, partition and rank remain stable. The Conexiuni source is
not pilot-eligible. No new Conexiuni, Perechi or Alchimie rounds are claimed. The shared
builder/runtime policy rejects stale or partial corrections and preserves trusted validation;
see [ADR-0121](../../adr/0121-exact-label-corrections-with-stable-board-identities.md).

## Measured improvement and limits

| Guess → target | V84 rank / feedback | V85 rank / feedback |
|---|---|---|
| Scorțișoară → Pâine | 4 / hot | 483 / cold |
| Scorțișoară → Sarmale | 8 / hot | 313 / cold |
| Scorțișoară → Plăcintă cu mere | 22 / warm | 3 / hot |
| Unt → Plăcintă cu mere | 506 / cold | 3 / hot |
| Cacao → Salam de biscuiți | 62 / warm | 3 / hot |

The comparison includes 5,376 first guesses per checkout over 224 old approved records
and 24 inputs. All old eligible pools, 82 Alchimie projections and 98 Lanț profiles remain
available and exact where claimed. Of 638 old pack records, 637 remain exact and one has
the two label corrections. Of 336 derived payloads, 335 remain exact and one clue changes;
all IDs, partitions, choices and ranks remain exact. Twenty-two old node degrees change;
all old native owners/forms, 9,278 retained edges and all legacy puzzles remain exact.

Indirect oven/yeast feedback remains too warm for some desserts. Refrigerator is weak for
Înghețată, bare “rece” is unrecognized, and Baclava is unexpectedly hot for that target.
The legal Poale-n brâu route is absent from the initial three Lanț suggestions. Additional
Cacao→Clătite and hazelnut/dessert routes were deferred. Human fairness/enjoyment and
real-device acceptance remain unmeasured; these checks do not establish release readiness.

## Verification

| Check | Final result |
|---|---|
| Python 3.12.3 backend | 1,299 passed in 679.74s |
| Python 3.14.6 backend | 1,299 passed in 595.00s |
| Isolated accounts | 53 passed on each Python version |
| Focused ingredient/public-round/board checks | 77 passed |
| Native frontend | 177 passed |
| Desktop/mobile browser checks | 122 passed; no skips or retries |
| Fixture, pack, pending gate, Ruff, docs, whitespace | passed |
| Frontend lint, typecheck, build and bundle | passed; 118.87/120 KiB |

Application assets rebuilt byte-identically to V84. Seed-38 expectations were regenerated
for current Contexto reachability and the intended Lanț selection change. No runtime scoring
formula, timing ceiling, request size or session limit was relaxed. Broad historical checks
first exposed seven stale Clătite ranks; historical values remain asserted on restored graphs,
and the 48-case follow-up and both fresh full suites pass. Other intermediate findings are
recorded in [verification.json](verification.json).

The actual public Intrusul journey was visually inspected at 390×844 after an incorrect
guess and a hint request. “Trei țin de Produse lactate.” is visible with no horizontal overflow.
See the [screenshot](screenshots/intrusul-dairy-mobile.png) and
[visual receipt](visual-review.json). This is desktop browser emulation, not a real-device test.

## Evidence

- [Graph candidates](graph-candidates.json), [independent graph review](GRAPH_REVIEW.md),
  [Mucenici correction](mucenici-link-correction.json) and [final source addendum](GRAPH_REVIEW_ADDENDUM.md).
- [Label candidates](board-label-candidates.json), [clarity review](BOARD_CLARITY_REVIEW.md),
  [verifier review](BOARD_VERIFIER_REVIEW.md) and [final digest addendum](BOARD_VERIFIER_ADDENDUM.md).
- [New-round evidence](gastronomie/CANDIDATE_REVIEW.md), [analyst judgments](analyst-review.json),
  [independent verifier](VERIFIER_REVIEW.md), [Contexto promotions](verdicts/contexto_verdicts.json)
  and [Lanț promotion](verdicts/lant_verdicts.json).
- [Six-game impact](impact/IMPACT_REVIEW.md), [content quantities](content-delta.json),
  [exact artifact delta](artifact-delta.json), [actual verification receipts](verification.json)
  and [final file bindings](review-manifest.json).

The initial graph review binds its original 40-link source. Its addendum binds the final
source including the independently reviewed Mucenici correction. Likewise, the board
addendum binds the final trusted catalog digest. Earlier review bytes remain unchanged.
Current project and rollout status live in [STATUS](../../STATUS.md) and
[BETA_CANDIDATE](../../BETA_CANDIDATE.md).
