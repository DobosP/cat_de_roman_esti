# Finish the Cat game migration

Branch: `feat/gui-cat-m3`
Session: GUI completion loop, M3 and M4
Worktree: `/home/dobo/work/_worktrees/cat_de_roman_esti/feat__gui-cat-m3`

## 1. Purpose / Big Picture

Finish the existing Preact game migration without changing game content, saved
progress or the accepted design. The owner requested completion on 2026-10-18.

## 2. Progress

- [x] 2026-10-18T17:09Z — inspected all98 unmerged paths and preserved their exact
  entry bytes in the compact scratch source packet; no other lane was changed.
- [x] Read-only review confirms all eight app paths and both Alchimie modes exist.
- [x] Static shared-control extraction removes18 CSS bags; exact site inventory retained.
- [x] Class-only Challenge markup uses native tags;47 wrapper tags, handlers unchanged.
- [x] 2026-10-18 — owner explicitly approves the reviewed mechanical score-module
  split and scoreSync import narrowing; all other source freezes remain.
- [x] Applied approved score split: original34 score tests/147 assertions,38focused,
  types/tools/lint/build/docs62 and26desktop/recovery cases pass.
- [x] Qualify native Preact state for the20 Challenge render snapshots (ADR-0204),
  retaining all asynchronous ownership/motion/focus/scoring and existing assertions.
- [x] 2026-10-18T19:01Z — all10JS caps pass: Challenge40,864/40,960, Home29,011/30,720 target.
- [x] Broad native-state diagnostic:111passed/2failed,0skip/flaky; exact source, logs and failure traces retained.
- [x] Two minimal fixes pass113/113desktop: committed key listener timing and new-round access after failed verification.
- [x] 2026-10-18T19:11Z — all6 real history regressions fail on old late-create pointer adoption (3games×2projects), not fixture/setup/timeouts.
- [x] 2026-10-18T19:16Z — reviewed three-screen repair passes139desktop/38focused/34score, all10JS caps/types/tools/lint/build/docs; strengthened history response/count witnesses pass.
- [x] Final bounded source review15256eff is clear for all8 route bindings, frozen boundaries,12 score-module bindings and22 critical runtime inputs.
- [x] Actual browser discovery retains933 existing case identities.
- [x] Focused38/38 checks pass after source census119/8 correction.
- [x] Real mode-switch blank-screen regression reproduced in both desktop projects;
  instance-local lazy retry fixes it and all four chunk/storage recovery cases pass.
- [x] Final app/tools types,38focused,lint/build and26desktop/recovery cases pass;
  both navigation regressions and immutable loader initialization are verified.
- [x] Unused Router export compiler candidate measured and rejected: positive
  DCE test fails and JS grows; entire candidate reversed, source/evidence retained.
- [x] 2026-10-18T19:18Z — committed71f871ca; clean unit27 passes560frontend/1930backend named/28authcore, independently acceptedcd8725e6.
- [x] First full actual933browser cases pass with0skip/flaky/retry; livePG12/301 covers all17default DSN skips and9 additional child cases, parity1206/legacy pass.
- [x] 2026-10-18T20:16Z — reviewed Home source-pin rebind and optional full parallel CLI pass10Python ownership/argument tests,43unchanged baseline DATA controls andGo doccheck62.
- [x] Same9c44 diagnostic and unit2/full2 pass original9PNG/Axe/Home/vitals/CSP; unit27/full37 independently accepted.
- [x] 2026-10-19 — M3 source9c44 independently accepted, feature published and exact tested source landed locally.
- [x] 2026-10-19 — final M4 source16733891 unit27/full38/image2 independently accepted and landed locally; CSS16,043/16,093,933browser/9exactPNGs/Axe/vitals/CSP0/PG/parity1206/legacy/cleanup pass. Documentation verified separately; owner retains app-main push.
- [x] Historical M4 setup checkpoint — applied independently reviewed M4 CSS/total-gate/Vitest/guidance candidates and ADR-0205. Optional CSS contingencies remain unapplied. Owning deps and focused types/lint/build/docs43focused/34scores pass; CSS16,022/16,093, all10JS caps. Six actual browser contracts plus5report guards pass after reviewed setup/report repairs; raw failures retained. Clean A measured; initial unit B refused4 protected-source fixtures. Restore exact original CspElements import without editing assertions/pins: lint/browser6/build pass, allactual CSS16,043 includes21B newline-only sheet. Final accepted source16733891 and its qualification below supersede these setup-stage pending items.

