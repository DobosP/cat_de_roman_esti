# V78 dessert target re-review

Valid until: the next relevant food-feedback or target wave — then treat as history.

V78 freshly screens Cozonac and Clătite after V77 repaired their flour paths.
Both candidates are **dropped before staging**: broader ordinary guesses still
produce misleading feedback. No game row is promoted, allocated or removed.
The decision is [ADR-0109](../../adr/0109-defer-dessert-targets-after-feedback-review.md).
This is a completed negative candidate review, not a new served-content release.

## Evidence affecting the decision

The exact two-row batch uses existing nodes, category `gastronomie`, difficulty
`usor`, and empty topology arrays. Its candidate SHA-256 is
`7a7c22fba430bbd23d84dd33d78979ba6b28670338151daeacf7999dce621b38`.
Sixty-eight fixed-target sessions exercise the actual Django guess API, including
ingredients, fillings, holidays, spelling/inflection wins and unrelated controls.
A second reviewer reran the same archived probe script and reproduced its JSON
byte-for-byte; `reproduction.json` records the command and both output digests.

| Target | Useful feedback retained | Reason to defer |
|---|---|---|
| Cozonac | Făină: 1 hop/rank 2/Fierbinte; Zahăr: 2/25/Cald; Desert: 1/4/Fierbinte | Nucă: 4/504/Rece, despite being an ordinary filling; generic Fruct is 1/17/Fierbinte. Unt is 4/503/Rece. Common holiday, oven and dough inputs remain unresolved. |
| Clătite | Făină: 1/2, Ou: 1/5 and Dulceață: 1/7, all Fierbinte; Lapte: 2/40/Cald | Gem: 6/1699/Înghețat while Dulceață is hot. Unt and Miere are 6/1698/Înghețat. The ordinary filling route remains inconsistent. |

The runtime counts 23 and 9 incoming non-distractor neighbors respectively;
`candidate-metrics.json` records those counts and the passing engine floors.
Factual and quality reviewers assess recognizable associations separately from
those counts. Both targets have tested exact-answer spellings. Neither fails for obscurity or
merely lacking a warm opener: the numerical C3/C4 floors do not settle the
fairness of accepted, obvious ingredient guesses. The full player-route review
finds those remaining contradictions unsuitable for this easy expansion.

`Gem` and `Nucă` are Contexto projection terms, not exact KG aliases. Both currently
borrow `Miere` as their feedback anchor, explaining the distant responses.
The broad probe also records unresolved vocabulary and unrelated fuzzy suggestions;
those observations are not all promotion blockers or a mandate to accept every term.
V76 still prevents accented Paște from being played as pasta without an attempt.

## Bound review and preservation

- `gastronomie/candidates.json`, `verify_factual.json` and `verify_quality.json`:
  exact raw batch and complete independent factual/quality screening.
- `FACTUAL_REVIEW.md`, `ADVERSARIAL_REVIEW.md` and `adversarial-review.json`:
  source checks and the independently challenged pre-staging disposition.
- `DIAGNOSIS.md`: independent source diagnosis and future test requirements;
  its V79 predictions are exploratory and no mapping change was applied.
- `runtime-openers.json`, `PROBE_FINDINGS.md`, `runtime-openers.py.txt`:
  complete API observations, direct neighborhoods and portable reproduction.
- `candidate-metrics.json`, `preflight.json` and `reproduction.json`: engine floors,
  complete read-only candidate binding, and the second execution of the probe runner.
- `preservation.json`: nine current generated/ledger artifacts are byte-identical
  to main `9abbc5289d97881ccd7a927c779fccfaacfe8e91`.
- `verification.json` and `review-manifest.json`: actual checks and SHA bindings.

This uses the early screening boundary of the [pack-only workflow](../../PACK_ONLY_CONTENT_WAVES.md).
Because both raw candidates are dropped, the importer and pending-item gate do not
run. There are no staged IDs, pending dossiers, V2 promotion artifacts or invented
verification flags. Existing V75 rejection evidence remains immutable.

All 620 pack rows (612 approved, 8 pending), 620 selection-ranking rows, 336 frozen
derived boards, 180 puzzles, 8,450 aliases and editorial holds remain exact.
Eligible Contexto stock stays 203. Unchanged runtime and artifact bytes preserve
selection and scoring; no new before/after selection sample is claimed.
The served graph remains `fixture-v77-flour-associations`, with 2,364 nodes and
9,219 edges. Session limits, hidden-answer behavior and frontend assets are unchanged.

For reproduction, copy `runtime-openers.py.txt` into the task scratch directory as
`runtime_openers.py` and run:

```bash
PYTHONPATH=. <python> <scratch>/runtime_openers.py --root . --out <scratch>/runtime-openers.json
```

The command creates and deletes temporary sessions in its own process. It does not
make these targets selectable or mutate fixtures. Exact checks and prior versus
fresh verification are distinguished in [STATUS](../../STATUS.md).

## Next bounded investigation

V79 should evaluate a Contexto-only `gem` feedback anchor using the existing
Dulceață concept. Keep submitted `gem` as a distinct, nonwinning projected word even when the hidden
target is Dulceață; direct `dulceață` input must still win that target normally.
Preserve the projection penalty and private anchor, and compare feedback across
all approved targets before accepting it. A convenient exact alias would conflate two concepts.
This is a repair hypothesis, not an approved mapping or an automatic Clătite promotion.
Cozonac still needs a separate honest nut route. Bread remains deferred from V77.

The reviewers are independent Codex agents with source checks, not human Romanian
players. No push, deployment, accounts enablement or production re-verification ran.
The external public-beta gates remain in [BETA_CANDIDATE](../../BETA_CANDIDATE.md).
