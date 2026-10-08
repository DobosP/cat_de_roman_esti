# PROGRAM.md — GUI performance migration (ro_teacher, cat_de_roman_esti, social_media_activities_app, roedu-ui)

Valid until: `core-v2` or a superseding PROGRAM.md — then treat as history.
Active launch copy from reviewed Linux adaptation 69368a8d889070a12cdddf9cb25b1d960e6d58be. Launch approval is recorded below. Written from RECOMMENDATION.md plus Paul's decisions of the same day. Every Codex session reads §0–§6 and §9 in full, then its own §8 block and §10 entry; the templ sessions (S0b, S2A/B, S3A/B) also read §7 in full.

## 0. Status, precedence, and the nine decisions

### 0.1 Precedence
`Paul's decisions (§0.2) + §1.2 invariants + §4.8 anti-gaming + §5.5 hard stops > session prompt > this file > ExecPlan (docs/execplans/<session>.md) > repo AGENTS.md > skills`. The ExecPlan is written by Codex: it may refine plans, order work and record decisions, but it may **never relax** a rule from this file or the session prompt — a Decision Log line that would weaken §1.2, §4.8 or §5.5 is void and is itself a hard stop. Where RECOMMENDATION.md or any evidence file disagrees with this document, this document wins. If an instruction makes a session pause, it quotes the file and line responsible.

