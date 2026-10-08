$ErrorActionPreference = 'Stop'
$packetRoot = 'C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$utf8 = [System.Text.UTF8Encoding]::new($false)
function Save-Lf([string]$relative, [string]$content) {
 $absolute = Join-Path $packetRoot $relative
 [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($absolute)) | Out-Null
 [System.IO.File]::WriteAllText($absolute,$content.Replace([string]([char]13)+[char]10,[string]([char]10)),$utf8)
}
function Replace-Once([string]$path,[string]$old,[string]$new) {
 $absolute = Join-Path $packetRoot ('after/'+$path)
 $content = [System.IO.File]::ReadAllText($absolute,$utf8)
 $position = $content.IndexOf($old,[System.StringComparison]::Ordinal)
 if ($position -lt 0 -or $content.IndexOf($old,$position+$old.Length,[System.StringComparison]::Ordinal) -ge 0) { throw ('Exact unique literal anchor missing: '+$path+' :: '+$old.Substring(0,[Math]::Min(80,$old.Length))) }
 Save-Lf ('after/'+$path) ($content.Substring(0,$position)+$new+$content.Substring($position+$old.Length))
}
Replace-Once 'docs/PROGRAM.md' '### 4.7 Device checkpoint (hard stop)' '**Cat startup accounting — accepted 2026-10-08, source amendment unapplied.** The frontend''s 120 KiB (122,880-byte) combined JS/CSS check counts all entry/static closures plus the immediately mounted AccountBar and its recursive static JS/CSS dependencies, with shared files and cycles counted once. Mandatory manifest roots/imports and emitted JS/CSS assets must exist; game routes and further dynamic children stay excluded. Default helper callers and frozen historical per-key closures retain their static-only scope. This does not replace the canonical cat-initial 40,960-byte JavaScript ceiling/30,720-byte target or separate CSS policy. Fresh startup measurements and Linux qualification remain pending; no threshold, phase or device condition changes.

Cat decision and pending application: [ADR-0185](adr/0185-accepted-eager-startup-bundle-accounting.md) and [S1 plan](execplans/s1-cat.md). Historical measurements retain their captured scopes.

### 4.7 Device checkpoint (hard stop)'
Replace-Once 'docs/adr/0020-bound-launch-runtime-and-first-load.md' 'Status: partially superseded by ADR-0184 for tooling/lint and generated-output handling; bounded session/input and120KiB acceptance remain' 'Status: partially superseded by ADR-0184 for tooling/lint and generated-output handling, and ADR-0185 for first-load JS/CSS accounting; bounded session/input limits and the 120 KiB default ceiling remain'
Replace-Once 'docs/adr/README.md' '- [0184](0184-native-spa-toolchain-and-managed-output.md) — native SPA tooling/managed-output prerequisites; runtime validation pending. ADR0183/Source7 preserved.' '- [0184](0184-native-spa-toolchain-and-managed-output.md) — native SPA tooling/managed-output prerequisites; runtime validation pending. ADR0183/Source7 preserved.

