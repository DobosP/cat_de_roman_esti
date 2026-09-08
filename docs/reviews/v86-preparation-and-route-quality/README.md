# V86 — preparation, route and replay quality

Valid until: the reviewed content, source or validation bindings change — then treat as history.

Verified against local main `14e8895a220d4c78ba34c2b3772f397064cca5b0`, which includes
landed V85 `317ae7d`. V86 is on `feat/v86-preparation-and-route-quality`.
Full integration is green, verified 2026-09-08; the candidate is ready for its next landing.
No push or deployment.

## Delivered player outcomes

All six games keep new-game failure feedback beside the action that can retry. Selected
options, previous progress/results and local scores survive failed replacement. Intros and
existing rounds remain mounted during creation, with synchronous flight guards and disabled
controls. Completed replay notices share ResultCard; Alchimie's live “Alt joc” footer has the
same behavior. Reserved responsive space prevents a new error from pushing retry offscreen.
Saved-game recovery remains separate. See [ADR-0124](../../adr/0124-persist-new-game-creation-failures.md).

Lanț preserves up to two available shortest continuations within the existing three corridor
slots, retaining a third exploratory slot, safe detours and the six-choice cap. Among the
96 old approved rounds, 59 menus change: summed visible shortest first hops rise 107→198,
starts showing none fall 32→0, and all 96 show at least two. No previously visible shortest
option disappears. The new round also shows both alternatives. Typed moves, graph direction,
optimal distances, score and private route metadata stay unchanged; see
[ADR-0122](../../adr/0122-visible-alternative-routes-in-lant.md).

Nine preparation concepts and specific directed relations improve ordinary ingredient and
cooling guesses. Congelator receives a native identity distinct from Frigider. Two reviewed
exact-target feedback pairs repair natural reverse pastry/filling guesses without reversing
Lanț edges or turning a related guess into a win. See
[ADR-0123](../../adr/0123-reviewed-preparation-and-cooling-concepts.md).

## Content quantities

| Measure | V86 change | Final stock |
|---|---:|---:|
| Native concepts | +9 | 2,397 |
| Accepted forms | +30 | 8,572 |
| Graph connections / newly legal directions | +41 / +41 | 9,360 connections |
| Removed or corrected old edges | 0 | 9,319 old edges exact |
| Approved playable rounds | +6 | 641 approved / 8 pending |
| Cald sau Rece eligible rounds | +5 | 229 |
| Lanț eligible rounds | +1 | 97 |
| Conexiuni, Alchimie and derived boards | no new rounds | existing stocks retained |
| Legacy puzzles | unchanged | 180 |

The nine concepts are Frișcă, Albuș, Gălbenuș, Zahăr pudră, Lapte praf, Amidon alimentar,
Cremă de vanilie, Congelator and Mixer de bucătărie. The 30 forms are grammatical or qualified
accepted variants; no separate synonym count is claimed. Existing owners and forms remain
exact. Only 21 old node degree fields change; all old edges and puzzles remain exact.

Five new Contexto rounds are Brânză (`ct_gastronomie_341`), Lapte (`342`), Savarină (`343`),
Frișcă (`344`) and Cremă de vanilie (`345`). Lanț adds Frigider→Înghețată
(`lt_gastronomie_222`) through Frișcă or Congelator. All six have complete raw screens and
separate dossier-bound promotion judgments: zero FAIL and two explicitly justified familiarity
warnings, without altering source salience. The eight historical pending holds remain.

All 643 old source records, all 336 derived rows, 82 old Alchimie projections and 99 old Lanț
profiles remain exact. Six ranking rows are added and 263 old ranking rows change; ranking
movement is distinct from authored stock. The 468 retained projection rows, 71 legacy proxies
and four prior native-audit tuples stay exact. The freezer domain retains 18 synthetic rows;
no vocabulary-floor change is needed. Bare mixer retains its previous projected identity.

## Measured feedback

| Guess → target | Before | V86 |
|---|---|---|
| Congelator → Înghețată | 197 / lukewarm, refrigerator projection | 3 / hot, native freezer |
| Frigider → Înghețată | 197 / lukewarm | 30 / warm |
| Frișcă → Ecler | fuzzy confirmation requested | 5 / hot, exact native input |
| Frișcă → Savarină | fuzzy confirmation requested | 5 / hot, exact native input |
| Ecler → Cremă de vanilie | 322 / cold after graph addition | 2 / hot, nonwinning |
| Savarină → Frișcă | 140 / lukewarm after graph addition | 2 / hot, nonwinning |

