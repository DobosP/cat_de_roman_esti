# Main publication review follow-ups — 2026-10-21

Valid until: the next change to `main` — then treat as history.

Scope: the medium findings of the [main publication review](../gui-main-publication/README.md),
fixed on `fix/gui-publication-followups` from `main` 1fbaad12. Operator: agent:claude (Claude Code).
Product: `20dab663` (`cbe86017` e2e, `20dab663` fail-fast); later commits on the branch are documentation only.

| ID | Change | Proof |
|---|---|---|
| KFA-1 | `frontend/e2e/conexiuni-keyboard-clear.spec.mjs`, `frontend/e2e/lant-live-region.spec.mjs` (desktop+mobile; inventory 933→937) | Focused shell on the built product: 4/4 pass. Five temporary source mutants, each rebuilt inside the gate mirror and never committed, fail their spec on both projects (table below) |
| DCR-1 | cat-server exits before serving when `ManagedUIError()` is non-nil; `-replay` exempt ([ADR-0207](../../adr/0207-fail-fast-on-unavailable-managed-ui.md)) | `cmd/cat-server/managed_ui_test.go` fails on the unfixed binary (`/healthz` answered while `GET /` = 503) and passes with the fix |
| EQ-1 | [ADR-0205 erratum](../../adr/0205-canonical-game-css-and-browser-contracts.md), STATUS, handoff, execplan | [css-gzip-basis.json](css-gzip-basis.json): one compressor for original and actual CSS |
| EQ-2 | `gui-m4/historical-test-replacements.json` erratum + two corrected rows; execplan rows | `gui-normalized-react/corrected-retirement-mapping.json` stays byte-identical (sha256 eebdd05b is bound by two review records) and is superseded for those rows |

## KFA-1 mutation proof

| Mutant (inside the gate mirror only) | Spec line that fails (desktop + mobile) | Expected / received |
|---|---|---|
| `no-escape`: `} else if (e.key === "Backspace") {` | `conexiuni-keyboard-clear.spec.mjs:29` | 0 / 2 |
| `no-backspace`: `} else if (e.key === "Escape") {` | `conexiuni-keyboard-clear.spec.mjs:33` | 0 / 2 |
| `live-always-polite`: `<div className="lant-current" aria-live="polite" aria-atomic="true">` | `lant-live-region.spec.mjs:36` | "off" / "polite" |
| `live-always-off`: `<div className="lant-current" aria-live="off" aria-atomic="true">` | `lant-live-region.spec.mjs:15` | "polite" / "off" |
| `no-atomic`: `<div className="lant-current" aria-live={won ? "off" : "polite"}>` | `lant-live-region.spec.mjs:16` | "true" / "" |

Product run: 4/4 pass. The restored bundle's manifest equals the build's (`89cff721…`, also the M4
measurement manifest). Script: [kfa1-proof.stdin.txt](kfa1-proof.stdin.txt); summary: [kfa1-mutation-proof.json](kfa1-mutation-proof.json).
The first run (shell at 20dab663) gave identical outcomes, but a later shell run replaced its raw reports;
the retained proof is a second run at docs-only 9a33d380 (same product binary). Raw reports and traces:
`dobostore:/volume1/agentops-home/temp-archive/2026-10-21/fix__gui-publication-followups-kfa1-proof.tar.zst`
(sha256 `be9210a3…`, verified on both ends).

## EQ-1 CSS gzip basis

| Basis | Original | Actual | Headroom |
|---|---:|---:|---:|
| gzip level 9 (gate) | 16,046 | 16,043 | 3 B |
| gzip level 6 (ceiling) | 16,093 | 16,138 | −45 B |

The ceiling stays 16,093 and the gate stays level 9; the verdict is unchanged.

## Gates

All on product `20dab663247937ea1dec93f5c7870f729a8c4c19`, tree `72e0cb01…`, toolchain `sha256:2e040a51…`:

| Gate | Command | Result |
|---|---|---|
| build | `GATE_OPERATOR=agent:claude bash scripts/gate.sh build --sha 20dab663… --parallel 2` | 11/11 pass |
| unit | `GATE_OPERATOR=agent:claude bash scripts/gate.sh unit --sha 20dab663… --parallel 2` | 27/27 pass, 18.7 min; result sha256 `2744a33a…`; CSP enforced 0/0; CSS 16,022 global / 16,043 total ≤ 16,093; budgets unchanged |
| full | `python3 -I scripts/gui-full-runner.py --sha 20dab663… --parallel 2` | 37/37 pass, 15.2 min; result sha256 `0736bc55…`; browser 937/937 (0 skip/retry/flaky); 9 PNGs, axe, Home semantics pass; PG accounts/httpapi pass; parity 1206; legacy owner journey pass; owned cleanup verified |
| host | `go test -race -count=1 ./cmd/cat-server` (fix removed, then restored) | 3 new failures without the fix, pass with it |

Full reused the same-SHA passing unit (ADR-0200 `same-sha-passing-unit`), so its whole-unit lanes ran
in 7 ms and the cross-SHA `cat-native-reuse-inputs` check (present in M4's 38) does not apply; the
browser, PG, parity, image and baseline lanes ran fresh. Before the full, `tools/gui-baseline-quality`
was installed in the fresh gate mirror with `npm ci` from its committed lock (axe-core 4.14.0,
web-vitals 6.2.3) through the owner shell: a procedural provisioning step, no source change.

Gate evidence (unit/full/build results, logs, reports and scratch drafts) is archived at
`dobostore:/volume1/agentops-home/temp-archive/2026-10-21/fix__gui-publication-followups-evidence.tar.zst`
(sha256 `9a901077…`, verified on both ends) before local cleanup.

Independent review (Claude Opus reviewer, read-only, own source copy and host race runs): PASS-WITH-NOTES,
no blocker; a second pass over the documentation commit also passed with a custody note, resolved by the retained run above. Its notes were applied: ADR-0207 names the `baseline`/plain `gen` lanes (N1), the replacement
accounting is corrected here (N2) and EQ-1 lands in this record's documentation commit (N3).

## Not done (low, optional)

- GSP-1 (Alchimie "Schimbă opțiunile" during action-sync recovery) and KFA-2 (lazy-chunk
  `role=status` fallback) change frontend source under the 246 B Challenge JS headroom and the exact
  PNG/axe evidence; they need their own measured change.
- DCR-6: `managedPortedRoutes` is not dead: `scripts/gui-route-budgets.mjs` parses it and
  `managed_delivery_test.go` pins its exact set (ADR-0197). Removal is a cross-file cleanup.
