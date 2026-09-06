# V82 playable food batch

Valid until: the reviewed targets, vocabulary policies or bound content change — then treat as history.

V82 adds **eight selectable Contexto rounds** and repairs the defining `burtă` guess for
Ciorbă de burtă in the same batch. It also adds reusable content-delta reporting and the
owner's broader version objectives. Decisions: [ADR-0113](../../adr/0113-outcome-based-version-batches.md)
and [ADR-0114](../../adr/0114-reviewed-food-batch-and-scoped-tripe-feedback.md).
Cold Alchimie generation also gains bounded pair-result reuse under
[ADR-0115](../../adr/0115-reuse-alchimie-pair-results-within-a-build.md).
Baseline: V81 `953391999a8b9f43cb96885716f1413445465123`, already merged into local main.

## Actual gains

| Target | Difficulty | Useful tested guesses | Public food-shelf seed |
|---|---|---|---:|
| Cozonac | usor | făină, nucă, desert, cacao | 12 |
| Pască | normal | brânză, desert, făină, ou | 38 |
| Muștar | usor | mici, sos, grătar, condiment | 6 |
| Mujdei | usor | usturoi, sos, grătar | 58 |
| Ciorbă de burtă | normal | burtă, ciorbă, oțet, usturoi, smântână | 9 |
| Urdă | normal | brânză, lapte, plăcinte | 74 |
| Friptură | usor | carne, grătar, sare | 5 |
| Bulz | normal | mămăligă, brânză, porumb, brânză de burduf | 17 |

The new IDs are `ct_gastronomie_321`–`328` in that order. Seeds use
`category=gastronomie` and the listed difficulty. All eight have real public-create,
useful-guess, repeat/resume, negative-control and exact-win coverage. Old public smoke
seeds become Mici 0, Salată de boeuf 11 and Clătite 9 on the easy food shelf.

- Contexto stock: **210→218**, approved **208→216**, runtime selectable **204→212**.
- Whole pack: **621→629** records, **613→621** approved, eight original pending holds.
- New canonical concepts, graph connections, forms and genuine synonyms: **0 each**.
- Other game records, all **336 frozen boards**, **180 puzzles**, KG and mobile payload: exact.
- Player-visible feedback repair: **one** defining ingredient route; no UI/game mechanic change.
- Generation efficiency: **88.89% fewer graph queries** across twelve fixed-seed Alchimie
  sessions, with the complete sessions and all 82 curated projections unchanged.

`burtă` previously borrowed body feedback: four hops, rank 434, Rece. For the exact soup
it now gives one hop, rank 2, Fierbinte without winning. Its surface, public identity,
body-domain vocabulary row and penalty stay exact. Explicit target-only policy prevents
borrowing the soup's adjacent routes; every other KG target retains the old body anchor.
Gem retains its reviewed direct-neighborhood policy. Privacy, repeat/resume, actual target
wins and missing-anchor/custom-graph behavior have focused regression coverage.

The initial full gate hit the existing Alchimie timing ceiling under host load 75. Profiling
found 20,606,576 common-neighbor calls across the twelve mined seeds, often for the same pair
in different search states. A build-local memo retains at most 4,096 immutable pair results,
then computes uncached misses normally. Calls fall to 2,288,987; frontier/pair order, search
limits, RNG, global projection LRU and session bounds stay exact. The unchanged 45-second
test passes at 29.96 seconds. Complete twelve-session and 82-projection comparisons match
their baseline hashes. These measurements are host-load dependent, not a universal speedup
claim. Synthetic tests cover empty results, capacity exhaustion and build isolation.

## Review and limits

The scout sampled 23 food targets and 764 fixed-session guesses. Eight entered the frozen
candidate file; the other 15 have explicit dispositions. Independent factual and quality
screens covered all eight raw references. Strict pending critique reported eight checked,
zero flagged; separate bound analyst/verifier reviews unanimously promoted the eight.
The existing serializer and applier completed the full batch with zero prospective FAILs.

