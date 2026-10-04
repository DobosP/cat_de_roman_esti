# Contributing — cat_de_roman_esti

## Branch & merge policy

Policy: [ADR-0004](docs/adr/0004-branch-merge-policy.md) — direct local merges to `main` once the
gate is green; pushing to `origin` is explicit-request-only; substantial work goes on a `feat/…` /
`fix/…` branch in its own worktree (see [`AGENTS.md`](AGENTS.md) "Parallel work").

## Local quality gate (run before merging)

```bash
go -C go-backend test -race ./... && go -C go-backend vet ./...
go -C shared-go/authcore test -race ./... && go -C shared-go/authcore vet ./...
python scripts/validate_fixture.py                       # offline KG fixture must be GREEN
python scripts/validate_games_pack.py                    # curated pack must be GREEN
ruff check                                               # lint
pytest -q                                                # offline differential/content oracle
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 pytest -q tests/accounts
( cd frontend && npm test && npm run lint && npm run build )
```

Native account release gates require the explicit disposable PostgreSQL flags in
[`docs/agent-testing.md`](docs/agent-testing.md); a skipped default database suite is not
release evidence. Python reference/content and browser helper tooling remains separate.

See [`docs/STATUS.md`](docs/STATUS.md) for current phase and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the original terminal-game model; native web serving is in
[`docs/NATIVE_BACKENDS.md`](docs/NATIVE_BACKENDS.md). Content work follows the
[repository content skill](.agents/skills/romanian-game-content/SKILL.md) and current review
gates; the older `expand_content.py` path is historical, not a release shortcut.
