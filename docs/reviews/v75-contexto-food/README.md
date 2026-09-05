# V75 Contexto food wave

Valid until: this frozen candidate batch or its bound content changes — then treat as history.

The wave adds two familiar, easy gastronomy targets with tested ordinary warm guesses.
It follows [ADR-0106](../../adr/0106-add-reviewed-contexto-food-targets.md) and the reusable
[pack-only workflow](../../PACK_ONLY_CONTENT_WAVES.md). Implementation gates are recorded
in [STATUS](../../STATUS.md).

## Hypothesis and bounded result

Recent alias waves improved spelling coverage but added no playable records. Five existing
food concepts were proposed for Contexto, category `gastronomie`, difficulty `usor`.
Acceptance required familiar targets, recognizable direct neighbors, useful ordinary
opening guesses, strict lint and unanimous independent pending-item promotion.

| Candidate | Result | Evidence affecting the decision |
|---|---|---|
| Mici | Promoted as `ct_gastronomie_318` | Grătar rank 2, Muștar rank 3, both distance 1/Fierbinte; food/adjective ambiguity independently assessed |
| Cozonac | Dropped before staging | Făină and zahăr distance 4/Rece; Crăciun unknown; Paște resolves to the pasta concept |
| Salată de boeuf | Promoted as `ct_gastronomie_319` | Salată rank 2, cartof rank 4, murături rank 6, all distance 1/Fierbinte; maioneză distance 2/Cald |
| Pâine de casă | Dropped before staging | Făină distance 4/Rece; cuptor unknown; useful secondary guesses do not repair the baking route |
| Clătite | Dropped before staging | Făină distance 6, rank 1696/Înghețat despite the ordinary recipe association |

The frozen candidate SHA is
`baef6c35007d7da7982058f0bbb220b3fbf95f91377247412368f63898e38431`.
The importer staged exactly two pending rows and skipped three. Both pending dossiers
passed strict lint with zero findings, then received independent `promote` judgments.
The existing V2 applier validated fresh bindings and applied two promotions.

## Evidence and provenance

- `gastronomie/candidates.json`: exact author-frozen five-row batch; nodes/edges are empty.
- `gastronomie/verify_factual.json` and `FACTUAL_REVIEW.md`: independent factual screening.
- `gastronomie/verify_quality.json`: complete five-row quality disposition.
- `gastronomie/runtime_openers.json`: 25 real guess-route probes, five per fixed target.
- `analyst-review.json`, `verifier-review.json`, `VERIFIER_REVIEW.md`: independent, bound
  judgments, objections and source URLs. Reviewers were root and session_refactor;
  candidate preparation was wave_audit. These are independently authored Codex-agent
  judgments with source checks, not human SME approval or Romanian-player playtests.
- `verdicts/contexto_verdicts.json` and its `dossiers/`: serialized V2 decisions, raw-review
  digests, exact coverage and the pending dossiers used for promotion.
- `selection-impact.json`: independent before/after selection sampling and public API probes.
- `allocation-receipt.json`: raw-reference-to-ID map, before/after artifact hashes,
  counts and the precise selection-weight changes.

Review provenance paths identify the original scratch inputs; their exact raw files are
archived here under matching names and SHA-256 digests. This does not establish historical
source provenance for the pre-existing KG, whose schema does not store source citations.
New game rows retain the importer's `source: ai` marker.

## Scope and selection effects

Pack stock is **620 = 612 approved + 8 pending**, up from 618/610/8. Contexto has 203
eligible targets, up from 201; original-game eligibility totals 450, up from 448.
There are zero new aliases, nodes, edges or puzzles. All 618 previous pack records and
all 336 frozen Intrusul/Perechi boards remain identical. Existing ranking scores, approval
and eligibility remain identical; adding two strong targets shifts ordinal ranks and
four existing Contexto selection-weight bands. The receipt records those exact changes.

Across seeds 0–99 and September 2026 daily dates, all same-artifact repeat runs matched.
The other five games had zero selection changes. Contexto changed 81/100 unfiltered seeded
selections and 1/30 daily selections; the gastronomie/usor shelf changed 55/100 and 10/30.
These are release-to-release sampling effects, not a repeat-rate or enjoyment measure.
Scoped public API seeds 5 and 6 select the new targets, hide the answer on creation, accept
ordinary warm guesses and finish with a server-scored win. The existing seed-38 public
start snapshot remains unchanged, even though it does not expose the selected target.

The next useful content investigation is the rejected candidates' ingredient/holiday
feedback, including the Paște/Paste sense collision. It requires separately reviewed
topology or input interpretation changes, followed by new candidate reviews. This wave
does not establish human enjoyment or authorize production rollout.