The same 764 probes were repeated after the repair: one changed (`burtă` against the soup),
763 remained exact. This is bounded API sampling, not all possible inputs. The policy's
changed-target set is separately tested across every current KG target.

Remaining imperfections are retained in the review, not counted as fixes: butter and some
pastry/holiday words for Cozonac/Pască; seeds for Muștar; fish/oil/lemon for Mujdei; whey and
some forms for Urdă; oven/pan/subtypes for Friptură; mălai and some forms for Bulz. Mămăligă
is still over-warm for the soup through a weak contrast edge. These are prioritized follow-up
candidates for another coherent feedback/vocabulary batch. Bread and the screened-out
sweet targets are not silently promoted. Agent reviews are not Romanian human playtests.

## Preservation and selection

The delta receipt reconstructs the complete original pack, ranking and derived files by
V81 SHA-256. Every old pack record, approval, quality estimate and eligibility remains exact;
rank insertion and nine global Contexto weight changes are recorded. Frozen payloads and
all original KG vocabulary/edges/puzzles remain exact. Historical review artifacts are intact.

Across 100 seeds and 30 September dates per scope, other curated games' selections match.
Contexto changes 85 unfiltered seeded selections, 96 easy-food and 86 normal-food selections;
10 easy-food and nine normal-food daily selections change. The unfiltered sampled dailies
match. Repeated selection against the same final artifacts matches exactly. All-six browser
journeys separately cover actual play; seed-38 public starting snapshots regenerate unchanged.

## Evidence and checks

- `gastronomie/`: exact candidate, factual and quality screens.
- `FACTUAL_REVIEW.md`, `analyst-review.json`, `verifier-review.json`, `VERIFIER_REVIEW.md`,
  `verdicts/` (including its dossiers): independent judgments and exact pending bindings.
- `runtime-evidence.json`, `runtime-correction.json`, `shortlist/dispositions.json`: compact
  probe results, changed observation and every screened-out candidate.
- `artifact-delta.json`, `content-delta.json`, `selection-impact.json`, `public-seeds.json`:
  actual content gains, complete baseline reconstruction and selection evidence.
- `performance-receipt.json`, `IMPLEMENTATION_REVIEW.md`: complete Alchimie equivalence,
  query reduction, bounded memo and independent implementation review.
- `performance-capture.py.txt`: reproduce complete Alchimie payload hashes in the baseline
  and candidate checkouts using `PYTHONPATH=.`, `--mode mined|curated` and `--output <scratch>`.
- `runtime-probes.py.txt`: reusable runner; execute from repo root with `PYTHONPATH=.` and
  `--output <scratch-file>`. It supports `--candidate-file`, `--targets` and `--words`.

Focused integration: **48 passed**, including the new report and feedback tests, all eight
public journeys, V75/V80 public routes and complete V81 history reconstruction.
Final complete backend suites: **1,057 passed** on Python 3.12.3 (641.60 s) and 3.14.6
(588.88 s), with no skips. Accounts: **53 passed** on each. Frontend: **173 native tests**,
lint/typecheck and retained bundle budget passed; **108 desktop/mobile browser checks**
passed in 7.7 minutes. Validators, strict pending gate, Ruff/docs/whitespace are GREEN.
`verification.json` records actual commands/results and intermediate failures. The current
state is [STATUS](../../STATUS.md). The old seed-dependent typo test now uses a fixed real
target so new content cannot silently skip the correction contract.

Reproduce the inventory report with
`python3 scripts/report_content_delta.py --baseline 9533919 --text`; omit `--text` for JSON.
The report separates forms, approvals and declared eligibility; linguistic synonym claims
and actual runtime availability still require their own evidence. It never treats file churn
as new game content. Deployment, real-device checks and Romanian-player acceptance remain
outside these local results; the [beta checklist](../../BETA_CANDIDATE.md) records those gates.
