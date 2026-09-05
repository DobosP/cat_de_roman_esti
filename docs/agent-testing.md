# Agent Testing Guide — cat_de_roman_esti

Last verified: 2026-09-06

## Environment
- Interpreter: `~/work/cat_de_roman_esti/.venv/bin/python` (Python 3.12.3; Django 5.2.16, pytest 9.1.1,
  pytest-django). It is gitignored and lives only in the shared checkout.
- From a task worktree, prefix every command with `PYTHONPATH=.`.
- Fresh venv: `pip install -c constraints.txt -e ".[dev,web]"` (ci.yml:48).
- Never use the `romania_scraper` venv: it has no Django, so collection gives 7 errors and only
  402 of 898 tests (verified 2026-09-05).
- Frontend needs Node 24 (ci.yml:76).

Below, `<interp>` = `~/work/cat_de_roman_esti/.venv/bin/python`.

## Commands
| Scope | Command | Expected |
|---|---|---|
| Word-game sessions | `PYTHONPATH=. <interp> -m pytest tests/test_wordgames_session_store.py -q` | `16 passed` |
| KG/app-pack contract | `PYTHONPATH=. <interp> -m pytest tests/test_app_pack_contract.py tests/test_data_client.py -q` | `23 passed` |
| Full backend | `PYTHONPATH=. <interp> -m pytest -q` | `922 passed`, 4m30s for V73 (load ≈ 5) |
| Accounts suite | `CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. <interp> -m pytest -q tests/accounts` | `53 passed` |
| Fixture gate | `<interp> scripts/validate_fixture.py` | `GREEN: fixture is valid (0 errors)` |
| Pack gate | `<interp> scripts/validate_games_pack.py` | `games pack GREEN` |
| Lint | `<interp> -m ruff check` | `All checks passed!` |
| Whitespace | `git diff --check` | no output |
| Frontend | `cd frontend && npm ci && npm test && npm run lint && npm run build` | build lands `cat_de_roman_esti/web/static/index.html` (ci.yml:92-95) |
| Browser | `cd frontend && npm run test:e2e` (after build + `npx playwright install chromium`) | six real-backend games, desktop + mobile; Python web runtime on `PATH` |
| Docs | `python3 ~/work/agent-ops/scripts/check_docs.py .` | `dead_links=0 stale_terms=0 retired_verbs=0 orphans=0` |

`pyproject.toml` sets `addopts = "-q"`, so a passing run prints dots only; add `-o addopts=""` when you
need the `N passed` summary line to paste into the verification record.

## Before commit
1. Run `git diff --check`.
2. Run targeted pytest for changed word-game/session code.
3. Run frontend build/test only when frontend files are touched; a frontend source change also commits the
   regenerated `cat_de_roman_esti/web/static` bundle and `.vite/manifest.json` (ADR-0020). Backend-only
   changes must not regenerate that bundle.
4. Record the exact commands and results in the `docs/STATUS.md` verification record (`TASK_RESULT.md` is retired).

## Known flaky / blocked
- `tests/test_alchimie_sparse_recipes.py::test_many_mined_sessions_stay_bounded_solvable_and_fast` asserts
  `elapsed < 45.0` (line 211) and is load-sensitive: on 2026-09-05 it passed inside the full suite at host load
  average ≈ 28 and failed alone at 49.0 s at load ≈ 39. Check `uptime` and re-run on a quieter host before
  treating a failure as a regression; no assertion other than the timing one fails.
- `tests/accounts/` is collect-ignored unless `CAT_ACCOUNTS_ENABLED=1` (pyproject.toml:75-77).