The two cream targets are new: their “before” values describe the initial V86 graph before
its reviewed feedback correction, not V85 playable rounds. The two exact pairs do not change
other target scopes. Qualified ingredient/tool meanings remain distinct; suitable sweet cream,
recipe variants and refrigerator/freezer compartments are described explicitly.

The independent old-target comparison covers 9,120 first guesses per checkout: 40 words over
228 approved records representing 225 distinct targets. Of these observations, 5,175 differ;
these include new identities, reachability and ranking changes, not 5,175 proven quality fixes.
All 41 new directed one-move journeys pass. The pure Lanț-policy comparison and final graph
comparison are archived separately; pending boards are excluded from served-menu claims.

## Verification and initial findings

| Check | Result |
|---|---|
| Python 3.12.3 backend | 1,353 passed in 666.27s |
| Python 3.14.4 backend | 1,353 passed in 515.00s |
| Isolated accounts | 53 passed on each Python version |
| Preparation/feedback/public journeys | 45 passed |
| Lanț policy and existing behavior | 65 passed |
| Current/historical compatibility | 128 passed |
| Fixture, pack, pending gate and Ruff | passed |
| Frontend native | 177 passed |
| Desktop/mobile browser matrix | 148 passed in 8.6m |
| Lint/typecheck/build/bundle/docs/whitespace | passed; 118.87/120 KiB |

No backend failures, skips or retries occurred in either full matrix. The graph applied through
the rollback-protected transaction, then six candidates were imported pending and promoted
through the existing independent-review serializer/applier. Generated mirrors and the trusted
catalog pin were refreshed together. Seed-38 snapshots reflect reachability 2,312→2,321 and
the intended Lanț selected-round change.

Focused browser work found real issues in the initial implementation: header-only errors could
be offscreen after long results; a failed first creation could remount/scroll the Lanț intro;
and inserting error text could push replay below a short viewport. Placement, retained DOM
and reserved message space repair these cases. Two setup assumptions confused sticky/partially
visible rules with short content and were corrected without relaxing notice/button viewport
checks. The full native gate also exposed four assertions tied to older loading flag/source
shapes; their original guard requirements are retained while checking the stronger guards.
Actual initial and final outcomes remain in the verification archive.

## Limits and evidence

Oven/yeast feedback remains too warm for some non-baked desserts; several butter/dairy guesses
and Sarmale associations remain noisy. Bare `rece`, `gheață`, `gelatină`, `praf de copt`,
`cremă` and `amidon` are not newly accepted. Biscuit was deferred because defining ingredient
and dessert guesses remain weak. Other investigated routes with plausible missing direct
associations were deferred. Colloquial “frigider” can mean the whole fridge-freezer appliance;
the new Lanț round counts its visible authored preparation/storage relations, not a universal
claim that a refrigerator appliance cannot contain ice cream. Human comprehension, fairness,
enjoyment and real-device acceptance remain unmeasured.

- [Independent graph review](GRAPH_REVIEW.md) and [exact candidates/sources](graph-candidates.json).
- [Raw factual screen](gastronomie/CANDIDATE_FACTS.md), [raw quality screen](gastronomie/QUALITY_SCREEN.md),
  [analyst judgments](analyst-review.json) and [bound independent verifier](VERIFIER_REVIEW.md).
- [Two feedback-pair judgments](feedback-pair-review.json), [before](feedback-pair-before.json)
  and [after evidence](feedback-pair-after.json).
- [Lanț policy evidence](lant/README.md), [full six-game impact](impact/IMPACT_REVIEW.md),
  [content delta](content-delta.json) and [exact inverse receipt](artifact-delta.json).
- [Independent source review](CODE_REVIEW.md), [UI review/screenshots](ui/README.md),
  [actual final gate receipts](verification.json) and [final file bindings](review-manifest.json).
  Current rollout gates remain in
  [STATUS](../../STATUS.md) and [BETA_CANDIDATE](../../BETA_CANDIDATE.md).
