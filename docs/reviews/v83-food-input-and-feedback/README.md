# V83 food input and feedback batch

Valid until: the reviewed forms, target records, scoring policies or bound artifacts change — then treat as history.

V83 combines five new playable rounds, six ingredient/filling feedback repairs and 24
reviewed grammatical forms. It also consolidates current-content test expectations and
keeps named-round journeys independent of incidental public-seed changes.
Decisions: [ADR-0116](../../adr/0116-share-current-content-test-expectations.md) and
[ADR-0117](../../adr/0117-food-forms-and-exact-target-feedback.md), under
[ADR-0113](../../adr/0113-outcome-based-version-batches.md).
Baseline: `38f0d62ff1cd72003ae94ed691db4c44eb78c794`, after V82's verified local landing.

## Actual gains

| Target | Difficulty | Repaired core guesses | Public food-shelf seed |
|---|---|---|---:|
| Cornulețe | normal | Gem | 6 |
| Gogoși | usor | Gem, Ulei | 26 |
| Telemea | usor | Sare | 95 |
| Cartofi prăjiți | usor | Ulei | 23 |
| Ardei umpluți | normal | Ardei | 5 |

The records are `ct_gastronomie_329`–`333` in that order. Seeds use category `gastronomie`
and the listed difficulty. All five have real public-create, core-guess, repeat/resume,
negative-control and exact-form win coverage.

- Contexto stock **218→223**, approved **216→221**, runtime selectable **212→217**.
- Whole pack **629→634**, approved **621→626**; all eight original pending holds remain.
- **24 new forms across eight existing owners**, including `urdei`, `mujdeiului`,
  `cartofilor prăjiți`, `cornulețului cu gem` and `gogoașa prăjită`.
- **Six corrected feedback pairs**, each rank 2/Fierbinte and nonwinning.
- New canonical concepts, shared KG edges and genuine synonyms: **zero**. Other game stock,
  all 336 frozen boards and all 180 puzzles remain exact.

Nine added forms previously reached only the intended fuzzy owner; fifteen were unresolved.
All are now exact inputs, retaining the same concept identity across case, spacing and
Romanian Unicode variants. Contexto repeat/resume and exact wins, plus legal Lanț hops,
are tested for every form. The original 13,180 authored surfaces retain their owners.
All eleven deliberately omitted bare/rare/holiday forms keep the same exact, fuzzy and
suggestion behavior. Normative mass-noun plurals denote product sorts; they are not synonyms.

## Feedback and review

Native exact-target pairs are closed reviewed data. Gem's two additional target IDs are
explicit; its previous preserve neighborhood/fallback and Burtă's policy remain intact.
Both modes preserve submitted public IDs, exact-self wins and private answers, and cannot
spread through target neighbors. Missing-source/anchor cases retain previous fallback.
No scoring formula, graph topology, session field, TTL, buffer or cache bound changes.

Separate baseline/candidate processes compared four canonical inputs over every baseline
approved record plus five candidates: **884 observations**, exactly six changes and **878
unchanged**. There are 218 distinct targets across those 221 record/candidate entries;
baseline stock contains three duplicate-target records. Sixty further control observations
remain exact. The changed-target boundary is also tested over the whole KG.

Independent lexical review accepted all 24 exact frozen forms. Independent factual/quality
screens covered all five raw candidate references. Strict pending critique checked five,
with zero flags; separate bound analyst/verifier reviews unanimously promoted all five via
the supported serializer/applier. These are agent judgments and source checks, not human
playtests or proof of enjoyment.

Material limitations remain explicit: Sarmale is still too hot for Cornulețe; the broad
Drojdie approximation is warm for Telemea/fries and hot for stuffed peppers; saramură and
other production/utensil vocabulary remain incomplete. Jam-filled doughnuts and oil frying
are conventional variants, not claims that every preparation uses those ingredients.
Future batches should address shared approximation problems with measured evidence.

## Refactor and preservation

`tests/current_content.py` contains manually authored immutable current expectations;
it does not load the fixtures to calculate its own expected values. Historical wave,
review, ledger, pre-apply and reconstruction hashes remain local to their tests. Independent
review found the pre-content refactor equivalent to its V82 expectations. Later current
version/count checks were centralized with their historical constraints retained.

