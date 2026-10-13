# M2 activation — original-React binding migration

Valid until: S1 M3 ports the remaining screens (then the frozen bundle and these bindings retire per PROGRAM §8.2) — then treat as history.

The UI1 activation (PROGRAM E7) removes the React 19 / UI 0.3.0 graph from the tree:
`frontend/vendor/roedu-ui-0.3.0.tgz`, `react`, `react-dom`, `react-router-dom`, `@types/react*` and
`@vitejs/plugin-react` are gone from the manifest, the lock and `node_modules`. Several current-tree
scripts bound the original React inputs through those paths. Each binding below now reads the
same bytes from the frozen original receipt (`docs/reviews/gui-original-react/`, promoted from the
qualified gen at 45edcf2c, hashes unchanged) or from the frozen legacy archive
(`legacy/cat_de_roman_esti-legacy-93066854…tgz`, ADR-0193). No assertion was deleted or weakened;
no value was fabricated — every migrated hash is the one the receipt already carries.

| Script | Before | After |
| --- | --- | --- |
| `scripts/gui-baseline.mjs` (inputs hashed into every capture/verify report) | `frontend/vendor/roedu-ui-0.3.0.tgz` | the archive the `@roedu/ui` manifest pointer selects (`frontend/vendor/roedu-ui-1.0.7.tgz`) plus `docs/reviews/gui-original-react/original-ui-0.3.0.tgz` |
| `scripts/gui-full-browser.mjs` `originalPrerequisites()` (gen `qualify-original-react` only) | live `frontend/package.json`/`package-lock.json`, vendored 0.3.0 archive, installed `react`/`react-dom`/`framer-motion`/`@roedu/ui` manifests, installed `@roedu/ui/dist/index.js` | receipt copies `original-package.json`/`original-lock.json`/`original-ui-0.3.0.tgz` (same exact hashes `efde2d3f…`, `f72661b4…`, `1934a81c…`); versions from the original lock rows; the SDK entry read from the archive member and compared to `receipt.runtime_sdk.entry_sha256` |
| `scripts/gui-original-execution.mjs` original profile | live manifest/lock bytes, vendored 0.3.0 archive, `lock.packages["node_modules/react"]` | receipt copies for manifest/lock/archive (hash-asserted as before); runtime identity from that lock; missing rows read as `null` (still refused by the identity check) |
| `scripts/gui-original-execution.mjs` `normalizedReactAdmission()` (gen `replay-normalized-react`) | vendored 0.3.0 archive, installed `@roedu/ui` package/entry equal to the archive | archive from the receipt copy; the installed-SDK equality is replaced by the receipt's `runtime_sdk` manifest/entry hashes that were already asserted. The normalized React graph itself no longer exists, so the admission fails honestly on its first live-graph assertion; `scripts/gui-repo-hook.mjs` now refuses the operation up front with the named check `cat-normalized-react-retired` instead of crashing on the removed `gui-sdk-allocation-audit.mjs` |
| `scripts/gui-style-plan.mjs` (gen style planner) | `extractRendererUnitless(frontend/node_modules/react-dom/cjs/react-dom-client.development.js)`; installed `react`/`react-dom` manifests; live `@roedu/ui` pointer and vendored archive; original profile's `cat_de_roman_esti/web/static/assets/index-qYTSE3Vo.js` | the unitless policy is bound to the frozen archive member `assets/index-qYTSE3Vo.js` (hash `3aeceaed…`, already the normalized profile's binding) for both profiles; React rows from `original-lock.json`; the sealed pointer/archive from `original-package.json`/`original-ui-0.3.0.tgz`. `extractRendererUnitless` stays exported for its fixture tests |
| `scripts/gui-style-operation.mjs` `captureProtected` / `validatePlannerOutput` | `frontend/vendor/roedu-ui-0.3.0.tgz`; required planner inputs under `frontend/node_modules/react-dom/**` and `cat_de_roman_esti/web/static/**` | `frontend/vendor` (whole active vendor tree) is the protected snapshot; required inputs are the receipt copies with their exact hashes; the original profile also requires the archive-member `frozen_renderer` binding; React rows validated against `original-lock.json` |
| `scripts/gui-validate-original-receipt.mjs` | `frontend/vendor/roedu-ui-0.3.0.tgz` | `docs/reviews/gui-original-react/original-ui-0.3.0.tgz` |
| `scripts/gui-repo-hook.mjs` `deps` (`baseline-quality-only` exactness proof) | live manifest/lock + vendored 0.3.0 archive stay byte-exact | live manifest/lock + the archive the manifest pointer selects stay byte-exact |
| `frontend/scripts/gui-sdk-allocation-plugin.mts`, `gui-sdk-allocation-audit.mjs` | React production allocation annotation of the 0.3.0 SDK | deleted: the Preact UI 1.0.9 payload has no React `forwardRef` allocations to annotate; the normalized replay that ran the audit is retired (above) |

