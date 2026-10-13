# ADR-0200: Bound Cat gate evidence reuse

Date: 2026-10-13
Status: Proposed; qualification pending
Authority: [ADR-0199](0199-owner-no-device-checkpoint-agent-lands-m3-m4.md), PROGRAM E10

## Context

The accepted M2 full repeated the unit's backend race for 17.2 minutes. Browser
cases used two workers despite the wrapper's four-worker cap. Backend tests also
read documentation, content manifests and frontend release/fixture inputs, so a
blanket exclusion of docs or frontend files cannot establish equivalent inputs.

## Decision

A clean full may reuse seven completed same-SHA unit lanes: frontend unit, lint
and types, plus backend/authcore race and vet. The exact result, execution,
wrapper/config/bootstrap bindings, commands and streams must verify against the
current source tree, toolchain, lock, CSP stage, configuration and resource limit.
Missing or invalid evidence executes the original commands. Build, managed asset
sync, identity, budgets, source checks and all full-only checks still execute.

For subsequent frontend changes, a single retained original whole-race proof may
authorize reuse only for Go packages independent of generated frontend embeds.
Every non-frontend source byte and executable mode, all docs, and the four known
frontend release/fixture inputs enter the input key. The actual race-enabled test
package graph determines the complete fresh/reused partition. Every package
depending on embedfs, including through external tests, reruns with `-race` and
`-count=1`. A changed key or graph executes the original whole race. No chain of
reused proofs becomes a new original authority.

Full browser workers use the committed GATE_PARALLEL_MAX cap and the wrapper's
effective GOMAXPROCS limit. Limits, assertions, retries and frozen artifacts remain
as established. Results distinguish retained evidence from newly executed tests.

## Consequences

Evidence is retained as one rolling original proof with exact logs. Fresh wrapper
runs have no cache and execute the original commands. Conservative package reruns
may prevent the desired five-minute unit target; only measured timings count.
Independent review and one clean unit/full qualification precede acceptance.

Implementation and validation: [ExecPlan](../execplans/gui-lighter-gates.md).
