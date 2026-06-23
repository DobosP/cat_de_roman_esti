# Agent Instructions — cat_de_roman_esti

## Project summary
`cat_de_roman_esti` is a Romanian-language app/game project in the RO-EDU fleet. Word-game/session behavior should stay bounded, deterministic, and test-covered.

## Read first
1. `docs/STATUS.md` for durable status.
2. `README.md` if present.
3. `docs/agent-map.md` and `docs/agent-testing.md`.
4. Task-specific service/test files.

## Token discipline
- Start with the feature area named in the task; do not load the whole app.
- Avoid large generated frontend/build artifacts and local caches.
- Use exact test/file anchors instead of pasted source dumps.

## Safety
- Never read or print secret values.
- Do not push or merge unless Paul explicitly asks.
- Keep game/session fixes narrow and test-backed.

## Commands
- Word-game session test: `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`
- Whitespace: `git diff --check`
- Frontend build/test only if frontend files are touched.

## Dispatch
- One game/session behavior change per branch/worktree.
- Worker briefs must include expected TTL/size/session behavior and targeted test command.