## 3. Surprises & Discoveries

At entry the latest actual measurement was Challenge44,592/40,960 gzip bytes:
a3,632-byte gap. Final current results are recorded in section5.
All other nine measurements pass; Explore40,087 leaves873 bytes. Older status
figures45,441/45,806 precede the current common-controls build layout.

## 4. Decision Log

2026-10-18 — resume the existing lane and preserve its98 unmerged source paths.
Existing S1 protected helper/API/content rules remain in force except the directly
approved mechanical scores.ts/scoreSync split. Owner answer: “Allow the
behavior-preserving module split”. Preserve original bodies, public API, keys,
formats, receipt locking/timing and all test assertions; no broader waiver.
The live explicit-unit audit inventory is rebound161→119 after24 historical Challenge bags and18
shared-control bags were transferred literally to authored CSS; all declaration checks and nested-bag assertions remain.
A build-only pinned preact-iso export rewrite may eliminate an unused Router
closure while retaining the original hoisted function and Provider assignment.
Use exact package source hash, original/transformed API and used/unused installed
Rolldown controls; reject if the positive DCE control fails. Never change vendor
bytes or broad tree-shaking defaults. Both source reviewers approved source evaluation. Actual installed Rolldown then
failed the positive removal assertion; the exact candidate was fully reversed.
Do not retry an export-alias variant or weaken that assertion.
Do not repeat nonclosing CSS/minifier/JSX experiments already measured.

2026-10-18 — ADR-0204 revises only the unqualified Signals direction. Independent
architecture review confirms that the adapter supplies render snapshots rather
than fine-grained observers; native Preact queues these synchronous setter groups.
Preserve all functional requirements and verify the actual runtime/complete budgets.

2026-10-18 — broader original journeys prove the keyboard listener must attach
with the committed selection via useLayoutEffect. Failed verification locks old
round mutations but must permit explicit new creation, as the original React
source did. Keep presence/loading/busy/create guards and existing owner
invalidation; change only that button and listener timing. Preserve assertions.
Measured record-writer startup grouping may share its already-startup core; all
routes must count the full writer bytes and Home target remains30,720.

## 5. Outcomes & Retrospective

M3 source9c44d01f is accepted and landed locally: unit27/full37, independently
verified4002424e/276eeab6. Full13.38min uses strict same-SHA unit reuse at
parallel2. Actual933browser cases have zero skips/retries/flaky/errors; all9
PNG bytes equal immutable originals, Axe/Home/five-run vitals/CSP0 pass, fresh
PG12/301 closes17 default DSN obligations, parity1206 and actual legacy pass.
[Qualification](../reviews/gui-m3/qualification.json) records exact commands,
source/image custody, cleanup and retained artifact/supplement hashes.

The stale current-Home source pin and two presentation regressions were repaired
without changing original captures/comparators/assertions. A diagnostic initially
refused stale managed assets correctly; canonical unit regenerated the matching
manifest before the successful diagnostic/full. Optional parallel forwarding
preserves default4 and ownership guards while matching unit2/full2.

Superseded raw/positive trace trees were replaced by the rolling run. Required
regular artifact rows are retained compactly; raw baseline metadata and9 exact
PNG joins use preserved original image bytes. Historical paths do not imply
that discarded raw attachments remain. Unique source packets remain intact.

M4 qualifies the original16,093-byte all-actual-CSS ceiling with16,043 bytes,
including the protected import's newline-only21gzip-byte file. Canonical authored
CSS,pinned browser contracts,full/image and independent acceptance pass. The
M3 canonical20,669 and separate baseline default-gzip20,756 are historical.


### M4 completion report — 2026-10-19

Exact qualified product: `1673389147a3ba432742008d55d28edb84d94af2`; tree SHA256
`0de103c4027967a43b7bc3ae97dab72f4303a7db980d30653d6d133584bebba7`.
Unit27/full38/image2 pass on this clean source. Full result74ee109b and versions
lockd7c0192f are bound in [qualification](../reviews/gui-m4/qualification.json).
[Independent acceptance](../reviews/gui-m4/independent-acceptance.json) approves
local landing. Feature publication retains source; app-main push and production
remain Paul's. No real account/child/provider/government activation occurred.

Main implementation commits, oldest first:

