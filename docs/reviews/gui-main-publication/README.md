# Main publication review — 2026-10-21

Valid until: the next change to `main` — then treat as history.

Scope: `origin/main` `3d602215` → local `main` `fb829aaa` (300 commits, fast-forward): GUI S1 M1–M4 and
reviewed content V1.8–V1.13. Authority: [ADR-0206](../../adr/0206-owner-authorized-main-publication.md).

Method: Claude Code orchestrator, independent of the Codex implementation. Five read-only reviewers
(gameplay/scoring/persistence; delivery/CSP/budgets; keyboard/focus/accessibility; content integrity;
evidence), one refutation pass per dimension, final adjudication. No product gate was re-run: product
`16733891` keeps its accepted unit27/full38/image2 evidence and `16733891..fb829aaa` is documentation only.

Checks executed by the reviewers: storage-key sets of `frontend/src` at production `abe93377` and
`fb829aaa` identical; STATUS V1.13 pins equal file hashes; `cat-content validate` and `export --check`
pass; content data byte-identical to reviewed `ed9932fa`; no secrets or large binaries; all M4 archive
numbers re-derived from the extracted unit/full/image evidence; `go test -count=1` of
`TestStateInventoryMatchesLegacy|TestManagedNonceLegacyAndInvalidFlag|TestManagedDelivery` passes.
The orchestrator verified all six archive SHA-256 values and sizes before the push.

Verdict: ready-with-notes, no blocker. Published: `git push origin main` → `3d602215..fb829aaa`;
`git ls-remote origin refs/heads/main` = `fb829aaa150c6263a92dc061befd254d4f5aeea8`.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| KFA-1 | medium | Retired React source-regex tests left Conexiuni Esc/Backspace clear (`Conexiuni.tsx:557`) and the Lanț `.lant-current` live region (`Lant.tsx:712`) without an assertion; the retirement map overstates replacement | Behaviour ships; first follow-up: two e2e cases and corrected map rows |
| EQ-1 | medium | CSS ceiling 16,093 is default-level gzip while actual 16,043 is level 9; "50 B headroom" is overstated | Docs follow-up: state the basis, re-derive with one compressor |
| DCR-1 | medium | A managed-UI build error (e.g. invalid `CAT_CSP_ENFORCE`) gives a silent site-wide 503 while `/healthz` stays 200 | Fail fast at startup before production enables enforcement |
| DCR-2 | low | Production compose stays CSP report-only; qualification ran enforced | Owner decision at deploy time |
| GSP-1 | low | Alchimie Challenge "Schimbă opțiunile" disabled during action-sync recovery | Restore or record intent with an e2e |
| KFA-2 | low | No `role=status` fallback while a lazy screen chunk loads | Follow-up |
| DCR-5 | low | Default listen moved from `127.0.0.1:8081` to `:8000` | Document or default to loopback outside the container |
| EQ-2 | low | `historical-test-replacements.json` partly stale | Docs follow-up with KFA-1 |
| CII-3/4, DCR-3/4/6/7 | low/info | Owner-approved parity 1207→1206; duplicate ADR numbers 0185/0186/0188/0189; web-kit q=0/Vary; dead `managedPortedRoutes`; public build identity | Tracked / kit request / cleanup |

Not covered: no browser, Playwright, `gate.sh`, Docker or npm re-run; no Romanian content-quality judgement.
