# ADR-0134: Reject numerically impossible Contexto neighborhoods before review

- Status: accepted
- Date: 2026-09-08
- Clarifies: [ADR-0071](0071-gate-contexto-by-feedback-legibility.md)

## Context

V89's final independent reviews rejected Făraș and Aspirator because each had only
three incoming KG neighbors. The initial author screen had counted a union of
incoming and outgoing links. That screen did not demonstrate the five recognizable
predecessors required by C3: an outgoing-only link cannot help a guess approach a
hidden target. The correction and rejected dossiers remain archived in
[V89](../reviews/v89-feedback-and-conexiuni-recovery/C3_REVIEW_CORRECTION.md).

The deterministic critique previously checked salience and regional associations
but omitted this necessary numeric condition. The V90 baseline has four approved
Contexto records below five incoming neighbors and two pending A5 holds above the
floor. A new approved-stock diagnostic must not silently change ranking scores,
selection weights, eligibility, or approved status.

## Decision

1. Add `contexto_incoming_floor` to deterministic critique. Count unique existing
   direct guess-to-target neighbors in the service's non-distractor directed graph,
   excluding the target itself. Bidirectional edges contribute both traversable
   directions; parallel edges contribute one predecessor. Missing nodes, self-links,
   distractors, outgoing-only links and projected guesses contribute none.
2. Fewer than five predecessors is `FAIL` for pending records and blocks strict
   critique and the promotion recheck. It is `WARN` for approved stock, producing a
   review proposal without an automatic demotion. Approved-stock changes remain a
   separate owner decision under rubric G4.
3. Reaching five passes only this numeric test. Recognition, semantic legibility,
   C1–C6, ordinary-player openers and A5 owner holds still need their existing review.
   Strength or salience cannot manufacture an extra predecessor; low-strength
   non-distractor links count numerically without receiving a quality endorsement.
4. Newly generated Contexto dossiers include `incoming_neighbor_floor`: minimum,
   exact count, a sorted sample of at most ten IDs and labels, truncation flag and
   `recognition_assessed: false`. Existing `incoming_degree`, strong-neighbor evidence,
   scoring formulas, ranking policy and runtime behavior stay intact.
5. Use the existing canonical binding version. The new evidence and revised rubric
   produce fresh current bindings. Embedded historical rubric digests and archived
   dossiers remain exact; old approvals cannot be relabeled as current reviews.
   Regenerate digest-bound ranking/derived metadata and supported default pins as
   part of V90 integration before the edited checkout serves games.

## Consequences

At the measured V90 baseline, Lacul Roșu (`ct_geografie_030`) has one predecessor,
Peștera Scărișoara (`ct_geografie_031`) has two, and Abdicarea Regelui Mihai
(`ct_istorie_309`) and B.U.G. Mafia (`ct_muzica_070`) each have four. Their new warnings
leave all 242 existing Contexto familiarity, play-quality, pilot-score and eligibility
profiles unchanged. They remain explicit review debt, not newly endorsed stock.

Pending Shitpost238 and Industrie257 have eight and thirteen incoming neighbors.
Both pass the new numeric floor while remaining pending under their prior A5 holds.
The eight-item pending rail requires no exception or weaker threshold. This change
adds a review safeguard; it adds no concept, edge, alias, projection or playable round.

Evidence and targeted verification are kept in the
[V90 critique record](../reviews/v90-household-discovery-and-critique-gates/critique/README.md).
