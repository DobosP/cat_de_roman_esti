# Agent Testing Guide — cat_de_roman_esti

## Environment
- Runtime: Python for backend/game tests; frontend tooling only when frontend files are touched.
- Current verified Python interpreter on this box is the `romania_scraper` venv.

## Commands
| Scope | Command | Expected success |
|---|---|---|
| Word-game sessions | `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q` | `10 passed` on current setup |
| Whitespace | `git diff --check` | no output |
| Frontend | run project package build/test only if frontend files changed | build/test passes |

## Before commit
1. Run `git diff --check`.
2. Run targeted pytest for changed word-game/session code.
3. Run frontend build/test only when frontend files are touched.
4. Record exact command output in worker result files.

## Known blockers
- If the shared Python venv is unavailable, create/use a project venv and update this guide after verifying.
- Do not commit generated frontend build artifacts.