- [0185](0185-accepted-eager-startup-bundle-accounting.md) — owner-accepted AccountBar startup JS/CSS accounting; unchanged limits, source amendment unapplied and Linux qualification pending.'
Replace-Once 'docs/STATUS.md' '[Pickup](GUI_MIGRATION_HANDOFF.md).' '[Historical pickup](GUI_MIGRATION_HANDOFF.md); [current plan](execplans/s1-cat.md).'
Replace-Once 'docs/STATUS.md' '- **GUI checkpoint:** core1.2 released; native7/current+candidate andfocusedMotion14 PASS; exact15 accepted/unapplied; deps64ea PASS. Fullnormalized replay/Node3/lint/unit/CSP/device/KIT_BUMP pending. Linuxsupervisor/worker paused.' '- **GUI checkpoint:** core1.2 released; native7/current+candidate andfocusedMotion14 PASS; exact15 accepted/unapplied; deps64ea PASS. [ADR-0185](adr/0185-accepted-eager-startup-bundle-accounting.md): Paul accepted entry+mandatory AccountBar static JS/CSS startup accounting; separate2-path source UNAPPLIED/UNQUALIFIED,4 retained+7 new tests(11) NOT RUN; current startup gzip UNACQUIRED. Frontend120KiB/canonical JS40960/30720 unchanged. Fullnormalized replay/Node3/lint/unit/CSP/device/KIT_BUMP pending. Linuxsupervisor/worker paused.'
Replace-Once 'docs/STATUS.md' 'ADRs (newest 0183)' 'ADRs (newest [0185](adr/0185-accepted-eager-startup-bundle-accounting.md))'
Replace-Once 'README.md' '- Frontend: React 19.2 + Vite 8.1 + TypeScript, Node 24 — see [`frontend/README.md`](frontend/README.md).' '- Frontend: React 19.2.7 + Vite 8.3.3 + TypeScript 7.0.2; selected Node 26.10.0/npm 12.2.0 ([ADR-0184](docs/adr/0184-native-spa-toolchain-and-managed-output.md)). [Startup accounting](docs/adr/0185-accepted-eager-startup-bundle-accounting.md) is owner-accepted, source-unapplied and unqualified; see [`frontend/README.md`](frontend/README.md).'
Replace-Once 'README.md' 'The launcher builds Go with an incremental cache under `~/work/_temp/` and builds
React only when its compiled bundle is missing. Node 24 is needed for that frontend
build. `PORT=9000 ./run.sh` changes the listener; a busy port fails explicitly.' 'The retained launcher builds Go with an incremental cache under `~/work/_temp/`
and still checks the historical tracked SPA output. Its Node 24 messages and missing
managed-asset sync do not establish selected-toolchain qualification. Current managed
build/sync prerequisites follow [ADR-0184](docs/adr/0184-native-spa-toolchain-and-managed-output.md)
and [STATUS](docs/STATUS.md); their complete normalized qualification remains pending.
`PORT=9000 ./run.sh` changes the listener; a busy port fails explicitly.'
Replace-Once 'frontend/README.md' 'Text-only word-game arcade SPA: **React 19.2 + Vite 8.1 + TypeScript**' 'Text-only word-game arcade SPA: **React 19.2.7 + Vite 8.3.3 + TypeScript 7.0.2**'
Replace-Once 'frontend/README.md' 'npm install
npm run dev' 'npm ci
npm run dev'
Replace-Once 'frontend/README.md' 'npm run lint         # ESLint 10 flat-config checks
npm run typecheck    # tsc --noEmit
npm run build        # typecheck + Vite build + initial-transfer/font gates' 'npm run lint         # owning GUI gate: Oxlint/tsgolint + native/SDK AST contracts
npm run typecheck    # verified native TypeScript 7 --noEmit
npm run build        # native typecheck + Vite build + startup-transfer/font gates'
Replace-Once 'frontend/README.md' '`vite build` emits the static SPA into `../cat_de_roman_esti/web/static`
(`build.outDir`, `emptyOutDir: true`) — the tracked bundle served by the Go runtime.
The browser implementation remains React/TypeScript/JavaScript; the backend migration
does not convert that frontend to Go.
The post-build check follows recursive static imports in Vite''s manifest, enforces
the 120 KiB initial JS/CSS gzip ceiling, and verifies that only Latin + Latin
Extended Fredoka/Inter fonts shipped (ADR-0020). If the build is absent the native backend
serves a "run npm run build" placeholder instead of 500-ing.' 'The selected Node 26.10.0/npm 12.2.0 toolchain and managed-output prerequisites are
recorded in [ADR-0184](../docs/adr/0184-native-spa-toolchain-and-managed-output.md).
`vite build` emits `frontend/dist`; the owning asset sync copies the managed
output to `go-backend/embedfs/dist` before rebuilding the Go server. The original
tracked 30-file `web/static` bundle and legacy archive stay frozen. An absent
managed index returns HTTP 503; build alone does not update an existing server binary.
The lint entry point requires the owning Linux wrapper''s current context, selected
configuration and installed kit. Complete normalized validation remains pending.

[ADR-0185](../docs/adr/0185-accepted-eager-startup-bundle-accounting.md) records Paul''s accepted
startup calculation: all entry/static JS/CSS plus the immediately mounted
`src/components/AccountBar.tsx` root and its recursive static dependencies,
counted once across shared files/cycles. Missing mandatory roots/imports or emitted
assets refuse the check. Other dynamic game routes and further lazy children remain
excluded. `checkInitialBundle` always requires AccountBar after integration;
default `collectInitialBundleFiles(manifest)` callers and frozen historical
closures retain their static-only scope.