| Commit | Result |
|---|---|
| 9c44d01f | Accepted M3 remaining screens,scoring module boundary and preserved original presentation |
| a5d5e1b9 | Canonical authored CSS,positive total-CSS gate,pinned real browser contracts and current guidance |
| 5be3556b | Historical clean-A measurement binding; later unit correctly refused4protected source pins |
| a9476883 | Restore exact original CSP component import without altering any fixture/pin |
| 271f5aac | Bind final product sizes to actual clean-C measurement |
| 16733891 | Add14initial readiness assertions at7checkpoint setup sites; preserve all original test bytes/IDs |

Gzip figures below count complete recursive static JavaScript closures: entry,
mandatory startup AccountBar and the selected screen/mode,with emitted files
deduplicated. CSS is separate. M0 used one Alchimie root for both modes and
embedded Home in its entry; current figures use actual shipping sidecars.

| Screen | React before (M0) | Preact after | Delta | Budget |
|---|---:|---:|---:|---:|
| Entry/shell + startup AccountBar | 117271 | 22222 | -95049 | 40960 |
| / | 117271 | 28879 | -88392 | 40960 |
| /intrusul | 128603 | 37306 | -91297 | 40960 |
| /perechi | 129357 | 38144 | -91213 | 40960 |
| /conexiuni | 131545 | 38030 | -93515 | 40960 |
| /alchimie | 138596 | 39154 | -99442 | 40960 |
| /cald-rece | 132257 | 38901 | -93356 | 40960 |
| /lant | 132047 | 38772 | -93275 | 40960 |
| /clasament | 118689 | 24870 | -93819 | 40960 |
| /alchimie?mode=challenges | 138596 | 40714 | -97882 | 40960 |
| /alchimie?mode=explore | 138596 | 39154 | -99442 | 40960 |
| All actual CSS | 16093 | 16043 | -50 | 16093 |

Home additionally meets the30,720-byte target. Current CSS is4,626bytes smaller
than accepted M3;50bytes of CSS and246bytes of Challenge JS headroom remain.
Future growth must pass those same positive ceilings. All8other non-Home/non-
Ranking routes retain unmet30,720aspirations visibly;the40,960ceiling passes.

| Throttled five-run median | Original LCP / INP / CLS | Final LCP / INP / CLS |
|---|---|---|
| Conexiuni select | 2836ms /184ms /0 | 1652ms /64ms /0 |
| Alchimie combine | 4228ms /200ms /0.00057706 | 1816ms /72ms /0 |

All9actual PNG bytes equal the immutable originals;Axe/Home semantics and
enforced current+legacy CSP0 pass. Actual933browser outcomes have zero skip,
retry,unexpected,flaky or global error. FreshPG12accounts/301HTTP has zero
skips/failures and covers all17defaultDSN obligations. Reviewed V1.13 parity
is1206;the old1207number remains historical,not a removed/fabricated check.

Warm unit7.12min uses791original plus1,139fresh backend identity results and
28freshauth;Node570and6actualVitest pass. Full20.07min correctly misses strict
whole-unit reuse on the warm command shape while preserving narrow native
reuse and freshGUI/API verification. The15min aspiration was not met;no
assertion was removed to improve it. Original cold D unit took30.52min.

| Image | Actual identity |
|---|---|
| Tested full | `sha256:1178e19f09c4f44ef16d46f31c4660739f66f7e0fb41e7e36ddb4c0dc93e84e0` |
| Explicit release | `sha256:47185da0586e292ddb3d66d564046443c1bb688e652e69e77399ba74503fe58c` |
| Both actual /app payloads | 26042528bytes; `sha256:ac1ccb891da94418c71113af016d068ef1b8f04cc4f7d0a4fdb6c746b0b5ce56` |
| Runtime base | static-debian13 nonroot; `sha256:e2e927ec666bae08560abb3c55d0659eceabb657f56b6782ab500a9fc7f555e3` |
| Node builder | 26.10.0-trixie-slim; `sha256:930557a230abacbc3f4fd9b8648abf8f4bee1e17cb72195dcdfb2f709bc85b33` |
| Go builder | 1.27.1-trixie; `sha256:8f58fd67ea075142d947a60e0caa4317746a55118d312f027793d382c7741734` |

Image IDs/layers differ and are not labelled equal. Two never-started image
copies prove identical app bytes,with exact source/tree labels,UID10001 and
healthcheck. Full gate/owner/coordinator and root Docker queries verify owned
cleanup;explicit-image/proof containers and empty network are absent.