## Active route-budget classification (ADR-0193 projection over ADR-0197)

`scripts/gui-route-budgets.mjs` measures two profiles with their own screen tables: `active`
(current Preact bundle) binds exactly the ported journeys `/`, `/intrusul`, `/perechi`, `/conexiuni`;
`frozen-legacy` keeps all ten original journeys. The evaluator refuses when the shell's literal
route switch (`frontend/src/App.tsx`), the client table (`frontend/src/routes.ts`) and the Go
server set (`managedPortedRoutes`) disagree. `qualification.delivery` names the bundle that serves
each journey; unported journeys stay `baseline:frozen-legacy:*` recorded rows (unchanged
40,960 B limit, raw SDK status retained) and never become active gate rows or disappear.

## Browser inventory and projects

`frontend/e2e/games.mjs` `start()` asserts `<html data-ui>` for every journey (`preact` for the
ported set, `legacy` otherwise). `frontend/e2e/gui-m2-pilot-journeys.spec.mjs` deep-links every
ported route, asserts the legacy routes, the client-side return to Home and the kit Presence
retention/variant; it also runs under the new `motion-on` project (`reducedMotion:
"no-preference"`, Desktop Chrome, this file only). `frontend/e2e/gui-inventory.json` adds the 33
cases (11 tests × desktop/mobile/motion-on): 900 → 933 (927 before the Perechi port).

## Full-gate findings (7c69f163)

`python3 -I scripts/gui-full-runner.py --sha 7c69f163c4687a7aaf68895f630036b4199e58bc` → `.gate/full/result.json`
fail (result sha256 0cac7fc28a4ab8356ad1e2315fadd0156697f8a2c62e79184953ec3abefb2412): 34/38 checks pass — unit lanes, `cat-active-ui`, route budgets (active
rows `/` 26,465 B, `/intrusul` 37,795 B, `/conexiuni` 40,198 B ≤ 40,960), PG accounts/httpapi with zero
skips, 1,207 HTTP parity, the same-image legacy owner journey (0 violations), CSP enforced with 0
violations on the nine active routes. `cat-browser-full` fails on 19 of 927 cases (908 pass, 0 skipped,
0 flaky), so the baseline PNG/axe/vitals comparison did not run. The 19 cases:

| Cases | Cause | Disposition |
| --- | --- | --- |
| 10 × `original/runtime.spec.mjs` Intrusul Presence fixtures (desktop+mobile) | kit Presence finalizes exits in the same frame under reduced motion and animates its wrapper, not `.screen`; the sealed fixtures need a mounted, dimmed, locked `.screen` for ≥ 1 frame | kit gap, `CORE_REQUESTS.md` REQ-8; fixtures unedited |
| 2 × `gui-m0-derived-presentation-parity` "Perechi preserves deliberately moved help focus…" | Perechi is served by the frozen original bundle, which predates the M1 source focus guard the test demands (its own comment names this expected failure on the original implementation) | resolves with the M3 Perechi port; frozen bundle untouched |
| 2 × `derived-action-recovery` "browser Back preserves the saved round…" (Perechi) | Back from a legacy document is a document navigation, so the held reply dies with the discarded document and the test hung on it | test adapted for unported games (ADR-0197 gap); assertions unchanged |
| 2 × `mobile-status-notices` Conexiuni finished state | UI 1.0 toasts carry a 44 px dismiss control, so three stacked notices overflowed the 30dvh notices row | `arcade.css` drops the toast block padding (44 px target kept) |
| 3 × `gui-m2-pilot-journeys` "home deep link…" | my test aimed at `/alchimie`, whose legacy default view is the explore screen (no `.game-intro`) | test aims at `/perechi` |

## Full-gate findings (8bd44c0e, second attempt)

`python3 -I scripts/gui-full-runner.py --sha 8bd44c0ede570e6281777906e51feeccbac60a43` → fail (result
sha256 f0269cf8de6785fc83e1e8a4e2cc50eb1bc9e6b2a857119f6d87cf07269cbfbb): 34/38 again, browser 913/927,
0 skipped, 0 flaky. The pilot home journey and the two Back journeys now pass. Remaining 14: the 10
sealed Intrusul Presence fixtures (REQ-8), the 2 Perechi focus cases (ported below) and 2 ×
`mobile-status-notices` Conexiuni `copy-failed` cases, now at the next assertion: with the 46 px
UI 1.0 toast (44 px dismiss target + borders) and the kit's 8 px stack gap, the fifth notice (copy
failure over four finish notices) ends at 270 px while the 30dvh row on the 850 px viewport caps
at 255 px (geometry attachment). `arcade.css` sets the in-row stack gap to 4 px and the row's top
padding to 4 px: 5 × 46 + 4 × 4 + 4 = 250 px ≤ 255 px, dismiss target unchanged.

