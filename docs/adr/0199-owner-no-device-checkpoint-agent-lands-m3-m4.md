# ADR-0199: No device checkpoint; M2 accepted; the agent lands M3 and M4; lighter gate cadence

Date: 2026-10-13
Status: accepted

## Decision

Paul (owner, Claude Code session 2026-10-13; programme erratum E10, roedu-ui ADR-0027) removes the physical
device checkpoint from the S1 plan: there is no phone measurement, no `DEVICE CHECKPOINT DONE` message and no
budgets-from-device receipt. `budgets.json` keeps the E7 defaults and the gate's emulated vitals (ADR-0190) are
the performance evidence. M2 is accepted on its landed gate evidence (`main` c9017b5b: unit 26/26, full 37/37)
and its two independent reviews. The orchestrating agent lands M3 and M4 on `main` itself (fast-forward after the
content-main merge) once the exact landed SHA has a green unit and full and an independent review. The full gate
runs once per milestone; iteration uses the cheap checks and unit; docs-only changes run the doc checks only.

## Context / why

The owner will not run phone tests and continues the migration from Codex. The M2 run measured a full at about
35 minutes (17 of them re-running the backend race suite the same SHA's unit had already passed) and a unit at
about 21 minutes (20 of them the backend race), so waiting for a full after every small fix stalled the work.

## Consequences

ADR-0198's acceptance conditions (a)/(b) no longer apply. S0b may start. The first follow-up is the lighter-gate
`GATE-CHANGE:` (full reuses the same-SHA unit lanes, browser workers follow `GATE_PARALLEL_MAX`, the backend race
is reused when its complete inputs are unchanged), qualified once. Pushing `main` to origin, production
activation and the go-live checklist stay Paul's.
