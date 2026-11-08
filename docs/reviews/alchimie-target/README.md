# Target-based Alchimie qualification

Valid until: a later Alchimie qualification supersedes this product — then treat as history.

Verified 2026-11-08 on `a4ed7013f5bfd42a06bb38d79b2382cedb8006ea` in PR #3.
Operator: agent:codex (PROGRAM E8).

- `GATE_OPERATOR=agent:codex bash scripts/gate.sh unit --sha a4ed7013f5bfd42a06bb38d79b2382cedb8006ea --parallel 4` passed 27/27.
  Result SHA-256 `ee5e26c56bf85a9515694a007d52f216ffb89cdaf5fcfd69cca2e4a3643f7b43`.
- `python3 -I scripts/gui-full-runner.py --sha a4ed7013f5bfd42a06bb38d79b2382cedb8006ea --parallel 4` passed 37/37.
  Result SHA-256 `4e150bf5a70b56a7cab1e2edbc982303d77c26746d12f64682fdc5ed2c5499d6`.
  Supervisor SHA-256 `5a6d08222c6cdc902c5d98956101610e158f141624b74cb879b348d819ff3ca4`; owned containers and network cleaned.

Playwright passed 859/859 with zero skips, unexpected failures, retries or flaky
cases. Report SHA-256 `18cc3b03cb97162a5d54e5db0647f369cb19f1d5d0ecfdab8d433bc2274b17dd`.
Seven original screenshots matched exactly. Both historical Alchimie screenshot
hashes were preserved, and the live aliases matched each other byte for byte.
Axe, vitals, explicit disposable PostgreSQL, 1206 HTTP parity cases and the frozen
legacy journey passed. Enforced CSP reported zero current and legacy violations.
Comparisons SHA-256 `eff1d74ae653e61ab3d5f89e66a41db3f750263868cfc90726ad764512e7ab38`.
CSP SHA-256 `48dd77639bd8b16ea9afaae8774c691065869b3e5115ffcf253ddbbe654d0f55`.

The first full on `4a5d6f5c` reported 852/859. Its only browser failures
were obsolete mode-query assertions and the replay test's scroll precondition.
Result SHA-256 `7e99405d4538f851e2d483ee77546b070f80a523c353c9f8d76f8763fcef2160`.
The corrected test-only commit retained the original checks' intent and all
unrelated identities. The rolling gate setup replaced the superseded raw run.

[ADR-0224](../../adr/0224-target-based-alchimie.md) · [PR #3](https://github.com/DobosP/cat_de_roman_esti/pull/3)

## Integration with main 37207de2 (landing)

Feature head `1c77d298` was merged with main `37207de2`, which carries the V3 content landing.
The integration commit is `9d1f1eb82f27139fe9649a9475d8d6b2e831e941`.
Outside `docs/STATUS.md` and `docs/tracked-markdown.json` it equals main plus exactly the branch delta.
Both 2026-11-08 STATUS records and both inventory sides were kept.
Operator: agent:claude-code.

- `GATE_OPERATOR=agent:claude-code bash scripts/gate.sh unit --sha 9d1f1eb82f27139fe9649a9475d8d6b2e831e941 --parallel 4` passed 27/27.
  Result SHA-256 `d918e1a939df623bfd0b95b8bf8871b523b6b1e96cc7b06712bc45034386e5aa`.
- `env -u GATE_OPERATOR python3 -I scripts/gui-full-runner.py --sha 9d1f1eb82f27139fe9649a9475d8d6b2e831e941 --parallel 4` passed 37/37 (859 browser cases, 0 skipped/unexpected/flaky; enforced CSP 0 current/0 legacy).
  Result SHA-256 `0e9bd8e92e25a4f3b30c2f7948c04258a4de204e2ce9bc056ef8dd6b57a5f934`.

Independent review (four lenses with an adversarial refutation stage and a final judge) found no blocker or major issue.
The lenses were: requirements, preservation and numeric limits, GUI build and correctness, and compatibility and data.
Budgets, baselines, frozen legacy bundles, `web/static`, `go.mod`/`go.sum` and screenshot files are byte-identical from main to the integration.
No numeric gate constant changed.
Recorded minor follow-ups (not blocking):
- The live intro has no pixel golden (ADR-0224 authorizes alias equality).
- On phones the bench is not sticky.
- The completion block lacks a live-region announcement.
- The recipe count and search cover the last 12 reactions.
- The Romanian "de" plural is wrong for 101–119.
- No test asserts the two-column layout at ≥760px.
- `frontend/historical-e2e/alchimie/` is archival and not executed; the reproducible Explore journeys live on `2cacc878`.
- Home still emits a vestigial `?mode=challenges`.
ADR-0205's exploration-before-common CSS-order clause is marked superseded by ADR-0224, which removed that stylesheet.