| Resolved tooling | Version / exception |
|---|---|
| Go / Node / npm | 1.27.1 /26.10.0 /12.2.0 |
| Preact /preact-iso | 11.0.0 /2.12.2 |
| UI /web-kit | 1.0.11 /0.1.11;original UI0.3.0 remains only frozen rollback,held until historical M2 |
| Motion | 14.0.0 public runtime shared with kit;no second engine |
| TypeScript /parser | Native7.0.2 /separate6.0.2compiler API |
| Vite /Oxlint /tsgolint | 8.3.3 /1.87.0 /7.0.2003 |
| Vitest/browser/providers /Playwright | 5.0.3 /1.63.0;generated owning deps lock provenance retained |
| Dependency exceptions | Runtime manifest unchanged in M4;only pinned test additions generated by deps;no hand locks/vendor edits |

[CORE_REQUESTS](../../CORE_REQUESTS.md) records current dispositions separately
from historical request text. No app-specific motion/security shim remains.

| REQ | Current disposition | Shim |
|---|---|---|
| REQ-1 | nonblocking historical tooling request,not explicitly closed | none |
| REQ-2 | nonblocking historical sync-back warning,closure not found | none |
| REQ-3 | resolved producer consumer resolver in core-v1.2 | none |
| REQ-4 | consumer explicit-unit enforcement implemented;broader producer lint request not explicitly closed | none |
| REQ-5 | resolved acceptance sequencing/frozen-baseline policy;active M3 budgets genuinely green | none |
| REQ-6 | resolved core-v1.6 secure native WebLocks origin;consumer accepted | none,never existed |
| REQ-7 | resolved core-v1.7 Presence variant,accepted through later kit | none |
| REQ-8 | resolved core-v1.9 one-frame reduced-motion exit hold;M2 accepted | none |
| REQ-9 | resolved core-v1.10 canonical layer statement | temporary layers.css removed |
| REQ-10 | resolved core-v1.10 frozen CSP descriptor support;M3 all-current main routes | none;consumer classification is supported contract,not workaround |
| REQ-11 | resolved producer core-v1.11 and accepted consumer M3 source9c44 | none |

M3/M4 delete no test file or case. M4 replaces only2null/recorded CSS
expectations with stronger positive16,093/pass expectations and adds controls.
Historical S1 retirement totals21unique source-test files plus6mixed-file UI
blocks;three temporary typed guards were later retired only after real typed
proof. C40original900browser/sealed16/78 passed;the ddbc typed proof was inside
a failing315/316unit and is not relabelled green. Subsequent accepted suites
exercise the replacements. Complete exact source references are retained in
[replacement accounting](../reviews/gui-m4/historical-test-replacements.json).