## Perechi port (pulled forward from M3)

Owner direction after the second full: port Perechi now so the two derived-parity focus cases get a
real fix instead of waiting for M3. `frontend/src/screens/Perechi.tsx` is the mechanical port of the
current source at 0a2687b3 (same pattern as Intrusul: `preact/hooks`, kit `Presence`/`useIsPresent`,
plain tile buttons, feedback row through `Presence mode="wait"`); the M1 focus guard
(`focusStillOwned`, `queueFocusAfterUpdate`, `pendingFocus` ownership) and `perechiFocus.mjs`,
`api/perechi.ts` are byte-identical. `styles/perechi.css` gains only the Presence wrapper rule;
`arcade.css` gives `.perechi-tile` the same `:active` scale as Intrusul. Bindings extended:
`routes.ts` (`PORTED_PATHS`, link scope), `App.tsx` lazy screen + literal case, Go
`managedPortedRoutes` + its exact-set test (the two tests that used `/perechi` as the legacy
example now use `/lant`; the assertions are unchanged), `gui-route-budgets.mjs` ported table,
`games.mjs` `portedRoutes`, the pilot spec (Perechi joins the per-game deep-link + exit loop; the
unported-card journey targets `/cald-rece`), home parity manifest closure, inventory 927 → 933,
`EXPECTED_CSS_BAGS` 53 → 59 (nested 3 → 5; six Perechi bags). ADR-0197 carries an addendum.
Unit 41946309 PASS 26/26: active rows `/` 26,559 B, `/intrusul` 38,008 B, `/perechi` 38,825 B,
`/conexiuni` 40,295 B (≤ 40,960; targets 30,720 met by `/` only). Expected until core-v1.9: the sealed
Perechi Presence fixtures in `original/runtime.spec.mjs` join the Intrusul ones (REQ-8); no full was
run on the Perechi commits.

## Exiting screen (REQ-8 consumer side)

The ported screens consume the existing kit API only: `useIsPresent()` locks every control and
drops pending focus claims; `arcade.css` dims `.app-content > .roedu-presence[data-state="exiting"]
.screen` to opacity 0.6 (static, no animation). No retention shim; the ≥ 1 frame retention under
reduced motion is the kit change (core-v1.9).

## Test adaptations

- `frontend/e2e/gui-m0-home-parity.spec.mjs`: the served-build closure check now expects the
  ported screens as dynamic entries and the unported screens absent from the current manifest.
- `frontend/e2e/conexiuni-simpler-ui.spec.mjs`: the kit Presence wraps each tile in
  `.roedu-presence`, so `conexiuni.css` makes every wrapper a grid cell and the column probe reads
  `gridTemplateColumns` from the grid element (`closest(".connections-grid")`) instead of the
  tile's parent; every geometry assertion is unchanged. The pilot spec asserts the same four
  columns before and after a solved group leaves.
- `frontend/src/styles/arcade.css`: UI 1.0 ships component rules in cascade layers, so the
  unlayered bridge rule `button { color: inherit }` would now beat the kit's per-variant button
  colours (primary text on coral); it is scoped to `button:not(.roedu-btn)`.
- `frontend/tests/v1-daily-intent.test.mjs` stubs `preact-iso`'s `useLocation()`/`route()` instead
  of `react-router-dom`.
- `frontend/tests/gui-route-budgets.test.mjs` binds the ported set contracts; the frozen profile
  keeps its ten-route fixture.
- `scripts/gui-style-audit.mjs` `EXPECTED_CSS_BAGS`: 162 → 59 (unported screens left the active
  source; 0 findings is still required).
- `frontend/tests/gui-style-plan.test.mjs` / `gui-style-operation.test.mjs`: the exact-source pins
  follow the migrated planner (`PLANNER_SHA256`) and the ported `CspStyle.ts`/`CspElements.tsx`;
  the normalized data fixtures model the sealed staged-react phase from the frozen receipt because
  the live `repo:kit-config` no longer carries one; the original React adapter can no longer be
  derived from the current adapter, so the controlled-refusal case was retired with the other
  React-era proposal cases (19 in all, Decision Log 8).
- `frontend/tests/gui-style-operation.test.mjs`: the React-era proposal protocol tests (normalized/
  original planner proposals, byte guards, native candidate graphs, the controlled planner refusal;
  18 cases) retired with the React tree they copied (Alchimie/Perechi screens, vendored 0.3.0
  archive, SDK allocation plugin, installed `react-dom`); the request-admission, identity,
  protected-map and failure-retention tests stay. Replacement for the explicit-unit contract:
  `scripts/gui-style-audit.mjs` + `frontend/tests/gui-style-audit.test.mjs` (live in unit) and the
  kit AST v11 rules. The planner's native-project input list names
  `frontend/scripts/gui-precompressed-plugin.mts` (the one `tsconfig.tools.json` still includes).
