# V87 — snack and action quality

Valid until: the reviewed source, content or validation bindings change — then treat as history.

Started 2026-09-08 from local main `daae025b19517c18cba2f46c6b11ea4991d9a19c`,
which includes landed V86 `7d8b177`. V87 is on `feat/v87-snack-and-action-quality`.
Implementation and full integration are GREEN; ready for local landing. No push or deployment.

## Player problems and delivered changes

V86 left Biscuit deferred: familiar flour, butter, sugar and dessert guesses were weak.
V87 connects familiar baked snacks to specific ingredients, preparation and type cues;
stronger feedback now supports six independently approved, selectable easy rounds.
The old UI also stranded a committed win when its response was lost and charged a second
clue on a natural retry. Contexto now checks the authoritative state once; failed
verification exposes a persistent read-only retry and pauses further mutations.

| Metric | V87 addition/change | Final inventory |
|---|---|---|
| Native concepts | +9; none removed | 2,406 |
| Directed graph links | +50; no old edge changed/removed | 9,410 |
| Accepted forms | +31: 30 grammatical/qualified, 1 sourced lexical equivalent | 8,603 |
| Reviewed lexical equivalent | `cremeș` → Cremșnit | Counted separately from grammatical forms |
| Projected inputs | Retire Chec/Brioșă; add generic `tort` | 467 across 26 domains |
| Exact feedback corrections | 3 native + 2 projected source/target pairs | 9 native pairs, 4 projected neighborhoods |
| Cald sau Rece rounds | +6, all newly authored/promoted/eligible | 241 total, 239 approved, 235 eligible |
| Lanț / Conexiuni / Alchimie rounds | +0 | 97 / 74 / 79 eligible |
| Intrusul / Perechi boards | +0; all 336 full rows exact | 183 / 153; 144 / 113 preferred |
| Legacy KG puzzles | +0, all exact | 180 |

The raw delta reporter cannot classify synonyms automatically. The one lexical-equivalent
claim above comes from the independently checked linguistic article and recipe usage
in the graph review.
No form, projection or edge is counted as a new playable round.

New concepts: Chec, Pandișpan, Cremșnit, Tort Diplomat, Pișcot, Brioșă, Praf de copt,
Bicarbonat de sodiu alimentar and Gelatină alimentară. Distinct baking/setting inputs
retain qualified senses; directed recipe relationships do not manufacture reverse moves.
All old concept owners/forms, 9,360 edges and 180 puzzles are preserved. Exactly 28 old
nodes change only their generated degree. All 649 old pack records remain exact.

## Playable batch and feedback boundaries

| ID | New easy target | Reviewed defining cues |
|---|---|---|
| `ct_gastronomie_346` | Biscuit | Flour, butter, sugar, oven and baking-powder variants |
| `ct_gastronomie_347` | Chec | Flour/egg/sugar/oil; related Pandișpan stays nonwinning |
| `ct_gastronomie_348` | Cremșnit | Vanilla cream, milk, starch, pastry type and powdered sugar |
| `ct_gastronomie_349` | Tort Diplomat | Pișcot, whipped cream, food gelatin, fruit and broad tort input |
| `ct_gastronomie_350` | Pișcot | Flour/egg/sugar preparation and related Biscuit input |
| `ct_gastronomie_351` | Ciocolată | Cocoa and explicitly qualified solid-chocolate recipe inputs; related hot drink |

The exact feedback fixes are Pandișpan→Chec, Biscuit→Pișcot, Prăjitură→Cremșnit,
projected Tort→Tort Diplomat and projected Ciocolată caldă→solid Ciocolată.
Each is hot at rank 2, preserves the guess identity and cannot win for a related word.
Hot chocolate keeps its former Tea fallback elsewhere. Tort uses Prăjitură elsewhere;
its secondary textile sense is disclosed and it is neither a native owner nor a synonym.

Review found that Tort's fallback would accidentally inherit Prăjitură→Cremșnit.
The final guard isolates exact native exceptions from projected scoring and typo filtering:
Tort→Cremșnit stays cold at rank 255 while native Prăjitură→Cremșnit is hot at rank 2.
Legacy projection proxying is retained. The ranking formula, graph direction and session
bounds are unchanged. Brioșă→Chiflă changes only the projection audit's representative;
the other 25 examples and all four prior native-audit tuples stay exact.

Six complete dossier-bound reviews have zero FAIL/WARN findings; separate analyst and
verifier judgments promote all six. These are agent reviews with primary-source checks,
not human Romanian-player acceptance. Public journeys cover selection, private clues,
projected guesses, repeats, resume and exact wins. Pandișpan and Brioșă remain valid
inputs, with hidden targets deferred for overlap and brioche/muffin sense ambiguity.

## Action reliability