### 0.2 Paul's decisions (2026-10-06) — verbatim, override everything below where they differ
1. **STACK ACCEPTED:** three interactivity tiers — T0 platform features (forms, dialog, popover, view transitions, speculation rules), T1 light-DOM custom elements (vanilla TS), T2 Preact islands. No React, no preact/compat, no framer-motion, no react-router. cat_de_roman_esti moves React 19 → Preact SPA (preact-iso) + an in-house WAAPI motion kit (Motion's small animate/spring for springs). social's 20-route SPA is retired into the server pages. ro_teacher's read-only islands are retired. Widgets: bundle first, rewrite only where justified.
2. **SERVER TEMPLATES:** FULL PORT of ALL existing pongo2 templates (ro_teacher ~133, social ~91) to templ IN THIS PROGRAM. This REVERSES the final recommendation's "keep pongo2" decision. It must be done safely: golden-HTML oracle first, per-route fallback to pongo2 until parity is proven, child-safety/privacy pages with extra review. The attackers' templ-port objections must be answered with mitigations, not ignored.
3. **ORDER:** Session 0 core (roedu-ui 1.0 + web-kit) → Session 1 cat alone until its pilot milestone is green (core shakedown) → ro_teacher and social sessions in parallel, pinned to the current core tag. 3–4 sessions total; splitting a big app into sequential sub-sessions is allowed only if justified by volume.
4. social SPA retired (supersedes social ADR-0016; `SOCIAL_REACT_UI` kept one release as fallback). MapLibre upgraded to the latest 6.x inside a lazy `<so-map>`. social image on debian-slim (its server requires ffmpeg/prlimit at startup); ro_teacher and cat on distroless.
5. PRODUCTION RUNS ON A LINUX SERVER; this Windows 11 PC is only the workstation. Linux is the canonical environment for every gate. Use native Linux with the pinned toolchain container; recorded Windows host mechanics are history.
6. **LATEST EVERYTHING:** newest STABLE release of every tool, library, runtime, base image and model (npm `latest` dist-tag, latest Go release, etc.; never pre-release / RC / beta / `next` tags). Versions are resolved at session start, recorded in lockfiles and in the ExecPlan Decision Log. This DROPS the 7-day release-age cooldown and the Preact 10.29.8 pin: Preact 11 is the target if it is the latest stable.
7. Implementation workers never push, merge, tag, delete branches or edit other repos. Paul explicitly delegated orchestration/review/green landing/pushing and finished-session cleanup to this parent chat. Workers commit locally; the parent performs verified owner operations.
8. Behaviour: parity + perf-driven UX changes allowed when they measurably help. Safety, privacy, a11y, CSP and child-protection gates must not regress. Perf target: low-end Android on slow networks (LCP < 2.5 s on 4G, INP < 200 ms, per-route JS budgets in CI).
9. Packaging: roedu-ui (UI) + a separate web-kit package (build/test/deploy). Deploy: one Go binary per app, assets `go:embed`'ed, one image per app; the same image runs in ephemeral docker-compose test envs, staging and prod.

### 0.3 Evidence tree
All prior analysis lives under `/home/dobo/work/_worktrees/roedu-ui/docs__gui-migration-linux-20261006/docs/plans/2026-10-06-gui-migration/` (recon, research, proposals, judges, spikes, attacks, scratch probes; index in §12). It is **reference, never code to copy**: the spike ports were built on Preact 10.x and must be re-derived on 11.

### 0.4 Deviations from §0.2 that need Paul's explicit acknowledgement before launch
Each line below departs from a decision's letter; none launches until Paul writes `ACK <n>` (or an alternative) in `docs/PROGRAM.md` of the bootstrap commit.
1. **Core is split into two sessions (S0a UI/delivery kit, S0b templ kit) — Decision 3 allows sequential sub-sessions "only if justified by volume".** Justification by numbers (§10.3): S0a already carries 7 milestones (toolchain jump, tokens, 16 components, 7 behaviours, motion kit, 7 Go delivery packages, 10 kit templates); S0b adds a ~1.5 k-line converter, 7 more Go packages, 224 classifier inputs and three golden-equal pilots. S0b is now **sequential**: it starts only after S1's pilot (M2) is green, so cat's shakedown runs alone as Decision 3 orders (§10.3). The alternative is one 13-milestone core session with two context restarts.
2. **Native Linux host environment exception — pending `ACK 2`.** Host Docker 29.5.3, Buildx 0.34.1 and Compose 5.1.4 are below verified upstream 29.8.2 / 0.37.2 / 5.6.0. The obsolete Ubuntu docker.io carve-out is replaced by retaining this working host stack while program tools stay container-pinned. No runtime/system upgrade or global config change is authorized by this pack. Alternative: Paul separately upgrades and re-proves host mechanics before launch. Native scoped Docker escalation succeeded during preparation; it is not blanket Docker authorization for S0a.
3. **`sw.js` is ported to Go `text/template`, not templ (§7.6, §8.1).** Decision 2 says "ALL existing pongo2 templates to templ"; `sw.js` is JavaScript under `{% autoescape off %}`, which templ cannot emit without escaping. The port removes pongo2 from it under a byte-equal golden; the service-worker logic itself is untouched (§1.4). Alternative: keep a pongo2 loader for this one file (two engines stay in the binary).
4. **The Playwright triple is pinned, not re-resolved — a carve-out from Decision 6's "re-resolve at every M0".** `@playwright/test`, `playwright` and the toolchain base `mcr.microsoft.com/playwright:v1.63.0-noble` are one unit (§3.2, `versions.lock.json` exceptions): the committed screenshot baselines depend on that exact browser build, so the three move together only in a `GATE-CHANGE: baseline recapture` by Paul/core with a new toolchain tag — never at an app's M0, even when npm `latest` has moved on (1.63.0 is also `latest` on 2026-10-06, so the seed itself is not a deviation; the freeze is). Alternative: re-resolve at every M0 and accept a baseline recapture per session.
5. **Postgres is `PROD_PG_MAJOR`, not the latest major.** The test env must match the production server's major (§3.2, §4.4), and upgrading the production Postgres major is a non-goal (§1.4); 18.6 is adopted only if prod is already 18. This is "environment, not program tool" like the WSL engine (§3.1), but Decision 6 says "every runtime", so it is listed. Alternative: Paul upgrades prod first and the test env follows.
6. **"Per-route JS budgets in CI" (Decision 8) means the Linux `gate:unit` run for the apps, not GitHub Actions.** `TestRouteBudgets` runs inside `gate:unit` on every milestone commit and every review; only roedu-ui gets a GitHub workflow (`ci.yml`, S0a M5). The apps' workflows are not edited by any session (ro: `workflow_dispatch`-only by ADR-0075; cat and social unchanged), §4.6. Alternative: each app session adopts the kit `ci.yml` as its own ADR'd commit.


## Launch authorization and execution notes — 2026-10-06

Paul explicitly acknowledged ACK 1–6 and PostgreSQL 16 in the GUI migration parent chat on 2026-10-06, then authorized end-to-end implementation, no further permission questions, parent review/landing and cleanup of completed managed work.

- ACK 1: accepted by Paul in the direct continuation message after the six recommended launch decisions.
- ACK 2: accepted by Paul in the direct continuation message after the six recommended launch decisions.
- ACK 3: accepted by Paul in the direct continuation message after the six recommended launch decisions.
- ACK 4: accepted by Paul in the direct continuation message after the six recommended launch decisions.
- ACK 5: accepted by Paul in the direct continuation message after the six recommended launch decisions.
- ACK 6: accepted by Paul in the direct continuation message after the six recommended launch decisions.

- Production/test PostgreSQL major: 16. No major database upgrade is authorized or needed.
- Parent owns bootstrap, image pins, trust pins, kit distribution, independent review, green landing and managed cleanup. Owner operations execute only while the assigned worker is idle. Automated review is identified honestly; never fabricate human Live/device/production-soak evidence.
- Initial bootstrap is installed by parent on feat/gui-core, not shared main. Bootstrap and implementation land together only after real green gates; deliberately refusing stubs are not product-gate passes.
- Managed per-call exact-wrapper escalation is the approved route. No global Codex config/rules or Docker socket permissions are changed. Hooks/project overrides are optional; a self-contained ExecPlan is sufficient.
- S0a implements actual gen/deps/unit/full bodies before its milestone boundaries. Bootstrap refusal is known initial state, not three failed product attempts. Implement the real sample app/image fixture before the first required M3 full gate.
- The source Windows record and reviewed Linux pack remain at their pinned commits. Historical preparation defects do not override this active dispatch.
- Physical measurements and actual release/runtime evidence remain facts to obtain, not approvals to invent. Continue independent authorized code/testing and keep unsafe production activation closed when release-only evidence is unavailable.

## 1. Goal and non-goals

### 1.1 Goal
Ship the three web apps as single Go binaries with embedded, precompressed, immutable assets, server-rendered by templ (ported from pongo2 under a golden oracle), with client JS reduced to three tiers (T0 platform, T1 light-DOM elements, T2 Preact 11 islands) and cat as a Preact 11 + preact-iso SPA. Measured target on a real Samsung A-series phone over throttled 4G: **LCP < 2,500 ms, INP < 200 ms** on the scripted interactions (§4.6), with per-route JS and CSS budgets enforced in CI. Every number in this document that was taken on loopback desktop Chrome at 4× CPU is directional only; the device checkpoint (§4.7) is where budgets get set.

### 1.2 Invariants that must not regress
Child-safety walls, never-diagnose neutrality (ro ADR-0001), DRAFT/PUBLISHED content lifecycle (ro ADR-0012), cohort gates and moderation (social), GDPR erasure, consent, auth, CSP (strict, nonce-based; zero violations at every stage and **enforced** in the test env from the milestone §4.4 names per app), a11y (focus, contrast, reduced motion, axe fingerprint), localStorage key names, CSRF names (`csrftoken` / `X-CSRFToken` / `csrfmiddlewaretoken`), `ReadingComfort` never on timed or psychometric surfaces.

### 1.3 Behaviour policy
Default is **parity**. A perf-driven UX change (e.g. local feedback from the shipped `correct` flag, overlap transitions in cat) is allowed only with before/after numbers in the ExecPlan Decision Log and, where it touches a child-facing surface, Paul's sign-off.

### 1.4 Non-goals
`/admin/` (CSP exemption scoped there), escrow bytes, `qdollar`, screening constants and answer keys, the service-worker **logic** of `sw.js` (its template engine is ported, §7.6), the 5 email `.txt` files (never rendered by the Go server; contract handling in §7.6) (ro); media/processing pipeline, e2ee crypto internals, ingestion, `meetups-worker.js`, moderation decision logic, accounts policy (social); `asyncControl`, `scores`, `api/*`, the 8-char hash convention (cat); the `rdu-` class rename (2.0), Terrazzo, `useFlip`, a distroless social image, upgrading the production Postgres major, htmx/Datastar, Svelte/Solid, pnpm.

## 2. Architecture per layer

### 2.1 Server templates — full templ port with pongo2 fallback
- Engine today: pongo2 v6.1.0 in all three Go modules. Target: **templ v0.3.1070** (resolved; re-resolve per §3) for every existing template in ro_teacher and social, converted by `djt2templ`, judged by a golden-HTML oracle, served through `webkit/engine` with per-route modes `Pongo2 | Templ | Shadow` and a committed `engine.json` (§7.4). cat has no pongo2 templates.
- Ordering per app: delivery milestone (M1, on pongo2: `embed.FS` via `NewFSLoader`, nonce from ctx, inline script/style externalised, compression) → golden capture → port route groups low-risk first → child-safety groups last with human review → one release on `Templ` with shadow-zero (prod via `<APP>_TEMPL_ROUTES`, `engine.json` `prod` stays `Shadow`; §7.6 definition) → delete pongo2 file + contract entry → pongo2 removed from the app at the end of its B-session, when **every** group has met the criteria (§7.6); a group that cannot meet them is a hard stop for Paul, never a carry-over.
- Streaming is a per-route measured opt-in with a mid-render-error test; the `httptest.NewRecorder` at ro `server.go:210,386` stays (atomic 500s, headers after render).
- Full design, mapping table, typing, runtime and risks: §7.

### 2.2 Interactivity tiers
| Tier | What | Cost | Rules |
|---|---|---|---|
| T0 platform | real `<form method=post>` + PRG, `<details>`, `<dialog>` with `command`/`commandfor` (0.5 KB shim for Samsung Internet <29 / Chromium <135), `popover`, `@view-transition { navigation: auto }` as progressive enhancement (absent on Samsung Internet ≤30, partial Firefox 144+), nonced `speculationrules` **moderate prefetch, never prerender**, `content-visibility:auto` | 0 KB | first choice everywhere |
| T1 light-DOM custom elements | `<roedu-*>` and app `<so-*>` elements found by the islands loader (≤1.1 KB gz; `import()` on `eager\|visible\|idle\|interaction`; props from nonced JSON script; failure ladder chunk-fail → keep server HTML → optional legacy script) | 0.5–3 KB each | vanilla TS, no framework; Trusted Types for any HTML sink |
| T2 Preact 11 islands | replace a same-size server skeleton in one `replaceChildren` inside a rAF; `min-block-size` reserved; CLS 0; **no hydration** | runtime ~5 KB gz (re-measure on 11, §10 S0a) | only where state or interaction demands it |

htmx and Datastar are rejected (13.0 KB gz measured, htmx 4 on npm `next`); T0 + T1 fragment fetch covers the need.

### 2.3 Client framework — Preact 11
- **Preact 11.0.0** (latest stable, 2026-09-30), `preact` / `preact/hooks` only; `@preact/signals` 2.11.3 opt-in per island; `preact-iso` 2.12.2 for cat only; `preact-render-to-string` 6.8.0 is a **required peer of preact-iso** (`>=6.4.0`, verified with `npm view`; npm installs it automatically), so cat always has it: pinned in `versions.lock.json`, covered by `versions:check`, imported only by tests.
- Banned imports (Oxlint `no-restricted-imports` + ast-grep): `react`, `react-dom`, `preact/compat`, `framer-motion`, `react-router*`, `@types/react`. `framer-motion@14.0.0` is a **hard dependency of `motion`**, so the lockfile check asserts `motion` is its only dependant and `@types/react` is absent; the ban is on imports, not on lockfile presence. The only exemption is the frozen legacy bundle path `embedfs/legacy/` (§8.2 frozen-legacy mechanism): prebuilt, minified artefacts that no lint, tsc or lockfile check walks.
- **v11 lint** (replaces the old "Preact-11-ready grep gate"): no `defaultProps`; no `useRef()` without an argument; no numeric `style` value without a unit (v11 dropped auto-`px` outside compat); no `forwardRef` (refs forward by default); no `render(_, _, replaceNode)`; no `Component.base`; no `JSX.HTMLAttributes` (use `preact.ButtonHTMLAttributes<HTMLButtonElement>` etc. — this is the fix for the spikes' 9–11 tsc errors).
- Semantics that matter for tests: `useEffect` cleanup is deferred until after paint; hook deps compare with `Object.is`. Presence/Confetti browser tests are written against these, not 10.x.
- Packaging ESM-only; browser floor Chrome 71 / Safari 12.1 / Firefox 69; TS ≥ 5.1. No audience change.
- Testing: plain `render()` + `@vitest/browser-playwright` locators + `page.getByRole`. `vitest-browser-preact` (peer `preact ^10`) and `@testing-library/preact` (2024, `@testing-library/dom ^8`) are **not used**.

### 2.4 Widgets — bundle first
Phase A for every app, zero behaviour change: each `static/js` file becomes a Vite entry (hashed, minified, `immutable`, nonce-loaded, counted in budgets); `thread-chat` imports `presend-nudge`; sockets close on `pagehide`. Measured: hovercard 1,722 → 802 B gz is minification, not stack; a signals rewrite of the combobox cost 2.6× and needed a 15-step canonical-DOM harness to catch three parity drifts. Phase B (rewrite) only where the §8 maps list it. Domain engines are framework-free TS with Vitest browser tests: `speech-core` (keeps `window.roSpeak`, claim-before-scan order), `trace-core`, `recorder-core` (`LIVE_EVERY_MS` 2200), `screen-clock`, `qdollar`, `e2ee-core` (crypto verbatim, known-answer tests), `ws-thread`, `certificate-export`.

### 2.5 Animation
CSS first (`@starting-style`, transform/opacity only, `data-motion` + `prefers-reduced-motion`), cross-document View Transitions where supported, same-document ≤200 ms transitions in cat. cat uses `@roedu/ui/motion`: in-house `<Presence mode="wait">`, `useIsPresent()`, `Confetti` (WAAPI, browser-tested in core, never regenerated per app); springs and `animateHeight` via **`motion/mini` `animate` + `spring`** from `motion` 14.0.0 — measured **5,078 B gz / 4,685 B br** (esbuild 0.28.2; the Vite 8/Rolldown figure is re-measured in S0a). Both opacity and transform run as WAAPI animations so `document.getAnimations()` stays truthful for cat's `accessibility.spec` wait. `useFlip` is cut; cat's five `layout` props animate 0 tiles in production (`App.tsx:72` uses `LazyMotion features={domAnimation}`; `layout` needs `domMax`, +13,134 B gz) and are dropped.

### 2.6 Routing and state
ro_teacher and social: MPA, no client router. cat: preact-iso `Router`/`lazy`/`ErrorBoundary`; the Go `index.html` history fallback and 8-char immutable hash regex (`website.go:23`) stay. State is server-authoritative; island-local hooks; module-level signals only for cross-island state; localStorage keys byte-identical and registered in core `storage/`.

### 2.7 i18n
Server-side only, 0 KB client runtime. templ pages use `webkit/i18n` `T/TA/TB/TN` with the **trusted-msgid rule** (§7.2.6): trans literals and catalogue msgstrs are trusted developer strings rendered raw; only interpolations escape — identical to what both Go servers do today (social `templates.go:201-234`). Catalogue lint in `gate:unit`. Islands get pre-translated strings as props.

### 2.8 Design system — roedu-ui 1.0
Explicit toolchain jump first (today React 18.3 peers, Vite 6.4.3, TS 5.9.3, vitest ^2, vite-plugin-dts → Vite 8.3.3, TS 7.0.2, Vitest 5.0.3, React peers dropped, declarations via `tsc -b`). `tokens/`: one DTCG JSON + a ~60-line generator → `tokens.css`, `theme-{teacher,cat,social}.css`, `tokens.ts`, `tokens.go`. `css/`: `@layer reset,tokens,base,components,utilities,app` on the **existing `roedu-` prefix** with a reserved-class list (ro's 46 local `roedu-spa*` classes are the collision to resolve). `preact/`: Button/Card/Stack/Container/Field/Input/Select/Checkbox/Radio/Dialog/Tabs/Badge/Spinner/Skeleton/ErrorBoundary/ToastHost/ReadingComfortBar, CSP-safe (ADR-0002: no `style` attributes; `useCspSafeStyle`). `behaviors/`: islands loader, invoker shim, `<roedu-hovercard>`, `<roedu-wizard>`, `<roedu-meter>`, `<roedu-speak>`, `<roedu-comfort>`, `<roedu-combobox>` on Zag vanilla 1.45.0 only if the 15-step parity harness is green. `motion/`, `net/` (fetch + CSRF + AbortSignal), `storage/`. No React package.

### 2.9 web-kit — build/test/deploy kit, inside the roedu-ui repo
`roedu-ui/web-kit/` is both npm `@roedu/web-kit` and Go module `github.com/DobosP/roedu-ui/web-kit` (one directory, two ecosystems, one `core-v1.N` tag). Go packages: `assets static csp island health golden i18n routes engine vm tmplfn ui lint` + `cmd/{djt2templ,golden,budget}`. npm: `vite-preset`, `budget`, `playwright`, `lint` (incl. the vendored `check_docs.py`, §6), `templates/{Dockerfile,Dockerfile.toolchain,compose.gate.yml,compose.test.yml,Taskfile.yml,.gate.env,gate.sh,ci,.codex,AGENTS-block.md}`, `scripts/resolve-versions.sh`. The wrapper lives **only** at `web-kit/templates/gate.sh`; every consumer's `scripts/gate.sh` is a byte-identical copy (`kit:check` in `gate:unit` verifies it, §9-8). Why same repo: one tag pins the island protocol on both sides and the gate contract; a new repo needs a remote + `fleet.json` entry (Paul-only) and a fourth review surface. Distribution: consumers vendor the two npm tarballs under `frontend/vendor/` and the Go sources under `<module>/third_party/webkit` with a `replace` directive, written **only** by `task kit:sync` from the committed `kit/` staging path that Paul lands per core tag (one protocol, §9-8); `gate:unit`'s `kit:check` fails on any drift between `kit/SHA256SUMS`, the vendored files and the gate-file copies. The template Taskfile includes a repo-owned `Taskfile.repo.yml` for the app's own gate steps, which `kit:sync` never touches. **Embed layout:** every Go module is a subdirectory and `go:embed` cannot reach `..`, so `task assets:sync` copies templates and `dist/` into an in-module `embedfs/` dir (committed `.keep` + `//go:embed all:...`); `gate:unit` depends on it.

### 2.10 Deploy
One `CGO_ENABLED=0 go build -trimpath` binary per app, assets embedded and precompressed (br + gz; no zstd — Samsung Internet lacks it). Dockerfile template stages: (1) `node:26.10.0-trixie-slim@digest` (`npm i -g npm@12.2.0`, `npm ci`, `vite build`, emit `.br`/`.gz`); (2) `golang:1.27.1-trixie@digest` (`task assets:sync`, `templ generate -check`, build); (3) per-app base: ro and cat `gcr.io/distroless/static-debian13:nonroot` (cat drops curl via a `healthcheck` subcommand); **social `debian:13.7-slim`** + ffmpeg (`7:7.1.5-0+deb13u1`), libavif-bin, util-linux, perl-base, because `app.go:195` calls `CheckRuntime()` unconditionally and media processing runs on the request path (`process.go:70-72`); `media-worker` runs the same binary with `--job transcode_videos`; the systemd tarball comes from the same stage. Every base pinned by digest in `versions.lock.json`. The same image runs in `compose.test.yml`, staging and prod. SBOM/provenance attestations are CI-only.

## 3. Toolchain and versions

### 3.1 Policy — latest stable, resolved at session start
- **Latest stable** = npm `latest` dist-tag / highest non-prerelease semver; Go = newest `go1.X.Y` marked stable at `go.dev/dl/?mode=json`; Go modules = `proxy.golang.org/<m>/@latest`; images = newest non-prerelease tag, pinned **by digest**. Never `next|rc|beta|alpha|canary|experimental|dev`.
- Linux host packages (docker engine, apt) are **environment**, not program tools: pinned by Paul, outside this policy.
- Resolution protocol: the wrapper's **`gen --resolve-versions`** (the only trigger; it sets `GATE_VERSIONS_RESOLVE=1`, under which `task gen` runs `versions:resolve` then `deps`, and syncs back `versions.lock.json` + `package.json`/`package-lock.json`/`go.mod`/`go.sum`, §4.2) runs the web-kit resolve script in the runner (needs network) and writes `versions.lock.json` entries `{tool, kind, scope, version, source, date, digest?, exception?, approved_by?}`; the diff is committed as `chore(versions): resolve <date>` and copied into the ExecPlan Decision Log. Allowed **only** at (a) session M0, (b) immediately after a `KIT_BUMP` (§9-8); there is no `versions:resolve` wrapper target. `task versions:check` (in `gate:unit`) fails if any `package-lock.json` / `go.mod` / Dockerfile / `.nvmrc` disagrees with the lock, or if any resolved version is lower than the lock (no silent downgrades).
- `.npmrc` contains exactly `save-exact=true` and `engine-strict=true` (npm 12 throws on unknown keys). `.nvmrc` = `26.10.0`; `engines.node = ">=26.10.0"`, `engines.npm = ">=12.2.0"`.
- Seed table with sources and dates: **Appendix A**. S0a re-resolves it on 2026-10-xx and every later session re-resolves at its M0.

### 3.2 Recorded exceptions (each needs a Decision Log line; re-check at every resolution)
| Tool | Taken | Reason |
|---|---|---|
| `@babel/core` | 7.29.7 (newest 7.x) | `@preact/preset-vite` 2.10.6 peers `@babel/core 7.x`; 8.0.6 fails peer resolution |
| `oxfmt` | excluded | 0.72.0 is beta on 0.x → prettier (latest) as a devDependency for TS/CSS, run via `npm run`, never global |
| `leaflet` | 1.9.4 | 2.x is alpha only |
| `@zag-js/*` | 1.45.0 | 2.x is `next` only |
| `pongo2` | v6.1.0 | v7 is alpha; removed at the end of the port anyway |
| `@lhci/cli` | 0.15.1 (Lighthouse 12.6.1) | stale; **advisory only**, never a gate |
| `axe-core` | 4.14.0 via `AxeBuilder({axeSource})` | `@axe-core/playwright` 4.13.0 depends on `~4.13` |
| `vitest-browser-preact`, `@testing-library/preact` | not used | peer `preact ^10` / unmaintained |
| `@typescript/typescript6` | 6.0.2, only if a tool needs the TS JS API | TS 7.0.2 has no stable programmatic API until 7.1; none planned |
| Postgres | **`PROD_PG_MAJOR = 16`** (Paul fills) — **deviation §0.4-5, needs Paul's ACK** | test env must match the production server's major; 18.6 is adopted only if prod is 18; upgrading prod is a non-goal (§1.4) |
| `@playwright/test`, `playwright`, `mcr.microsoft.com/playwright:v1.63.0-noble` | 1.63.0 / `v1.63.0-noble`, **pinned as one unit** — **deviation §0.4-4, needs Paul's ACK** | screenshot baselines depend on the exact browser build; the three move together only in a `GATE-CHANGE: baseline recapture` with a new toolchain tag, never at an app's M0 (1.63.0 is also npm `latest` on 2026-10-06) |
| `pa11y-ci` | 5.0.0 kept in ro `go-browser-tests.sh` only | pulls puppeteer 25 + its own Chrome; not added to `gate:unit` |
| `preact-render-to-string` | 6.8.0 (transitive, required peer of `preact-iso` 2.12.2 `>=6.4.0`) | present in cat's lockfile whether or not a test imports it; pinned in `versions.lock.json` and checked by `versions:check` like a direct dependency |
| Linux host Docker / Buildx / Compose | 29.5.3 / 0.34.1 / 5.1.4 — deviation §0.4-2, ACK pending | environmental stack, separately provisioned by Paul; no global changes in workers |

### 3.3 Breaking-change checklists (apply in each M0)
- **npm 12.2.0:** unknown `.npmrc` keys and abbreviated/unknown CLI flags throw → audit every `.npmrc` and script; `allow-git`/`allow-remote` default `none` (whether `file:` vendor tarballs are affected is **unverified** — S0a M0 proves it with the kit tarball install); `npm view --json` always returns an array; `npm-shrinkwrap.json` ignored; root `preinstall` runs before dependencies install.
- **TS 7.0.2:** removed `target es5`, `downlevelIteration`, `moduleResolution node/node10/classic`, `module amd/umd/system/none`, **`baseUrl`** (use relative `paths`); `esModuleInterop`, `allowSyntheticDefaultImports`, `alwaysStrict` can no longer be `false`. Today's three app tsconfigs use `moduleResolution: bundler` and no `baseUrl`; only ro's compat `paths` (`react` → `preact/compat`) changes (deleted, S2A M0). roedu-ui's `vite-plugin-dts` → `tsc -b` declaration emit; dts parity is **unverified** → S0a M0 d.ts snapshot test.
- **Vitest 5.0.3:** Node 22+, Vite 6.4+; browser providers are separate packages (`@vitest/browser-playwright` is the one used); mocks cleared before each test; `browser.locators.exact` true; `toHaveTextContent` strict (`toMatchTextContent` loose); un-awaited async assertions fail; `sequential` removed; config not looked up in parent dirs (each package has its own `vitest.config.ts`); reports default to **`.vitest/`** → gitignored in every repo.
- **Vite 8.3.3 / Rolldown 1.2.12:** budget attribution uses `output.codeSplitting` (`advancedChunks` deprecated, ignored when both set); peer `esbuild ^0.27 || ^0.28`.
- **Preact 11.0.0:** §2.3 list; `render()` lost `replaceNode`; "Hydration 2.0" unused (no hydration here).
- **Motion 14.0.0:** `motion/mini` exports only `animate` and `animateSequence`; `spring` from `motion` (tree-shakes); hard dep on `framer-motion@14.0.0`; React peers optional.
- **MapLibre 6.12.0:** ESM-only (`import * as maplibregl`); WebGL2-only (`GPUInitializationError` thrown and on `.on("error")` → list fallback); worker is a real URL (`setWorkerUrl()` once; CSP `worker-src 'self'`, `img-src data: blob: 'self'`); `styleimagemissing` notify-only → `setMissingStyleImageResolver`; `map.transform` removed; event `type` field not `instanceof`; `GeoJSONSource.setData` one arg; `zoomLevelsToOverscale` default 4; nested GeoJSON properties are objects; style-spec 26 may warn/throw on the remote OpenFreeMap style (S3A M2 tests it). Size gz: main 151,515 + shared 147,057 + worker 6,154 = **304.7 KB** + CSS 10,487. Advisory **GHSA-jrc7-96c5-q579 / CVE-2026-85061 confirmed** (CVSS 10.0, CWE-79, zero-click XSS via attribution `DOM.sanitize()`, affects ≤ 6.4.0 incl. 5.24.0, fixed 6.4.1).
- **templ v0.3.1070:** `go get -tool github.com/a-h/templ/cmd/templ@v0.3.1070` (Go ≥1.24 tool directive; module needs `go 1.26.0`); `templ generate -check`, `templ fmt -fail` exist; new: `.templignore_*`, Go comments in attributes, prettier applied to constant attribute values. **Gotcha:** `templ fmt` shells out to prettier when on PATH and silently skips otherwise → the gate pins `-prettier-required=false` and keeps prettier **off** the toolchain image PATH.
- **Node 26.10.0** (Current line; LTS on 2026-10-28) bundles npm 11.19.1 → `npm i -g npm@12.2.0` in the toolchain image.
- **Docker on native Linux:** installed tools work under scoped approval, while the active sandbox denies the Unix socket. Owner-reviewed absolute wrapper invocation is the product gate path. No engine/package upgrade is performed by a worker.

## 4. Gates and environments

### 4.1 Topology

Native worktree `/home/dobo/work/_worktrees/<repo>/<slug>` → `scripts/gate.sh` →
rsync copy `/home/dobo/work/_temp/<slug>/gates/<repo>` → pinned container runner.
`.gate/<target>/` and the per-target generated files return to the worktree.
Trust remains owner-owned at `~/gates/trust`; immutable image archives at
`~/gates/toolchain`. Scratch is inside the registered `_temp` root, never host `/tmp`.

The copy excludes `.git node_modules .gate .vitest dist frontend/dist test-results`,
secret `.env*` inputs and dispatcher artifacts. Unexpected ignored files fail before
copying. Unexcluded symlinks fail closed. No source contents outside the worktree
are read by the gate. All script/text files must be LF; native `git ls-files --eol`
checks existing attributes without modifying or renormalizing evidence.

One gate per worktree, enforced by flock. Compose project/app-image identity includes
repo, slug and a 12-hex hash of the canonical worktree path; no normalization aliases.
Shared named caches are `roedu-gocache roedu-gomodcache roedu-npmcache roedu-pwcache`.
The runner has no Docker socket or host credentials mounted. Product builds use an
owner-provisioned `roedu-gates-linux` Buildx builder, inspected before each build for
8-CPU/10GiB limits, amd64 only. The test prep builder has a separate name.

Node, Go and the frozen Playwright base are checksum/digest verified. Gate `.gate.env`
and `versions.lock.json` retain unresolved production fields until Paul supplies the
production PG major and pins the built image ID. Synthetic PG16 build IDs stay in
the preparation report and never populate production pins. A pinned tag is never
rebuilt: new toolchain → new tag → owner digest commit → trust → kit propagation.

Native Git verifies actual HEAD and cleanliness. `--dirty` is inner-loop evidence;
owner `trust/toolchain` refuse it. Tree hashes include relative filenames, executable
mode and file bytes, with exactly the copy exclusions. Reviewer recomputes with the
same wrapper version on a clean fresh copy; Windows and Linux hash algorithms differ.

### 4.2 Wrapper contract — `scripts/gate.sh`

The reviewed `bootstrap/gate.sh` is copied byte-identically into each bootstrap and
later `web-kit/templates/gate.sh`. The script is the source for exact behavior.

```
bash /absolute/worktree/scripts/gate.sh <target> --sha <literal HEAD> [--dirty] [--parallel N] [--fresh] [--resolve-versions] [--keep] [--tag roedu-toolchain:<new>]
```

Closed targets are `unit full gen deps kit:sync build image baseline golden:capture
golden:verify contract:refresh legacy:freeze e2e perf`; owner-only `qualify shell
toolchain trust` and `--keep` require ephemeral `GATE_OPERATOR=paul`. `kit:sync`,
`e2e` and `perf` remain Paul-only by policy/rules, even though the parser accepts them.
No worker sets wrapper environment variables. `--resolve-versions` is `gen` only at
M0/KIT_BUMP; `--tag` is `toolchain` only. Parallelism may only decrease from the
committed cap (1–4). SHA/dirty claims are checked against native Git before copying.

The wrapper validates canonical paths, storage/lock/evidence symlink absence and
unexpected ignored inputs; obtains flock; clears stale result; rsyncs; computes
source hash; and confirms no edit occurred during copy. `.gate.env` is literal LF
KEY=VALUE, never sourced. All eleven keys must occur once, including empty values;
unknown/duplicate/missing keys fail, and inherited committed-key values are reset.
Compose uses explicit `--env-file .gate.env` and no unit DSN/app URL. Full-profile
targets require resolved PG/database values and a real app Dockerfile. Unit never
starts DB/app; full explicitly starts them with `up -d --wait`, then `run --no-deps`.

Trust pins cover exactly four regular files: `scripts/gate.sh .gate.env
compose.gate.yml Taskfile.yml`, including executable mode and bytes. Missing files
fail. Only Paul pins reviewed clean contents. Every other target except the owner
new-image build requires a matching pin and local toolchain image ID. New-image
build requires clean roedu-ui, a new unpinned/absent/unsaved tag and capped builder.

Protected hashing includes the original anti-gaming set plus `versions.lock.json`,
`Taskfile.repo.yml`, `kit/`, `engine.json` (including nested module copies),
`.gitattributes`, `AGENTS.md`, `docs/PROGRAM.md` and `.agent/PLANS.md`. Changes to
content, executable mode, creation/deletion or symlink replacement invalidate the
result and exit 3. Captures permit only their named generated artifact set. A
`gen --resolve-versions` permits the lock; `kit:sync` permits only kit contract files
and lock/env. A worker may never use these allowances to write owner sign-offs.

Before any generated source returns, the wrapper validates schema-1 identity,
SHA/dirty/tree hash, executing image ID, post-task lock SHA, parallelism, CSP stage,
nonnegative counts, zero nonlegacy CSP violations on pass, no failed budget and
skip policy. Process and JSON failure states cannot return success. Missing or
invalid required evidence exits 5; substantive targets with no result never pass.
`image/qualify/shell` remain host operations: exit 0 alone never attests a migration
gate. Fresh source hash must still match before sync-back; otherwise exit 4 with
no overwrite. Any sync failure removes pass evidence. Final evidence is published
only after sync-back; failures carry `wrapper-fail.json`. Nonzero tasks never copy
generated source. Compose teardown runs on exit unless Paul requested `--keep`.

Per-target sync-back remains:

| Target | Generated paths |
|---|---|
| gen | SYNC_BACK + `*_templ.go routes_gen.go vm_gen.go tokens.css theme-*.css tokens.ts tokens.go`; lock/dependency files only with `--resolve-versions` |
| deps | SYNC_BACK + `package.json package-lock.json go.mod go.sum` |
| kit:sync | four gate files + `vendor/*.tgz vendor/*.tgz.sha256 third_party/webkit/** versions.lock.json` and dependency files |
| golden:capture | `testdata/golden*/** golden/testdata/**` |
| contract:refresh | `internal/contract/assets.json` |
| legacy:freeze | root `legacy/**` |
| baseline | `baselines/**` |
| other | evidence only |

A successful kit sync carries only valid `TOOLCHAIN_IMAGE/DIGEST` lines into the
source `.gate.env`; all other bytes are preserved. Exit codes: task 0/1; refusal 2;
protected mutation 3; sync/source conflict 4; invalid/missing result 5.

Bootstrap Taskfile is **smoke-only**: `bootstrap:smoke` is a direct test-container
reachability check. `gate:unit/full`, resolution, generators, sync and captures
explicitly fail until implemented. Bootstrap emits no invented migration
`result.json`, CSP count, budget/golden/browser parity or zero-skip claim. S0a's
initial smoke is not a milestone pass; real gate bodies must exist by their named
boundaries and match each session's required checks table.

### 4.3 `result.json` (written by `task`, never by the wrapper)
```json
{"target":"unit","status":"pass|fail","sha":"…","dirty":false,"tree_sha256":"…","toolchain_digest":"sha256:…",
 "versions_lock_sha256":"…","parallel":4,"started":"…Z","finished":"…Z",
 "checks":[{"name":"go-test","status":"pass|fail|skipped","reason":"no-dsn|no-device|…","duration_ms":0}],
 "csp":{"stage":"report-only|enforced","violations":0,"legacy_violations":0},
 "budgets":{"<route-or-entry>":{"limit":0,"actual":0,"status":"pass|fail"}},
 "artifacts":["…"]}
```
`gate:unit` may contain `skipped` only with reason `no-dsn` or `no-device`; **`gate:full` fails if `skipped > 0`**. `.gate/` is gitignored. Codex quotes the path and `status` of `result.json` in every milestone status; a result with `dirty:true` is inner-loop evidence only and never satisfies a milestone boundary or a `GATE-CHANGE:`. Claude Code re-runs from a clean checkout at `sha` (`--fresh`) and compares `tree_sha256`, `toolchain_digest`, `versions_lock_sha256`; any mismatch stops the review (a different `tree_sha256` for the same `sha` means Codex gated a tree that is not the commit).

### 4.4 Targets
| Target | Runs (inside runner unless noted) | Who | Time |
|---|---|---|---|
| `gen` | `templ generate`, `routes.Gen`, `djt2templ` for the group (selected by a committed request file, never an argument), tokens generator → sync-back (§4.2 step 10); with `--resolve-versions` (M0 / `KIT_BUMP` only) also `versions:resolve` + `deps`, syncing back `versions.lock.json` and the dependency files | Codex | s–min |
| `deps` | `npm install --package-lock-only --ignore-scripts` per `package.json` and `go mod tidy` per `go.mod` from the hand-edited manifests → sync-back of `package.json package-lock.json go.mod go.sum` (+ `SYNC_BACK`); the only sanctioned lockfile writer | Codex | min |
| `kit:sync` | vendor the two npm tarballs, copy the Go kit, refresh the gate-file copies, merge `versions.lock.json`, run `deps` — all from the committed `kit/` staging path (§9-8); may rewrite the trust-pinned files, so the next gate waits for Paul's `trust` | **Paul** (§9-8; the wrapper and the §5.2 sentence accept it from Codex, the protocol never needs it) | min |
| `golden:verify` | `cmd/golden verify` (replay + coverage report) over the committed goldens without PG; full-profile Live is in `full` | Codex | min |
| `unit` | `versions:check`; `kit:check` (§9-8); tsc 7 strict; Oxlint + tsgolint + ast-grep (v11 lint, restricted imports, `templ.SafeURL(`, `style=`, `on*=`); Vitest browser (headless Chromium); `go vet`; `go test -race ./...` (PG-gated → `skipped no-dsn`); `templ generate -check`; `templ fmt -fail -prettier-required=false`; `rawcheck`; `i18n.Lint`; golden **replay**; `TestRouteBudgets` vs `budgets.json`; docs gate (vendored `check_docs.py`, §6); ro `teacher-go check --repo ..`; cat `cat-doc-check` + `cat-content validate/export --check`; social `check-native.sh <go>` | Codex inner loop | ~3–8 min (estimate) |
| `full` | `unit` + compose `db` (PROD_PG_MAJOR; social: PostGIS + pgvector image rebuilt from the kit template) + migrate/seed + `app` (prod image from the worktree) + PG-backed Go tests with DSN (ro `go-pg-tests.sh` in-runner with `initdb`: `compose.gate.yml` sets `HOME=/home/runner` and `TEACHER_GO_PG_SCRATCH_ROOT=/tmp/_temp/teacher-go-pg` — writable, contains `/_temp/`, short enough for the script's 89-char socket limit, pre-created `chmod 1777` in `Dockerfile.toolchain` because the runner is `--user $(id -u)` with no passwd entry; social `-web-domain-test-dsn`) **fail on any skip** + golden **Live** + shadow-zero + Playwright journeys (`motion-on` project) + screenshot parity vs committed baselines + axe fingerprint + **CSP trap, staged per app**: stage A (from each app's M1) = strict nonce-based policy in **report-only**, violations collected through `report-to` / the Reporting API endpoint `csp.Report` and through the browser console in Playwright, `csp.violations == 0` required; stage B (from the milestone named here: **cat S1 M1, ro S2A M2, social S3A M2**) = the same policy **enforced** in the test env (`<APP>_CSP_ENFORCE=true`; social's existing `DJANGO_CSP_ENFORCE`), still zero violations, and a journey that fails under enforcement fails the gate; legacy-bundle journeys (`CAT_UI=legacy`, `RO_TEACHER_REACT_UI`, `SOCIAL_REACT_UI`) run under the same policy and report `csp.legacy_violations` separately (advisory — the frozen bundle cannot be edited; a prod rollback to legacy also rolls CSP back to report-only) + web-vitals 6 at 4× CPU / 150 ms RTT / 1.6 Mbps (LCP < 2,500, INP < 200 on scripted interactions) + Lighthouse advisory | Codex at milestone boundaries; Claude Code at review | 15–40 min (estimate) |
| `build` / `image` | `vite build` → `assets:sync` (unpacks `legacy/*.tgz` into `embedfs/legacy/`, SHA-checked) → `go build`; `docker build` (host-side buildx, `--no-cache` on dependency changes), digest-pinned bases | Codex / Paul | min |
| `toolchain --tag roedu-toolchain:<new>` | host-side `docker buildx build --load --build-arg PG_MAJOR -f Dockerfile.toolchain -t <new>` from a clean roedu-ui worktree, before the trust check; refuses a pinned/present/saved tag, saves the `.tar`, prints `TOOLCHAIN_IMAGE=`/`TOOLCHAIN_DIGEST=`; Paul records both in `.gate.env`, `web-kit/templates/.gate.env`, `versions.lock.json` as one `GATE-CHANGE: toolchain <tag>`, then `trust` + `unit` | **Paul only — wrapper-enforced** (`GATE_OPERATOR=paul` in the single owner invocation; Codex cannot set it, §5.2) | min |
| `trust` | pins the sha256 of the four gate files (`scripts/gate.sh`, `.gate.env`, compose file, `Taskfile.yml`) under `~/gates/trust/`; required before any other target runs on changed gate files; clean commit only | **Paul only — wrapper-enforced** | s |
| `baseline`, `golden:capture`, `contract:refresh`, `legacy:freeze` | generate GATE-CHANGE artifacts from the current tree (screenshots, axe, sizes, vitals; goldens + ctx.json incl. the pre-M1 set; ro `assets.json`; the frozen legacy tarball from the parent commit's frontend, §8.2) | Codex only inside a `GATE-CHANGE:` commit Paul re-runs | min |
| `qualify` (social) | `qualify-native.sh $QUALIFY_ARGS` 21 lanes + Trivy + govulncheck (versions re-resolved), host-side; the review protocol (09 §2.1) runs it with per-review values instead of the wrapper target | Paul/Claude Code before landing — Paul-only in the wrapper | long |
| `e2e`, `perf`, `shell` | subsets of `full`; `shell` = interactive runner (`bash`) | `e2e`/`perf` Paul by policy; `shell` Paul-only wrapper-enforced | — |

### 4.5 Who runs what; fallback ladder

Workers edit/commit only their assigned worktree. Product builds/tests run in the
pinned container through `bash <absolute worktree>/scripts/gate.sh <allowed target>
--sha <literal>`. Read SHA/status separately first. If sandbox socket/storage access
is denied, request scoped `require_escalated` with `Linux gate (Paul-authorized)`.
No worker requests a generic Docker, shell or host-toolchain allow rule.

The candidate rules enumerate the absolute script path and allowed target tokens.
Owner targets are forbidden in worker rules. Prefix rules are not a filesystem
integrity boundary; the editable wrapper and appended arguments still require
closed parsing, trust review, protected hashing and clean fresh reviewer reruns.
Scoped read-only Docker escalation succeeded during preparation. That does not
prove a future trusted bootstrap invocation or grant broad host rights.

Fallback: record `GATE PENDING <target> sha=<sha> | <reason>` in Progress and
GATE_REQUESTS; continue independent preparation. Parent/Paul may run the exact
wrapper and relay evidence, or explicitly move the worker to CLI and re-prove the
same shape. No Full access, bypass flag, host npm/Go install, global policy edit
or secret-store access. Unavailable evidence remains unavailable.

### 4.6 Budgets (`budgets.json`, Paul-owned, read-only to Codex)
```json
{"schema":1,"measured_at":"<sha>","js":{"server-page":{"limit_gz":10240},"island-route":{"limit_gz":35840},
 "cat-initial":{"limit_gz":40960,"target_gz":30720},"vendor-gated":{"maplibre":{"limit_gz":317440}}},
 "css":{"global":{"limit_gz":<measured baseline or null>}},"routes":{"<route>":{"class":"server-page|island-route","islands":[],"widgets":[]}},
 "vitals":{"lcp_ms":2500,"inp_ms":200,"throttle":{"cpu":4,"rtt_ms":150,"down_kbps":1600}}}
```
This is the schema of the shipped `bootstrap/budgets.json` (`measured_at: null`, `routes: {}`, one `css.global` entry — there is no per-layout CSS key); the budget tool's schema (S0a M5) must validate that committed file unchanged, and a `null` limit means "record the actual size, never fail silently and never pass silently" — `TestRouteBudgets` accepts it and reports the number. JS classes are **estimates until the device checkpoint** (server pages ≤10 KB, island routes ≤35 KB, cat initial ≤40 KB target 30 KB; MapLibre ratchet 310 KB from the measured 304.7 KB). **CSS ratchets** (`css.global.limit_gz`) start at measured baselines (social 16,954 B gz = `base.css` 14,891 + vendored roedu-ui 2,063; ro 16,807 = `app.css` 10,575 + SPA CSS 6,232; cat and roedu-ui `null` until their M0 baseline capture) and tighten only after that app's CSS-consolidation milestone, via `GATE-CHANGE:`. `TestRouteBudgets` walks the Go route table (ro 399, social 155, cat ~10) summing islands + widgets + global CSS + eager vendor per route. Scripted INP interactions: StepRunner trace, Alchimie combine, Conexiuni select, chat send.

**Where "budgets in CI" (Decision 8) runs.** `TestRouteBudgets` is part of `gate:unit`, which every milestone commit and every review runs on Linux through the wrapper; that WSL run **is** the program's CI for the apps. GitHub Actions wiring exists only in roedu-ui (`web-kit/templates/ci.yml`, S0a M5: `push`/`pull_request`/`workflow_dispatch` → toolchain build → `task gate:unit` incl. `TestRouteBudgets`). No app session edits its GitHub workflow: ro's is `workflow_dispatch`-only by ADR-0075, cat's and social's keep their current triggers; adopting the kit `ci.yml` in an app is Paul's own commit after the session (recorded as an ADR there), listed as deviation §0.4-6.

**Cat startup accounting — accepted 2026-10-08, source amendment unapplied.** The frontend's 120 KiB (122,880-byte) combined JS/CSS check counts all entry/static closures plus the immediately mounted AccountBar and its recursive static JS/CSS dependencies, with shared files and cycles counted once. Mandatory manifest roots/imports and emitted JS/CSS assets must exist; game routes and further dynamic children stay excluded. Default helper callers and frozen historical per-key closures retain their static-only scope. This does not replace the canonical cat-initial 40,960-byte JavaScript ceiling/30,720-byte target or separate CSS policy. Fresh startup measurements and Linux qualification remain pending; no threshold, phase or device condition changes. Decision: cat_de_roman_esti/docs/adr/0185-accepted-eager-startup-bundle-accounting.md.

### 4.7 Device checkpoint (hard stop)
After each app's M1 delivery milestone Paul measures LCP/INP on one real Samsung A-series phone over throttled 4G in Chrome and Samsung Internet, records `Device checkpoint: <date> LCP/INP per route` in the app's status doc, sets `budgets.json` defaults from it (`GATE-CHANGE:`), and writes `DEVICE CHECKPOINT DONE` in the ExecPlan Progress (or queues it). No M2 pilot starts without it; tests, fixtures, goldens, codemod prep and docs may continue while waiting. Today **no real-device or 4G measurement exists in any repo**.

### 4.8 Anti-gaming
Read-only files — **wrapper-enforced set** (the `prot()` list of `gate.sh`: a run that changes one of them exits 3 and its result is discarded, §4.2 step 10): `budgets.json`, `baselines/**`, `testdata/golden*/**` and `golden/testdata/**` (incl. `golden-pre-m1/`), `internal/contract/assets.json`, `legacy/` (frozen bundles, §8.2), `scripts/gate.sh`, `compose.gate.yml`, `Taskfile.yml`, `.gate.env`, `Dockerfile.toolchain`, `.codex/`. **Policy-enforced additions** (AGENTS.md, auto-review and the review diff; the wrapper does not hash them): `kit/` (§9-8), `engine.json` (§7.4), `Taskfile.repo.yml` (the repo's own gate steps, included by `Taskfile.yml`; `GATE-CHANGE:`-only but not trust-pinned), `.gitattributes`. Changes only in commits whose subject starts with `GATE-CHANGE:` with justification in the body, or — for exactly the files §9-8 lists — in Paul's `chore(kit):` commit; CI and the review diff them. No new `t.Skip`, no loosened assertions, no deleted tests without a Decision Log entry, no `--legacy-peer-deps`, no hand-edited lockfiles, no `engine.json` flip without Live zero, no suppressed shadow diffs. Review re-runs the gate on a fresh ext4 copy and compares `tree_sha256`. Baselines and goldens captured by Codex are re-captured from the parent commit by the reviewer and hash-compared.

### 4.9 Parallel-session caps

At most two product gate sessions, distinct worktrees/branches/chats/copies/locks/
Compose projects, no host ports. Wrapper GOFLAGS/GOMAXPROCS default 4, lower with
`--parallel 2` when overlapping. Compose totals 8 CPUs/10GiB per full project:
runner 4 CPUs/6GiB; DB 2 CPUs/2GiB; app 2 CPUs/2GiB. Two full projects total 20GiB;
prereqs require 24GiB MemAvailable for headroom and at least 10GiB free disk.
Toolchain/image builds are separately capped at 8 CPUs/10GiB and do not overlap
full gates when capacity is insufficient. No unrelated containers/cache are pruned.

## 5. Codex operating model

### 5.1 Configuration

Prepared config/rules are review artifacts under `bootstrap/`. Nothing in this
preparation changes global Codex config/rules, provider settings, model/effort or
system packages. The current managed workspace-write/auto-review policy controls
this chat. Candidate trusted project config keeps general host network restricted;
bounded registry requests and gates can request scoped approval. No writable Docker
socket grant or broad full-access mode is prepared.

Official OpenAI documentation establishes Linux bwrap/seccomp and trusted project
config/rule loading. `gen-rules.sh --output <new file in owned work/scratch> <absolute
worktree>...` renders a local candidate without installing or overwriting global
rules. Owner review and per-session command probes are required before activation.
Check exact wrapper `allow`, owner target `forbidden`, other path/raw shell unmatched,
and host product toolchain `forbidden` using `codex execpolicy check` on the candidate.
Hook setup is optional review preparation: never fabricate its execution/trust.

### 5.2 AGENTS.md Codex block

The installation manifest includes the exact authorization sentence below. It is
proposed for future bootstrap; it is not evidence that Paul installed it or ACKed.

**Gate authorization:** Paul authorizes `bash <this worktree absolute path>/scripts/gate.sh
<target> --sha <HEAD sha> [--dirty] [--parallel N] [--resolve-versions]` with
`require_escalated`, justification `Linux gate (Paul-authorized)`, for targets
`unit full gen deps build image baseline golden:capture golden:verify
contract:refresh legacy:freeze`. Compute SHA/status separately and pass literals.
No other shell shape, target, environment prefix or trailing command is authorized.
A sandbox denial requests scoped review; never work around it. `git add/commit`
request escalation only if the active sandbox actually denies them. Owner operations
and sign-off lines belong to Paul; workers never run kit sync or set GATE_OPERATOR.

Keep one-worktree scope, PROGRAM precedence, ExecPlan living sections, secrets by
name only, read-only subagents unless disjoint files are assigned, and the §5.5 stops.

### 5.3 ExecPlan
`docs/execplans/<session>.md`, written first, all twelve sections (Purpose/Big Picture; **Progress** with UTC-stamped checkboxes; **Surprises & Discoveries** with evidence; **Decision Log** incl. every resolved version with source and date; **Outcomes & Retrospective**; Context and Orientation; Plan of Work; Concrete Steps; Validation and Acceptance; Idempotence and Recovery; Artifacts and Notes; Interfaces and Dependencies). The four living sections are mandatory and are the restart artifact. Self-contained, no links out.

### 5.4 Milestone loop and checkpointing
Pilot → tune (gotchas into AGENTS.md) → sweep; one route group / widget / screen per milestone; **one commit per milestone**, `gate:unit` green, `gate:full` at the boundaries the session plan names. Checkpoint after every milestone: update Progress, Decision Log, Surprises → commit locally (escalated) → print a 5-line status (milestone, HEAD sha, `result.json` path + status, next item, blockers). Proceed milestone by milestone without asking for next steps; prepare a reviewable result before asking anything.

### 5.5 Hard stops (the only reasons to stop and ask)
push / merge / tag / branch deletion; touching another repo, `agent-ops`, `.codex/`; weakening safety, privacy, a11y, CSP, child-protection, reduced-motion, focus or contrast (including any ExecPlan line that would relax a §1.2/§4.8/§5.5 rule, §0.1); red gate after 3 honest attempts; auto-review denying the same action 3× (circuit breaker); a required dependency with only prerelease versions or a peer conflict; the device checkpoint; **any golden diff on a child-facing or privacy template (bold groups, §7.6) that is not one of the M1 externalisation classes listed in §8** (inline `<script>`/`<style>`/`style=`/`on*=` moved to nonced, hashed assets; `vite_entry`/`static` paths rehashed; nonce from ctx) — measured against the pre-M1 golden set captured at M0 (§7.1.1); a route group that cannot reach its §7.6 thresholds (coverage, replay zero, Live zero, shadow zero) after 3 honest attempts — escalate to Paul, never carry it on pongo2; anything the §8 must-not-touch lists name.

### 5.6 Protocols
- `CORE_REQUESTS.md` (app sessions): `REQ-n | blocking yes/no | app-local shim path`; shims live in `src/kit-shims/` (Go: `internal/kitshims/`) marked `// KIT_SHIM REQ-n`. Paul fixes core on `fix/<slug>` in roedu-ui, lands, tags `core-v1.N`, and **applies the kit himself** in the app worktree while the Codex turn is idle (`GATE-CHANGE: kit stage core-v1.N` → `kit:sync` → `chore(kit): bump to core-v1.N` → `trust` → `unit`), then sends `KIT_BUMP: core-v1.N applied sha=<sha7>; delete the shims for REQ-<n>, then gate unit.` The session verifies HEAD, deletes the shims in `chore(kit): remove REQ-n shims after core-v1.N`, runs `gate:unit`, and copies the lock-merge lines into its Decision Log. The single definition, including the M0 case, is **§9-8**; no session runs `kit:sync` itself.
- `GATE_REQUESTS.md`: `GATE PENDING <target> sha=<sha> | <reason>` (§4.5 ladder; also the wrapper's "untrusted gate files" refusal), review-request tokens (§7.6), `BLOCKED: …`.
- Subagents (`ultra`): read-only exploration and test triage only; never edit files unless assigned disjoint files in the prompt.
- Final report: What changed / Where / Risks / Next steps / Open questions / gate evidence (`result.json` path, `tree_sha256`, image digest, `versions.lock` sha) / per-session tables the §10 entry names.

### 5.7 Prompting rules (the configured Codex model)
Goal / Context / Constraints / Verification / Stop list / Output structure; the official follow-through block (infer intent, bias to action, persist to completion, act autonomously on reversible work; no stopping at a plan); explicit precedence; "quote file and line when pausing"; "run tests appropriate to the change; broaden on failure" but the full gate at every milestone boundary; short plain messages reporting commands and results.

## 6. Fleet rules that bind every session
- One task = one branch `<type>/<slug>` (`feat|fix|perf|docs|chore|content|test`) = one worktree under `/home/dobo/work/_worktrees/<repo>/<slug with / → __>`, created by Paul with `create_task_worktree.py --write`; the shared checkout stays on `main`, clean.
- Commit locally when green. Never push, merge, tag, delete branches, rewrite history. Never edit another repo, `agent-ops`, `.codex/`, the consumers' vendored tarballs, `third_party/webkit/` or `kit/` (written only by Paul's kit commits, §9-8).
- Clean includes untracked (ADR-0063): `.gate/`, `.vitest/`, `test-results/`, `node_modules/` gitignored; scratch under `_temp/<slug>/`; `git status --porcelain` empty at the end; stray files not yours are reported, not deleted.
- Docs definition of done in the same commit: status doc updated with `Last verified: YYYY-MM-DD`; a decision made or reverted gets `docs/adr/NNNN-<slug>.md` with the number claimed in `docs/adr/README.md`, the superseded ADR's `Status:` flipped; ADRs append-only; no decision language in READMEs; dated handoffs open with `Valid until:`.
- Budgets: AGENTS.md ≤ 80 lines, status doc ≤ 120, `agent-map.md` ≤ 60, `agent-testing.md` ≤ 80; overflow to `WORKLOG.md`. Doc gate: Windows side (python is not banned) `python3 "/home/dobo/work/agent-ops/scripts/check_docs.py" .` — on this PC `~/work` holds only `_temp`/`_worktrees`; agent-ops lives under `personal_repos/`; from `core-v1.0` the same script is vendored into the kit (`web-kit/lint/check_docs.py`, SHA drift-checked against agent-ops by core's `gate:unit`; consumers get it through the vendored tarball, §9-8) and runs inside `gate:unit`, so the Linux gate and the host command agree.
- ADR numbers and status docs: roedu-ui next 0004 (0004 monorepo + Preact/light-DOM reframing, 0005 version policy, 0006 gate contract, 0007 templ kit), status doc `README.md`; ro_teacher next 0077 (never backfill gaps), `screener/STATUS.md` (at 120/120 lines — move history to `WORKLOG.md`); cat next **dynamically rechecked** (verified 2026-10-06: 0173 and 0174 are claimed on unlanded `codex/v1-5-*` worktree branches — 0173 on 7 of them, 0174 on 5 — so S1 claims only currently free numbers after reconciling the content lane and re-verifies the first free number at M0 against README and those branches), `docs/STATUS.md`; social next 0050 (0041–0049 reserved; retire-SPA ADR supersedes ADR-0016; cite 0009 by slug), `STATUS.md`.
- Secrets: env var names only (`ROEDU_API_URL`, `ROEDU_API_KEY`, …); never open `~/.codex/auth.json`, `.env`, cookies or auth stores.
- Codex is opt-in (ADR-0065); this program is Paul's opt-in. The bridge is one-directional.

## 7. templ full-port design

### 7.1 What the port must be true to (measured 2026-10-06, read-only)
| Fact | Consequence |
|---|---|
| ro: 85/133 templates use only the common Django subset; the other 48 use 10 shim tags (`vite_entry` 35, `get_current_language` 2, `risk_spark` 2, `widthratio` 1, 6 URL-set tags). social: 70/91; the rest use 7 tags (`nonced_json_script` 7, `spa_entry` 2, `get_*language*` 4, `activity_accent` 1, `ifchanged` 1). Zero unknown filters, zero `\|safe`, zero `autoescape` outside `sw.js`. | A table-driven converter covers 223/224 syntactically; `ifchanged` is the only hand case. |
| Context roots: ro 383 distinct names, mean 5.3/template, max 42 (`learning/progress.html`); social 442, mean 8.3, max 60 (`place_detail.html`). ro `display()` wraps every `{{ }}`, resolves `_display`/`message`/`widget` keys and 13 `renderDates` keys (`render.go:418-452,474`). | View models are generated from usage; typing is staged (§7.3). |
| pongo2 renders `{% trans %}` **raw** (`native_static_translate` → `translate(msg)` unescaped, `templates.go:201-208`); `translateBlock` escapes interpolations only (`templates.go:223-234`); ro's 7 entity literals go through `display()` with autoescape — the drift to check. | T/TB/TN return raw; only interpolations escape (§7.2.6). |
| templ probe: newline between inline siblings → one space; same line → none; `{ "&mdash;" }` → `&amp;mdash;`; `templ.SafeURL("javascript:…")` passes verbatim; a plain string href → `about:invalid#TemplFailedSanitizationURL`; void elements without `/`; inter-block whitespace dropped. | Normaliser must be DOM-based (§7.1.2); `SafeURL` and `about:invalid` are gated. |
| Oracles today: ro 33 PG cases (`parity_review_reference.json`) gated by `TEACHER_GO_RENDER_REVIEW_PG_TESTS=1` + a Unix-socket DSN under `/_temp/` (`guard.go:15-28`); social skips 32 of 101 web tests without `-web-domain-test-dsn` (`testdb.go:22-25`); cohort fixtures `profileAuthorityFixture(t, cohort)` exist. | The Linux lane has the oracle's shape; it needs route × cohort breadth and must stop skipping. |
| ro `assets.json` pins 139 templates + 17 static by sha256 (`manifest.go:96-137`, `ci.yml:46`). | Every port commit is a `GATE-CHANGE:` artifact (§7.5). |

#### 7.1.1 What a golden is
One file per **case** = route × cohort/role × state × SPA mode, rendered by the **current pongo2 path after M1 delivery has landed** (CSP externalisation, embedded `NewFSLoader`, hashed widgets), so the port is a pure engine swap with expected diff zero. M1 itself is not oracle-free: at **M0** each app session captures a **pre-M1 golden set** (`GATE-CHANGE: golden capture pre-M1 <sha>`, directory `testdata/golden-pre-m1/`) from the untouched pongo2 tree over the fixtures that already exist (ro: the 33 `parity_review_reference.json` PG cases plus anon/parent/teacher walks of every GET route; social: the DSN-backed web tests plus anon/adult walks) — not coverage-complete, replay-only is enough. M1's edits to every template are then reviewed as explicit golden diffs against that set, classified by the §8 externalisation classes; a diff outside those classes on a bold-group template is the §5.5 hard stop. After M1 lands and the §7.1.5 matrix exists, the post-M1 set is captured and `golden-pre-m1/` is deleted in the same `GATE-CHANGE:` commit. Layout (committed, read-only, GATE-CHANGE):
```
ro_teacher/go-backend/internal/golden/testdata/<group>/<case>.html        normalised HTML
                                                 /<group>/<case>.ctx.json   recorded render context
                                                 /<group>/<case>.meta.json  status, Content-Type, template, engine
                                                 /cases.json                case table (route, actor, session, flags, query, mode)
social.../services/server/internal/web/golden/testdata/...                 same layout
```

#### 7.1.2 Normaliser — `webkit/golden.Normalize`
Parse with `golang.org/x/net/html`, serialise a canonical tree: lowercase names; attributes sorted; boolean attributes canonical; void elements without `/`; entities decoded (`&mdash;` ≡ `—`). **Whitespace:** whitespace-only text nodes between block-level/`<head>` children dropped; inside a text run `\s+` → one space **but leading/trailing presence is kept**, so `<img>␤<a>` vs `<img><a>` is a diff (the spike's visible-gap bug). Masks (attribute values only, never text): `nonce`, `csrfmiddlewaretoken` value, `<script type="application/json">` bodies re-serialised as sorted-key JSON with `csrf` masked, hashed asset paths mapped through the manifest to `{asset:<entry>}`, `Set-Cookie`. Time is **not masked**: every capture runs under the server's injected frozen `Now` (ro has `server.Now`; social gets the same hook). Hard failures regardless of golden: any `about:invalid#TemplFailedSanitizationURL`, any `{%`/`{{` leak, any `src=""`/`href=""`/`action=""` absent from the oracle. Mutation tests (drop an attribute, flip an `if`, change one character, swap sibling order) must each diff.

#### 7.1.3 Context recording
During capture, `Renderer.Render` is wrapped to record its data (`platform.Row` / `pongo2.Context` minus injected function globals) as JSON with type tags for `time.Time` and pre-rendered safe values. Two test modes: **`TestGoldenReplay`** (native, PG-free; `vm.Bind(ctx.json) → templ render → Normalize → diff`; Codex's done-when per group) and **`TestGoldenLive`** (Linux lane; full HTTP through fixtures, both engines; catches handler/adapter drift; what Paul lands on).

#### 7.1.4 PG gates always-on in `gate:full`
ro: `scripts/go-pg-tests.sh` provisions a private `initdb` cluster and exports the flag + DSN (line 141); runs in-runner with PG server binaries; `gate:full` parses `go test -json` — any `"Action":"skip"` in `internal/app`, `internal/golden` → exit 1. social: `qualify-native.sh` gains a `web` lane with `-web-domain-test-dsn "$native_dsn"` and the same zero-skip assertion; `compose.gate.yml` `db` = PostGIS + pgvector of `PROD_PG_MAJOR`. `task golden:capture` (Paul/Claude Code, or Codex inside a `GATE-CHANGE:`) and `task golden:verify` are separate; `gate:unit` runs replay only and reports `skipped no-dsn` for Live.

#### 7.1.5 Fixture matrix (data, written against pongo2 before any port)
| App / group | Cohorts and states |
|---|---|
| ro public, catalog, demo, digilit | anon; parent; teacher; examiner (`can_author_content`); researcher; each nav-gating flag combination (`DIGILIT_ENABLED`, `CATALOG_ENABLED`, `PUBLIC_DEMO_ENABLED`) |
| ro accounts (adult) | anon; parent with/without consent; TOTP enrolled/not; reset token valid/expired/done; reviewer grant present |
| ro teachers, reports | teacher with 0/1/n children; share valid/revoked; `parent_result` with band and with neutral/withheld result |
| ro learning | child session per step kind (13) × SPA on/off/missing; `correct` flag on tap kinds; escrow banner on/off; reading-comfort partial |
| ro screening | child session; examiner-run; each of 5 tasks; older-neutral (answer key absent — reuse the `screen-older` assertion); paused/abandon/done |
| ro accounts (child) | login grid; signup steps 1–5 × `CHILD_SELF_SIGNUP_ENABLED` |
| social public | anon en/ro; adult; `cache_public` pages |
| social account/self | adult; teen; child (supervised field present/absent, `forms.go:52-57`); guardian with wards; moderator; staff |
| social organise/forms | adult; child (restricted fields); edit with errors (422 re-render) |
| social communities/connections | adult; child-walled person (veto 404); minor pair (clamped card) |
| social threads/posts | adult thread; **CHILD thread (no sentiment footer, no dissent/concern)**; blocked user; guardian read-only; report always rendered |
| social messaging/guardianship/moderation | adult DM; guardian observe; moderator dashboard; concern detail |

#### 7.1.6 Coverage
`webkit/routes.Export()` dumps the route table (ro 399 from `manifest.json`, social 155 from `routes.json`); `golden-coverage.json` joins routes → templates → cases; `TestGoldenCoverage` fails if any template in a scheduled group has zero cases. Template-conditional coverage is measured by core cmd/golden coverage --metric template-conditionals (every arm including implicit false/empty paths, mapped to .templ lines, kit-owned filter excludes generated error plumbing): **100 %** of template conditional arms in every bold group (ro G3p, G6–G8; social G2p, G5–G6); **≥ 90 %** elsewhere, every uncovered branch named in the group's Decision Log.

### 7.2 Conversion method

#### 7.2.1 Converter, not hand-port
`cmd/djt2templ` (Go, in web-kit, ~1.5 k lines estimated) is justified by the counts: 2,464 `trans`, 324 `blocktrans`, 620 `url`, 223 `csrf_token`, 52 `json_script` — byte-exact mechanical items an LLM gets subtly wrong (the spike author typed `—` for `&mdash;`). It copies msgid bytes, emits route calls with positional args, never invents markup. S0b acceptance: `--check` parses 224/224; `templ generate` succeeds on all output; three pilots (social `connections.html`, ro `public/home.html`, ro `learning/steps/warmup.html`) golden-equal after the typed holes are fixed. LLM conversion only for what the table cannot express (`ifchanged`, `block.super`, two `<style>`-heavy print pages), judged by the same golden, marked `TODO(super|type)`.

#### 7.2.2 Mapping table (converter spec)
| Django/pongo2 | templ output | Notes |
|---|---|---|
| `{% extends %}` + blocks | ro `@layout.Adult(page, body)` / `@layout.Child(...)`; social `@layout.Base(page) { … }`. Blocks → `layout.Page` fields (`Title`, `MetaDescription`, `BodyClass`, `PageH1`, `NavCatalogReview`); slot blocks (`extra_head` 15, `extra_js` 45, `scripts` 12, `structured_data` 10, `og_*`) → `templ.Component` fields, nil = default | 2-level only; `block.super` → child calls `layout.DefaultX(page)`, `TODO(super)` |
| `{% include "x" with a=b %}` (ro 6, social 18) / plain (44, 20) | `@partials.X(XVM{...})`; plain includes get a generated VM from the parent VM | partial VMs from the classifier root list |
| `if/elif/else`, `for … empty`, `with` | native templ `if/else if/for` + `len()==0` branch; `with` → `:=` | `forloop.counter/first/last` → index vars |
| tuple `for a, b in pairs` (ro 12, social 14) | `for _, t := range vm.Pairs { a, b := t.A, t.B }` with generated pair struct | `tupleLoops` shim retired |
| `{% trans "x" %}` | content `@i18n.T(ctx, "x")`; attribute `{ i18n.TA(ctx, "x") }` | §7.2.6 |
| `{% blocktrans with k=v count n=… %}…{% plural %}…` | `@i18n.TB(ctx, "msgid", "k", v)` / `@i18n.TN(ctx, "sing", "plural", n, kv...)` | msgid bytes verbatim incl. newlines |
| `{% url 'name' a b %}` | `routes.Name(a, b)` → `templ.SafeURL`, generated | compile error on unknown name (today silent `""`/`"#"`) |
| `{% static 'p' %}` | `assets.Static("p")` | hashed when the manifest knows it |
| `{% csrf_token %}` | `@ui.CSRF()` | token from ctx |
| `json_script`, `nonced_json_script` | `@templ.JSONScript("id", vm.V)` | nonce from ctx (masked in goldens) |
| `vite_entry` / `spa_entry "src/main.tsx"` | `@assets.Tags(ctx, "src/main.tsx")` | kept for parity; island retirement removes later as its own golden update |
| `risk_spark`, `widthratio`, `activity_accent`, `get_current_language`, `get_available_languages`, URL-set tags | `@tmplfn.RiskSpark`, `tmplfn.WidthRatio`, `@tmplfn.ActivityAccent`, `i18n.Lang(ctx)`, `i18n.Available()`, `vm.DigilitHomeURL` etc. | one table entry each |
| filters (`default` 32, `date` 31, `linebreaksbr` 8, `safe_href` 7, `truncatewords` 7, `avatar_uri` 6, `join`, `cents`, `linebreaks`, `event_url`/`place_url`, `urlencode`, `truncatechars`, `capfirst`, `yesno`, `floatformat`, `slice`, `add`, `length`, `field_display`, `timeuntil`) | `tmplfn.*` | `Date(loc, t, fmt)` — ro Romanian month names, social English (`render.go:467-471` vs `templates.go:338-365`): one function, per-app locale |
| `{{ x }}` where x is a ro date key / `time.Time` | `tmplfn.DateTime(vm.X)` (`"j F Y, H:i"`) | replaces `displayValue` |
| `get_state_display`, `_display`, `message` | VM fields `StateDisplay`, `Display`, `Message` | adapter maps keys (§7.3) |
| `{{ form.as_p }}` (25), `{{ field.widget }}`, `non_field_errors` | `@ui.FormAsP(vm.Form)`, `@ui.Widget(f)` | Go builders unchanged; only non-i18n `templ.Raw` sites |
| `request.path/GET/csp_nonce/user`, `messages` | `webkit.Req(ctx)` struct; `page.Messages` | |
| `<script nonce="{{ request.csp_nonce }}">` (10) | `<script nonce={ templ.GetNonce(ctx) }>` | |
| `style="…"` (ro 6, social 49), `<style>`, `onclick` | **not converted** — removed on pongo2 in M1 before capture; converter errors if seen | |

#### 7.2.3 Whitespace
The converter emits inline siblings exactly as the source had them. `templ fmt` runs **once** during conversion before the first golden run so any reflow is caught; the gate then uses `templ fmt -fail -prettier-required=false`.

#### 7.2.4 Autoescape
templ `{ }` always escapes; raw only via `templ.Raw`. Allowed raw sites: `webkit/i18n` (T/TB/TN), `ui.FormAsP/Widget`, `tmplfn.RiskSpark/ActivityAccent/Linebreaks`, `templ.JSONScript`. The `webkit/lint/rawcheck` `go vet` analyzer fails any other `templ.Raw` or `JSUnsafeFuncCall`. All eight `AsSafeValue` producers today map onto that list.

#### 7.2.5 CSRF and URLs
`ui.CSRF()` reads the token from ctx; the 223 call sites stay explicit. `routes.*` are the only `templ.SafeURL` producers; `tmplfn.SafeHref` ports `safe_href` (`templates.go:279-286`); `tmplfn.AvatarURI` allows `data:image/svg+xml`, `/`, `https:`; ast-grep bans `templ.SafeURL(` in app code; query strings via `tmplfn.Query(kv...)`.

#### 7.2.6 i18n — T/TA/TB/TN, trusted-msgid rule
`T(ctx, msgid) templ.Component` raw; `TA(ctx, msgid) string` unescapes entities then lets templ escape (attribute context); `TB`/`TN` raw with `html.EscapeString` on each argument (= `translateBlock`). `i18n.Lint` in `gate:unit`: every literal msgid in `.templ` resolves in the `.po` (100 % hit rate; the spike's `—` typo fails here); any msgstr introducing a tag or attribute absent from its msgid fails (0 today); the entity-bearing list is generated (88 msgids with entities, 125 under "& or <" over the full multi-line catalogue). ro: `T` is identity over Romanian literals (`LANGUAGE_CODE="ro"`); lint = literal set only.

#### 7.2.7 Spike friction → gated rules
1 byte-exact msgids → converter copies bytes, lint 100 %. 2 entity double-escape → T raw / TA unescape; goldens compare decoded. 3 inline-whitespace gap → presence kept (§7.1.2). 4 `SafeURL` reflex → ast-grep ban + `about:invalid` hard failure. 5 silent `src=""` → empty-URL hard failure + strict `vm.Bind`. 6 `<style>`/`style=` → removed on pongo2 before capture. 7 CSRF repetition → `@ui.CSRF()`. 8 no golden against real pongo2 → §7.1 is the first milestone of every app session; no `.templ` lands before its group's goldens exist.

### 7.3 Typing — generated view models, staged
**Stage A (this program):** `djt2templ` emits `vm_gen.go` per template: one struct per page/partial, fields from the root list, types inferred (`for` → slice of generated element struct; `.a.b` → nested struct; `|date`/date key → `time.Time`; `|default`/text → `string`; `if`-only → `bool` when the handler's Row has one, else `any` + `TODO(type)`). Estimated counts: ro ≈ 98 page + 12 partial + 2 layout ≈ 112; social ≈ 71 + 15 + 1 ≈ 87; **~200 generated, 0 hand-written**. Handlers and the 110/44 `Render` call sites are untouched: the engine does `vm.Bind(row, &PageVM{})` — reflection adapter with explicit key rules (snake_case ↔ field, `get_x_display` → `XDisplay`, the 13 date keys, `[]platform.Row` → slices). **Strict** in tests (unknown key or missing required field → error, so a template reading a key the handler never sets fails in replay); **lenient** in prod with a `vm_bind_missing_total` counter (pongo2 parity: silent empty). **Stage B (optional, per group, after pongo2 removal):** handlers build the struct directly; `Bind` deleted for that route; `any` fields become concrete. social's 20 `BuildSPA` projections are already typed and become the VMs of the retired SPA routes directly.

### 7.4 Runtime — `webkit/engine`
```go
type Mode int // Pongo2, Templ, Shadow
type Env struct{ Column string /*"test"|"prod", from <APP>_ENGINE_ENV; anything else = "prod"*/; On, Off string /*<APP>_TEMPL_ROUTES, <APP>_TEMPL_OFF*/ }
type Registry struct{ def Mode; byGroup, byRoute map[string]Mode; groupOf map[string]string /*route → group*/ }
func Load(static []byte /*engine.json*/, env Env) (*Registry, error)   // error on unknown mode, unknown route/group name, or a Pongo2/Shadow mode in a binary without a pongo2 loader
func (r *Registry) Resolve(route string) (Mode, Source)              // Source = env-off | env-on | route | group | default
type Page struct{ Route, Template string; Data map[string]any; Comp func(ctx) templ.Component }
func (e *Engine) Render(ctx context.Context, w http.ResponseWriter, p Page) error
func (e *Engine) Report() []RouteEngine                                // route, group, mode, source — printed by `healthcheck --engines`
```
- **`engine.json` — committed schema (one file per Go module that renders templates, at the module root next to `go.mod`, `//go:embed`'ed; read-only, §4.8).** Every group carries **two explicit modes, `test` and `prod`**; there is no single-mode form, and a file with one mode per group is invalid (S0b M3 rejects it; 07's entry assertion 8 checks for exactly this shape):
```json
{"schema":1,
 "default":{"test":"Pongo2","prod":"Pongo2"},
 "groups":{"G0":{"test":"Templ","prod":"Shadow","routes":["home","about"]},
           "G1":{"test":"Pongo2","prod":"Pongo2","routes":["events","event_detail"]}},
 "routes":{"event_detail":{"test":"Shadow","prod":"Pongo2"}}}
```
  `groups.<G>.routes` lists route names from the route table (`routes.Export()`; a name that is not in the table is a `Load` error, so the file cannot drift from the server). `routes` is the rare per-route exception inside a group. **Which column applies** is decided by `<APP>_ENGINE_ENV`: the test env sets `<APP>_ENGINE_ENV=test` on the `app` service (the app's M1 `GATE-CHANGE:` compose wiring; S0b's `compose.test.yml` template carries it), production never sets it, so an unset or unknown value means `prod` — the fail-safe column. **Env overrides**, evaluated in this order on top of the column: `<APP>_TEMPL_OFF=<comma list of group or route names, or all>` → `Pongo2` (the one-release rollback); `<APP>_TEMPL_ROUTES=<comma list of group or route names>` → `Templ`; then `routes`, then `groups`, then `default`. Unknown names in either variable are a startup error, not a silent no-op. **Every change to `engine.json` is its own commit `GATE-CHANGE: engine <group> test=<mode> prod=<mode>`** (body: the Live-zero and shadow-zero `result.json` paths; bold groups additionally cite Paul's Live-review line, §7.6), after a clean `full`; a session never writes a `prod` value other than `Shadow`/`Pongo2` before its final-removal milestone (§7.6).
- **Atomic render:** both engines render into a buffer; headers + body written after. ro keeps its handler-level recorder (`server.go:386`); the port changes nothing above `Renderer.Render` (`render.go:99`); social keeps the buffer-then-write shape (`renderer.go:98-114`). A mid-render error is a 500 with no partial body; a test asserts it for both engines.
- **Shadow mode** (test env: every request; prod: sampled, `<APP>_TEMPL_SHADOW=<fraction>`, default `0.01`): serve pongo2, render templ in a goroutine with the recorded context, `Normalize` + diff, log `shadow_diff{route}`; `TestShadowZero` in `gate:full` fails on any diff for flagged groups. Shadow never changes served bytes.
- **Per-route flag:** the committed `engine.json` columns above plus the two env variables; `Report()` printed by `healthcheck --engines` so STATUS can state which routes run on which engine in which environment (the STATUS engine table has one column per environment: route group | test | prod, §7.6).
- **CSP nonce:** `csp.Middleware` puts one nonce in ctx (`templ.WithNonce`) and in `request.csp_nonce` for pongo2 — identical bytes.
- **Streaming:** `engine.Stream(route)` allowlist, default empty; opt-in only after measurement with a test that an error after first flush closes the connection without a 200 body.
- **Embed:** pongo2 from `embed.FS` via `NewFSLoader` (M1); templ views compiled in; each ported group removes files from `embedfs/templates/` and from the image.

### 7.5 ro_teacher release contract
`assets.json` gains kinds `templ_source` (`go-backend/internal/web/views/**/*.templ`) and `templ_generated` (`*_templ.go` + templ version in `meta`) beside `template|static|generated_widget`, plus at final removal `sw_template` (the `text/template` source of `sw.js`), `email_text` (the 5 `.txt` files, sha unchanged) and `legacy_bundle` (`legacy/*.tgz`, §8.2); pongo2 `template` entries are deleted in the same commit as the route group's pongo2 file, and the final-removal `contract:refresh` asserts the `template` kind is empty. `task contract:refresh` regenerates; `teacher-go check` additionally runs `go tool templ generate -check` and `templ fmt -fail`. Every refresh is a `GATE-CHANGE:` commit, one group at a time. A templ version bump regenerates all `_templ.go` → one GATE-CHANGE + full golden rerun.

### 7.6 Sequencing per app and removal criteria
Each group = one milestone: fixtures/goldens exist → converter run → compile → replay zero → Live zero (bold groups: Paul's Live-review line) → `GATE-CHANGE: engine <G> test=Templ prod=Shadow` → one release on `Templ` in production (below) → delete pongo2 file + contract entry at the app's final-removal milestone.

**What "one release on `Templ`" means (one definition; 02 M3, 04, 05, 06 §10 and 07 cite it).** Production runs a release with **`<APP>_TEMPL_ROUTES` listing the group** (the deployment's env var, set by Paul; removing the name is the rollback), while the committed `engine.json` `prod` column for that group **stays `Shadow`** — the previous release, in which prod was on `Shadow` with the sampled diff at zero, plus the test env's continuous shadow-zero are the shadow evidence. The `prod` column is never flipped per group: it flips **once**, for every group, in the B-session's final-removal commit `GATE-CHANGE: engine all test=Templ prod=Templ`, when pongo2 has left the binary and `Load` would reject anything else; the now-redundant `<APP>_TEMPL_ROUTES` is removed from the deployment by Paul after that release. A session never writes a `prod` value other than `Shadow`/`Pongo2` before that commit, and Paul writes no `GATE-CHANGE: engine` commits of his own: his production switch is the env var, and his evidence is a STATUS line. The A-session's soak (ro: G0–G5 incl. G3p; social: G0–G4 incl. G2p) therefore runs as `<APP>_TEMPL_ROUTES=<every A-group>` on the first release after the A-session landed; the B-session adds its groups to the same list on its own release soak (07 "Release wait"); a group named in `<APP>_TEMPL_OFF` during a soak restarts that group's soak.

**Paul's STATUS lines — the only formats, written once here.** *Provenance rule:* a line counts only if the commit that introduces it carries the trailer `Signed-off-by-Paul: <the line verbatim>` and was authored by Paul on `main` or in the session worktree while the Codex turn was idle; Codex never writes, stages or paraphrases one (it stages STATUS hunks by explicit path only), and relays arrive as `codex queue … "SIGNED: <the line>"`. The reviewer checks `git log --format=%B -S'<line>' -- <status doc>` for the trailer (09 §3). Dates are `YYYY-MM-DD`; `<sha>` is the full 40-hex sha of the reviewed commit; `<tag>` is the production release tag.
| Line (exact) | When Paul writes it | Unblocks |
|---|---|---|
| `Device checkpoint: <date> LCP/INP per route` (+ the per-route table) | after the app's M1 on the real phone (§4.7); queued to the session as `DEVICE CHECKPOINT DONE` | M2 |
| `never-diagnose needles signed off: Paul <date>` (ro only) | after reviewing the §8.1 needle list at S2A/S2B M0 | the first port |
| `G<a>–G<b> fixture matrix signed off: Paul <date> file=docs/golden/<a>-<b>-matrix.md` | before a bold group's conversion; for a B-session, on `main` before it starts (S2B: `G6–G8`, S3B: `G5–G6`); the file lists the signed case table and the exact template paths | that group's / session's port |
| `G<n> Live reviewed: Paul <date> sha=<sha>` | after a bold group's Live-zero run that he reviewed (`sha` = the reviewed commit) | the group's `GATE-CHANGE: engine …` flip |
| `G<n> <milestone> <island> Live reviewed: Paul <date> sha=<sha>` | same, for an island-retirement golden update on a bold group's templ version (05 M4) | landing that island |
| `G<n> served on Templ in prod for release <tag>, shadow zero: Paul <date>` | one line per group, after a full production release with `<APP>_TEMPL_ROUTES` listing it (the soak) | the group's pongo2 deletion (removal criterion) |
| `S2A soak signed off: Paul <date>` / `S3A soak signed off: Paul <date>` | once every A-group has its soak line; on `main` | S2B / S3B entry |
| `<FLAG> fallback release done: <tag> <date>` (`CAT_UI`, `RO_TEACHER_REACT_UI`, `SOCIAL_REACT_UI`) | after the first production release that shipped the replacement with the legacy fallback still present | deleting the frozen legacy tarball + flag (§8.2) |
| `Review <session> <sha7>: ACCEPTED — WORKLOG.md <date>` | the reviewer's landing line (09 §7) | landing |
Codex's matching request tokens in `GATE_REQUESTS.md` and Progress are `REVIEW PENDING <kind> G<n> sha=<sha> result=<path> <UTC>` (`<kind>` = `matrix | live | island`), `RELEASE SOAK PENDING <groups> sha=<sha>` (with the exact `<APP>_TEMPL_ROUTES` value, from `healthcheck --engines`), and `WAITING: <what>`; the answer is always Paul's STATUS line, relayed as `SIGNED: …`.

**Inventory (reconciled with the contracts):** ro `assets.json` pins **139** `template` entries = **133 `.html`** (the port below) **+ `frontend/sw.js` + 5 `accounts/email/*.txt`**. social: 91 loader-root templates = 84 ported + 7 SPA-support files (5 `snapshots/`, `spa.html`, `spa_preview.html`) that are retired, not ported. Group sizes are verified against the loader-root inventory at each app's M0 (risk 19); the ro accounts split below is counted from the classifier (32 files: 7 child login/signup, 11 privacy, 14 adult auth).

| ro_teacher (133 html) | social (91; 84 ported, 7 retired) |
|---|---|
| G0 layouts + 403/404/500 + `partials/` (6) | G0 `base.html` + static/legal (7; `privacy.html`/`terms.html` are legal text, not account data) |
| G1 public 4, dev 1, offline 1, demo 9 (15) | G1 public SEO 15 (landing ×4, events, event_detail, places, places_list, place_detail, series ×2, discover, campaigns, partners, donate). The 5 `snapshots/` + `spa.html`/`spa_preview.html` stay **unported and frozen** (byte-pinned in the golden suite) for one release as the `SOCIAL_REACT_UI` fallback and are deleted in **S3B M4** (§8.3, §10.2) |
| G2 catalog 8, curriculum 5, reviewing 5, digilit 9 (27) | G2 account/self **12** (profile, you, interests, topic/access/display preferences, notifications, notification_preferences, saved_searches, my_donations, my_meetups, my_venues) |
| G3 adult auth/session **14** (login, signup, password_reset ×4, TOTP ×4, verify_email, verification_required, dashboard, parent_claim_code) | **G2p privacy/child-data 6** (settings — data download, account-deletion entry, API-token revoke; account_delete; my_privacy; verify_age; account_restricted; register — cohort/age entry). guardianship/wards are already in bold G6. The `account/export/` download is a non-HTML response covered by the fixture matrix, not a template |
| **G3p privacy/child-data 11** (consent, consent_request_landing, account_delete, child_privacy, child_form, child_detail, child_invite, child_delete, child_add_adult, adult_gate, set_pin) | G3 organise/forms 14 (activity_form/edit, wizard, group_form, series_form, gauge ×4, place_propose/claim/pending, organize, home) |
| G4 teachers 7 + reports 4 (11) | G4 communities/connections/cards 11 |
| G5 learning non-step 18 | **G5 threads/posts/membership 13** (CHILD walls, sentiment footer absence, report always rendered) |
| **G6 learning steps 13** | **G6 messaging/guardianship/moderation 7** (incl. guardianship, wards, `moderation/*`) |
| **G7 screening 11** | — |
| **G8 child login/signup 7** (incl. `_picture_grid`) | — |
| `frontend/sw.js` (not html): ported to Go **`text/template`** in S2B M5 — same 6 data keys (`cache_name`, `cache_version`, `precache_json`, `offline_url`, `nav_allow_json`, `never_intercept_json`), `{% verbatim %}` body copied byte-for-byte, **byte-equal golden** (no normaliser) against the pongo2 output for the pwa fixtures; the worker logic is never edited (§1.4). Contract kind `sw_template`. Deviation §0.4-3 | — |
| 5 `accounts/email/*.txt`: **not rendered by the Go server** (zero Go references outside the contract) — not ported, not loaded by any engine; they stay on disk under `web/templates/accounts/email/` and in `assets.json` re-kinded `email_text` (same sha256) in the S2B M5 `contract:refresh`, so `teacher-go check` still pins their bytes after pongo2 is gone | — |

**Bold groups** (child-safety **and privacy/child-data**: ro **G3p, G6, G7, G8**; social **G2p, G5, G6**) get the same treatment without exception: Paul's human review of the case list **before** conversion and of the Live run **after**; **100 %** template-conditional coverage (§7.1.6); shadow-zero in the test env for a full release; social bold groups need the independent reviewer AGENTS.md mandates (`NEEDS-INDEPENDENT-REVIEW`) plus `DJANGO_CSP_ENFORCE=true` in the test env; ro never-diagnose neutrality (`screen-older` key-leak assertion, forbidden adult fields) stays a hard test; for G3p/G2p the fixture matrix must additionally exercise: consent given/withdrawn/pending, erasure requested/confirmed, child record with/without guardian, age verification each state, guardian with 0/1/n wards, API token present/absent. The privacy groups are scheduled **in the A-session** (ro S2A M4, social S3A M5) because GDPR erasure and consent are §1.2 invariants that the oracle must cover before any child-facing group ports — they are not "low risk" merely because they are adult-facing. A template is owned by **one track at a time**: island retirement and widget Phase B edit the templ version after its group is ported, as a separate approved golden update (diff = removed `data-mount`/`vite_entry`/`spa_context`). Delivery precedes capture; port precedes retirement.

**Removal criteria per group:** golden-equal in Live across all cases with zero approved exceptions; shadow zero in the test env; one release on `Templ` as defined above (Paul's `G<n> served on Templ in prod …` line); for bold groups additionally Paul's `G<n> Live reviewed …` line — both passing the provenance rule. **Exit criterion of S2B and S3B (Decision 2 — not best effort):** **every** group of the app is on `Templ` with its pongo2 file and contract entry deleted, `pongo2` gone from `go.mod`, and `embedfs/templates/` empty, apart from a deviation Paul has approved by name in STATUS (§0.4-3 is the only one planned). A group that cannot reach its thresholds (coverage, replay zero, Live zero, shadow zero) after three honest attempts is a **§5.5 hard stop escalated to Paul** with the diff report and the uncovered branches named — never a silent carry-over on pongo2; Paul decides between more fixture work, a named deviation, or a scope change to this file. **Final removal per app (S2B M5 / S3B M4):** delete `transform()`/`tupleLoops` (`render.go:183-416`), `transformTemplate`/`native_static_translate` (`templates.go:59-222`), pongo2 from `go.mod`, `embedfs/templates/`; ro `sw.js` moves to `text/template` in the same milestone (`RenderPage("frontend/sw.js")` at `pwa.go:117` becomes `swTemplate.Execute`), and the 5 `.txt` entries are re-kinded; the goldens stay as the frozen regression suite.

### 7.7 web-kit templ deliverables (Go)
| Package | API |
|---|---|
| `webkit/golden` | `type Case{Name, Route, Group string; Actor, Session, Flags map[string]any; Query url.Values; Mode string}`; `Capture(t, h http.Handler, cases []Case, dir string)`; `Normalize(b []byte, o Options) ([]byte, hard []string)`; `Diff(want, got []byte) (Report, bool)`; `RecordContext(name string, data map[string]any) []byte`; `Replay(dir string, render func(name string, ctx []byte) ([]byte, error)) []Result`; `Coverage(routes []routes.Route, dir string) Report` |
| `webkit/tmplfn` | `Default, Date(loc Locale, t time.Time, f string), DateTime, Timeuntil, Join, Capfirst, Linebreaks/Linebreaksbr (templ.Component), Truncatewords/chars, Cents, Yesno, Floatformat, Slice, Add, Length, URLEncode, Query(kv ...any) templ.SafeURL, SafeHref(string) templ.SafeURL, AvatarURI(string) templ.SafeURL, WidthRatio, RiskSpark(...) templ.Component, ActivityAccent(seed) templ.Component, Pluralize` |
| `webkit/i18n` | `LoadPO(fs, path) (*Catalog, error)`; `WithLang(ctx, lang)`, `Lang(ctx)`, `Available()`; `T(ctx, msgid) templ.Component`; `TA(ctx, msgid) string`; `TB(ctx, msgid string, kv ...any) templ.Component`; `TN(ctx, sing, plur string, n int, kv ...any) templ.Component`; `Lint(cat *Catalog, src fs.FS) []Finding` |
| `webkit/routes` | `Gen(table []byte, pkg string) ([]byte, error)` → `routes_gen.go` with `func <Name>(args ...any) templ.SafeURL`; `Export(mux) []Route` |
| `webkit/engine` | §7.4 |
| `webkit/vm` | `Bind(src map[string]any, dst any, o Options{Strict bool, DateKeys []string}) error`; key rules documented and tested |
| `webkit/ui` | `CSRF()`, `JSONScript(id, v)`, `FormAsP(f Form)`, `Widget(f Field)`, `Island(name, props)` |
| `cmd/djt2templ` | `djt2templ --app ro\|social --templates <dir> --routes <manifest.json\|routes.json> --group <g> --out <views> --vm-out <vm> [--check] [--classify classify.json]`; emits `.templ`, `vm_gen.go`, `TODO(type\|super)` markers, per-template report |
| `cmd/golden` | `capture`, `verify`, `coverage`, `report` |
| `webkit/lint` | `rawcheck` analyzer; ast-grep rules for `templ.SafeURL(`, `style=`, `on*=`, `<script>` without nonce |

### 7.8 Attacker A1 answered, and risks ranked
1. **A1 "the port buys ~0 ms and is the riskiest item"** — accepted as a perf statement; the port is Paul's decision for typing, one engine, deletion of the two regex shims (the silent-failure surface), compile-time route/msgid checking, and templates leaving the image. Each cost is neutralised by a gate: never precedes M1 or the device checkpoint; oracle exists before any `.templ` lands and is runnable natively via recorded contexts; converter validated on 224/224 before app sessions; ~200 VMs generated with a strict-in-test adapter; child-safety groups last, human-reviewed, shadow-verified, per-route rollback for one release; the normaliser never masks text, so a dropped cohort wall or sentiment footer is a diff by construction.
2. **Fixture breadth** (largest real cost; ~120 ro + ~150 social cases, estimates) — data written in M0/M2 against pongo2; coverage and branch reports make gaps visible; a bold group cannot flip with uncovered branches.
3. **Normaliser hiding a real diff** — mutation tests; DOM compare; hard failures; masks limited to five attribute classes.
4. **Adapter drift** (`Bind` vs pongo2 map/method/`forloop` resolution) — replay over all recorded contexts; strict in tests; counter in prod.
5. **i18n byte-exactness/raw rendering** — converter copies bytes; 100 % lint; msgstr-markup lint; TA unescape; decoded compare.
6. **Codex gate reachability** — replay is PG-free; Live/capture reachable through the wrapper; fallback ladder.
7. **ro contract churn** — new kinds; `contract:refresh` per group; `generate -check` inside `teacher-go check`.
8. **templ pre-1.0 / "latest" policy** — exact `tool` pin; generated files committed; bump = GATE-CHANGE + golden rerun; `about:invalid` hard failure pins sanitiser behaviour.
9. **Two engines in prod during the port** — bounded by the B-session exit criterion (§7.6: every group on Templ, pongo2 deleted); `engine.json` + `Report()` + STATUS table make the current state visible; a group that stalls is a hard stop for Paul, not a longer overlap.
10. **Date/locale divergence** — one `tmplfn.Date(loc, …)`; frozen `Now`.
11. **Forms stay string-built** (25 `as_p`) — deliberate; only non-i18n `Raw`; retyping forms out of scope.
12. **Golden churn from island/widget work** — one-track-per-template rule.

## 8. Per-app maps

### 8.1 ro_teacher
Facts: 133 templates / 7,385 lines, 14 islands, 14 widgets; per-route cold cost 19,873–38,139 B gz, 12 of 14 routes over the 20,480 B budget, served uncompressed with `max-age=3600` and no modulepreload (`static.go:43`, `render.go:172-175`); `frontend/tsconfig.json` has compat `paths`; SPA kill switch `RO_TEACHER_REACT_UI` (ADR-0016).

| Surface | Target | Diff. | Perf-UX change | Fallback |
|---|---|---|---|---|
| Asset manifest (M0) | `task contract:refresh` per group as `GATE-CHANGE:`; kinds `template\|static\|generated_widget\|templ_source\|templ_generated`; `teacher-go check` in every gate | L | — | — |
| 133 templates + 2 layouts (S2A G0–G5 incl. **G3p**, S2B G6–G8) | M1 on pongo2 (reviewed as golden diffs against the M0 pre-M1 set, §7.1.1): `NewFSLoader` embed, nonce from ctx, 5 inline scripts / 5 `onclick=print` / 6 `style=` / 12 `<style>` externalised — these are the **M1 externalisation classes** the §5.5 hard stop exempts — → strict CSP **report-only, zero violations** (stage A, ro has no CSP header today) → **enforced in the test env at S2A M2** (stage B; prod flip `RO_TEACHER_CSP_ENFORCE` is Paul's after the S2A soak); then the §7.6 port per group; `form.as_p` untouched | M–H | streaming opt-in per route after measurement | per-route `Pongo2` via env for one release |
| Read-only islands: ParentResult, ParentDashboard, TeacherDashboard, ChildView, PathMap, StoryPage, LibraryShelf (19.9–21.6 KB each) | **Retired** on the templ versions (S2A M5); T1 `<roedu-speak>`/`<roedu-comfort>`; sparkline stays server SVG | L | 0 JS, no double paint | `RO_TEACHER_REACT_UI` per key, one release, served from the **frozen legacy tarball** (§8.2 mechanism; `legacy/ro_teacher-legacy-<sha>.tgz` frozen at S2A M1 from the parent commit's `frontend/`); deleted S2B M5 |
| ChildLogin, ChildSignup ×5 (S2B) | T1 `<roedu-wizard>` + native forms; `_picture_grid.html:20` externalised | L–M | — | old island from the frozen tarball |
| StepRunner (1,345 LOC, 10 twinned kinds; S2B) | one island, per-kind lazy chunks on engines; untwinned `build_word`/`choice`/`review`/`library_material` stay server + Phase-A vanilla | H | local feedback from the shipped `correct` flag | per-kind kill switch → legacy widget from the frozen tarball |
| ScreeningTask (793 LOC; S2B) | island on `screen-clock`; **450/350/1300 ms rule and latency stamps encoded as Vitest browser tests in S2A M0 before any edit** | H | — | legacy island from the frozen tarball; any semantic diff blocks |
| Digilit hub, 5 sims, Certificate, teacher flows (38.1 KB) | island; split `Debrief` per sim; `pushState` for Back | M | ≤28 KB cold (estimate) | old island from the frozen tarball |
| 14 vanilla widgets | Phase A bundle (S2A M1); fold into engines as each passes parity; `material_*`/`math_*` stay vanilla | L–M | hashed + immutable | file kept until parity |
| CSS (`app.css` 10,575 + SPA 6,232 B gz) | consolidation milestone with screenshots; ratchet from 16,807 | M | — | — |
| `/admin/`, escrow, `qdollar`, screening constants, answer keys | **out of scope**; CSP exemption scoped to `/admin/` | — | — | — |
| `sw.js` (pongo2 `{% autoescape off %}` + 6 keys + `{% verbatim %}` body, `pwa.go:117`) | engine → Go `text/template` at S2B M5 under a **byte-equal** golden; worker logic untouched (§7.6, deviation §0.4-3) | L | — | pongo2 path until the golden is byte-equal |
| 5 email `.txt` (`accounts/email/`) | not rendered by Go; stay on disk, re-kinded `email_text` in `assets.json` at S2B M5 (§7.6) | — | — | — |

Existing gates to keep green: `cd go-backend && go test -race ./... && go vet ./... && go run ./cmd/teacher-go check --repo ..`; `CGO_ENABLED=0 go build -trimpath ./cmd/teacher-go`; `bash scripts/go-pg-tests.sh` (21 synthetic DBs, zero skips); `bash scripts/go-redis-tests.sh`; `bash scripts/go-browser-tests.sh all|pwa`; `cd frontend && npm ci && npm run test:logic && npm run build && npm run a11y` (20 KiB gzip budget, axe, contrast); `npm audit --audit-level=moderate` (frontend and `web/`); `git diff --check`. Test-DB knobs: `TEACHER_GO_BIN`, `TEACHER_GO_PG_BINDIR`, `TEACHER_GO_*_SCRATCH_ROOT`; never real DBs, media or model weights. Docs: ADRs from 0077 (templ port, embed, retirement); `screener/STATUS.md` ≤ 120 lines. Gotchas: never-diagnose (ADR-0001), DRAFT/PUBLISHED (ADR-0012), launch gates unmet; new deps need justification (stdlib preferred); CI `workflow_dispatch` only (ADR-0075). **Budgets in CI:** `TestRouteBudgets` runs in the Linux `gate:unit` of every milestone commit and review (§4.6, §0.4-6); `.github/workflows/` is not edited by S2A/S2B.

### 8.2 cat_de_roman_esti
Facts: React 19 + framer-motion 12.42.2 + react-router 7; entry 119.78/120 KiB gz, react-dom 51.6 % + motion 22.6 % + router 11.6 %; spike port 13,111–15,616 B gz for Conexiuni + ResultCard + Confetti + shell (on Preact 10 — re-measure on 11); `App.tsx:72` `LazyMotion domAnimation` makes the 5 `layout` props inert; 203 `style={{}}` objects; 39 node test files (16 execute src, 11 mixed, 22 regex-only, 1 bundle budget), ~159 Playwright tests; committed `web/static` + `.vite/manifest.json` (ADR-0020); `@roedu/ui` vendored 0.3.0; 3 live `codex/v1-5-*` worktrees.

| Surface | Target | Diff. | Perf-UX change | Fallback |
|---|---|---|---|---|
| `App.tsx` shell, `AnimatePresence mode=wait` | preact-iso + `<Presence mode="wait">`; `reducedMotion=user` semantics kept | M | overlap transitions ≈0.2 s (measure in M2) | whole-app `CAT_UI=legacy` from the frozen tarball (below) |
| Home (lobby) | stays client-rendered (`Home.tsx:20-56,91,124` localStorage-driven); font subset preload; `backdrop-filter` gated by `deviceMemory` | L | — | legacy |
| Intrusul, Perechi | `useIsPresent()`; contract test proves a leaving screen is inert | M | — | legacy |
| Conexiuni (**pilot**) | Presence-per-tile exits, shake, feedback swap; `layout` dropped | H→M | none | legacy |
| Alchimie / AlchimieExplore | signals for the 22 `useState`; native DnD unchanged | H | — | legacy |
| CaldRece, Lant | `layout` dropped; `animateHeight` via Motion mini; shake keyframes | M | — | legacy |
| Ranking, ResultCard, Confetti, GameIntro, AccountBar, pickers | mechanical port | L | — | — |
| 203 `style={{}}` | **required codemod in M2 before the first screen port**: numeric values get explicit units (v11 dropped auto-px); ast-grep enforces | L | — | — |
| Tests | ~22 regex-only files + source assertions in the 11 mixed files rewritten as behaviour tests **in M0 against React**; Playwright gains a `motion-on` project; Oxlint replaces ESLint (typescript-eslint peer blocks TS 7) | M | — | — |
| `index.html` from disk, curl HEALTHCHECK, `sh -c ${PORT}` | Go shell with nonce + font preload; `go:embed` via `assets:sync`; `healthcheck` subcommand; `PORT` in Go; `/data/submissions` volume; distroless | L | — | — |
| Committed bundles (30 files) | untracked in M1 (ADR supersedes 0020) **after** the frozen-legacy tarball below is cut from them | L | — | — |
| CSS (`arcade.css` 1,846 lines) | consolidation milestone; ratchet from M0 measurement | M | — | — |

**Frozen-legacy mechanism (all three apps; the only source of every legacy fallback once the source is rewritten).** At each app's M1, before any source rewrite, `task legacy:freeze` (wrapper target, §4.4) runs the **parent commit's** frontend build in the runner (`npm ci && vite build` on the pre-M1 `package-lock.json`, or for cat the 30 committed bundle files as they are) and packs the output plus the HTML shells it needs (social: `spa.html`, `spa_preview.html`, the 5 `snapshots/`) into **`legacy/<app>-legacy-<parent-sha>.tgz`** + `legacy/<app>-legacy-<parent-sha>.tgz.sha256`, committed as `GATE-CHANGE: legacy freeze <parent-sha>` (binary via `.gitattributes`, read-only per §4.8, contract kind `legacy_bundle` in ro). `task assets:sync` unpacks it into `<module>/embedfs/legacy/` (gitignored, `//go:embed all:embedfs`) after verifying the SHA, so a Docker build from the worktree always contains the fallback even though the React source is gone, the bundles are untracked and `react*` imports are lint-banned. **Exemptions are limited to that path:** `embedfs/legacy/` and `legacy/` are excluded from Oxlint/ast-grep/tsc, from `versions:check` and from the lockfile assertions (they are prebuilt artefacts, not dependencies); budgets count them only in the legacy journeys. The flags `CAT_UI=legacy`, `RO_TEACHER_REACT_UI=<key>` and `SOCIAL_REACT_UI` route to those bytes; `gate:full` runs one legacy journey per app under the same CSP policy (`csp.legacy_violations`, §4.4). **Deletion milestone — one release after the replacement shipped:** cat in the first post-S1 release (Paul's `chore(legacy): drop cat legacy bundle` after the device-verified release), ro at **S2B M5**, social at **S3B M4**; the deletion commit removes the tarball, the flag, the `embedfs/legacy` unpack step and the legacy journey together.

Existing gates: `go -C go-backend test -race ./... && go -C go-backend vet ./...`; same for `shared-go/authcore`; `go -C go-backend run ./cmd/cat-doc-check --root ..`; `go -C go-backend run ./cmd/cat-content validate --root ..` and `export --root .. --check` (never hand-edit `web/static` or fixture JSON); `go -C go-backend run ./cmd/cat-qualify parity --binary <bin>` (1,207 responses); `cd frontend && npm ci && npm test && npm run lint && npm run build`; `npm run test:e2e` (`CDR_E2E_PORT`, `CDR_E2E_OUTPUT_DIR`, `CDR_BROWSER_PLAN_BINARY`, `CDR_NATIVE_BINARY` built in the runner); PG lanes need explicit disposable DSNs (`-accounts.database`, `-arcade.database`; skips do not qualify); `scripts/qualify_go_toolchain.sh` for full native qualification. Must not touch: `asyncControl`, `scores`, `api/*`, hash convention (`website.go:23`), `web/static` fixture JSON by hand, `shared-go/authcore` semantics; production stays anonymous until `docs/DEPLOY.md:35-40` is met. Docs: ADR from **0175** (§6; re-verify at M0), `docs/STATUS.md`. **Budgets in CI:** `TestRouteBudgets` runs in the Linux `gate:unit` of every milestone commit and review (§4.6, §0.4-6); cat's existing GitHub workflow is not edited by S1.

### 8.3 social_media_activities_app
Facts: 91 templates / 4,596 lines (inventory from the Go loader roots in S3A M0 — recon found 4 outside `apps/`, a raw `find` returns 358 including retired Django apps; do not trust `find`); 20-route SPA (`BuildSPA`, one caller `server.go:236`, `?_data=1` zero consumers, off by default, stale July React bundle on disk while `vite.config.ts:13` has used `@preact/preset-vite` since `0d9cece`); 13 widgets; MapLibre 5.24.0 (373 KB gz) as a blocking classic script on `/places/`; only app with a CSP (report-only unless `DJANGO_CSP_ENFORCE`); 49 `style=`; `app.go:195` `CheckRuntime()` needs ffmpeg/prlimit; 24 live worktrees; ADR 0041–0049 reserved.

| Surface | Target | Diff. | Perf-UX change | Fallback |
|---|---|---|---|---|
| 71 pages + 15 partials + `base.html` (S3A G0–G4 incl. **G2p**, S3B G5–G6) | M1 on pongo2 (reviewed as golden diffs against the M0 pre-M1 set): embed, nonce, 49 `style=` → classes, gauges → `<roedu-meter>` CSSOM var — the M1 externalisation classes — with the existing report-only CSP at **zero violations** (stage A); **`DJANGO_CSP_ENFORCE=true` in the test env at S3A M2** (stage B, after the SPA retirement and the `<so-map>` `worker-src`/`img-src` additions land); then §7.6 port | M–H | — | per-route `Pongo2` env one release |
| 5 SEO snapshot templates, `spa.html`, `spa_preview.html` (`server.go:254`, `renderer.go:127`, `spa.go` reference them) | **kept, frozen** (unported; byte-pinned in the golden suite) for one release as the `SOCIAL_REACT_UI` render path; **deleted at S3B M4** together with the legacy tarball | L | — | — |
| 20-route SPA | **retired** (S3A M2, `/events/` first); `BuildSPA` projections kept as typed VMs; supersedes ADR-0016 | M | 0 JS + no double paint | `SOCIAL_REACT_UI` one release, served from the frozen tarball (`legacy/social-legacy-<sha>.tgz` = the SPA bundle rebuilt from the parent commit, + `spa.html`/snapshots; §8.2 mechanism) |
| Browse deck | one Preact island (S3A M6) | M | — | `browse-modes.js` bundled |
| hovercard, concept-combobox, form-wizard, site, near-me, my-meetups | Phase A; hovercard → `<roedu-hovercard>` (veto null-cache preserved); combobox Phase B only if the 15-step harness is green | L–M | — | bundled original |
| `thread-chat.js` + `presend-nudge.js` | Phase A (S3A); Phase B island on `ws-thread` with one Trusted Types policy for `body_html` (S3B) | H | — | bundled pair behind flag |
| `e2ee-messaging.js` | Phase A; crypto verbatim + known-answer tests; shell → island only after independent review (S3B) | H | — | current file |
| `places-map.js` + MapLibre | `<so-map>`: `places_list` first, `import()` on tap/visibility, **MapLibre 6.12.0** per §3.3; ratchet 310 KB | M | ≤6 KB before tap vs 373 KB | list |
| `place-picker.js` + Leaflet 1.9.4 | bundled, lazy on picker open | L | — | — |
| `community-graph.js` + 3d-force-graph | tap + `saveData` gate; `<style>` injection → scoped report-only exception on `/communities/graph/` only (S3B) | M | — | text list |
| `meetups-worker.js` | untouched (SHA-pinned) | — | — | — |
| Image | `debian:13.7-slim` + ffmpeg/libavif-bin/util-linux/perl-base; `media-worker` same image | L | — | — |
| CSS (`base.css` 14,891 B gz) | consolidation milestone; ratchet from 16,954 | M | — | — |

Existing gates: `scripts/check-native.sh /abs/path/to/go`; `GOWORK=off go -C services/server test -race ./... && vet` (same for `services/authcore`, `services/agentapi`); `go -C services/server run ./cmd/check-contracts -root "$PWD" -summary`; `node --test` for the offline service worker; `cd frontend && npm ci && npm test && npm run build`; `bash scripts/test-native-gates.sh`; `scripts/qualify-native.sh GO IMAGE PRIVATE_NETWORK SYNTHETIC_DSN SCRATCH` (Linux, 21 lanes, zero skips, Paul's landing gate with Trivy/govulncheck versions re-resolved and recorded). Concurrency env: `GOWORK=off` + task-owned `GOCACHE`/`GOMODCACHE`/`TMPDIR`; `GOMAXPROCS`/`GOFLAGS=-p` come from the wrapper (`GATE_PARALLEL_MAX=4` in `.gate.env`, Paul-set); when the session prompt names an overlapping social lane (S3B ∥ a hotfix, or Paul's `qualify`), Codex passes `--parallel 2` on every gate — it cannot edit `.gate.env` or `compose.gate.yml`, and does not need to. Landing rule ADR-0040: `check-native.sh` + full `qualify` on the exact head + no-cache docker build on dependency changes; **an independent reviewer, not the implementer, approves and confirms new tests fail without the fix** — any child-safety/privacy/moderation/GDPR/auth-adjacent change is flagged `NEEDS-INDEPENDENT-REVIEW` in the ExecPlan and final report. Forbidden: real network ingestion, scheduled sync, deploys, Terraform, authorising minors, paid infrastructure; `apps/ingestion/sources/_roedu_client_core.py` is generated. Docs: ADR from 0050, `STATUS.md`. **Budgets in CI:** `TestRouteBudgets` runs in the Linux `gate:unit` of every milestone commit and review (§4.6, §0.4-6); social's existing GitHub workflow is not edited by S3A/S3B.

## 9. Core contracts frozen at `core-v1.N`
A contract change = new tag + `KIT_BUMP`; never a silent edit.

1. **Island protocol.** `<div data-island="<key>" data-props="<id>" data-load="eager|visible|idle|interaction">` + nonced `<script type="application/json" id="<id>">`; module export `mount(root: Element, props: unknown, ctx: {signal: AbortSignal, nonce: string}) => dispose`; the island replaces a same-size server skeleton in one `replaceChildren` inside a rAF; events `island:mounted`, `island:failed` (bubbling, `detail: {key, error}`); failure ladder chunk-fail → keep server HTML → optional legacy script via `data-legacy`; kill switch env `<APP>_ISLAND_<KEY>=off` renders the skeleton without `data-island`; Go emitter `island.Island(name, props)` and the npm loader agree, asserted by one contract test.
2. **Go API (web-kit).** `assets.Load(fs embed.FS) (*Manifest, error)`, `assets.Tags(ctx, entry) templ.Component`, `assets.Static(path) string`; `static.Handler(fs, opts)` (statigz br+gz, `immutable` hashed / `no-cache` HTML); `csp.Middleware(policy)`, `csp.Nonce(ctx)`, report endpoint; `island.Island(name, props)`; `health.Command` (`healthcheck [--engines]`); `golden.*`, `i18n.*`, `routes.*`, `engine.*`, `vm.*`, `tmplfn.*`, `ui.*` as §7.7; pongo2 `NewFSLoader` wiring helper; `lint/rawcheck` analyzer.
3. **CSS/token contract.** `roedu-*` classes with state in `data-state`/ARIA, never inline `style`; `@layer reset,tokens,base,components,utilities,app`; token custom properties named `--roedu-<group>-<name>` (34–40 today), per-app theme CSS files, the reserved-class list (includes ro's 46 `roedu-spa*`), `tokens.go` constants for server-side use.
4. **Components, behaviours, motion.** Preact 11 component signatures (props typed with `preact.*HTMLAttributes`); behaviours API (`define()`, `connected/disconnected` with `AbortSignal`, props from nonced JSON); motion-kit API: `<Presence mode="wait"|"sync" initial?>`, `useIsPresent(): boolean`, `<Confetti count durationMs>`, `animateHeight(el, from, to, spring?)`, `springs.<name>` built on `motion/mini` `animate` + `spring`; `data-motion="off|reduced|on"` with `prefers-reduced-motion` honoured; every animation visible to `document.getAnimations()`.
5. **Gate CLI.** `task gate:unit` / `task gate:full` and the §4.4 targets; exit codes 0/1; `result.json` schema (§4.3); `budgets.json` schema (§4.6); baselines at `baselines/<target>/<project>/…` captured with `mcr.microsoft.com/playwright:v1.63.0-noble`; `GATE-CHANGE:` rule (§4.8); `.gate.env` keys = exactly the eleven of §4.2 step 4 (`TOOLCHAIN_IMAGE TOOLCHAIN_DIGEST COMPOSE_FILE SYNC_BACK PG_MAJOR PG_SCRATCH_ROOT GATE_PARALLEL_MAX GATE_DB_IMAGE CSP_STAGE APP_DOCKERFILE QUALIFY_ARGS`; any other key is a refusal); wrapper flags `--sha/--dirty/--parallel/--fresh/--resolve-versions/--keep/--tag` and exit codes 0/1 task, 2 refusal, 3 protected path, 4 sync-back; Paul-only targets `qualify|shell|toolchain|trust` and `--keep` gated by `GATE_OPERATOR=paul`; the trust pin over the four gate files; per-target sync-back (§4.2); `kit:check` in `gate:unit` (§9-8).
6. **Embed layout and contract refresh.** `task assets:sync` → `<module>/embedfs/{templates,dist,legacy}` with committed `.keep` and `//go:embed all:embedfs`; `legacy/<app>-legacy-<sha>.tgz` + `.sha256` unpacked into `embedfs/legacy/` after SHA verification (§8.2); ro `task contract:refresh` with the `assets.json` kinds `template|static|generated_widget|templ_source|templ_generated|sw_template|email_text|legacy_bundle`.
7. **Version policy.** §3.1 and `versions.lock.json` schema; exceptions table §3.2.
8. **Core patch protocol and kit distribution (`kit/` → `kit:sync`) — the single definition.** Every other file (README §7/§9, the session prompts' M0 steps and KIT_BUMP paragraphs, the resume template's rule 10, 09 §0-3/§8) describes this protocol by reference to this item; where their text differs, this item wins.
   - **Why Paul runs it.** The runner sees only the worktree (`.:/work`) and the four cache volumes; the npm tarballs and Go sources of a `core-v1.N` tag live in roedu-ui, which no app gate can reach; and `kit:sync` may rewrite the four trust-pinned gate files, after which no gate runs until Paul's `trust`. So the kit enters an app repo only through **Paul's commits from Claude Code** — in a Paul-owned worktree of the app repo for the first sync (landed on `main` before the session worktree exists) or in the session worktree while the Codex turn is idle (`KIT_BUMP`). Codex never stages, syncs or merges a kit; the §5.2 sentence lists `kit:sync` only because the wrapper accepts it.
   - **Input: the committed staging path `kit/`** at the repo root (read-only, §4.8; one tag staged at a time, older archives deleted in the same commit):
     ```
     kit/CORE_TAG                      one line: core-v1.N
     kit/roedu-ui-<ver>.tgz            `npm pack` of @roedu/ui at the tag            — from the tag's `build` run (.gate/build/*.tgz, 09 §8 step 4)
     kit/roedu-web-kit-<ver>.tgz       `npm pack` of @roedu/web-kit at the tag       — carries templates/ and the tag's versions.lock.json
     kit/web-kit-go-core-v1.N.tgz      `git -C roedu-ui archive --format=tgz core-v1.N web-kit/` — the Go module sources (npm-only dirs stripped)
     kit/SHA256SUMS                    sha256sum of the three archives
     ```
     Staged by **`GATE-CHANGE: kit stage core-v1.N`** (body: tag, the three sha256s, the toolchain image ID). The commit touches `kit/` only — no gate file, so the existing trust pin still holds and `kit:sync` can run; the tag's `TOOLCHAIN_IMAGE`/`TOOLCHAIN_DIGEST` arrive through `kit:sync` (next bullet), never by hand. When the tag has a new toolchain image, that image must already be loaded on the Linux host (built by the core release's `toolchain --tag`, or `docker load`ed from its `.tar`) before step 5 below.
   - **What `task kit:sync` writes** (in the runner, from `kit/` only, no network, no git metadata is mounted in `/work`): (1) verify `SHA256SUMS`; (2) `frontend/vendor/<both>.tgz` + `.tgz.sha256` (previous ones removed) and `package.json` `"@roedu/ui": "file:vendor/roedu-ui-<ver>.tgz"`, `"@roedu/web-kit": "file:vendor/roedu-web-kit-<ver>.tgz"`; (3) `<module>/third_party/webkit/` replaced wholesale from the Go archive, `go.mod` `require github.com/DobosP/roedu-ui/web-kit v0.0.0-<tag>` + `replace … => ./third_party/webkit`; (4) the gate-file copies from the web-kit tarball's `templates/`: `scripts/gate.sh`, `compose.gate.yml`, `Taskfile.yml`, `Dockerfile.toolchain`; the tag's template `.gate.env` is written into the ext4 copy only, and the **wrapper** then carries just its `TOOLCHAIN_IMAGE`/`TOOLCHAIN_DIGEST` lines into the worktree's `.gate.env`, every repo value and every other line byte-identical (§4.2 step 10) — **never** `Taskfile.repo.yml` (the repo's own gate steps), `ci.yml` or `.codex/` (reference copies; not in the wrapper's sync-back); (5) `versions.lock.json` merged per the lock's `kit_sync_merge` rule — core, environment and toolchain entries replaced by the tag's verbatim; an app copy of a core entry that is **higher** than the tag's is a hard stop, never lowered; app-scope entries present in both: higher wins, ties keep the app entry; app-only entries kept; core-only app-scope entries dropped unless they list the app; `resolved` = the later date; `core_tag` = `kit/CORE_TAG`; (6) `task deps` (lockfiles from the edited manifests); (7) `.gate/kit-sync/result.json` with one `checks[]` entry per step. Destinations come from `Taskfile.repo.yml` vars `KIT_VENDOR_DIR` (default `frontend/vendor`) and `KIT_GO_DIRS` (default: every module whose `go.mod` carries the `replace`); the wrapper's sync-back (§4.2 step 10) brings exactly these paths back. On an already-synced tree the task changes nothing and exits 0.
   - **Drift check: `kit:check` in `gate:unit`** (every repo from `core-v1.0`): fails when a vendored sha256 ≠ `SHA256SUMS`, `third_party/webkit` ≠ the Go archive, a gate-file copy ≠ the tarball's template (this is the "wrapper byte-identity" check), `package.json`/`go.mod` do not point at the vendored files, or `kit/CORE_TAG` ≠ the lock's `core_tag`. This replaces every "`kit:sync --check`" phrase.
   - **Sequence (Paul, native bash; `WT` = the app worktree; Codex turn idle or chat closed):** 1. core release per 09 §8 (land, tag, `build` in a detached roedu-ui worktree, copy the tarballs + Go archive + `SHA256SUMS` to `_temp/core-release-v1.N/`); 2. copy them into `WT/kit/`, write `kit/CORE_TAG` → `GATE-CHANGE: kit stage core-v1.N` (nothing else in the commit); 3. `bash "<WT>/scripts/gate.sh" kit:sync --sha <sha>`; then `git status --porcelain` shows only the §4.2 `kit:sync` sync-back paths plus `.gate.env`, `cmp scripts/gate.sh <(git -C roedu-ui show core-v1.N:web-kit/templates/gate.sh)` is identical, and `git diff -- .gate.env` is empty or exactly the two `TOOLCHAIN_*` lines; 4. commit **`chore(kit): bump to core-v1.N`** (KIT_BUMP) or **`chore(kit): sync core-v1.N`** (first sync); body: tag, sha256s, image ID, the `result.json` path — this is the only non-`GATE-CHANGE:` subject allowed to touch the protected set, and only for those paths (09 §3 checks each file against the tag's template; a `.gate.env` delta beyond the `TOOLCHAIN_*` lines or any other protected path is a finding); 5. `GATE_OPERATOR=paul bash "<WT>/scripts/gate.sh" trust --sha <new sha>` (the gate files changed), then `unit --sha <new sha>` green (`kit:check`, `versions:check`, digest check against the new image); 6. first sync: land on `main` (`--ff-only`) before `create_task_worktree.py` creates the session worktree — the session's M0 "kit check" is then Codex reading `kit/CORE_TAG` and its own first `unit`; KIT_BUMP: send **`KIT_BUMP: core-v1.N applied sha=<sha7>; delete the shims for REQ-<n>, then gate unit.`** (`codex queue --thread …`, or the resume template's `RELAYED_NOTE`), adding `; resolve versions` only when app-scope versions should move too.
   - **Codex on receipt:** HEAD is `<sha7>` or descends from it, `git status --porcelain` is empty, `git diff --name-only <sha>~1 <sha>` lists only the step-3 paths (else stop and ask); `unit` on HEAD; delete that REQ's shims in **`chore(kit): remove REQ-n shims after core-v1.N`**; `unit`; one Decision Log line per changed lock entry (from `git show <sha> -- versions.lock.json`); `gen --resolve-versions` only if the message said so; if the bump moved the templ version, `gen` regenerates every `_templ.go` → ro `GATE-CHANGE: contract refresh` + full golden rerun (§7.5). Conflicts with in-flight work are resolved by Paul in Claude Code, never by Codex. A session never adopts a tag it was not sent (09 §8 step 5 picks recipients; Go-only tags never go to cat).
   - **What this replaces (delete these claims wherever they still appear):** the README's `docker run … -v "$K":/kit:ro` form (the runner has no `/kit` mount and `compose.gate.yml` is `GATE-CHANGE:`-only); `deps.request.json` routing and a `CORE_TAG=` key in `.gate.env` (an unknown key is a wrapper refusal; the tag lives in `kit/CORE_TAG`); every "Codex runs `kit:sync`", "no `kit:sync` wrapper target", "`GATE PENDING kit:sync`" and "`BLOCKED: KIT_BUMP … no kit:sync wrapper target`" sentence; the `GATE-CHANGE: chore(kit): …` and `GATE-CHANGE: kit sync …` subjects; `_temp/core-release-v1.N/` as the tarball source (the runner cannot see it — it is only Paul's hand-off into `kit/`). `CONSUMER_NOTES.md` in core lists every breaking change for app sessions.

## 10. Session plan

### 10.1 Global entry conditions (Paul / parent)

S0a launches only after the parent dispatch and an owner-reviewed native bootstrap.
All six literal ACKs/alternatives must be recorded in the installed docs/PROGRAM.md;
production PG major/DB digest/toolchain ID remain unset in this preparation. Stable
registry resolution is fresh, but exception approvals remain pending. Parent chooses
and provisions the core worktree after review; this adaptation worktree is not S0a.

Required bootstrap manifest: `.codex/config.toml` and optional trusted SessionStart
hook; `.agent/PLANS.md`; `scripts/gate.sh`; `Dockerfile.toolchain`, `compose.gate.yml`,
`Taskfile.yml`, `.gate.env`, `versions.lock.json`, budgets seed; `.gitignore` exclusions;
AGENTS owner block; request templates; `docs/PROGRAM.md`, `docs/execplans/`. Owner
provisions external caches, trust store, capped builder and immutable toolchain
archive without changing unrelated host services. LF checks inspect native Git and
preserve existing oracle/binary attributes; no blind normalization or replacement.

Before dispatch: prerequisite check complete (exit 0, no SKIP), scoped candidate
rules/config review and exact positive/negative probes, concrete toolchain smoke on
the production-major image, clean source/trust/image consistency, and documented
bootstrap gate unavailability. S0a may implement the real checks under its dispatch;
no bootstrap stub pass satisfies a milestone. All substantive checks required by
§10.2 and session check tables must exist before their boundaries.

App kit bootstrap follows §9-8: Paul stages committed kit/, syncs while worker idle,
commits verified output, pins trust and reruns real unit before an app session starts.
Before S1/S3A, reconcile existing branches/ADR claims by read-only inventory; never
bulk-delete unlanded work. Device scheduling is known before apps launch; measurements
remain mandatory after each app M1 and before M2.


### Consumer readiness corrections (native recon, 2026-10-06)

Teacher first UI1.0 sync is blocked until the unchanged Preact10+compat+UI0.3 timing
suite is authored and passes in separately dispatched pinned baseline preparation.
Owner lands that reviewed suite/receipt before full kit adoption. S2A M0 verifies
baseline provenance and reruns identical assertions across Preact11/compat removal.
No test/source change can substitute for untouched timing qualification.

Cat ADR0175/0176 are occupied, peer0177 active; dynamically claim only after rechecking
main/all refs/worktree untracked ADRs. Candidate0178 is not a reservation. Preserve
20 frozen CRLF research files and only scope LF checks to executable/source inputs.

Social GUI source qualification and source retirement are distinct current boundaries.
Keep check-contracts actual rc/output/unresolved1651 as a named not-retired artifact;
never mark it pass or suppress its declaration inventory. Real source qualification
and all21 disposable lanes remain required. Separate retirement hook demands zero
unresolved/exit0 before Python/oracle removal. Parent must accept this explicit hook
classification before S3A dispatch; the original generic-unit wording is unresolved
until then. Native group partition, Report eligibility and clamp fixtures require
source-derived independent resolution before capture. No native retirement is attested.

Concrete owner hook/phase proposal is in bootstrap/project-bootstrap.md. Consumer
readiness evidence is scratch-only and must be rechecked at each actual dispatch.

### 10.2 Sessions
| Session | Repo / branch / worktree (`_worktrees/…`) | Pin | Milestones (one commit each; `unit` green; `full` where marked) | Done-when | Must not touch |
|---|---|---|---|---|---|
| **S0a core-v1.0** | roedu-ui / `feat/gui-core` / `roedu-ui/feat__gui-core` | — | **M0** toolchain jump + `versions:resolve` → Decision Log; React peers and `vite-plugin-dts` out; `tsc -b` dts + d.ts snapshot test; `forwardRef` removed; `.nvmrc`/`.npmrc`; the bootstrap `Dockerfile.toolchain`/`compose.gate.yml`/`Taskfile.yml`/`.gate.env` are already committed and `roedu-toolchain:core-v1.0` already built (§10.1), so **the first scoped wrapper run proves reachability only until real checks exist**; bootstrap unit/full deliberately refuse. Implement required gates before their named milestone boundaries, and never count smoke as M0/M3/M5/M6 acceptance. **M1** tokens + layered CSS + reserved classes, CSS size recorded. **M2** Preact 11 components, CSP-safe, v11 lint, plain `render()` tests. **M3** (`full`) behaviours + motion kit with v11-semantics browser tests (Presence deadlock, sibling effects, WAAPI end states, `getAnimations()`); loader ≤1.1 KB; motion mini+spring ~5.1 KB; `net/`, `storage/`. **M4** Go delivery packages (`assets static csp island health golden.Normalize routes.Export`, `NewFSLoader` helper, `engine` Pongo2-only). **M5** (`full`) npm kit + templates (Vite preset, Oxlint/ast-grep, budget tool validating the shipped `budgets.json` schema incl. `null` limits, vendored `check_docs.py`, Playwright base, Dockerfile, `ci.yml`, `.codex/`, AGENTS block, PLANS.md, `CORE_REQUESTS.md` templates, `Taskfile.repo.yml` include, `docs/llm/` v11/preact-iso/Motion mini/kit contracts), the **real `kit:sync` / `kit:check` / `versions:resolve` / `versions:check` targets exactly as §9-8 and §3.1 specify** (the web-kit tarball carries `templates/` and the tag's `versions.lock.json`), and **publishes the reviewed gate templates into `web-kit/templates/`; wrapper and consumer copies remain byte-identical, while Taskfile stubs must first become real fail-closed checks** (from here on consumers get them via Paul's `kit:sync`, §9-8). **M6** (`full`) sample Go app with three stress islands + a pongo2 page + a templ page; `npm pack` both tarballs; ADR-0004/0005/0006; README `Last verified`; `CONSUMER_NOTES.md`. | `gate:full` pass; tarballs + SHA in report; measurements (Preact 11 runtime, loader, motion, per-component CSS) | app repos; `agent-ops`; `.codex/`; consumers' vendored 0.3.0 tarballs |
| **S0b core templ kit** (sequential: starts after S1 M2 is green, §0.4-1) | roedu-ui / `feat/gui-core-templ` / `roedu-ui/feat__gui-core-templ`, based on `core-v1.0` | `core-v1.0` | **M0** classifier re-run over both apps' template roots (read-only by path) → `web-kit/testdata/djt/` (224 inputs). **M1** `tmplfn`, `i18n` (`LoadPO`, T/TA/TB/TN, `Lint` with the social `.po`), `routes.Gen` compiling for both route tables. **M2** `vm.Bind` + round-trip over `parity_review_reference.json` contexts. **M3** `engine` Templ/Shadow, atomic render, mid-stream-error test, `Report()`, nonce parity. **M4** `cmd/djt2templ` (`--check` 224/224; `templ generate` green; three pilots golden-equal via `cmd/golden verify` against goldens captured from the sample app's pongo2 engine), `rawcheck`, ast-grep rules, `cmd/golden`. **M5** (`full`) `docs/llm/templ.md`, pinned `templ fmt` flags, ADR-0007. Go-side version resolution only. | `gate:full` pass; converter dry-run report; pilot diff reports; lands as Go-only `core-v1.N` (cat not bumped) | `src/ css/ preact/ behaviors/ motion/`; app repos |
| **S1 cat** (core shakedown) | cat_de_roman_esti / `perf/gui-cat` / `cat_de_roman_esti/perf__gui-cat` | `core-v1.0` | **M0** ExecPlan; versions (`gen --resolve-versions`); kit check (§9-8: `kit/CORE_TAG` = `core-v1.0`, first `unit` green incl. `kit:check` — the kit itself was applied by Paul on `main`); tsconfig audit; behaviour tests against React; `GATE-CHANGE: baseline capture <sha>` before any code change. **M1** delivery: `GATE-CHANGE: legacy freeze <parent-sha>` first (§8.2 — the 30 committed bundles become `legacy/cat_de_roman_esti-legacy-<sha>.tgz`), then Go shell (nonce, font preload), `assets:sync` embed (+ `embedfs/legacy/`), `healthcheck`, `PORT`, statigz, `CAT_UI=legacy` routed to the tarball, bundles untracked (ADR supersedes 0020), strict CSP **enforced** in the test env from here (stage B, §4.4 — new shell, no legacy template surface), distroless → **device checkpoint (hard stop for M2)**. **M2** pilot: numeric-style codemod, Intrusul then Conexiuni, `layout` dropped, motion-on project. **M3** remaining screens + preact-iso shell, Alchimie signals, CaldRece/Lant `animateHeight`. **M4** (`full`) ~159 Playwright + motion-on green; budgets tightened (`GATE-CHANGE:`); CSS consolidation with screenshots; `cat-qualify parity` 1,207; ADRs + `docs/STATUS.md`. | `gate:full` pass at M4; `CAT_UI=legacy` verified; per-screen before/after gz table | `asyncControl`, `scores`, `api/*`, hash convention, fixture JSON by hand, authcore semantics |
| **S2A ro_teacher A** | ro_teacher / `perf/gui-ro-a` / `ro_teacher/perf__gui-ro-a` | current `core-v1.N` incl. templ kit | **M0** ExecPlan, versions (`gen --resolve-versions`), kit check (§9-8), delete compat `paths`, `contract:refresh` + new kinds, **verify pre-bootstrap original-runtime timing receipt and rerun immutable tests across adoption**, `GATE-CHANGE: baseline capture`, **`GATE-CHANGE: golden capture pre-M1`** (§7.1.1), **`GATE-CHANGE: legacy freeze <parent-sha>`** (§8.2). **M1** delivery on pongo2 (embed, nonce, externalisation reviewed as golden diffs vs the pre-M1 set, Phase A ×14, compression, CSP stage A report-only at zero violations, `assets.json` GATE-CHANGE) → **device checkpoint**. **M2** (`full`) oracle: fixtures G0–G5 incl. G3p, `GATE-CHANGE: golden capture` (pre-M1 set deleted), `TestGoldenCoverage`, PG lanes zero-skip, **CSP stage B: enforced in the test env**. **M3** port G0–G2 (replay zero → Live zero → `engine.json`). **M4** port G3, **G3p (bold: Paul's case-list review before, Live review after, 100 % branches)**, G4–G5. **M5** read-only islands retired on templ versions, `RO_TEACHER_REACT_UI` per key from the frozen tarball. **M6** (`full`) CSS consolidation (ratchet from 16,807), budgets, ADRs, `screener/STATUS.md`. | `gate:full` incl. `teacher-go check`, `go-pg-tests.sh` zero skips, `go-browser-tests.sh all\|pwa`, `npm run a11y`; shadow-zero per flagged group; per-group golden table; G3p sign-off line | `/admin/`, escrow, `qdollar`, screening constants, `sw.js` logic, email `.txt` bytes, G6–G8 beyond M1 edits, untwinned kinds beyond Phase A, answer keys |
| **S2B ro_teacher B** | ro_teacher / `perf/gui-ro-b` / `ro_teacher/perf__gui-ro-b`, from `main` after S2A landed | then-current `core-v1.N` | Entry assertions: S2A soak done; Paul's G6–G8 matrix sign-off line in `screener/STATUS.md`; timing tests green. **M0** fixtures + `GATE-CHANGE: golden capture` G6–G8. **M1** port G6 learning steps (13). **M2** port G7 screening (11). **M3** port G8 child login/signup (7) — 100 % branch coverage each. **M4** ChildLogin/Signup → `<roedu-wizard>`; ScreeningTask island on `screen-clock` (legacy embedded; timing diff blocks); StepRunner for twinned kinds with per-kind kill switch; digilit split. **M5** (`full`) **exit criterion (§7.6): pongo2 deleted for every group**, `transform()`/`tupleLoops` removed, `pongo2` out of `go.mod`, `embedfs/templates/` empty; `sw.js` → Go `text/template` under a byte-equal golden; the 5 `.txt` re-kinded `email_text`; legacy tarball + `RO_TEACHER_REACT_UI` + legacy journey deleted (one release after S2A M5 shipped); ADRs, STATUS sign-off lines. A group that cannot meet its thresholds is a hard stop for Paul, not a carry-over. | `gate:full`; never-diagnose assertions green; Paul's Live review per bold group recorded; `assets.json` has no `template` kind entries; `go list -m all` shows no pongo2 | as S2A + timing constants, answer-key handling, neutrality wording, forbidden adult fields, latency stamps |
| **S3A social A** | social_media_activities_app / `perf/gui-social-a` / `social_media_activities_app/perf__gui-social-a` | current `core-v1.N` incl. templ kit | **M0** ExecPlan, versions (`gen --resolve-versions`), kit check (§9-8), loader-root template inventory, fresh `npm run build` baseline + `GATE-CHANGE: baseline capture`, **`GATE-CHANGE: golden capture pre-M1`**, **`GATE-CHANGE: legacy freeze <parent-sha>`** (SPA bundle rebuilt from the parent commit + `spa.html`/`spa_preview.html`/5 snapshots), DSN fixture inventory, `.vitest/` ignore. **M1** delivery on pongo2 (embed, nonce, 49 `style=` → classes, gauges → `<roedu-meter>`, Phase A ×13, compression, debian-slim image, `media-worker`; existing report-only CSP at zero violations = stage A; **snapshots and `spa.html` kept, frozen**) → **device checkpoint**. **M2** SPA retirement (`/events/` first, then all 20; `SOCIAL_REACT_UI` now serves the frozen tarball) + `<roedu-hovercard>` + lazy `<so-map>` MapLibre 6.12.0 + **`DJANGO_CSP_ENFORCE=true` in the test env (CSP stage B)**. **M3** (`full`) oracle G0–G4 incl. G2p, `GATE-CHANGE: golden capture` (pre-M1 set deleted), `qualify-native.sh` web lane zero-skip. **M4** port G0–G2. **M5** port **G2p (bold: Paul's review + independent reviewer, 100 % branches)**, G3–G4. **M6** (`full`) browse deck island, CSS consolidation (ratchet from 16,954), budgets, ADRs (retire SPA supersedes 0016, templ port, MapLibre 6 citing CVE-2026-85061), `STATUS.md`. | `gate:full`; `check-native.sh`; Paul runs `qualify` + Trivy/govulncheck; `NEEDS-INDEPENDENT-REVIEW` entries resolved; MapLibre before/after bytes on `/places/` | e2ee internals, `meetups-worker.js`, cohort/safety gates, Leaflet version, media/processing, generated `_roedu_client_core.py`, G5–G6 beyond M1 edits, moderation logic |
| **S3B social B** | social_media_activities_app / `perf/gui-social-b` / `…/perf__gui-social-b`, from `main` after S3A | then-current `core-v1.N` | Entry: S3A soak; Paul's G5–G6 sign-off in `STATUS.md`; `DJANGO_CSP_ENFORCE=true`. **M0** fixtures + `GATE-CHANGE: golden capture` G5 (CHILD thread, blocked user, guardian read-only, minor pair, veto 404, report always rendered) + G6. **M1** port G5. **M2** port G6 (100 % branches). **M3** thread-chat Phase B on `ws-thread` with one Trusted Types policy; e2ee shell → island only after independent review (crypto verbatim + known-answer tests); community-graph tap + `saveData` gate with the scoped report-only exception. **M4** (`full`) **exit criterion (§7.6): pongo2 removed for every group**, `transformTemplate`/`native_static_translate` deleted, `pongo2` out of `go.mod`, `embedfs/templates/` empty; `spa.html`, `spa_preview.html`, the 5 snapshots, the legacy tarball, `SOCIAL_REACT_UI` and the legacy journey deleted (one release after S3A shipped); ADRs, STATUS reviewer lines. A group that cannot meet its thresholds is a hard stop for Paul, not a carry-over. | `gate:full` + `qualify`; independent reviewer sign-off per child-safety change; `go list -m all` shows no pongo2 | as S3A + moderation decision logic, GDPR erasure paths |

### 10.3 Parallelism and pinning
```
S0a ──▶ tag core-v1.0 ──▶ S1 cat M0..M2 (pilot green; the ONLY Codex session running — core shakedown, Decision 3)
S1 M2 green ──▶ S0b templ kit (∥ S1 M3..M4 only) ──▶ tag core-v1.N
core-v1.N (templ kit) ──▶ S2A ∥ S3A   (two Codex sessions max)
S2A landed + soak + matrix review ──▶ S2B ; S3A landed + soak + matrix review ──▶ S3B  (S2B ∥ S3B allowed)
```
Never two chats in one worktree; Claude Code is the third active context (review, landing, hotfix). Pin = the `core-v1.N` in `kit/CORE_TAG`, named in the prompt; it moves only through Paul's `KIT_BUMP` (§9-8), never by a session. Sub-session B always branches from `main` after A landed. Count: **4 top-level sessions (S0, S1, S2, S3) = 7 chats** with three volume-justified **sequential** splits, each listed for Paul's ACK in §0.4-1: core — S0a carries 7 milestones (toolchain jump, tokens, 16 components, 7 behaviours, motion kit, 7 Go delivery packages, 10 kit templates) and S0b another 6 (a ~1.5 k-line converter, 7 Go packages, 224 classifier inputs, 3 golden-equal pilots), together ~13 milestones against the ≤7 per context the ExecPlan loop assumes; ro — 7,385 template lines in 9 groups plus 14 islands and 14 widgets; social — 4,596 template lines in 8 groups plus the 20-route SPA retirement, MapLibre 6 and 13 widgets. Each exceeds one context, and the human fixture-matrix review between halves is a natural boundary. No split runs concurrently with cat's shakedown (S1 M0–M2).

## 11. Risks and open questions (ranked; owner; retiring milestone)
1. **No real-device measurement exists**; all timings are loopback 4× CPU. — Paul; each app's device checkpoint after M1.
2. **Future trusted wrapper invocation must be re-proven.** Preparation proved scoped Docker access and candidate rule shapes, not a production bootstrap trust pin or gate. — parent before S0a dispatch.
3. **Escalated wrapper runs with host rights.** Exact path/target rules plus closed parser, protected hashes, source checks and independent clean reruns constrain it; prefix rules alone do not establish integrity.
4. **Preact 11.0.0 is six days old**: Presence/Confetti semantics, preset-vite + Babel 7 under Vite 8/Oxc, no tested browser testing library. — S0a M2/M3 browser tests; a core blocker delays every app session.
5. **TS 7.0.2 dts emit** for roedu-ui unverified. — S0a M0 snapshot test; fallback `@typescript/typescript6` for the dts step (recorded exception).
6. **Production Postgres major unknown.** — Paul before S2A/S3A M0 (§3.2); test env must match prod.
7. **Fixture-matrix cost** (~120 ro + ~150 social cases, estimates; the privacy groups G3p/G2p add consent/erasure/age-verification states) is the largest real unknown; a group that cannot meet coverage is a **hard stop for Paul** (§7.6 exit criterion), which may push a B-session's end date — it never leaves the group on pongo2 by default. — S2A M2 / S3A M3; S2B/S3B M0.
8. **`djt2templ` does not exist**; three pilots may not predict `place_detail.html` (60 roots) or `learning/progress.html` (42 roots). — S0b M4.
9. **ro release-contract churn** (`teacher-go check` pins every template). — S2A M0 kinds + per-group `contract:refresh`.
10. **ScreeningTask/StepRunner construct validity** (no tests today). — S2A M0 timing tests; legacy islands embedded; S2B M4.
11. **Capacity:** native full projects are capped at 10GiB aggregate each; two require 24GiB available headroom. Inspect capacity before builds/gates; never prune unrelated data.
12. **MapLibre 6.12 vs the remote OpenFreeMap style under style-spec 26 and the real-URL worker CSP** verified only by reading. — S3A M2.
13. **Motion 14 size** (5.1 KB with esbuild; Rolldown may differ) and the `framer-motion` hard dependency pulling React types later. — S0a M3 measurement; lockfile check on every KIT_BUMP.
14. **npm 12 strictness** (`allow-remote=none` vs `file:` tarballs untested). — S0a M0 toolchain image build.
15. **LF:** inspect native working tree; preserve original binary/oracle rules, no unnecessary Windows repair commit or evidence renormalization.
16. **social `qualify-native.sh`** (Trivy v0.75.0, govulncheck v1.8.0) must be bumped under "latest" and re-run host-side; `social-native-db:local` (578 MB) needs a reproducible PostGIS/pgvector definition at `PROD_PG_MAJOR`. — S3A M0/M3; Paul at landing.
17. **`ultra` subagents** share the worktree; cap and read-only instruction are prompt-level only. — README fallback to `max`.
18. **Device checkpoint scheduling** blocks three sessions at M1. — Paul schedules it.
19. **social template count** (91 vs 4 vs 358) resolved only by S3A M0; §7.6 group sizes (incl. the G2/G2p split) may renumber; ro's accounts split (14 + 11 + 7 = 32) is counted from the classifier and re-verified at S2A M0.
23. **Frozen legacy tarballs** (§8.2) are binary blobs in git for one release each and carry the old React code's CSP behaviour; a prod rollback to legacy rolls CSP back to report-only. — deleted at the named milestones; `legacy_violations` reported separately.
24. **Per-session rule regeneration** (`gen-rules.sh`) is a manual Paul step; a stale rules file either blocks the wrapper (old path → auto-review on every gate) or, worse, keeps an old worktree pre-approved. — §10.1 entry check runs `execpolicy check` for the three canonical shapes before every session.
20. **Forbidden-rule enforcement under Full access unverified**; a composer mis-click removes every guardrail except review. — never pick Full access; `/status` check.
21. **ADR-number collisions / merge conflicts** with cat's 3 and social's 24 live worktrees. — Paul lands or retires them first; verify numbers at M0.
22. **cat motion feel** (not gateable) and the **MPA soft-navigation gap** on Samsung Internet ≤30 / Firefox. — motion-on project + on-device review + `CAT_UI=legacy`; progressive enhancement with an instant-paint check on device.

Open questions for Paul: `PROD_PG_MAJOR`; production Node/OS on the Linux server (image bases assume none); the six §0.4 ACKs (core split, native host environment exception, `sw.js` via `text/template`, the pinned Playwright triple, Postgres at `PROD_PG_MAJOR`, budgets-in-CI = Linux `gate:unit`); which Samsung A-series phone and when.

## 12. Evidence index
Root: `/home/dobo/work/_worktrees/roedu-ui/docs__gui-migration-linux-20261006/docs/plans/2026-10-06-gui-migration/`.
- `RECOMMENDATION.md` — final reviewed recommendation (superseded by this file where they differ). `review/RECOMMENDATION-draft.md` — pre-attack draft with the original full port plan. `review/attack-approach.json`, `review/attack-facts.json` — the two attacks answered in §7.8 and §4.
- `proposals/{first-principles,go-server-first,preact-evolution,svelte-everywhere,solid-everywhere}.md`; `judges/{perf,llm,risk,ops}.json`.
- `spikes/first-principles.result.json`, `spikes/preact-evolution.result.json`; sources under `spikes/first-principles/`, `spikes/preact-evolution/` (templ port of social `connections.html`, cat Conexiuni port, motion kit, hovercard/combobox ports) — **built on Preact 10.x; reference only**.
- `evidence/recon/{ro_teacher-spa,ro_teacher-server-ui,cat-spa,social,roedu-ui-and-dup,build-test-deploy}.md` — verified recon. `evidence/research/{frameworks-2026,go-server-ui,llm-codegen-perf,animation-interaction,toolchain-2026,design-system-cross}.md` — fact-checked research (`llm-codegen-perf.md` ends with the concrete prompt rules).
- `scratch/versions/` — unavailable Windows scratch reference (not shipped), tarball unpacks, size measurements (Motion, MapLibre). `scratch/probe_*.jsonl` — Codex escalation probes (`docker version`, `git add` via auto-review). `scratch/gates.rules` — the first prefix rules (superseded: its `--cd` prefix allow pre-approved `--cd C:/x -u root -- id`); **`scratch/gates-narrow.rules` + `scratch/probe_narrow.py`** — the narrowed WSL rules of §5.1 and the 14-shape `codex execpolicy check` probe (0.160.1, 14/14 on 2026-10-06; native entry probes are separately required; this Windows scratch is not shipped). `scratch/classify.py` output — 224-template classifier; `scratch/parity.py` — ro parity reference summary; `scratch/wsprobe` — templ v0.3.1070 whitespace/escaping probe; `scratch/critic-buildkit/` — buildx failure reproduction; `scratch/execplans.md` — cookbook ExecPlan text; `scratch/doc_*.md`, `d_*.md`, `e_*.md` — raw doc copies.
- Historical Windows record (not a Linux attestation): `npm view` dist-tags and peers for every npm entry in Appendix A; `go.dev/dl`, `proxy.golang.org`, Docker Hub / gcr.io / mcr tag lists; GitHub advisory API for GHSA-jrc7-96c5-q579; `codex exec` escalation and `execpolicy check`; `wsl.exe --cd` with the spaced path; `/mnt/c` vs ext4 timings; `git ls-files --eol`; WSL docker/buildx/compose/node/go state; the templ render probe; the template classifier; pongo2 `NewFSLoader` at `template_loader.go:21` (v6.1.0). Taken from reports, not re-run: per-route ro byte figures, spike timings, js-framework-benchmark and HTTP Archive figures (correlational), Docker image digests.

## Appendix A — Resolved latest-stable versions (seed, resolved 2026-10-06)
Sessions **re-resolve at M0** (the wrapper's `gen --resolve-versions`, §3.1; the Playwright triple of §0.4-4 is excluded) and may only move up. Method: `npm view <pkg> dist-tags/version/time/peerDependencies/engines --json`, `go.dev/dl/?mode=json`, `proxy.golang.org/<m>/@latest`, Docker Hub v2 / gcr.io / mcr `tags/list`, GitHub releases API.

| Tool | Version | Released | Kind | Notes |
|---|---|---|---|---|
| preact | **11.0.0** | 2026-09-30 | npm | ESM-only; see §2.3 |
| preact-iso | 2.12.2 | 2026-08-11 | npm | peer `preact >=10 \|\| >=11.0.0-0` |
| @preact/signals | 2.11.3 | 2026-09-30 | npm | |
| @preact/preset-vite | 2.10.6 | 2026-07-18 | npm | peer `vite 2–8`, **`@babel/core 7.x`** |
| @babel/core | 7.29.7 (exception) | 2026-05-25 | npm | latest 8.0.6 fails peer |
| preact-render-to-string | 6.8.0 | 2026-10-01 | npm | only if SSR tests need it |
| vite | 8.3.3 | 2026-10-06 | npm | node `^20.19 \|\| >=22.12`; rolldown `~1.2.11` |
| rolldown | 1.2.12 | — | npm | `output.codeSplitting` |
| esbuild (reference) | 0.28.2 | — | npm | in Vite 8's peer range |
| typescript | **7.0.2** | 2026-07-08 | npm | native; `bin: tsc`; no stable JS API |
| @typescript/typescript6 | 6.0.2 | — | npm | only if a tool needs the TS API |
| vitest / @vitest/browser / @vitest/browser-playwright | 5.0.3 | 2026-09-30 | npm | node `^22.12 \|\| ^24 \|\| >=26`; vite `^6.4 \|\| ^7 \|\| ^8` |
| @playwright/test, playwright | 1.63.0 | 2026-09-04 | npm | |
| oxlint | 1.87.0 | 2026-10-05 | npm | + `oxlint-tsgolint` 7.0.2003 |
| oxfmt | 0.72.0 **beta — excluded** | 2026-10-05 | npm | prettier latest as devDependency instead |
| @ast-grep/cli | 0.45.3 | 2026-08-31 | npm | |
| motion | **14.0.0** | 2026-10-02 | npm | hard dep `framer-motion 14.0.0`; `motion/mini` = `animate`, `animateSequence` |
| @zag-js/combobox, @zag-js/vanilla | 1.45.0 | 2026-10-05 | npm | 2.x is `next` |
| maplibre-gl | **6.12.0** | 2026-10-03 | npm | ESM-only; 304.7 KB gz JS |
| leaflet | 1.9.4 | 2023-05-18 | npm | 2.x alpha only |
| 3d-force-graph | 1.80.1 | 2026-09-29 | npm | peer `three >=0.179 <1` (0.186.1) |
| web-vitals | 6.2.3 | 2026-10-05 | npm | |
| axe-core | 4.14.0 | 2026-10-05 | npm | via `axeSource` |
| @axe-core/playwright | 4.13.0 | 2026-08-11 | npm | depends `axe-core ~4.13` |
| @lhci/cli | 0.15.1 (Lighthouse 12.6.1) | 2025-06-25 | npm | advisory only |
| pa11y-ci | 5.0.0 | 2026-10-05 | npm | puppeteer 25; ro browser script only |
| Node.js | **26.10.0** (Current; LTS 2026-10-28) | 2026-09-21 | runtime | bundles npm 11.19.1 |
| npm | **12.2.0** | 2026-09-30 | npm | node `^22.22.2 \|\| ^24.15 \|\| >=26` |
| Go | **1.27.1** | 2026-09-01 | runtime | |
| github.com/a-h/templ (+ CLI) | **v0.3.1070** | 2026-10-04 | gomod | `go 1.26.0`; `go get -tool` |
| github.com/flosch/pongo2/v6 | v6.1.0 | 2026-05-02 | gomod | `NewFSLoader(fs.FS)` at `template_loader.go:21` |
| github.com/vearutop/statigz | v1.5.0 | 2025-04-09 | gomod | |
| go-task/task | v3.54.0 | 2026-10-01 | gomod | fixes GHSA-679p-658w-m3wr; cancel exits 205 |
| golang image | `golang:1.27.1-trixie` | 2026-10-06 | image | pin by digest |
| node image | `node:26.10.0-trixie-slim` | 2026-10-06 | image | `npm i -g npm@12.2.0` |
| postgres image | `postgres:<PROD_PG_MAJOR>-trixie` (latest 18.6) | 2026-10-06 | image | must match prod; `19beta4` excluded |
| debian-slim | `debian:13.7-slim` | 2026-09-12 | image | social base |
| distroless | `gcr.io/distroless/static-debian13:nonroot` | 2026-09-13 push | image | ro and cat base; rolling tag → digest |
| playwright image | `mcr.microsoft.com/playwright:v1.63.0-noble` | — | image | fixed choice; baselines depend on it |
| ffmpeg (Debian 13) | `7:7.1.5-0+deb13u1` | — | apt | |
| toolchain image | `roedu-toolchain:core-v1.0` | — | image | digest filled by Paul's build |
| docker-buildx (WSL apt) | 0.30.1 (environment) | — | apt | upstream 0.37.2 needs docker-ce |

Not checked today: `@types/*`, `three`/`kapsule` beyond peer ranges, Go module minor dependencies, image digests, Trivy/govulncheck latest (S3A M0).

## Appendix B — Glossary
- **ADR** — architecture decision record under `docs/adr/`, append-only, numbered per repo.
- **Baseline** — committed screenshot/axe/size/vitals artifact captured from the pre-change code; read-only; updated only by `GATE-CHANGE:`.
- **Bold group** — a child-safety or privacy/child-data route group (ro G3p, G6–G8; social G2p, G5–G6) needing Paul's human review, 100 % branch coverage and, for social, an independent reviewer.
- **Frozen legacy tarball** — `legacy/<app>-legacy-<sha>.tgz`, the pre-rewrite frontend build cut at M1 and unpacked into `embedfs/legacy/` so `CAT_UI=legacy` / `RO_TEACHER_REACT_UI` / `SOCIAL_REACT_UI` still work after the source is gone; deleted one release later (§8.2).
- **Pre-M1 golden set** — `testdata/golden-pre-m1/`, captured at M0 from the untouched pongo2 tree so M1's edits are reviewed as golden diffs (§7.1.1).
- **`core-v1.N`** — a tag on roedu-ui pinning `@roedu/ui`, `@roedu/web-kit`, the Go kit and the gate contract together.
- **Device checkpoint** — Paul's real-phone LCP/INP measurement after an app's M1; hard stop for M2.
- **`djt2templ`** — the table-driven Django-template-to-templ converter in web-kit.
- **`engine.json`** — committed per-group template-engine modes (`Pongo2 | Templ | Shadow`) with explicit `test` and `prod` columns, selected by `<APP>_ENGINE_ENV` and overridden by `<APP>_TEMPL_ROUTES` / `<APP>_TEMPL_OFF` (§7.4).
- **`kit/`** — the committed staging path (`CORE_TAG`, the two npm tarballs, the Go source archive, `SHA256SUMS`) from which `kit:sync` vendors a core tag; written only by Paul's `GATE-CHANGE: kit stage core-v1.N` (§9-8).
- **`kit:check`** — the `gate:unit` check that the vendored files, gate-file copies and lock match `kit/` (§9-8).
- **ExecPlan** — `docs/execplans/<session>.md`, the session's living plan and restart artifact.
- **`GATE-CHANGE:`** — commit subject prefix required for any edit to read-only gate files; Paul re-runs and hash-compares.
- **`gate:unit` / `gate:full`** — PG-free inner-loop gate vs the full compose + PG + browser gate; both run on Linux via the wrapper.
- **Golden** — normalised pongo2 HTML per case, the oracle the templ port must equal.
- **Island** — a T2 Preact component mounted into a server skeleton via the island protocol.
- **`KIT_BUMP`** — Paul's one-line message after he has staged and synced a newer `core-v1.N` in the session worktree (`KIT_BUMP: core-v1.N applied sha=<sha7>; …`); the session only deletes shims and gates (§9-8).
- **Trust pin** — Paul's `trust` target recording the sha256 of the four gate files under `~/gates/trust/`; no gate runs on unpinned gate files (§4.2 step 5).
- **Live / Replay** — golden tests through HTTP + fixtures (Linux lane) vs through recorded contexts (PG-free).
- **Phase A / Phase B** — bundle a widget unchanged vs rewrite it.
- **`PROD_PG_MAJOR`** — the production Postgres major Paul fills in; the test env matches it.
- **Shadow mode** — serve pongo2, render templ in parallel, log any normalised diff.
- **T0 / T1 / T2** — platform features / light-DOM custom elements / Preact islands.
- **Toolchain image** — `roedu-toolchain:core-v1.N`, the pinned runner every gate executes in.
- **`tree_sha256`** — NUL-safe sha256 over the rsync'd source set (same excludes, relative paths), computed by the wrapper before the task runs and recorded in `result.json`; the reviewer compares it with a clean checkout at `sha`.
- **`vm.Bind`** — the reflection adapter from pongo2-style context maps to generated view-model structs; strict in tests, lenient in prod.
- **Wrapper** — `scripts/gate.sh`, identical to `web-kit/templates/gate.sh`; native absolute bash invocation on an enumerated worktree, scoped approval if needed.


## Native erratum E1 — first consumer and corrective core release

Recorded 2026-10-07 by the automated parent under Paul's direct end-to-end
implementation, owner-operation and no-further-permission authorization. Literal
ACK1–6, PG16, safety/privacy/CSP/a11y gates, trust, original fixture provenance and
real device/live/soak sign-offs remain authoritative. This is not a human physical
measurement or sensitive-page review signature.

Published core-v1.0 at214aada is immutable and its actual code gates passed. An
owning-tag rebuild exposed shipped incremental compiler state changing only the
UI tarball's tsconfig.tsbuildinfo bytes. Canonical consumer bundle staging is held.
The corrective target is core-v1.1 with UI1.0.1 and web-kit0.1.1; two independent
clean builds must reproduce actual TGZ hashes with no compiler-cache members.

The original approved S1 plan retains React/UI0.3 through M1 and switches UI atM2.
Current unconditional first-sync UI activation contradicts that requirement. E1
corrects that activation and startup timing only, by the closed ui_adoption
contract in [.agent/CORE-PATCH-1.md](../.agent/CORE-PATCH-1.md). Default remains
active. The temporary staged-react mode is Cat-only, seals the original UI SDK and
its actual original-runtime receipt, preserves only an already-active old pointer,
and still verifies/stages the selected new UI and adopts the new web-kit/Go kit.
There is no backward switch, alternate tag selector or dependency-graph waiver.

This versioned addition supersedes unconditional UI pointer/old-SDK removal in
§9-8 only while the explicit verified phase is active. The three selected input
archives, committed kit/CORE_TAG, eleven env keys, exact protected/frozen sync-back
controls and owner staging/sync/trust remain unchanged. Report staged UI as actual
pending with its real configuration provenance. M2 unit/full requires enforceable
active UI proof and no staged UI pending; actual device prerequisites are retained.

The same S1 chat first authors/qualifies original React M0 behavior/Presence
fixtures and real application hooks before any dependency or source port. It then
becomes idle for parent kit staging/sync/trust and resumes M0. This supersedes the
first-sync-before-chat-creation clause for this qualified original M0 work; it does
not permit dependent UI adoption before prerequisites are satisfied.

After original-runtime qualification, move the required class/CSSOM explicit-unit
CSP conversion and exact original bundle freeze/retirement before first green
unit. Future generated output uses managed dist/embedfs layout. Normalize active
Motion14/Framer14 ownership and toolchains, then rerun the unchanged original
assertions. Keep existing narrow legacy import/package/compat pending records.
Never exempt inline styles, unsafe URLs, inline handlers, native JSX or generated
old-runtime code by a broad ignore. Original bytes and fallback remain proved.

Support legitimate same-repo Go module replacements only through confined,
symlink-free audited targets with exact matching module identity and recursively
audited requirements. Only those verified local edges omit remote checksum proof.
Other replacements remain refused. go_dirs remains kit destinations; preserve the
independent authcore lane and meaningful SDK use in each actual receiver.

Workers do not edit this owner erratum or the readonly PROGRAM. Implement the
concrete dispatch on dedicated fleet worktrees with justified gate changes and
actual trust. No human permission question or manufactured owner evidence is
required for these authorized repairs. Parent releases only actual green work.

## Native erratum E2 — configured consumer resolver correction

Parent authorized a consumer-tooling core-v1.2 correction for Cat S1 CORE_REQ3 under
[ADR-0010](adr/0010-configured-consumer-version-resolution.md). Keep released
core-v1.0/core-v1.1 immutable and UI runtime source unchanged. UI1.0.2 versions
updated published README metadata; web-kit0.1.2 versions the resolver change.
The packaged resolver must work from configured consumer CWD, owning the npm
manifest beside vendor_dir and auditing confined source Go module closure.
It must validate the complete plan before source writes, preserve incoming
core/environment/Playwright floors and file pointers, and require real E1
staged-react proof for originalUI0.3. App scope resolution records actual direct
app dependencies and forbids downgrades. Native deps still generates locks/sums.

The single gen --resolve-versions trigger, trust/current-result identity, original
fixtures, style/CSP gates and every device/live/privacy/soak checkpoint remain.
Ship only after genuine unit/full and reproducible owning archives pass review;
parent applies the exact kit while Cat is clean and idle, then sends the new
KIT_BUMP. This repairs an SDK prerequisite within Cat's exclusive shakedown,
without starting S0b or another app implementation lane.

## Native erratum E3 — original-runtime budget and pilot acceptance order

Cat CORE_REQ5 supplied an actual unchanged-original Home entry counterexample:
114,086 bytes gzip against the literal40,960 limit and30,720 target. Independent
parent review verified committed manifest/budget hashes. The original program
requires React throughM1, but also green budget checks before replacing it;
already-lazy game screens and the documented ReactDOM share provide no credible
40KiB React entry proof. [ADR-0011](adr/0011-original-runtime-budget-qualification-order.md)
records the parent's correction within the existing implementation authorization.

Preserve budgets.json unchanged. Execute real TestRouteBudgets at every checkpoint,
with complete actual route/entry bindings, and retain its red measured report.
The old120KiB combined JS/CSS checker never substitutes for the40KiB JS gate.
Original qualification and React delivery prerequisite implementation may proceed;
M0/M1 remain formally unqualified while the mandatory budget is red. Accept no
other failed mandatory check as a prerequisite. Preserve every failed aggregate
result; never rename the budget check into a pass, use a skip, omit a route,
raise/null a limit or claim a green unit/full milestone.

For the preliminary M1 CSP-stage transition, the parent may accept precisely
scoped non-budget evidence from an actual full report whose only substantive
failure is the initial budget. Aggregate exit failure remains recorded. Every
required browser, PG, identity, privacy, safety, nonce, CSP and accessibility check
must actually pass; cite that actual failed receipt and independent review rather
than claim the old green-full prerequisite was met. Production activation stays
closed. The enforced test-stage run must preserve the same honest qualification.

The real Samsung A-series Chrome and Samsung Internet checkpoint remains before
M2 runtime adoption, with actual source-named measurements and owner provenance.
An automated desktop observation cannot replace it. Once that prerequisite is
real, M2 also implements Home and the complete necessary shell previously inM3,
so the default replacement entry is genuinely measured. Bind every active route
and separately measured frozen-legacy journey; retain original assertions and
fallbacks. Require actual active UI proof and clean green unit/full, including
40,960 bytes and all unchanged safety/privacy/CSP/a11y checks, before accepting
M2 or startingS0b. An over-budget replacement remains blocked. M3 retains the
remaining screens and logic. No other dependency or release gate changes.