The separate two-path calculator amendment is source-accepted, **UNAPPLIED and
UNQUALIFIED**. Its four retained and seven new tests (11 total) are **NOT RUN**
under the amended source; current manifest/startup gzip measurements are unacquired.
The frontend default remains 120 KiB (122,880 bytes), summing each selected JS/CSS
file''s gzip level-9 size; existing limit configuration and Latin/Latin Extended
Fredoka/Inter subset checks remain. Fonts are checked separately from JS/CSS bytes.
The canonical 40,960-byte JS ceiling/30,720-byte target and separate CSS policy
remain independent requirements; no new total, savings or compliance is claimed.'
Replace-Once 'frontend/README.md' 'The canonical runner builds/starts Go. Python web dependencies available as `python3`
provide only offline fixture-answer helpers. Run:' 'The current runner starts an already-built Go server (`CDR_NATIVE_BINARY`, default
`build/cat-server`) and uses the native private `cat-browser-plan` helper.
Complete the owning managed-assets/server/planner prerequisites before these Linux
browser steps; Python helpers below are optional offline references:'
Replace-Once 'frontend/README.md' 'The runner starts its own native anonymous Go server on port 8138 (`CDR_E2E_PORT` overrides it). On the fleet host, put
the project `.venv/bin` and the Node 24 runtime first on `PATH`. Failure artifacts live' 'The runner starts its own native anonymous Go server on port 8138 (`CDR_E2E_PORT` overrides it).
Use the selected Node 26 toolchain and the owning built server/planner inputs. Failure artifacts live'
Replace-Once 'frontend/README.md' '- Tooling is pinned by the lockfile to ESLint 10.7 flat config, typescript-eslint
  8.63, and TypeScript 5.9; TypeScript 7 is not yet in typescript-eslint''s peer range.
- Per ADR-0020, frontend source changes include the matching tracked `web/static`
  bundle and `.vite/manifest.json`; backend-only changes leave that bundle alone.' '- Selected tooling and managed-output handling follow [ADR-0184](../docs/adr/0184-native-spa-toolchain-and-managed-output.md).
  Native TypeScript 7 owns diagnostics; the separately bound TypeScript 6 package is
  for required AST/transpilation APIs. Current normalized gate qualification is pending.
- Preserve the frozen original30 files/archive; managed output sync and reviewed source
  retirement follow ADR-0184. Historical reports keep their captured closure scopes;
  [ADR-0185](../docs/adr/0185-accepted-eager-startup-bundle-accounting.md) does not recompute them.'
Replace-Once 'docs/agent-testing.md' 'Last verified: 2026-10-04' 'Last verified: 2026-10-08 — documentation/source review only; amended runtime gates NOT RUN.'
Replace-Once 'docs/agent-testing.md' 'Go 1.27.1 serves the arcade, accounts/proposals and native content/tooling; Node 24 builds the SPA.' 'Go 1.27.1 serves the arcade, accounts/proposals and native content/tooling; selected Node 26.10.0/npm 12.2.0 SPA tooling follows [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md).'
Replace-Once 'docs/agent-testing.md' 'Node 24 is the qualified frontend build environment; verify `node -v`/`npm -v` before use.' 'Original Node 24 qualification is historical; selected ADR-0184 tooling needs actual owning Linux context/version evidence and complete normalized qualification.'
Replace-Once 'docs/agent-testing.md' '4. Frontend JS/TS/CSS changes run frontend/build/browser gates and commit regenerated
   original30 preservation and managed output/retirement per ADR-0184; backend/docs-only edits do not regenerate it.' '4. Frontend JS/TS/CSS changes run applicable frontend/build/browser gates. Keep original30 frozen;
   managed output sync and reviewed source retirement follow ADR-0184; backend/docs-only edits do not regenerate output.
   After integration, [ADR-0185](adr/0185-accepted-eager-startup-bundle-accounting.md) counts entry+mandatory AccountBar recursive static JS/CSS once in the build check.
   Default helper/frozen historical closures stay static-only; source is unapplied/unqualified and amended tests NOT RUN. All native/privacy/browser checks remain.'
Replace-Once 'docs/agent-testing.md' 'Complete native-only qualification: `scripts/qualify_go_toolchain.sh`, documented in
[NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md), requires explicit disposable PG and task scratch,
Go 1.27.1/Node 24, Python/Rust absent from PATH; no missing required gate becomes a skip.' 'Retained [ADR-0168](adr/0168-qualify-complete-native-toolchain.md) qualification script `scripts/qualify_go_toolchain.sh` still requires
Go 1.27.1/Node 24, explicit disposable PG/task scratch and Python/Rust absent from PATH; see [NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md).
This historical recipe does not qualify selected ADR-0184 tooling; no missing required gate becomes a skip.'
Replace-Once 'docs/execplans/s1-cat.md' '## 3. Surprises & Discoveries' '- [x] 2026-10-08 13:12 UTC — Paul accepted the startup calculation recorded in [ADR-0185](../adr/0185-accepted-eager-startup-bundle-accounting.md). The separate2-path source counts entry+mandatory immediately mounted AccountBar recursive static JS/CSS once; frontend120KiB and canonical JS40960/30720 stay unchanged. Four retained+seven new tests(11) are authored NOT RUN; code application/current startup gzip/Linux qualification remain pending. Original38-path source packet and separate calculator/doc packets are immutable, unapplied and unqualified; this is decision/source acceptance only.
- [ ] Accepted-calculation validation — after exact guarded source integration on Linux, acquire the current Vite manifest and actual mandatory AccountBar-inclusive file inventory/per-file gzip sum; run the amended11 contracts and all applicable existing lanes, retaining every real failure. No inferred savings or40KiB/120KiB pass.