[Baseline proof](action/README.md) records two actual-BFF defects: a lost winning response
left no client result/score, and a lost paid-clue response let a retry buy the next clue.
A shared synchronous action owner now serializes guess, clue, giveup and verification.
An ambiguous failure issues one GET, adopts only the matching owned session, and never
replays the mutation. Failed reads keep “Verifică jocul” visible; all mutating controls
stay paused until recovery. A different saved pointer is detected before a POST and
provides “Încarcă jocul curent”. Unmounted or stale responses cannot displace a new game.

Confirmed expiration forgets only the owned pointer; uncertain exit preserves recovery.
Storage failure still permits local play. Existing terminal effects record verified
completion once. No server-session fields, TTL, size cap, request limits, score formula
or dependency were added. Other five games retain V86's creation/replay improvements.

## Validation

- Exact independent graph review: 9 nodes / 31 forms / 50 edge indices accepted; no blockers.
  Supported graph/import/promotion transactions pass both validators. The preflight covers
  324 beginner words and all 50 added links.
- New content suite: **56 passed**, including exact history reconstruction and six public journeys.
- Focused action checks: **193 native / 20 desktop-mobile browser checks passed**.
  The new browser cases passed their first run. Lint/build/bundle pass at **118.90/120 KiB**.
- Full six-game frontend is GREEN: **193 native / 168 desktop-mobile browser checks**,
  lint, typecheck, build and bundle. Full backend: **1,409 passed on each Python
  3.12.3/3.14.4**, with **53 accounts tests each**. Both initial runs passed 1,408/1,409; a stale projection test was corrected and
  both complete matrices reran GREEN.
- Historical compatibility: 196/197 initially passed; a V85 loop incorrectly compared the
  new Tort row with its old vocabulary. It now requires exact reconstructed historical rows;
  all 57 affected-module cases pass. Original evidence is preserved in `impact/`.
- Final capture covers 9,087 old-target first guesses (233 approved records × 39 inputs).
  All 82 Alchimie and 100 Lanț profiles and 336 derived rows stay exact, with no lost
  eligible stock or shortest-menu choices. One existing menu gains Chec within bounds.
- Root and UI author inspected desktop/mobile retry screenshots. The notice, retry and
  disabled action controls fit the viewport; mobile's pre-existing horizontal HUD remains.
- Initial native run was 189/192: three stale source-shape expectations were updated to
  require owned authoritative recovery. Then 192 passed; one added behavior case gave 193.
  Original evidence is preserved, including the two baseline defect demonstrations.
- Seed-38 changes only Contexto reachability 2,321→2,330; other game start payloads stay exact.

Both content validators, the strict pending gate, Ruff, documentation and whitespace checks
pass. [Actual verification receipts](verification.json) bind all 16 final green commands
and their complete lossless logs; [review manifest](review-manifest.json) binds the changed
source, generated artifacts, decisions and evidence, including removed built assets.

## Evidence map

- [Graph authoring](GRAPH_AUTHORING.md), [exact graph review](GRAPH_REVIEW.md),
  [candidate inventory](graph-candidates.json), [graph delta](graph-delta-check.json).
- [Content delta](content-delta.json), [artifact inverse](artifact-delta.json),
  [candidate facts](gastronomie/CANDIDATE_FACTS.md), raw factual/quality screens under
  `gastronomie/`, and complete `dossiers/`, `analyst-review.json`, `verifier-review.json`
  and portable V2 `verdicts/contexto_verdicts.json`.
- [Feedback isolation](feedback-isolation-review.json),
  [audit representative](audit-representative-change.json),
  [independent implementation review](CODE_REVIEW.md).
- [Impact captures, regression limits and compatibility receipts](impact/IMPACT_REVIEW.md).
- [Action proof, actual logs and rendered screenshots](action/README.md).
- Decisions: [ADR-0125](../../adr/0125-reviewed-snack-concepts-and-biscuit-cues.md),
  [ADR-0126](../../adr/0126-reconcile-uncertain-contexto-actions.md).

## Remaining release limits

Retiring the Pâine projections has a real cost: Brioșă→Pâine changes from rank 2/hot
to 424/cold, while Chec→Pâine becomes 193/lukewarm. Their former false Zacuscă
affinities cool. Correct native ownership does not establish good feedback for every
other hidden target. Eight old-native warm→lukewarm movements retain identical
distances (for example Zahăr→Înghețată 66→71); rank boundaries move with the graph.
The 6,941 changed old-target observations are not all improvements.

Some broad Prăjitură cues, optional butter/dairy ingredients, reciprocal Pișcot→Biscuit
and indirect Sarmale/oven/yeast associations remain noisy. This wave does not claim a
comprehensive semantic-distance solution, new Lanț/Alchimie/Conexiuni rounds or derived
catalog expansion. No human enjoyment, real-device acceptance or production smoke ran.
The [anonymous beta gates](../../BETA_CANDIDATE.md) still require player/device evidence,
operator/contact verification and an authorized rollout. Production remains documented V72.
Current state and exact artifact pins: [STATUS](../../STATUS.md).
