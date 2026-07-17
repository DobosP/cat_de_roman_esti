# Task Brief

## Goal
Repair the stale v25 byte-stability SHA after the common-word dataset pack landed first. Change no pack or runtime behavior; verify both pack copies remain byte-identical and validator-green. Run the failing v25 test, full pytest, Ruff, both validators, workflow syntax, and git diff --check.

## Repo / branch
- Repo: `C:\Users\Paul Work\personal_repos\cat_de_roman_esti`
- Base branch: `main`
- Worker branch: `fix/v25-pack-baseline-integrity`
- Worktree: `C:\home\dobo\work\_worktrees\cat_de_roman_esti\fix__v25-pack-baseline-integrity`

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