| Historical source test | Replacement browser / compiled contracts |
|---|---|
| `alchimie-empty-recovery.test.mjs` | `alchimie-empty-pairs.spec.mjs`, `alchimie-workbench.spec.mjs`, `alchimie-action-recovery.spec.mjs`, `gui-m0-alchimie-parity.spec.mjs` |
| `alchimie-lineage.test.mjs` | `gui-m0-alchimie-parity.spec.mjs`, `alchimie-workbench.spec.mjs`, `alchimie-journal-search.spec.mjs`, `help.spec.mjs` |
| `alchimie-projection.test.mjs` | `alchimie-workbench.spec.mjs`, `alchimie-journal-search.spec.mjs`, `gui-m0-alchimie-parity.spec.mjs`, `alchimie-action-recovery.spec.mjs`, `api-consumer2`, `native-whole-http1207` |
| `v42-alchimie-fresh-board.test.mjs` | `gui-m0-alchimie-parity.spec.mjs`, `game-touch-targets.spec.mjs` |
| `contexto-api.test.mjs` | `api-consumer2`, `native-whole-http1207` |
| `contexto-comparative-controls.test.mjs` | `contexto-simpler-ui.spec.mjs`, `gui-m0-contexto-parity.spec.mjs`, `gui-m0-contexto-lifecycle-parity.spec.mjs`, `api-consumer2`, `native-whole-http1207`, `extended-native7-consumer` |
| `contexto-progressive-clue.test.mjs` | `gui-m0-contexto-parity.spec.mjs`, `contexto-action-recovery.spec.mjs`, `contexto-simpler-ui.spec.mjs`, `api-consumer2` |
| `cald-rece-recovery.test.mjs` | `contexto-action-recovery.spec.mjs`, `gui-m0-contexto-lifecycle-parity.spec.mjs`, `gui-m0-contexto-parity.spec.mjs`, `api-consumer2`, `extended-native7-consumer` |
| `v42-caldrece-legend-confirm.test.mjs` | `gui-m0-contexto-parity.spec.mjs`, `contexto-simpler-ui.spec.mjs`, `api-consumer2` |
| `conexiuni-one-away.test.mjs` | `conexiuni-action-recovery.spec.mjs`, `gui-m0-conexiuni-parity.spec.mjs`, `conexiuni-coach-layout.spec.mjs`, `conexiuni-simpler-ui.spec.mjs`, `selection-key3` |
| `persistent-game-navigation.test.mjs` | `lifecycle.spec.mjs`, `conexiuni-action-recovery.spec.mjs`, `conexiuni-coach-layout.spec.mjs`, `conexiuni-simpler-ui.spec.mjs`, `game-touch-targets.spec.mjs` |
| `lant-recovery-feedback.test.mjs` | `lant-action-recovery.spec.mjs`, `lant-current-position.spec.mjs`, `lant-relationship-captions.spec.mjs`, `lant-simpler-ui.spec.mjs`, `gui-m0-lant-parity.spec.mjs`, `api-consumer2`, `native-whole-http1207` |
| `v37-pilot-lobby.test.mjs` | `gui-m0-replacement-parity.spec.mjs`, `gui-m0-home-parity.spec.mjs` |
| `v38-six-game-ui.test.mjs` | `gui-m0-replacement-parity.spec.mjs`, `gui-m0-home-parity.spec.mjs`, `gui-replacement-contracts.spec.mjs`, `game-touch-targets.spec.mjs`, `quick-games-simpler-ui.spec.mjs`, `sealed16-78` |
| `v39-verified-ranking.test.mjs` | `gui-replacement-contracts.spec.mjs`, `gui-m0-replacement-parity.spec.mjs`, `gui-m0-account-copy-parity.spec.mjs`, `native-whole-http1207`, `preserved-score-receipts`, `extended-native7-consumer` |
| `v41-ranking-recovery.test.mjs` | `gui-replacement-contracts.spec.mjs` |
| `v41-category-availability.test.mjs` | `gui-m0-category-parity.spec.mjs`, `contexto-simpler-ui.spec.mjs`, `api-consumer2` |
| `v1-board-grid-steps.test.mjs` | `v1-board-grid-steps.spec.mjs`, `game-touch-targets.spec.mjs`, `alchimie-workbench.spec.mjs`, `accessibility.spec.mjs` |
| `v42-derived-loss-and-starter.test.mjs` | `perechi-loss-progress.spec.mjs`, `quick-games-simpler-ui.spec.mjs`, `gui-m0-derived-presentation-parity.spec.mjs`, `native-whole-http1207` |
| `v14-romanian-replay.test.mjs` | `lifecycle.spec.mjs`, `gui-m0-daily-intent-parity.spec.mjs`, `gui-m0-alchimie-parity.spec.mjs`, `gui-m0-lant-parity.spec.mjs`, `gui-m0-account-copy-parity.spec.mjs`, `help.spec.mjs`, `sealed16-78` |
| `mobile-beginner-ui.test.mjs` | `help.spec.mjs`, `game-touch-targets.spec.mjs`, `v1-board-grid-steps.spec.mjs`, `mobile-status-notices.spec.mjs`, `accessibility.spec.mjs`, `v96-input-and-focus.spec.mjs` |
| `game-help.test.mjs` | `help.spec.mjs`, `alchimie-workbench.spec.mjs` |
| `v38-recovery.test.mjs` | `derived-action-recovery.spec.mjs`, `gui-m0-derived-presentation-parity.spec.mjs`, `sealed16-78` |
| `v39-derived-ui-clarity.test.mjs` | `gui-m0-derived-presentation-parity.spec.mjs`, `gui-m0-daily-intent-parity.spec.mjs`, `gui-m0-replacement-parity.spec.mjs`, `quick-games-simpler-ui.spec.mjs`, `native-whole-http1207` |
| `v1-daily-intent.test.mjs` | `gui-m0-daily-intent-parity.spec.mjs`, `v1-testing-ux.spec.mjs`, `resume-recovery.spec.mjs` |
| `v39-local-daily-circuit.test.mjs` | `gui-m0-home-parity.spec.mjs`, `gui-m0-replacement-parity.spec.mjs`, `gui-replacement-contracts.spec.mjs` |
| `v42-meta-loop.test.mjs` | `gui-m0-home-parity.spec.mjs`, `gui-m0-replacement-parity.spec.mjs`, `gui-replacement-contracts.spec.mjs` |

