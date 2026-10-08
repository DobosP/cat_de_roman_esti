# RO-EDU core monorepo

Last verified: 2026-10-08 — post-release documentation; qualification binds the source below.

@roedu/ui 1.0.2 retains the Preact 11 runtime with updated package metadata.
@roedu/web-kit 0.1.2 implements configured consumer version resolution.
The [ADR ledger](docs/adr/README.md) records architecture and policy.

## Current state

S0a UI/delivery and the core-v1.2 corrective release are qualified and published
at immutable source `9e0a88e33d44ba7ce9e84ead890c897b36d41dd4`.
Annotated tag object: `b5e1c817608e79411595da7f46618475e92acc13`.
Clean unit passed 28 checks plus only pg-live/no-dsn; worker full and independent
parent fresh full each passed 41 with zero skips/retries, 16 HTTP browser cases
executed once, six exact PNG comparisons and zero CSP/axe violations.
Two fresh builds and the owning-tag build each passed 5 checks; all seven outputs
were byte-identical, also matching ten actual clean/contaminated consumer packs.
The real five-file consumer bundle passed shipped parser/sync, genuine offline
npm lock generation/Go tidy, repeat byte/full-mode drift checks and extracted
Go vet/race qualification: 41 files, 11 packages, 66 tests, zero skips.
The [release evidence](docs/reviews/gui-core-v12/README.md) binds receipts,
archive hashes, executing images and the parent's preserved physical captures.
This is native Linux/local Chromium and disposable PostgreSQL qualification;
desktop browser measurements supply no physical Samsung or production proof.

Earlier core-v1.0 and core-v1.1 remain immutable. At 9acd440, v1.1 unit passed 27
plus permitted PG skip; full and parent fresh full passed 40/16 cases/six PNGs,
with zero CSP/axe violations or skips/retries. Its lab 432 ms LCP/40 ms INP and
compiler-cache correction retain their original scope in [WORKLOG](WORKLOG.md)
and [ADR-0008](docs/adr/0008-release-artifacts-exclude-compiler-state.md).

Linux implementation resumed on 2026-10-07 under the parent's recorded current
authority. The [Windows handover](docs/GUI_MIGRATION_HANDOFF.md) remains history.
Cat's original baseline, 16 fixtures/78 assertions and exact 30-file legacy freeze
retain their earlier accepted scope. The shared CORE_REQ3 correction in
[ADR-0010](docs/adr/0010-configured-consumer-version-resolution.md) is included in
core-v1.2; consumer adoption still uses the clean idle owner sequence.
Historical d0e6c7c passed unit28 plus the permitted PG skip and full41 with no
skips, six exact screenshots and independently checked185/231 bindings. Those
receipts do not qualify the recovered changed source.

The sealed Windows81 preparation is source-accepted and applied in the native
owning task worktree. [ADR-0012](docs/adr/0012-go-archive-budget-closure.md) records
the narrow budget Go archive closure and real parser/extracted-module regression.
[ADR-0013](docs/adr/0013-confined-declaration-preparation.md) records confined
pre-emission declaration regeneration, compatible with ADR-0008's postbuild stage.
Private bundle admission and Go planning preserve public exports and failure order;
their parity/refusal checks passed actual native qualification. The
[owning integration ExecPlan](docs/execplans/core-integration.md) records exact
selected-source provenance, current Linux checks and evidence retention.
Final clean unit verified 292 artifact hashes and 21 declaration safety cases;
each full verified 337 artifact hashes. The actual owning Git Go exports A/B
reproduced 41 files/55,202-byte TGZ, SHA256
`f499198a0b229b6b04488344724f5ba8873c6e1bd8da64096b76cc371f228bb4`.
Cat's original 114,086-byte gzip entry still exceeds 40,960; M0/M1 remain unqualified.
Its physical Samsung Chrome/Internet checkpoint remains UNMET. Active UI adoption,
production and S0b templ migration remain pending.
[ADR-0011](docs/adr/0011-original-runtime-budget-qualification-order.md) corrects
preliminary acceptance ordering while keeping the budget red, the real device
checkpoint and the green M2 requirement before S0b unchanged.

