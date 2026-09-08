# ADR-0137: Finish V91 and stop automatic iteration

- Status: accepted
- Date: 2026-09-08

## Decision

The owner ended the automatic version loop after V90, then explicitly extended the final
completion to V91. V90 is already landed. Finish the existing V91 task, perform its
independent reviews and required green integration checks, merge it into local main,
record the result and clean only verified-merged task artifacts. Stop there: do not
create or begin V92 without a new explicit owner request.

The recurring scheduler is paused so it cannot start further autonomous versions while
V91 completes under this direct request. Machine-specific scheduler details stay outside
the repository. Any queued earlier loop wake must respect this later owner instruction.

## Scope retained

V91 still follows the repository's worktree, content-review, bounded-session, anonymous
production, exact evidence and green local landing requirements. This does not authorize
pushing, deployment, accounts rollout, external contact, purchases or discarding unfinished
work. If V91 cannot pass its gates, preserve it and report the concrete blocker rather
than land incomplete work to satisfy the stopping point.

This supersedes [ADR-0127](0127-recurring-local-version-loop.md) for ongoing automatic
iteration authority. Its verification and local-only boundaries remain applicable to V91.
