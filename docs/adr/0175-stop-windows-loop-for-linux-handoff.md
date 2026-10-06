# ADR-0175: Stop the Windows content loop for Linux handoff

Date: 2026-10-06
Status: partially superseded by ADR-0177 for the owner-renewed Linux loop; historical Windows stop remains — partially superseded by ADR-0176 for the finite CRLF source-transport check; Windows stop remains

## Decision

Paul directly stopped Windows content discovery and the recurring loops, requested reuse of
existing checkouts and asked for prepared source work to land locally and unfinished work to
be pushed to origin for Linux continuation. The coordinator paused the heartbeat and transferred
this one source-preparation landing/push operation to the existing Cat worker.

This supersedes ADR-0173/0174 only for the active Windows loop, new per-iteration workspaces
and their former no-push scope for this handoff. Preserve every prior branch/worktree/immutable
receipt; do not create another workspace or resume discovery. No deletion or force push is allowed.

## Consequences

Ordinary light source/docs/whitespace checks precede landing. The full prepared source chain
fails default whitespace on preserved i04 CRLF artifacts, so main stays unchanged and the source
chain plus handoff is preserved on the existing candidate branch for a non-force push. Historical
frozen bytes are not normalized and failing, missing or skipped checks are not called green.

V1.5 is still NOT_QUALIFIED. This source handoff is not runtime/gameplay/history/assembled
acceptance, a new release, deployment or native QUIET_WINDOW release. Linux continuation must
read the exact handoff, source packets and unresolved gates before making further changes.
