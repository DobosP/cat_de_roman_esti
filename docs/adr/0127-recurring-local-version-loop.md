# ADR-0127: Continue verified local versions until the owner stops the loop

- Status: accepted
- Date: 2026-09-08

## Context

The owner requested landing V87, starting V88, and a loop that lands each completed
version and starts the next until explicitly stopped. Earlier versions required a
separate landing request. The existing release boundary remains local main (ADR-0004).

## Decision

Use a recurring task attached to the existing conversation to continue one active
version at a time. Each run inspects current main, STATUS and the active task worktree,
resumes unfinished work, and follows the latest owner instructions. A wake is not a
version deadline. Do not duplicate live work or create empty versions to show activity.

Retain ADR-0113's complete player outcomes, meaningful content batches and purposeful
refactors. Assess all six games; include new playable content where independent critique
supports it. Counts alone never justify a promotion, invented synonym or filler edge.

Before each local landing, require a committed, independently reviewed candidate with
current source/artifact bindings and all applicable integration checks green. Resolve
real failures and disclose initial test failures and semantic tradeoffs. Recheck main
and the candidate immediately before merging. Never land incomplete or red work.

After landing, record facts in STATUS and WORKLOG, clean up only the verified-merged
branch/worktree/scratch, then create and begin the next numbered version. Preserve
unfinished and unrelated work. Shared main stays clean; task work uses the existing
isolated worktree workflow. Machine-specific task/chat identifiers stay outside git.

The owner's stop/pause instruction takes precedence immediately: pause the recurring
task, stop issuing merges or new versions, and preserve unfinished work. Resume requires
an explicit owner instruction. Local continuation does not authorize pushes, remote PR
publication, deployment, accounts enablement, contacting people or buying usage. Those
remain separate owner decisions. A real external blocker is reported and preserved,
never bypassed to keep the loop moving.

## Verification and limits

V87's 167 file/deletion bindings and 16 original green gate receipts were rechecked
against `fa8cffd` before its local merge. The recurring task was created and confirmed
active; its native schedule and machine-specific state remain in the application.
The first V88 implementation and future unattended landings are not yet verified.
Automated critique and browser emulation do not establish human Romanian-player or
real-device acceptance. Public rollout remains gated by DEPLOY and BETA_CANDIDATE.