Paul accepted Cat's startup calculation on 2026-10-08: entry/static JS/CSS plus
immediately mounted AccountBar and its recursive static closure, counted once.
[Cat ADR-0185](../cat_de_roman_esti/docs/adr/0185-accepted-eager-startup-bundle-accounting.md)
records the source decision. At the Windows checkpoint, code/docs are unapplied
and unqualified; current Vite/startup gzip is unacquired and all 11 amended tests NOT RUN.
Frontend 120 KiB JS/CSS and canonical 40,960/30,720-byte JS remain distinct and unchanged.

The Cat-only sealed staged-UI contract and confined same-repo Go audits from
[ADR-0009](docs/adr/0009-corrective-release-and-staged-sdk.md) remain enforced.
Staged UI is pending; M2 requires actual active installation proof. Bootstrap
uses the bound current descriptor and host-private result checks. The
[core ExecPlan](docs/execplans/core-v1.md) preserves S0a history; the
[consumer resolver ExecPlan](docs/execplans/consumer-resolution.md) records the
current fix. [PROGRAM](docs/PROGRAM.md) retains the release and consumer gates.

## Source and interfaces

| Area | Path | Surface |
| --- | --- | --- |
| Tokens | src/tokens/ | DTCG input, generated CSS/app themes, TS and Go constants |
| Layered CSS | src/css/ | reset, tokens, base, components, utilities, app |
| Components | src/preact/ | CSP-safe and keyboard accessible Preact components |
| Behaviors | src/behaviors/ | light-DOM elements, invoker and island protocol |
| Motion | src/motion/ | Presence, springs, Confetti and mini playback controls |
| Network/storage | src/net/, src/storage/ | same-origin CSRF and registered keys |
| Go delivery | web-kit/ | assets, static, csp, island, health, golden, routes, engine |
| Sample | web-kit/sample/ | three stress modules, Pongo2 and compiled templ pages |
| Gate | scripts/gate.sh | pinned Linux execution and bound evidence |
| Templates | web-kit/templates/ | shared gate files, repo hooks and CI reference |

## Consumption

Consumers select only committed kit/CORE_TAG and adopt through the owner
staging/sync/trust sequence. The [consumer notes](CONSUMER_NOTES.md) list every
breaking API/style change and the exact kit protocol. Import components from
@roedu/ui/preact, CSS from @roedu/ui/styles.css and one generated theme.
Reading comfort requires a self-paced surface and rejects timed/psychometric use.
Preact island adapters render into a stable owned child, then dispose it on abort.

## Verification and documentation

Qualification and published UI1.0.2/web-kit0.1.2/Go archive identities bind exactly
the immutable 9e0a88e source, not this later documentation HEAD. README is packaged:
repacking changed metadata would change archive bytes; a subsequent product release
must bump affected package versions rather than replace these published archives.
Earlier post-tag documentation checks retain their recorded scope. This source-only
amendment has no executed checks. Full native captures remain
parent-owned outside this transient docs worktree; earlier receipts retain scope.

Every product build/test runs through the pinned native wrapper. Full adds real
PostgreSQL, an image-built app, all registered-page nonce checks, axe/vitals,
journeys and exact committed screenshot comparisons. Full permits no skips.
The [testing guide](docs/agent-testing.md) describes commands and evidence.
Requests and resolutions are append-only in [GATE_REQUESTS.md](GATE_REQUESTS.md).
Source maps: [agent map](docs/agent-map.md), [architecture](docs/architecture.md),
[theming](docs/theming.md), [tokens](docs/design-tokens.md),
[consumer guide](docs/consuming-web-react.md) and [LLM guides](docs/llm/README.md).
The original React 0.3.1 verification remains historical in [WORKLOG.md](WORKLOG.md).
