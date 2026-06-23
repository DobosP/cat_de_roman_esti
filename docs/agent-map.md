# Agent Map — cat_de_roman_esti

## What this repo owns
- Romanian-language app/game behavior.
- Word-game session services and tests.

## Entry points
| Area | Path | Notes |
|---|---|---|
| Word games | `cat_de_roman_esti/wordgames/` | Session/service behavior. |
| Tests | `tests/` | Pytest suite for game/session behavior. |
| Status | `docs/STATUS.md` | Existing durable project status. |

## Read first
1. `AGENTS.md`
2. `docs/STATUS.md`
3. `docs/agent-testing.md`
4. Relevant service/test files

## Common task routes
| Task type | Start here | Verify with |
|---|---|---|
| Word-game session fix | `cat_de_roman_esti/wordgames/service.py`, matching tests | targeted wordgames pytest |
| UI/frontend touch | frontend source and package scripts | frontend build/test if touched |
| Docs/status | `docs/STATUS.md`, `README.md` | `git diff --check` |

## Do not load by default
- Build outputs
- Local caches/logs
- Secret/env files

## Known pitfalls
- Session stores must stay bounded; do not reintroduce unbounded in-memory growth.
- Use deterministic tests for TTL/max-size behavior.
