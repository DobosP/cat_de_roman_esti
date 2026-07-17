# Task Brief

## Goal
Audit and complete the critique layer, then author a web-grounded game-content session; keep the 2-hour TTL and 1000-entry per-game LRU unchanged and run tests/test_critique_pack.py plus relevant validators.

## Repo / branch
- Repo: `C:\Users\Paul Work\personal_repos\cat_de_roman_esti`
- Base branch: `main`
- Worker branch: `feat/critique-content-v22`
- Worktree: `C:\Users\Paul Work\personal_repos\_worktrees\cat_de_roman_esti\cat_de_roman_esti\feat__critique-content-v22`

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
