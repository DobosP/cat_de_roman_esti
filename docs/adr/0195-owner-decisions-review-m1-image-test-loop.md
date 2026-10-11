# ADR-0195 — Owner decisions 2026-10-11, M1 app image and test-loop speedups

Date: 2026-10-11
Status: Accepted for source on `fix/gui-review-20261011`; trust pin and full NOT RUN.

## Owner decisions (verbatim)

On 2026-10-11 (~20:24 UTC) Paul answered a structured question set. Provenance:
owner answer in Claude Code independent-review session (no signature implied).
Core records them as PROGRAM erratum E5 (roedu-ui ADR-0019).

Questions and answers as recorded in the review session (Cat effect after each):

- Q1 "Kit-update deadlock: KIT_BUMP needs a fully green same-SHA unit, which
  includes the 40,960-byte route-JS budget that only the Preact replacement can
  meet, while the replacement needs the kit first." → "Budget-only-red OK": apply
  the existing E3 rule to kit updates: a same-SHA unit whose only substantive
  failure is the recorded active route-JS budget (plus the aggregate exit) is
  sufficient for KIT_BUMP; every other check must pass; M2 acceptance still needs
  a genuinely green budget. Unblocks the pending core-v1.6 staged bump now and
  also covers the later M2 UI-activation sync. Cat: the `@roedu/ui` pointer moves
  only through the parent's protected `kit:sync` (S1 M2 step 2 corrected).
- Q2 "Teacher/Social prep slices run while the plan says Cat alone until M2
  green." → "Authorise prep": Teacher/Social may run original-oracle and pre-M0
  preparation slices on their feature branches in parallel with Cat — no landing,
  no kit sync, no formal S2A/S3A milestone claims, never during a timed Cat
  (LCP/INP) run.
- Q3 "Cat gate-hook changes" → APPROVED: "Fail fast" (cheap doc/inventory/content
  checks before the backend race; stop the full when they fail) and "Fresh content
  tests" (-count=1 for content packages; Go's test cache does not recheck
  out-of-module inputs). NOT approved: "Exclusive timed runs".
- Q4 "Cat gate qualifies Dockerfile.gui but compose/prod/anon/CI build
  Dockerfile" → "Follow the plan": S1 M1 step 3 — make the canonical Dockerfile
  distroless and point the gate at it (GATE-CHANGE: cat M1 app image);
  port/healthcheck changes recorded in the M1 ADR; one trust pin (Paul runs it,
  never an agent). Cat: this ADR records the image contract below.

On 2026-10-11 (~21:35 UTC) Paul answered a follow-up in the same session.
Provenance: owner answer in Claude Code independent-review session (no
signature implied).

- Q5 Port → "PORT in Go, default 8000": add `PORT` handling in cat-server and
  the healthcheck, then revert the compose/Caddy/CI/run.sh port edits.

Still open: PROGRAM §4.7 "sets budgets.json defaults" vs E3 "Preserve
budgets.json unchanged" (ruled at the device checkpoint); the physical Samsung
Chrome + Samsung Internet throttled-4G checkpoint remains UNMET.

## Gate hook (Q3, commit 8e56bae)

`cat-doc-check`, `cat-content-validate`, `cat-content-export` and `cat-docs-gate`
run right after the doccheck source preflight; if they or
`cat-doccheck-source-contracts` fail, unit returns before the race and full stops
before binaries/PG/parity/legacy/browser. Build, route budgets and frontend
unit/lint/types still always run; no check is removed or renamed. The go-backend
race adds `-count=1` (ten previously cached packages: 10.16 s fresh vs 0.16 s
cached); `-timeout=30m`, skip allowlist and authcore race are unchanged.

## M1 app image contract (Q4 commit 83ed8b9; Q5 port commits a5d24f0, 11a6825)

- `.gate.env` `APP_DOCKERFILE=Dockerfile`; `Dockerfile` is the formerly qualified
  distroless recipe (same digest-pinned bases, identity bake, asset sync, export
  check). `Dockerfile.gui` is deleted; its ignore file is `Dockerfile.dockerignore`.
- Port (Q5): `PORT` is read in Go. Without an explicit `-listen`, `/app` binds
  `:$PORT`; `PORT` unset or empty means 8000, otherwise ASCII decimal 1–65535,
  anything else exits non-zero naming `PORT`. An explicit `-listen` wins and does
  not consult `PORT`. The image has no `CMD`; `EXPOSE 8000`. Container default
  stays 8000 (Compose `PORT: "8000"`, Caddy `app:8000`, host
  `127.0.0.1:${PORT:-8000}`); `compose.gate.yml` (unchanged) sets `PORT=8080`,
  so the gate app listens and is probed on 8080. The native default moved from
  `127.0.0.1:8081` to `:$PORT`; in-repo native callers pass `-listen` or
  `-replay`.
- Entrypoint `/usr/local/bin/cat-server` → `/app`; prod/accounts compose
  `command` is `["-migrate"]` (no port); healthcheck `curl /api/health` →
  `/app healthcheck` (probes `http://127.0.0.1:$PORT/healthz`, same `PORT`
  rule). No shell, curl or Python in the image.
- User stays `10001:10001` (CI asserts it); `/data/submissions` 10001 mode 700.
- `run.sh` is byte-identical to e042587 (S1 §5.5 must-not-touch; 0f51b96
  reverted). CI keeps port 8000; its only remaining change is the no-shell
  Python check (`docker export` + `tar` listing), required because the approved
  distroless image (Q4) has no shell. This conflicts with PROGRAM:644 ("cat's
  existing GitHub workflow is not edited by S1") and is recorded here as an
  owner-accepted consequence of Q4.

## Test-loop speedups (no behaviour change)

Measured with `GOMAXPROCS=2 -race -count=1`, host load 28–42 on 32 CPUs, before
= `git archive e042587` run concurrently; after = perf commits (verifier rerun).

- httpgolden indexes reviewed corpus sources once per process: package
  884.0 s → 114.8 s (96.1 s); V1.8 refusal test 331.7 s → 5.4 s (6.4 s).
- contentrails builds the installed-authority fixture once per process: six
  fixture tests 746.6 s → 389.9 s (362.3 s). Whole package after: 1352.3 s, no
  same-host before; the e042587 full measured 1384.7 s of the 1800 s limit.
- The quick-audit catalog hoist was reverted: `quick.go` is an ADR-0189 auditor
  file whose digest the installed rails pin; it needs an owner re-audit/re-sign.
- aac8eff (review host): three world-audit rail tests 444 s → 236 s; `state()`
  CPU 151.8 s → 34.1 s. A new oracle test compares it with the pre-aac8eff loop
  on 3000 random worlds and bundled replays.

## Qualification boundary

Paul's trust pin for `.gate.env`, then a managed unit/full on this branch, are
NOT RUN. Hook and asset byte changes rebind receipts on the next run. Active
route-JS limits, frozen baselines and every privacy/content/CSP/a11y gate are
unchanged; this is not GREEN, M1, KIT_BUMP or device evidence.
