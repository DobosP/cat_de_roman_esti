# ADR-0203: mechanical score module boundaries

Status: Accepted — source architecture only; migration qualification remains pending.
Date: 2026-10-18

## Context

Every game currently loads Home-only history import/export and daily-circuit
presentation code through the monolithic score store. The S1 plan froze that
store and its synchronization helper during the framework migration.

Paul explicitly approved the prepared behavior-preserving split: “Allow the
behavior-preserving module split”. This overrides only the `scores.ts` and
`scoreSync` source freeze for mechanical relocation and import narrowing.

## Decision

Keep `scores.ts` as the complete public compatibility facade. Production
consumers import the required core, record, read, daily and history modules.
Preserve all42 original function bodies, public exports, constants, storage
formats/keys, receipt locking/timing, bounds and existing test assertions.
The synchronization helper changes imports only. Other S1 freezes remain.

The five existing score suites keep their facade entry and assertion bodies;
their loader compiles the local module graph with shared module identity.
No budget, content, account policy or acceptance requirement is waived.

## Consequences

Bundle savings require actual complete-route measurements. Existing score,
receipt/concurrency, history and daily tests plus types/lint must pass. Clean
unit/full and independent review still precede M3/M4 acceptance and local landing.
The prior reviewed source packet and all failed diagnostic evidence are retained.