- `frontend/tests/gui-precompressed-assets.test.mjs`: its all-screens synthetic manifest is measured
  as the frozen-legacy profile.
- `frontend/tests/fixtures/gui-hook-runtime-bootstrap.json`: the `package.json` pin follows the
  bootstrap manifest, and the `scripts/locate-kit.mjs` pin follows the core-v1.9 file (it admits the
  optional `operator` descriptor key, core ADR-0024); the other six pins are unchanged.
- `frontend/testdata/motion-layout-shadow/` (React 19 projected-layout regression lane: React/Framer
  entry, runner outside default discovery) is deleted with the React graph; the retired
  `plan-normalized-styles` gen operation that executed it keeps its bindings and fails honestly.

## E7 integration, content merge and landing (2026-10-13)

- Commits: `GATE-CHANGE: kit stage core-v1.9` (kit only) → `GATE-CHANGE: activate UI1 with the M2 port`
  (the single E7 integration; detailed history on local branch `archive/gui-cat-m2-prework`) → merge of
  content `main` ed9932fa (V1.13, ADR-0194/0196 method) → this docs commit. Core-v1.9 (UI 1.0.9, web-kit
  0.1.9) carries REQ-8; the sync passed 9/9; trust pinned as `op=agent:claude-code`.
- Seven descriptor readers admit exactly the optional `operator` key the core-v1.9 wrapper records
  (gui-hook-runtime, gui-baseline-checks, gui-native-preflight, gui-browser-capability,
  gui-style-operation and its test, gui-style-plan test); every other extra key is still refused.
- Unit at the first merge passed 26/26 (route JS gz `/` 26,643, `/intrusul` 38,092, `/perechi` 38,909,
  `/conexiuni` 40,380 ≤ 40,960). Full at the same merge: 34/38, browser 929/933, zero skips/flaky, CSP
  enforced 0/0, PG and 1,207/1,206 parity pass; all ten sealed Intrusul and the Perechi Presence fixtures
  passed on core-v1.9 (REQ-8 closed). The 4 failures were Perechi's lost-response focus recovery on both
  projects: Preact commits the recovered state before the awaited unlock, so the focus effect met disabled
  tiles and dropped its claim; the port now restores in a layout effect once the tile is enabled
  (Intrusul's pattern). The next full (81988a01) passed the whole 933-case matrix but its exact PNGs
  differed on the three game intros: the kit stylesheet states no layer order, so `reset` outranked
  `components` (REQ-9); `frontend/src/styles/layers.css`, imported first, declares the order. Full
  76a67431 then matched every PNG except the autofocused intro button's ring (offset 3px vs 2px): UI 0.3
  supplied the 2px/2px ring unlayered, so Cat now states it after its generic `:focus-visible` rule.
  Full cb370487 passed every check except the kit's `csp-measurement` shape: the five frozen routes load
  the frozen entry, which the kit validator cannot represent (REQ-10); the runner now reports them as
  `frozenNonceObservations` bound to the frozen archive's file list, keeping every CSP assertion. The qualifying unit/full of the landed SHA are recorded in the roedu-ui loop
  ledger and `docs/STATUS.md`.
- Additions to E7's permitted paths, accepted as port-required: `frontend/index.html`,
  `frontend/vite.config.ts`, `frontend/tsconfig*.json`, `frontend/oxlint.config.json` (lane removal), the
  deleted SDK allocation plugin/audit and `frontend/testdata/motion-layout-shadow/`, the bootstrap tool's
  core byte copies, `CORE_REQUESTS.md` and `frontend/README.md`.
- Independent review (Claude Code reviewer agent, 2026-10-13): approve with notes; landing additionally
  needed the owner's recorded device-checkpoint waiver, which is [ADR-0198](../../adr/0198-owner-lands-m2-before-device-checkpoint.md).
  Open follow-ups: the gen `plan-*-styles` paths now refuse untested (add a retired-operation refusal
  check like `cat-normalized-react-retired` or delete them); `tools/gui-bootstrap-webkit/package-lock.json`
  root version is 0.1.7 until the next `deps`; `tools/gui-bootstrap-webkit/templates/gate.sh` is still a
  core-v1.5 copy read by `wrapper-config-test.mjs`.
- Read green budgets correctly: 40,960 B applies to the four ported routes; frozen-legacy rows are
  recorded only (E3/E4, ADR-0197). Pilot motion assertions are meaningful only in the `motion-on` project.
