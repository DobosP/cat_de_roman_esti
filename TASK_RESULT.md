# Task Result — V48 anonymous production rollout

## Outcome

- Fast-forwarded the clean production checkout from rollout-record commit `2853eaf` to
  exact V48 commit `d59caed25a1fdbca7556cb66740beb8cb449cb28`.
- Rebuilt and recreated only the anonymous `app` service through
  `docker-compose.anon.yml` + `.env.anon`; Caddy stayed running and retained TLS ownership.
- The replacement image is `sha256:d18295ae372cb3cf38298d9f0a7eb13a0c1ff78a0347bfc9ef2c93ffa357292c`.
  Its one Python process is healthy with zero restarts.
- Production now serves the exact V48 pack: 618 records = 610 approved + 8 pending /
  449 selectable, including 79 selectable Alchimie boards and promoted Făt-Frumos.
- Accounts and submissions remain disabled. No database, migration, submissions volume,
  second worker, graph change, or deployment-configuration change was introduced.

## Public and runtime proof

- Exact in-container SHA-256 checks passed for KG, pack, rankings, and derived catalog:
  `f2a4229c…`, `05e80ab2…`, `0e2b5cda…`, and `87544c899…`.
- Raw game counts are 232/207/97/82; approved runtime pools are 232/205/94/79; ranked
  eligibility is 74/202/94/79. The frozen derived catalog is 183 Intrusul + 153 Perechi.
- Frontend, `/healthz`, `/api/health`, `/api/manifest`, `/api/me`, and all 14 categories
  passed through public HTTPS. The manifest is `fixture-v44-contexto-common-words` with
  2,364 nodes / 9,217 edges / 180 puzzles.
- Anonymous `POST /api/submissions` returned its required 503. A deterministic literature
  Alchimie request selected Făt-Frumos with a hidden target ID and playable recipe summary.
- Alchimie, Intrusul, Perechi, Conexiuni, Contexto, and Lanț all passed public fixed-seed
  create + exact resume checks, including non-terminal hidden-answer contracts.
- Post-smoke logs contain one expected submissions 503 and zero unexpected errors or 5xx.
  Every game route logged successful requests; Caddy logged no upstream error.

## Pre-deploy verification

- Backend: 726/726; accounts-on: 53/53; bounded sessions: 16/16.
- Frontend: 28/28 tests; ESLint and TypeScript green; production build 118.03/120 KiB with
  the Romanian font-subset gate green.
- Pack, ranking, derived-catalog, KG, Ruff, mirror, and whitespace gates: green.
- Host preflight: clean repository, healthy V43 app, accounts-off anonymous stack, and only
  the expected `app` + `caddy` services.

## Files changed

- `docs/STATUS.md` records exact V48 production state and verified probes.
- `docs/DEPLOY.md` now tags the running known-good image before replacing `latest`; this
  closes the rollback gap observed during this rollout.
- `TASK_RESULT.md` records the sanitized rollout evidence and residual risks.
- No ADR is required: this separately authorized exact-commit rollout changes no default,
  architecture, account mode, worker model, or release decision.

## Residual risks and rollback

- Recreating the app reset active in-memory game sessions. Browser-authored progress and
  records remain local; anonymous production persists no player data.
- The old V43 image was not tagged before rebuild and Docker did not retain its captured
  image ID. This rollout can still roll back by rebuilding exact known-good code commit
  `38da2f4`; the updated runbook preserves an immediate image tag before future rebuilds.
- `npm audit` reports four high findings: brace-expansion and PostCSS are build-only and do
  not enter the runtime image; the two production findings are one React Router advisory.
  The primary advisory applies only to unstable RSC APIs, while this app uses BrowserRouter
  and no RSC API. Track the upgrade separately:
  <https://github.com/advisories/GHSA-qwww-vcr4-c8h2>.
- The shared VPS is appropriate for this low-traffic anonymous pilot, not hardened or scaled
  for a high-load public launch. Accounts remain off pending the compliance checklist.

## Merge recommendation

Production is healthy on V48. Green to land and push this three-file deployment record;
retain the deployment worktree/branch until explicit owner authorization to delete it.
