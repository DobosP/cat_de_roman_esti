Valid until: V1.8 lands or the owner closes the wave — then treat as history.

V1.8 everyday-core follows docs/CONTENT_LOOP.md at procedure revision 2eb73d1.
Step 0 began on 2026-10-10 at wave_base 2eb73d18f040c40bf06774bfb0d198fe2da6c909.
The branch is content/v1-8-everyday-core.
The planned batch is 40–60 everyday concepts and missing input families from the procedure backlog.
No candidate research or content installation occurred in this baseline tick.
Accepted 0; installed 0; cat-content-ops delta reports 0 concepts, 0 connections and 0 forms.

Baseline
Go reports go1.27.1 with PATH=/usr/local/go/bin:$PATH and GOTOOLCHAIN=local.
go -C go-backend run ./cmd/cat-content validate --root .. passed: Native sources GREEN.
go -C go-backend run ./cmd/cat-content export --root .. --check passed: Native private content current.
go -C go-backend run ./cmd/cat-content-ops check --root .. --check passed: 2419 nodes, 9473 links, 180 puzzles and 716 pack boards.
BLOCKED: go -C go-backend run ./cmd/cat-content-rail all --root .. --check -> cat-content-rail: final live audit incomplete/stale/unaccepted.
The literal 7272424 remains in go-backend/internal/contentbuild/source6_build_test.go:19.
go -C go-backend test ./internal/contentrails/ ./internal/contentbuild/ ./internal/httpgolden/ exited 1: contentbuild and httpgolden passed.
BLOCKED: go -C go-backend test ./internal/contentrails/ -> rail_test.go:48: final live audit incomplete/stale/unaccepted (TestAllFourBaselineArtifactsRebuiltFromAuthoredInputsExactBytes).
The rail result was checked on main at wave_base; the unchanged worktree shares that commit.
Install is disabled; steps 1–3 continue as research-only, with waiting null until the step-3 table.
The fixed independent reviewers are factual-v1-8 and quality-v1-8; neither authors items.
Previous-wave pool states and reasons were read without resuming V1.7.
Documentation and whitespace gates passed; docs/STATUS.md remains at 120 lines.

Owner decisions
The owner requires one sub-step per tick, a commit for changed files, and a state.json update.
LANDING_MODE=local: merge to local main only after the procedure's green gates; never push.
V1.7 remains parked. CONTENT_LOOP.md and ADR-0188 remain unchanged.
No GUI, runtime, tooling, CI, deployment, PostgreSQL or retention-policy work is authorized.
