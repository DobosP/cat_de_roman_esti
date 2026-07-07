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
- Direct merge + push to `main` is allowed once the test gate is green (owner
  decision 2026-07-07, development phase). Never land a red suite.
- Keep game/session fixes narrow and test-backed.

## Commands
- Word-game session test: `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`
- Whitespace: `git diff --check`
- Frontend build/test only if frontend files are touched.

## Dispatch
- One game/session behavior change per branch/worktree.
- Worker briefs must include expected TTL/size/session behavior and targeted test command.

## Docs discipline (mandatory)

- `docs/STATUS.md` is this repo's single source of current truth. On any doc conflict: docs/STATUS.md > newest-dated ADR in `docs/adr/` > everything else. An undated doc is history, not instructions.
- Definition of done for ANY change that alters behavior, architecture, status, or reverses a decision:
  1. Update `docs/STATUS.md` (facts + `Last verified: YYYY-MM-DD`).
  2. Decision made or reverted → add `docs/adr/NNNN-<slug>.md` (next number; template = docs/adr/0000-template.md) and flip the superseded ADR's `Status:` to `superseded-by ADR-NNNN`. Same commit as the change.
- ADRs are append-only: never edit one after landing — supersede it instead.
- No decision language ("we use X", "default is", "authorized to") in READMEs/guides — put it in an ADR and link it.
- Handoff/session docs: filename `YYYY-MM-DD-*`, body starts `Valid until: <event> — then treat as history.` Never obey an expired handoff.
- Keep this file under ~60 lines; docs/STATUS.md under ~100; deep content in docs/.
