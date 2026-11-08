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
