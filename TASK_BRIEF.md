# Task Brief

## Goal
Expose bounded server-authored Alchimie crafting lineage inline with touch-friendly recovery if the audit supports it. Preserve hidden target, scoring, deterministic recipe validation, two-hour sliding TTL, and 1,000-entry session cap. Targeted gate: python -m pytest tests/test_wordgames_alchimie.py tests/test_wordgames_session_store.py -q; frontend lint, typecheck, tests, and build if frontend files change.

## Repo / branch
- Repo: `C:\Users\Paul Work\personal_repos\cat_de_roman_esti`
- Base branch: `main`
- Worker branch: `feat/alchimie-crafting-lineage-v26`
- Worktree: `C:\home\dobo\work\_worktrees\cat_de_roman_esti\feat__alchimie-crafting-lineage-v26`

## Context to read first
1. `AGENTS.md` or `.hermes.md`
2. `README.md`
3. `docs/agent-map.md`
4. `<task-specific source/test files>`

## Non-goals
- Do not broaden scope beyond the task; do not touch secrets or unrelated files.

## Acceptance criteria
- [ ] Implement the requested change with minimal scope.
- [ ] Add/update focused tests or document why no test applies.
- [ ] Run the verification commands and record exact results.

## Verification commands
```bash
# fill in project-specific targeted test command
# fill in lint/typecheck/build command if applicable
```

## Safety constraints
- Never read or print secret values.
- Do not run recursive deletes outside the worktree or `~/work/_temp/`.
- Do not commit, push, or merge unless the dispatcher/human explicitly asks.
- Keep result artifacts out of commits unless requested.

## Required output
Write `TASK_RESULT.md` with:
- summary
- files changed
- commands run and exact results
- risks/manual review
- merge recommendation

Direction changed? ADR + STATUS.md update is part of definition of done.
