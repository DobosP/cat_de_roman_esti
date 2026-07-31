# V46 Conexiuni pending-pool quality gate

_Reviewed and closed 2026-07-31. This report records the evidence for ADR-0070._

## Scope and release bar

V46 rebuilt exact dossiers for all 79 pending Conexiuni records against the V45 pack,
KG, current rubric, 75 owner-demoted boards, and 43 existing rejection tombstones. The
quota-free release bar required:

1. strict deterministic novelty, predicate, type, fairness, mirror, leakage, and
   red-herring checks against the complete inventory;
2. an adversarial gameplay analyst judging B1–B10, recognition, factual honesty, clue
   arc, and fun;
3. an independent inventory verifier checking full-board/group reuse, member pressure,
   rejected debt, and empty-shelf incentives;
4. exact-byte two-reviewer synthesis: two promotions are required to ship, either
   rejection rejects, and only a keep/promote disagreement may remain pending.

The V42 result was history, not authority. Its published outcomes cover only 77 rows
(1 promote / 34 reject / 42 keep), and its available bindings are stale. V43 compared
these records as novelty debt but did not individually re-gate them. V46 therefore reused
no old judgment.

## Deterministic census

The exact 79-ID set has SHA-256
`0bd5fd1667b33897aa0954c7155552ccfa84d0cfb0f2111d4fc1195dfa221593`.
All records pass the basic Conexiuni payload envelope, but the strict critique reports
438 FAIL findings across 76 records:

| Check | FAIL findings |
|---|---:|
| Duplicate exact/three-of-four groups | 214 |
| Projected member overuse | 67 |
| Eight-of-sixteen board reskin | 42 |
| Tile fairness | 41 |
| Mirrored groups | 38 |
| Label self-leakage | 25 |
| Red-herring budget | 7 |
| Board type shortcut | 3 |
| Vague predicate wording | 1 |

Seventy-four records have immutable current-record novelty debt through a duplicate
group, board reskin, or overused member. The two remaining deterministic rejects are
`cx_film_tv_168` and `cx_meme_net_202`, whose category buckets admit unfair crossfits.
No pending record can safely fill any of the ten empty eligible Conexiuni shelves.

## Human review of the lint-clean frontier

Only three records have no deterministic finding. Both reviewers still found no release
candidate:

| Board | Strict blocker |
|---|---|
| `cx_societate_294` | The eight family tiles support an equally valid female/male split in addition to parents-and-children versus extended family; the rest is flat taxonomy. |
| `cx_societate_295` | “Destinații cotidiene în oraș” also admits station/hub tiles, while transport and weather self-sort as worksheet categories. |
| `cx_viata_de_roman_293` | All four writing supplies also satisfy “În sala de clasă”; that group mixes room, furniture, object, and person roles. |

These boards use familiar words and make no doubtful external factual claim. Their defect
is the game: ambiguous partitions, leftover solving, and no satisfying difficulty arc.

The gameplay analyst rejected all 79. The inventory verifier rejected 38 and marked 41
as owner-boundary keeps because their overlap, alcohol, or profanity context warranted a
maximally cautious A5 reading. Under the existing conservative contract, the analyst's
rejection still resolves each of those disagreements to rejection. The final artifact is
therefore 79 rejects: 38 unanimous and 41 reject/keep disagreements, with zero promotions
and zero quota holds.

## Applied outcome

- **0 promoted and 0 kept pending.** No exact record met the release bar.
- **79 rejected and removed.** Conexiuni is now 232 approved records with no pending
  queue; the ID high-water mark remains 361.
- **Durable debt retained.** All 79 exact records were appended transactionally to the
  rejection ledger, which now contains 122 boards / 488 groups. One legacy named-group
  record exposed a fail-closed writer incompatibility; the writer now deterministically
  normalizes such keys to `g1`–`g4` while preserving the exact record digest, review
  binding, and member partition.

The original-game pack is now 645 records = 608 approved + 37 pending. Runtime eligibility
stays 447, including 74 Conexiuni boards, because V46 removed only dormant pending stock.
Rankings and derived metadata were regenerated. The frozen derived `boards` payload is
unchanged at 336 records (183 Intrusul / 153 Perechi), SHA-256
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
The KG, graph, frontend, hidden-answer boundary, scores, session TTL/caps, and deployment
are unchanged.

Machine evidence is `critique.json`, the 79 files under `dossiers/`, and
`conexiuni_verdicts.json`. The V46 regression contract cross-binds every removed record to
its dossier, verdict artifact, and durable tombstone so later authoring cannot recycle it.
