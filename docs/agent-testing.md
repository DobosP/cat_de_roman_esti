# Agent Testing Guide — cat_de_roman_esti

Last verified: 2026-10-08 — documentation/source review only; amended runtime gates NOT RUN.

## Native serving gates

Go 1.27.1 serves the arcade, accounts/proposals and native content/tooling; selected Node 26.10.0/npm 12.2.0 SPA tooling follows [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md).
[ADR-0162](adr/0162-select-go-production-backend.md) and [ADR-0163](adr/0163-complete-native-go-accounts.md)
record serving boundaries; [ADR-0166](adr/0166-native-content-operators-and-builder-rails.md)
records native operator/review rails. Python commands below are optional independent references.

| Scope | Command | Expected |
|---|---|---|
| Native backend | `go -C go-backend test -race ./... && go -C go-backend vet ./...` | all hermetic game/HTTP/content contracts pass |
| Shared native identity | `go -C shared-go/authcore test -race ./... && go -C shared-go/authcore vet ./...` | crypto/session/provider fixtures pass |
| Native account release | `go -C go-backend test -race ./internal/accounts -accounts.database <disposable-dsn>` | real PostgreSQL migration/consent/erasure contracts pass |
| Native combined HTTP release | `go -C go-backend test -race ./internal/httpapi -arcade.database <disposable-dsn>` | real signup/consent/game ownership/credit/erase races pass |
| Native source freshness | `go -C go-backend run ./cmd/cat-content validate --root .. && go -C go-backend run ./cmd/cat-content export --root .. --check` | complete source gates and exact sealed export |
| Independent frozen HTTP | `go -C go-backend run ./cmd/cat-qualify parity --binary <native-binary>` | all 1207 independent expected responses/source bindings |
| Frontend | `cd frontend && npm ci && npm test && npm run lint && npm run build` | original30 frozen; managed output/retirement per ADR-0184 |
| Browser | `cd frontend && npm run test:e2e` after build/browser setup | Go server/private planner; six real journeys on desktop/mobile |
| Native docs | `go -C go-backend run ./cmd/cat-doc-check --root ..` | empty error/budget arrays |
| Whitespace | `git diff --check` | no output |

Native PG gates require an explicit disposable fixture, never a live or production DSN.
Default Go runs skip those tests without the flags and cannot establish release qualification.
Provider tests use local mocks only. Production accounts/proposals remain gated off.
Build/runtime/container and retained Rust research commands: [NATIVE_BACKENDS](NATIVE_BACKENDS.md).

## Offline content/reference environment

`<interp>` is `~/work/cat_de_roman_esti/.venv/bin/python` (Python 3.12/Unicode 15 export).
The venv is gitignored in the shared checkout; from a worktree set `PYTHONPATH=.`.
A fresh reference venv uses `pip install -c constraints.txt -e ".[dev,web]"`.
Django/pytest-django support the offline oracle, not the selected serving process.
Do not use the `romania_scraper` venv: its missing Django gives incomplete collection.
Other supported Python versions test the retained implementation without regenerating the export.

| Scope | Command | Expected |
|---|---|---|
| Reference sessions | `PYTHONPATH=. <interp> -m pytest tests/test_wordgames_session_store.py -q` | `16 passed` |
| KG/app-pack reference | `PYTHONPATH=. <interp> -m pytest tests/test_app_pack_contract.py tests/test_data_client.py -q` | `23 passed` |
| Full offline reference/content | `PYTHONPATH=. <interp> -m pytest -q` | totals in [STATUS](STATUS.md); timing is load-sensitive |
| Reference accounts | `CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. <interp> -m pytest -q tests/accounts` | `53 passed`; no production activation |
| Fixture | `<interp> scripts/validate_fixture.py` | `GREEN: fixture is valid (0 errors)` |
| Pack | `<interp> scripts/validate_games_pack.py` | `games pack GREEN` |
| Reference/content lint | `<interp> -m ruff check` | `All checks passed!` |

`pyproject.toml` adds `-q`; use `-o addopts=""` when recording assertion totals.
Original Node 24 qualification is historical; selected ADR-0184 tooling needs actual owning Linux context/version evidence and complete normalized qualification.
Playwright setup uses `npx playwright install chromium`; `CDR_E2E_PORT` and
`CDR_E2E_OUTPUT_DIR` scope the local server and scratch receipts. Private answer helpers run Go; `CDR_BROWSER_PLAN_BINARY` selects the scratch planner.
Windows targeted reference tests use `PYTHONUTF8=1`; the full Unix `resource`-using suite needs WSL.
For browser fixtures, build `cat-browser-plan` and set its absolute scratch path.

## Before commit

1. Run docs/whitespace gates; documentation-only changes need no game or asset rebuild.
2. Native behavior changes run focused Go race/vet and applicable PG/HTTP release lanes.
3. Content changes run native source/operator/rail freshness and independent review contracts.
4. Frontend JS/TS/CSS changes run applicable frontend/build/browser gates. Keep original30 frozen;
   managed output sync and reviewed source retirement follow ADR-0184; backend/docs-only edits do not regenerate output.
   After integration, [ADR-0185](adr/0185-accepted-eager-startup-bundle-accounting.md) counts entry+mandatory AccountBar recursive static JS/CSS once in the build check.
   Default helper/frozen historical closures stay static-only; source is unapplied/unqualified and amended tests NOT RUN. All native/privacy/browser checks remain.
5. Record exact commands/results in `docs/STATUS.md`; overflow history belongs in WORKLOG.

## Known load-sensitive reference check

`tests/test_alchimie_sparse_recipes.py::test_many_mined_sessions_stay_bounded_solvable_and_fast`
asserts a 45-second wall-clock bound. Check host load and repeat on a quiet host before
classifying an isolated timing failure as a regression; do not weaken its assertion.
Reference `tests/accounts/` collection requires `CAT_ACCOUNTS_ENABLED=1`.
Current content expectations: [ADR-0116](adr/0116-share-current-content-test-expectations.md),
`tests/current_content.py` and `tests/content_scenarios.py`; historical pins remain separate.

The separate `scripts/qualify_go_toolchain.sh` source alignment prepares exact Node 26.10.0 per [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md); **UNAPPLIED, UNQUALIFIED, NOT RUN**.
It remains separate from the owning GUI wrapper; actual Linux/version/lint context, disposable PG/task scratch and all native/privacy/browser qualification obligations remain.
[ADR-0168](adr/0168-qualify-complete-native-toolchain.md) retains historical Node 24 proof; [NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md) records the pending aligned recipe. No missing required gate becomes a skip.