## 3. Surprises & Discoveries'
Replace-Once 'docs/execplans/s1-cat.md' '## 4. Decision Log' 'AccountBar is imported with React lazy syntax but mounts unconditionally in the initial Suspense shell before play. The accepted build calculation therefore includes its static closure. Default helper calls, gui-baseline per-key closures and gui-assets initial_gzip_bytes remain static-only; historical114086/114111/119.78/119.80/121.94 measurements retain their original scopes. There is no observed new total.

## 4. Decision Log'
Replace-Once 'docs/execplans/s1-cat.md' '## 5. Outcomes & Retrospective' '2026-10-08 — [ADR-0185](../adr/0185-accepted-eager-startup-bundle-accounting.md) records Paul''s accepted Cat-local first-load accounting correction and ADR-0020 metadata-only partial supersession. ADR-0184, all numeric budgets, font policy and React19/UI0.3 throughM1 remain. Application/testing/current measurements are pending; no core SDK/phase change, waiver or new execution authority follows.

## 5. Outcomes & Retrospective'
Replace-Once 'docs/execplans/s1-cat.md' 'Implementation in progress. Completion requires actual clean native reports and physical prerequisite evidence; unavailable facts remain explicit constraints.' 'Current 2026-10-08 Windows continuation is **SOURCE ONLY**: original38-path source, separate2-path eager-accounting source and this documentation proposal are unapplied/unqualified. All product execution/tests/parsers/compilers/validators/generators/formatters/builds/Docker/setup/environment probes are NOT RUN in this continuation. Earlier Linux-active paragraphs below are historical context, not Windows execution authority. Core1.2 release identities remain unchanged; E3 budget-red, device/M2, S0b/teacher/social/live/soak and production holds remain.

Implementation in progress. Completion requires actual clean native reports and physical prerequisite evidence; unavailable facts remain explicit constraints.'
Replace-Once 'docs/execplans/s1-cat.md' '## 8. Concrete Steps' 'The future Linux integration order is original38-path source packet, separate2-path accepted startup-accounting amendment, then this separate documentation amendment. Verify each sealed packet and every exact beforeimage/mode or new-path absence; stop for owner sequencing on relevant drift. Preserve Source6/Source7 current truth and all old failures/receipts. After integration, acquire a fresh manifest and AccountBar-inclusive startup inventory/gzip measurement; the default helper and historical report fields stay static-only. No new HEAD/tree/image/qualified identity is assigned by these source proposals.

## 8. Concrete Steps'
Replace-Once 'docs/execplans/s1-cat.md' 'All commands run from this worktree.' 'Current source-only hold: no command below is executed in this Windows continuation. These are future Linux owner steps after guarded integration and current admission/preservation; source acceptance does not grant admission.

All commands run from this worktree.'
Replace-Once 'docs/execplans/s1-cat.md' '## 10. Idempotence and Recovery' 'Accepted startup-accounting acceptance additionally requires the real current Vite key src/components/AccountBar.tsx, its recursively static JS/CSS files, deduplicated shared inventory and strict refusal for absent required roots/imports/output. Run all11 amended bundle contracts and acquire the genuine per-file gzip level-9 sum against unchanged frontend120KiB(122880B). This frontend combined JS/CSS check does not replace canonical cat-initial JS40960/30720 or CSS policy. Keep old static-only baseline/report fields frozen; add any fresh startup evidence separately. Preserve unchanged original assertions and every applicable native/auth/privacy/browser/lint/CSP lane, actual same-final-SHA trust -> GREEN unit -> canonical KIT_BUMP, E3 formal qualification limits and physical device/M2/S0b/production holds.

## 10. Idempotence and Recovery'
Save-Lf 'after/docs/adr/0185-accepted-eager-startup-bundle-accounting.md' 'Valid until: a superseding accepted calculation decision — then treat as history.

