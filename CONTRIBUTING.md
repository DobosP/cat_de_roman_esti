# Contributing — cat_de_roman_esti

## Branch & merge policy

Policy: [ADR-0004](docs/adr/0004-branch-merge-policy.md) — direct local merges to `main` once the
gate is green; pushing to `origin` is explicit-request-only; substantial work goes on a `feat/…` /
`fix/…` branch in its own worktree (see [`AGENTS.md`](AGENTS.md) "Parallel work").

## Local quality gate (run before merging)

```bash
python scripts/validate_fixture.py                       # KG fixture must be GREEN
python scripts/validate_games_pack.py                    # curated pack must be GREEN
ruff check                                               # lint
pytest -q                                                # backend (offline fixture, accounts off)
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 pytest -q tests/accounts
( cd frontend && npm test && npm run lint && npm run build )
```

Interpreter + expected outputs: [`docs/agent-testing.md`](docs/agent-testing.md).

See [`docs/STATUS.md`](docs/STATUS.md) for current phase and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the game model. Editing KG content? Use `scripts/expand_content.py` (it regenerates
puzzles via the validator's own BFS and refuses to emit anything the gate would reject).
