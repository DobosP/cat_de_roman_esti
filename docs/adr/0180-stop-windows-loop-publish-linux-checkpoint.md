# ADR-0180 — Stop the Windows loop and publish the Linux checkpoint

Date: 2026-10-07
Status: Superseded by ADR-0181 — historical human-requested stop and WIP feature publication

## Context

V1.6 remains partial and unmerged. Qualifying Linux-specific runners on Windows/WSL
under existing time/resource gates consumed the session. The human explicitly asked
to stop the loop, save the current state and push origin for continuation on Linux.

## Decision

Stop the original-chat version loop and pause its automation. Save all owned pending
V1.6 source, exact raw evidence and current status on `codex/content-v1-6`, then push
that feature branch to origin under the explicit human instruction. This permits a
WIP checkpoint before the incomplete native documentation and assembled gates; it
confers no version qualification, main landing or permission to advance to V1.7.
Keep shared main clean and retain unmerged/failed work and local scratch.

This supersedes ADR-0179 automatic continuation. Linux continuation must refresh the
actual host/toolchain/path/resource admission and finish the outstanding full native
and independent content gates. Existing failed outcomes are immutable history.
