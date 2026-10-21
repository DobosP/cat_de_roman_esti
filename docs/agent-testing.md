# Agent Testing Guide — cat_de_roman_esti

Last reviewed: 2026-10-18 — guidance/source only; actual qualification and accepted milestones remain in [STATUS](STATUS.md).

## Native serving gates

Go serves the arcade/accounts/content (Go 1.27.3 for release builders and the core-v1.13 gate runner: [ADR-0208](adr/0208-go-1-27-3-security-release-builders.md), [ADR-0209](adr/0209-kit-bump-core-v1-13.md)); current GUI source uses Preact11/preact-iso (ADR-0202/0204). Selected Node26.10.0/npm12.2.0, native TS7/Oxlint/tsgolint and SDK AST checks follow [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md).
[ADR-0162](adr/0162-select-go-production-backend.md) and [ADR-0163](adr/0163-complete-native-go-accounts.md)
record serving boundaries; [ADR-0166](adr/0166-native-content-operators-and-builder-rails.md)
records native operator/review rails. Python below is an optional reference ([ADR-0186](adr/0186-go-authoritative-content-validation.md)).
GUI commands execute inside the owning pinned wrapper, not host npm/Go. From the trusted task worktree use literal clean `<full-SHA>`:
`GATE_OPERATOR=agent:codex bash scripts/gate.sh unit --sha <full-SHA> --parallel 2`; full: `python3 -I scripts/gui-full-runner.py --sha <full-SHA> --parallel 2`.
Focused/dirty iterations use the owning `shell --sha <full-SHA> --dirty` and committed preflight. Table commands are inner checks; a shell/preflight pass is not canonical acceptance.

| Scope | Command | Expected |
|---|---|---|
| Native backend | `go -C go-backend test -race ./... && go -C go-backend vet ./...` | all hermetic game/HTTP/content contracts pass |
| Shared native identity | `go -C shared-go/authcore test -race ./... && go -C shared-go/authcore vet ./...` | crypto/session/provider fixtures pass |
| Native account release | `go -C go-backend test -race ./internal/accounts -accounts.database <disposable-dsn>` | real PostgreSQL migration/consent/erasure contracts pass |
| Native combined HTTP release | `go -C go-backend test -race ./internal/httpapi -arcade.database <disposable-dsn>` | real signup/consent/game ownership/credit/erase races pass |
| Native content check | `go -C go-backend run ./cmd/cat-content-ops check --root .. --check` | graph/pack, full rank/derive values, exact native format/mirrors and source stability |
| Native source freshness | `go -C go-backend run ./cmd/cat-content validate --root .. && go -C go-backend run ./cmd/cat-content export --root .. --check` | complete source gates and exact sealed export |
| Independent frozen HTTP | `go -C go-backend run ./cmd/cat-qualify parity --binary <native-binary>` | every source-bound independent expected response; current count in STATUS |
| Frontend (pinned shell) | `cd frontend && npm ci && npm test && npm run typecheck && npm run lint && npm run build` | original30/legacy frozen; managed dist synced before Go rebuild (ADR-0184) |
| Browser (pinned runner) | `cd frontend && npm run test:e2e` after managed Go/planner/browser setup | original live-game/recovery/keyboard/motion/drag assertions; no device testing (ADR-0199) |
| Native docs (pinned shell) | `go -C go-backend run ./cmd/cat-doc-check --root .. --inventory docs/tracked-markdown.json` | empty error/budget arrays |
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
Historical Node24/React/ESLint receipts do not qualify current Preact/Oxlint source. Keep historical/frozen references intact; record current wrapper/source/toolchain identities in STATUS.
Playwright setup uses `npx playwright install chromium`; `CDR_E2E_PORT` and
`CDR_E2E_OUTPUT_DIR` scope the local server and scratch receipts. Private answer helpers run Go; `CDR_BROWSER_PLAN_BINARY` selects the scratch planner.
Windows targeted reference tests use `PYTHONUTF8=1`; the full Unix `resource`-using suite needs WSL.
For browser fixtures, build `cat-browser-plan` and set its absolute scratch path.

## Before commit

1. Run docs/whitespace checks only for documentation changes; no game/asset rebuild. GUI iterations use focused checks/unit and full once per milestone (ADR-0199/0200); no device tests.
2. Native behavior changes run focused Go race/vet and applicable PG/HTTP release lanes.
3. Content changes run native source/operator/rail freshness and independent review contracts; `cat-content-rail all --root .. --check` runs fresh native audits under main's [behaviour-bound rule](adr/0189-behaviour-bound-installed-content-authorities.md): strict three auditor pins, exact artifact/review/source bindings and guarded runtime readsets remain mandatory. Runtime hashes are recorded provenance; other HTTP/GUI/safety gates remain independent.
4. Frontend changes run required tests/types/lint/build, managed sync/Go rebuild and applicable browser/PNG/axe/CSP/vitals/route budgets. Preserve original30/legacy and historical receipts; never hand-commit a new `web/static` bundle (ADR-0184).
   Entry, mandatory AccountBar, real selected game/mode leaves and recursive imports stay charged (ADR-0185/0202); no lazy required leaf is omitted. Backend/docs-only changes do not regenerate frontend output.
5. Record exact commands/results in `docs/STATUS.md`; overflow history belongs in WORKLOG.

## Optional load-sensitive reference check

`tests/test_alchimie_sparse_recipes.py::test_many_mined_sessions_stay_bounded_solvable_and_fast`
asserts a 45-second wall-clock bound. Check host load and repeat on a quiet host before
classifying an isolated timing failure as a regression; do not weaken its assertion.
Reference `tests/accounts/` collection requires `CAT_ACCOUNTS_ENABLED=1`.
Current content expectations: [ADR-0116](adr/0116-share-current-content-test-expectations.md),
`tests/current_content.py` and `tests/content_scenarios.py`; historical pins remain separate.

The separate `scripts/qualify_go_toolchain.sh` source alignment already selects exact Node 26.10.0 per [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md); aligned standalone qualification remains **UNQUALIFIED, NOT RUN**.
It remains separate from the owning GUI wrapper; actual Linux/version/lint context, disposable PG/task scratch and all native/privacy/browser qualification obligations remain.
[ADR-0168](adr/0168-qualify-complete-native-toolchain.md) retains historical Node 24 proof; [NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md) records the pending aligned recipe. No missing required gate becomes a skip. The native content check starts no PG or frontend scope.