`tests/content_scenarios.py` searches at most 1,000 normal picker seeds for a named round,
then journey tests exercise the real API. It fails rather than skipping an unavailable
round. Separate seed/date regression snapshots and immutable review archives remain.

The browser reload helper also binds to a state request issued by the new document and
reads that response immediately. A trace showed that the old URL-only waiter could select
an in-flight recovery response from the previous document, then lose its body on reload.
The repaired assertions still compare full server state and retain their original timeouts.

Inverse receipts reconstruct the complete baseline KG, pack, ranking and derived files by
original SHA-256. Every old node field outside the appended aliases, every graph edge and
puzzle, all 629 old pack records and all 336 frozen boards remain exact. Of old ranking
rows, 142 change only rank and/or selection weight; four global Contexto weights change.
Other curated games' sampled selections remain exact. Current selection repeats exactly
across 100 seeds and 30 September dates: Contexto changes 80 all-difficulty unfiltered seeds,
58 easy-food seeds/four dates and 21 normal-food seeds/two dates. The unfiltered sampled
dates and eight reviewed fixed-date selections remain exact. Seed-38 public starting
snapshots regenerate unchanged. This is bounded sampling, not all future selections.

## Evidence and verification

- `morphology-candidates.json`, `morphology-review.json`, `MORPHOLOGY_REVIEW.md`,
  `morphology-delta.json`: exact forms, ambiguity exclusions, review and full KG inverse.
- `feedback-candidates.json`, `FACTUAL_REVIEW.md`, `runtime-evidence.json`,
  `runtime-correction.json`: six facts, before/after observations and retained limitations.
- `gastronomie/`, `analyst-review.json`, `verifier-review.json`, `VERIFIER_REVIEW.md`,
  `verdicts/`: exact five-item candidate, complete screens and independent bound promotion.
- `artifact-delta.json`, `content-delta.json`, `selection-impact.json`, `public-seeds.json`:
  actual additions, preservation and current selection evidence.
- `PIN_REFACTOR_REVIEW.md`, `IMPLEMENTATION_REVIEW.md`: independent implementation checks.
- `runtime-probes.py.txt`: reusable separate-checkout capture runner; its CLI supports
  reproducing the baseline and candidate observations without duplicated API-response dumps.

Focused integration: **156 passed**, including V75–V83 history and public journeys, the
24 forms across both typed APIs and all six feedback fixes. Independent implementation
review: 53 focused checks passed. Final results:

- Python 3.12.3: **1,115 passed in 751.83s**. Python 3.14.6: **1,114 passed** and one
  known load-sensitive timing failure (50.30s against 45s); that sole case passed unchanged
  on targeted retry at **21.96s**. This is not a claim of a single all-green 3.14 full run.
- Accounts: **53 passed on each runtime** (6.29s/7.07s).
- Frontend: **173 native tests** and **108 browser checks** passed; lint/typecheck/build
  and the 118.73/120 KiB bundle gate passed. Rebuilt application assets are byte-identical.
- Both validators, strict pending gate, Ruff, docs and whitespace passed. Clean Node24
  install/audit reported zero vulnerabilities. No test threshold or session bound changed.

The initial browser run had 99 passes/nine failures: page/target crashes and timeouts under
heavy host pressure, plus the confirmed old-response race repaired above. The full rerun
passed all 108 in 6.9 minutes. Resource pressure was observed; it is not proof of each
crash's cause. Post-build Django web checks also passed (12 in 6.54s).
Actual command receipts, initial failures and retries: [verification.json](verification.json).
Source/review bindings: [review-manifest.json](review-manifest.json).
V83 is ready on `feat/v83-food-input-and-feedback` for its next landing request;
[STATUS](../../STATUS.md) remains the current status source.

Content reproduction uses the shared V24 applier with `--data-module food_input_v83_data`,
then the existing pack-only import/critique/review/apply flow and ranking/derived/mobile
builders. The alias module and existing review bytes remain authoritative; direct fixture
editing is outside this workflow. Inventory report:
`python3 scripts/report_content_delta.py --baseline 38f0d62 --text`.
No push, deployment, real-device acceptance or human playtest is claimed.
