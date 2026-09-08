# V89 — feedback and Conexiuni recovery

Valid until: the final V89 review supersedes this kickoff — then treat as history.

Started 2026-09-08 from local main `b614bfe735a27b9703025420daf603118f6a7f74`,
which records landed V88 `000b0a2`. Branch: `feat/v89-feedback-and-conexiuni-recovery`.
**Phase: kickoff and measured baseline; no V89 implementation or promotion yet.**
The recurring local loop remains authorized by [ADR-0127](../../adr/0127-recurring-local-version-loop.md).

## Intended player outcomes

1. **Recover uncertain Conexiuni actions.** Its submit and clue handlers currently
   refresh only for HTTP 400/409. A lost committed 503/network reply can leave a stale
   board or clue state. GET already exposes earned groups/clues and terminal scores.
   Reproduce lost clue, solved group, final win/loss and failed GET in an actual browser,
   then reuse shared owned-action recovery. Never replay a mutation or spend another
   clue to discover what happened. Preserve mistake/repeat handling, private unsolved
   groups, saved-pointer ownership and score-once behavior; use neutral synchronization
   copy when GET cannot reconstruct the transient one-away verdict.
2. **Review a coherent household Contexto batch.** Reuse familiar existing words where
   the full rubric and actual proxy-aware journeys support them. Four candidates with
   at least five distinct direct neighbors are Făraș, Mop, Aspirator and Burete de vase;
   that numeric screen is not approval or proof of five good incoming cues. Review
   ordinary first guesses, warmer clues, repeat/resume/exact wins, recognition and sense
   boundaries before deciding. New nodes/links are justified only by real knowledge gaps.
3. **Repair bounded feedback weaknesses.** Start with the documented Tort Diplomat→Frișcă
   cost and unrelated Zacuscă control. Review each pastry/filling relation separately;
   keep correct sour/sweet/whipped cream ownership and nonwinning identities. Audit
   household-context costs without restoring broad Casa/Aspirator proxies indiscriminately.

## Fresh baseline

[kickoff-baseline.json](kickoff-baseline.json) binds the current source files and records
these eight actual technical profiles plus seven fresh private-BFF first guesses.
[capture-kickoff.py.txt](capture-kickoff.py.txt) reproduces them; every probe session was
removed afterward. All eight targets are currently unused as approved Contexto targets.
All have 2,343 reachable concepts and exceed the technical responsive floor, but that
alone does not establish C1–C6 quality.

| Candidate | Responsive guesses | Distinct direct neighbors | Initial disposition |
|---|---:|---:|---|
| Făraș | 250 | 5 | Review |
| Mop | 627 | 6 | Review |
| Aspirator | 358 | 5 | Review |
| Burete de vase | 332 | 5 | Review |
| Mătură | 81 | 4 | Hold for neighborhood/sense review |
| Găleată | 1,488 | 4 | Hold for neighborhood review |
| Detergent | 624 | 4 | Hold for neighborhood review |
| Taburet | 968 | 4 | Hold: poor ordinary cue and thin incoming neighborhood |

The direct-neighbor check narrowed the earlier technical shortlist. Do not promote a
four-neighbor item merely because its responsive count passes; any new relationship
must be true and useful without reference to the desired quota.

Actual nonwinning ranks: Făraș→Mătură 4, Podea→Mop 2, Mătură→Aspirator 4,
Apă→Găleată 2, Scaun→Taburet 2189, Tort Diplomat→Frișcă 345, Zacuscă→Frișcă 24.
The existing 71 scorer policies materially affect these outputs and remain part of the
baseline. The high Taburet responsiveness masks its failed obvious chair cue.

A preliminary in-process Conexiuni scout identified a repeat-clue defect on
`cx_arta_cultura_240` after three mistakes: retrying a lost first clue can consume clue
number two and reduce the eventual score by another 100 points. Archive the exact
reproducer and browser fault-injection evidence before implementation; the source
inspection/scout is not a completed V89 browser test.

## Completion requirements

- Pick and independently review a bounded content batch; report actual additions,
  removals, forms, lexical equivalents, promotions and per-game eligibility separately.
- Capture relevant before/after profiles before code or graph changes. Preserve old
  owners, valid directed links, reviewed ambiguity boundaries and accepted stock.
- Do not undo V88's truthful cream correction or bypass the critique rubric to revive
  its held Diplomat Alchimie candidate. The held Taburet target needs real repair/review.
- Keep deterministic server authority, unsolved-answer privacy, 7,200-second session TTL,
  1,000 sessions/game, locks and bounded requests/history. Preserve existing action and
  local-score ownership contracts in every consumer.
- Run focused checks during development, then independent review and all applicable
  final integration gates on frozen source/data. Treat interrupted runs as incomplete;
  preserve actual failures and never overlap mutating content transactions.
- Update STATUS, decisions and the final review before a green local merge, clean up only
  verified-merged work, and start the next version under the active loop.

No new round, graph word, source change or finished version is claimed by this kickoff.
Human/device acceptance and public rollout remain separate gates in
[BETA_CANDIDATE](../../BETA_CANDIDATE.md); current truth is [STATUS](../../STATUS.md).