# ADR-0185: Count immediately mounted AccountBar in startup JS/CSS

Date: 2026-10-08
Status: accepted by Paul; source amendment unapplied and unqualified; actual Linux validation pending
Supersedes: ADR-0020 first-load JS/CSS accounting only; ADR-0184 tooling/output and other ADR-0020 limits remain.

## Decision

For the frontend build''s initial-transfer check, count the union of every Vite
entry''s recursive static JS/CSS closure and the immediately mounted
`src/components/AccountBar.tsx` root''s recursive static JS/CSS closure. Count
shared emitted files once and terminate cycles through a shared visited set.
Require the fixed AccountBar root in `checkInitialBundle`; caller/environment
options cannot remove that root. Missing or malformed required eager root/import
bindings and missing emitted JS/CSS files refuse the check. Other dynamic game
routes and further dynamic descendants remain outside this bounded startup set.

Sum each selected file''s gzip level-9 bytes. Keep the frontend default at
120 KiB (122,880 bytes), its existing limit configuration and its separate exact
Fredoka/Inter Latin and Latin Extended font-subset checks. Fonts, images and other
non-JS/CSS assets are not added to this sum. The canonical `cat-initial`
JavaScript ceiling of 40,960 bytes and target of 30,720 bytes, and the separate
CSS policy, remain independent unchanged requirements.

Keep `collectInitialBundleFiles(manifest)` static-only by default; explicit
bounded `eagerRoots` support the build check without changing other callers.
Frozen historical per-key baselines, `gui-assets initial_gzip_bytes` and
original observations retain their exact captured static-only scopes.

## Context / why

Paul directly accepted this calculation on 2026-10-08: "accept this new
calculation update all documentation with this new calculation and continue".
`App.tsx` defines AccountBar with React lazy import syntax, then mounts it
unconditionally in the initial Suspense shell before any play action. Auth state
can make its rendered UI empty only after its module has been fetched. Dynamic
syntax therefore does not exclude this immediately requested chunk from startup
accounting. Games remain loaded on play.

The retained original Vite manifest at
`93066854f67245d4b70c0ea97dc2401445a3218c` binds that source-relative root.
It is historical source evidence, not a fresh manifest or observed startup sum.
The existing entry/static-only calculator omits AccountBar; the accepted separate
two-path amendment changes that calculator and its meaningful source contracts.
It does not change application/auth/score/game/motion behavior or add product bytes.

## Consequences

At this decision checkpoint, the calculator amendment is **SOURCE ACCEPTED,
UNAPPLIED and UNQUALIFIED**. Four original contracts remain, seven are added
(11 total); the amended suite is **NOT RUN**. Actual current manifest, emitted
file inventory, gzip total and appropriate Linux checks remain pending. This
decision records no new measurement, savings, budget PASS, image or release identity.

The stricter calculation can expose a genuine failure of the unchanged 120 KiB
default. Preserve that failure and its exact inputs; do not omit AccountBar,
weaken assertions or rewrite original numbers to obtain a pass. Preserve
ADR-0020''s historical115.34KiB body/evidence and all original baseline reports.

[ADR-0184](0184-native-spa-toolchain-and-managed-output.md) still governs selected
tooling and managed output; React19 and UI0.3 remain throughM1. PROGRAM E3''s real
budget-red/formal M0/M1 constraints, actual same-final-SHA trust -> GREEN unit ->
canonical KIT_BUMP, device/M2, S0b/teacher/social/live/soak and production holds
remain. Immutable core1.2 release/tag identities are unchanged. Current facts
and future owner obligations live in [STATUS](../STATUS.md) and the
[S1 plan](../execplans/s1-cat.md); source acceptance grants no Windows execution
authority or runtime qualification.
'
Save-Lf 'PROGRAM_CLARIFICATION.md' '**Cat startup accounting — accepted 2026-10-08, source amendment unapplied.** The frontend''s 120 KiB (122,880-byte) combined JS/CSS check counts all entry/static closures plus the immediately mounted AccountBar and its recursive static JS/CSS dependencies, with shared files and cycles counted once. Mandatory manifest roots/imports and emitted JS/CSS assets must exist; game routes and further dynamic children stay excluded. Default helper callers and frozen historical per-key closures retain their static-only scope. This does not replace the canonical cat-initial 40,960-byte JavaScript ceiling/30,720-byte target or separate CSS policy. Fresh startup measurements and Linux qualification remain pending; no threshold, phase or device condition changes.
'
Write-Output 'Authored exactly9 documentation afterimages in separate scratch; no repository changes or runtime execution.'