Earlier B unit failed4unchanged protected-source fixtures;restoring the
original import fixed them without pin changes. FirstDfull931/933then found
2old-document response-body errors during checkpoint setup. Exact trace
request ordering proves the new document restored correctly. Fourteen
additive fresh-intro readiness expectations fix all7same-pattern setup sites;
every original action/assertion/caseID remains. Required failed artifacts and
raw traces are retained and never presented as acceptance.

Latest required unit/full/image rows,all9actualPNG bytes,rawreport/identity,
and seven physical publication fixtures plus literal link/referent remain
compactly archived. Superseded rolling raw/positive trace paths were replaced
as authorized;manifests do not claim deleted bytes remain. Original baseline,
source branches,unique unmerged packets and canonical keepers are preserved.

Remaining owner steps: push app main when chosen,production/account go-live,
and a separately governed eventual legacy-tarball deletion release. The M2
per-route navigation gap is closed:every normal route is current;explicit
CAT_UI=legacy remains a verified rollback. No blocking GUI KIT_BUMP is pending.
Next agent implementation is the bounded Teacher/Social UI programme;their
main/milestone landing and realchild activation remain owner-only.

## 6. Context and Orientation

Local main at entry: `d30b0aa47248b9a5944e015f2daf54cc5a795617`.
M3 qualified/landed product: `9c44d01ff476637bd1749b51f632312524d6f7ff`.
Read `.agent/S1.md`, `docs/STATUS.md`, the programme completion ledger and
`docs/execplans/s1-cat.md`. Original/frozen sources and content stay authoritative.

## 7. Plan of Work

Review the actual emitted dependency graph, implement a substantive allowed
reduction and measure every route's complete closure. Preserve mandatory account
and mode dependencies. Then run the existing functional and visual contracts,
integrate literal content-main only at the milestone boundary, and qualify.
Separate M4 source changes from M3 acceptance; retain one rolling test setup.

## 8. Concrete Steps

Work in this worktree. Use the pinned `scripts/gate.sh shell --sha <HEAD> --dirty`
for focused iterations. After clean commits run `scripts/gate.sh unit --sha <SHA>
--parallel 2`, then `python3 -I scripts/gui-full-runner.py --sha <SHA>`.
Run image qualification at M4 and record actual command/result hashes.
After the first failed full, use the reviewed supervisor `--parallel 2` with
unit `--parallel 2`; the strict reuse validator requires matching settings.
Use the existing clean owner-diagnostic baseline mode to expose any remaining
visual findings before the expensive successor unit/full; it is not acceptance.

## 9. Validation and Acceptance

Existing assertions, gzip caps, saved-game lifetimes, native drag/drop, focus,
motion/reduced-motion, CSP, nine exact PNGs, full browser inventory, zero-skip PG,
the reviewed V1.13 parity1206 and independent review remain required.
The old1207 count describes the earlier content reference, not an extra case to
invent; the canonical native parity check already validates current1206. No physical device testing.
Only a green exact-SHA unit/full plus review permits local main landing.

## 10. Idempotence and Recovery

Never overwrite or delete prior unmerged source packets. Preserve failed-run
evidence compactly, then prune only owned stopped raw outputs after verification.
No writer may change a worktree while its gate runs. Never force-push app history.

## 11. Artifacts and Notes

Entry packet: `_temp/feat__gui-cat-m3/renovation/entry-unmerged.tar.gz`, SHA256
`b0f9babf3bfe920a36a0e6274d2959481f68a7c807138b8c8393992e90cd06b5`.
Disk check before runs:52GiB available,93% used. Keep evidence compact.

## 12. Interfaces and Dependencies

Current core-v1.11 consumer dependencies remain pinned. Do not hand-edit locks,
kit/vendor files or baselines. Cat main may be landed locally under PROGRAM E10;
pushing main, production and real-account activation remain owner-only.
