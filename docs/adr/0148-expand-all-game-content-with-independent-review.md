# ADR-0148: Expand all game content with independent review

- Status: accepted
- Date: 2026-09-14
- Partially supersedes: [ADR-0052](0052-derived-beginner-games.md) and
  [ADR-0054](0054-refine-derived-pilot-before-expansion.md), for the requirement that
  Intrusul and Perechi draw exclusively from the frozen V38 source collection.

## Authority and outcome

The owner requested the same content expansion for all games, with quality preserved.
This continues V92 from `75584bf`. Alchimie's recently reviewed 221-concept, 285-recipe
world remains exact. The other five games gain **70 rounds or targets**:

| Game | Added | Resulting total | Eligible or preferred |
|---|---:|---:|---:|
| Conexiuni | 4 | 238 | 80 |
| Cald sau Rece | 8 | 252 | 246 |
| Lanțul Cuvintelor | 13 | 113 | 110 |
| Intrusul | 25 | 208 | 169 |
| Perechi | 20 | 173 | 133 |

These are new playable combinations of existing graph concepts. The KG, mobile pack,
Alchimie content, all 661 previous four-game pack records and all 336 original quick-game
board records remain unchanged. The 25 new pack records pass pending import, fresh
dossiers, independent analyst/verifier decisions and promotion; all are ranking eligible.
Existing eight pending records retain their status. Publication and deployment remain
outside this local task.

## Quality before volume

There is no per-game quota. Twelve of 37 proposed pack additions were excluded: eight
Contexto targets with factual or feedback-neighborhood weaknesses, three Lanț routes
with weak associations or an A5 dependency, and one generic Conexiuni duration-unit board.
The accepted Contexto targets include everyday objects and ingredients, plus familiar
actors with usable checked neighborhoods. Conexiuni predicates use precise Romanian
wording; Lanț routes retain alternative paths and pass the existing branching gates.

Intrusul adds everyday objects, nature and food categories. Perechi adds twenty mixed
association boards in `viata_de_roman`, using practical vocabulary and Romanian culture.
Each new board has an authored predicate, source references and distinct factual/quality
judgments. Novelty checks exclude reused visible boards and existing Intrusul trios.
The supplement introduces 92 concepts previously unseen in Intrusul and 130 previously
unseen in Perechi; 73 of its 80 intended pairs are new to that game. These counts describe
exposure inside each game, not new global concepts. No pair repeats within the supplement.

## Bounded authored quick-game supplement

Preserve the complete V38 board collection and score fields. Add a separately generated,
digest-pinned `quick_games_v92.json` with 45 reviewed boards. The served catalog joins both
collections; the legacy loader still returns only V38 for historical validation. Existing
selection, source balancing, starter progression, hint, repeat and scoring rules remain.
Starter shelves grow from 24/26 to 43/42. Added boards all meet the preferred score floor.
Rank fields are calculated within the supplement and remain private audit fields; runtime
selection uses the established score bands, never ordinal ranks.

The new generator accepts at most 256 authored boards in a 2 MiB catalog, with at most
three variants per source family. It enforces the original graph-strength, ambiguity,
node-type and familiarity rules and recomputes the original V38 scores. Graph evidence
alone cannot establish a human predicate, so complete factual and quality reviews are
required for the exact candidate before building a proposal. Their accepted intersection
determines the proposal; rejected content is excluded, never silently promoted.

The artifact binds the exact KG, critique rubric, current pack, frozen core payload and
core artifact. Full node snapshots preserve provenance. Runtime rechecks these bindings,
snapshots, structural gates, ratings and artifact digest, failing closed on drift. A
future bound-artifact change therefore requires an explicit rebuild and fresh final
review even when it leaves the supplement's authored rows intact.

Package write is atomic and requires a saved byte-identical proposal, a live API audit
and two final judgments from the original independent reviewers. The audit binds the
candidate, proposal, live artifacts and eight relevant runtime/generator source files.
Changed code, stale evidence, incomplete coverage or a missing review blocks the write.
Session bounds and public API shapes remain unchanged; unearned answers and private
source/catalog identifiers stay server-controlled.

## Direction-independent Lanț explanations

Review found that graph labels such as `se varsă în` can become false when displayed for
the reverse traversal of a bidirectional link. Lanț now displays short neutral noun
phrases describing the pair: `mare și deltă`, `fluviu și deltă`, `autor și operă`, and
other reviewed captions. Sixty-eight exact edge snapshots cover the representative
paths of the thirteen additions. Their captions work in either supported direction.

Unmapped or changed edges receive a neutral relation-type caption, sometimes the less
specific `legătură directă`. This avoids presenting a reversed directional claim; richer
wording for more existing edges remains editorial work. Graph edges, original labels,
weights, routes, move costs and scoring remain unchanged. Choices, earned hints, moves
and resumed paths share the same caption function. New Lanț dossiers contain actual
display captions and the caption-module digest, so subsequent display changes invalidate
the review binding.

## Verification and limits

Independent reviewers replayed every new quick-game board through natural category/seed
selection and the APIs. Additional replays cover wrong attempts, free repeats, earned
hints, hidden answers and persistent terminal scores. Lanț review exercised every new
route and representative alternatives, including forward/reverse caption behavior.
Historical tests reconstruct the exact predecessor artifacts before running earlier
wave assertions; their historical hashes are not replaced with the new content hashes.

The content-delta tool includes the authored supplement alongside the frozen quick-game
catalog, so reporting cannot silently omit these additions. Exact candidates, exclusions,
reviews and final integration results live in the
[review record](../reviews/v92-all-games-content/README.md) and [STATUS](../STATUS.md).
Automated correctness and editorial review do not establish measured enjoyment. Human
playtesting, physical-device acceptance and broader shared-KG factual cleanup remain open.
