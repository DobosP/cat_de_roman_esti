# V91 — recovery, mobile clarity and existing-content quality

Valid until: final V91 review supersedes this kickoff — then treat as history.

Baseline: local main `e2e03638b90fc9248c33f70eedaa8c9c5fbd87ad`, which records landed
V90 `13a78fd` (implementation `0039b1e`) and the owner's final stopping point.
Branch: `feat/v91-recovery-and-mobile-clarity`.
**Complete and land V91, then stop. Do not start V92.** Automatic recurrence is paused;
this work continues under the direct request and [ADR-0137](../../adr/0137-finish-v91-and-stop-iteration-loop.md).
No V91 implementation or content revision is claimed by this kickoff.

## Outcomes to pursue

1. Reproduce remaining Intrusul/Perechi uncertainty and ownership risks in real browser/BFF
   journeys. Both already attempt one recovery GET and have a synchronous mutation lock;
   inspect successful and failed reads, stale successful POSTs, another saved round,
   unmount, terminal scores and owned404 cleanup. Introduce the reviewed owner pattern
   only where actual evidence supports a defect; never replay mutations automatically.
2. Improve shared mobile HUD and resume-notice clarity across all six games. Existing
   screenshots show a top toast covering Exit/title/status, while status badges scroll
   horizontally with a hidden scrollbar. Keep the current visual language, readable
   controls and keyboard access. Verify real320/390/desktop layouts and visible feedback;
   moving an obstruction somewhere else is not sufficient.
3. Review existing easy-content quality before adding another noun batch. Start with
   al_sport_083: Washington Bullets is a recognition concern, and Medalie, the2022swimming
   record and Bazin olimpic begin depleted in the current sparse projection. Review A1/E1
   and actual useful openings/goal inference; do not fabricate a correction or demotion.
   Prefer a concrete, source-checked improvement using familiar useful existing concepts.
   Four approved C3 warnings and17 unknown household surfaces remain a separately assessed
   backlog; neither a numeric floor nor a word quota establishes quality.

[The prior read-only scout](../v90-household-discovery-and-critique-gates/prospective-v91-scout.md)
binds source/screenshots and frames untested risks. Any content or graph change needs
exact independent factual/quality review, supported transactions and new bound judgments.
Keep approved-stock protections and all unaffected records; no automatic A5 resolution.

## Fresh baseline evidence

[kickoff-baseline.json](kickoff-baseline.json) binds12source/data files, the exact Sport
record/seeds, four thin approved targets and15 actual BFF requests over two fresh games.
[The runner](capture-kickoff.py.txt) deletes both sessions. In both games the paid clue
already survives GET, and a second hint POST returns400 while hints_used stays1.
These are cue-persistence/cap observations, not browser loss or ownership reproductions.
They do not establish a second charge or a missing backend clue field.

| Existing review target | Current incoming count |
|---|---:|
| Lacul Roșu030 |1|
| Peștera Scărișoara031 |2|
| Abdicarea Regelui Mihai309 |4|
| B.U.G. Mafia070 |4|

The first kickoff script finished its BFF assertions/cleanup, then failed while hashing
an incorrectly located hook path. Original script/log are preserved; the corrected run
completed exit0. This was a capture-path error, not a product failure.

V90 baseline inventory:2,416nodes/9,459edges/8,641stored forms/180CLI puzzles;
661pack records=653approved+8pending,491eligible. Contexto238eligible, Conexiuni76,
Lanț97, Alchimie80; derived183Intrusul/153Perechi, preferred144/113. Projection rows464,
26domains,71legacy proxies,11native exact pairs. All baseline hashes belong to STATUS.
V90 full gates passed1608backend tests per Python runtime,53accounts each,193native and
246browser checks; the incomplete earlier process is preserved as history, not a pass.

## Completion requirements

- Coordinate shared frontend/build ownership; keep one task worktree and a clean main.
- Preserve server authority, private answers,7200s slidingTTL,1000sessions/game,locks,
  64KiB requests and bounded histories. No backend schema expansion without observed need.
- Capture before/after evidence, independently review changes and report actual concepts,
  links, forms, synonyms, rounds and revisions without padding. Curated approval differs
  from graph-mined fallback; do not claim unapproved concepts can never be mined.
- Freeze code/data/tests before applicable complete backend/account/frontend/content gates.
  Keep original failures and exact histories; bind real receipts to final artifacts.
- Update STATUS/decisions in the same change, locally land only green V91, clean its
  verified-merged artifacts and stop. No V92, push, deployment, external contact or purchase.
