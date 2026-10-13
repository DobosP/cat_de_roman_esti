# ADR-0198: Owner lands M2 on main before the device checkpoint

Date: 2026-10-13
Status: accepted

## Decision

Paul (owner, Claude Code session 2026-10-12/13: "finish with M2, land it on main, and stop … I will add
my Samsung when you are done") lands the S1 M2 E7 integration on Cat's local `main` before the §4.7
device checkpoint. This is the recorded waiver of the landing hold in `.agent/S1.md` M1 step 7 and PROGRAM
E6 Q8 for M2 only; it is programme erratum E9 (roedu-ui ADR-0026). The landed source is the merge of the
E7 integration with content `main` ed9932fa after a green trust/unit/full on that exact merge and an
independent review. Perechi is part of the M2 ported set (ADR-0197 addendum).

## Context / why

The device checkpoint is a physical step only Paul can take, and he will take it after the port lands.
Keeping the migrated GUI on a feature branch while content work moved on `main` had already forced three
reconciliation merges (ADR-0194/0196), and the continuing work (M3) is planned from a Codex session on top
of the landed port.

## Consequences

`main` serves `/`, `/intrusul`, `/perechi` and `/conexiuni` from the Preact 11 / UI 1.0.9 bundle and every
other route from the frozen legacy bundle. M2 is landed, not accepted: acceptance still needs (a) `DEVICE
CHECKPOINT DONE <date> sha=<sha7>` and (b) Paul's `GATE-CHANGE: budgets from device checkpoint <date>`;
the receipt may measure the landed build and names the image it measured. S0b waits for acceptance.
Production stays anonymous and closed (DEPLOY.md go-live); pushing `main` to origin stays an explicit
request (ADR-0004). M3 may start on a feature branch before acceptance; landing M3/M4 returns to Paul.
