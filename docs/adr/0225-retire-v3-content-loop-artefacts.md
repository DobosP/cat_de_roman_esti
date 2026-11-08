# ADR-0225: Retire the V3 content-loop artefacts to the NAS

Date: 2026-11-09
Status: accepted (Paul, 2026-11-08: "Yes, archive and delete v3.").
Supersedes [ADR-0221](0221-consolidate-historical-stock-and-retire-checkouts.md) Decision 5 for the V3 loop artefacts.
Amends [ADR-0220](0220-continuous-codex-content-loop.md): the V3 loop is retired.
[CONTENT_LOOP.md](../CONTENT_LOOP.md) stays as the recorded procedure until a later decision replaces it.

## Context

V3 ran from 2026-10-26 to 2026-11-08. It landed 210 inflected inputs (batches n1, n2 and n4) on main 37207de2.
The bulk batch n5 qualified nothing and stopped. Its Codex automation `cat-content-v3` is paused.
ADR-0221 kept the live `content/continuous` checkout and all `_temp` loop evidence while the loop ran.
After the landing review, Paul asked for the V3 artefacts to be archived and deleted.

## Decision

1. The merged branch `content/continuous` (tip 3ca792da, an ancestor of main) and its clean worktree were salvaged.
   The salvage is a refs bundle plus a worktree salvage archive, at `branch-archive/2026-11-09/cat_de_roman_esti/` on the NAS (`dobostore`, `/volume1/agentops-home`).
   Both were deleted locally after byte verification (`ops cleanup`, agent-ops ADR-0105).
2. `~/work/_temp/content-loop/` (V1/V2/V3 loop history, controller, ledger, state, evidence, and a copy of the paused automation definition) was archived and deleted.
   So was `~/work/_temp/content-continuous/` (its gate mirror).
   They are at `temp-archive/2026-11-09/content-loop.tar.zst` (SHA-256 `b5c5a2b0bc671f6988c65ae8c8a12affebb9cfc9b18fb00bc2e41d25c27209c7`) and `temp-archive/2026-11-09/content-continuous.tar.zst` (SHA-256 `93f55722f7e2e7913cec2ecf11179e8adde3873eb9944716f1277ca27d8d1549`).
3. Paths in tracked records that cite `~/work/_temp/content-loop/...` now resolve inside that archive.
   Restore follows agent-ops `docs/36-fleet-cleanup.md` §5. Signed evidence is not rewritten.
4. Before deletion, a 40 MB seed set for the proposed next loop was copied with a SHA-256 list.
   It holds the miner helpers, owner-authority records, controller, ledger, state, intake, drawing board, landing queue and today's landing-review receipts.
   The copy is `~/work/_temp/adhoc-content-loop-v4-20261108/v3-seed/`. It is scratch, not a source of truth.
5. Removing the paused `cat-content-v3` automation in the Codex app is Paul's step.

## Consequences

No serving content, fixture, pin or gate changes. Running V3 again needs a restore from the NAS.
