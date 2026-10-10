# ADR-0190: Owner-approved LCP/INP regression criterion

Date: 2026-10-10
Status: accepted by explicit owner instruction; actual focused43 PASS at2a6e1bc, full qualification pending

## Authority and context

Paul answered the concrete policy question with: “Allow improvements; keep slowdown limits”. The question explicitly proposed retaining the same 10%/50ms slowdown allowance and warned that the slower Conexiuni observation would still fail. This is an owner-approved acceptance amendment, not a source-bug classification or a replacement baseline.

The previous absolute predicate rejected improvements as well as regressions. In the retained instrumented19b diagnostic, Conexiuni LCP2836→3436 remains a regression beyond283.6ms; Conexiuni INP184→96 and Alchimie LCP4228→3464/INP200→112 are improvements. Those original failed receipts remain failed historical receipts. Diagnostic overhead was not measured; these numbers are not a new full acceptance or causal performance claim.

## Decision

For each existing LCP/INP median comparison, require finite nonnegative original and current values. Reject only when `current - original > max(original * 0.1, 50ms)`. Equality at the existing boundary passes; improvements pass. Retain the original values, current values, absolute deltas and numeric tolerance in reports.

This supersedes only the LCP/INP comparison direction in ADR-0188 and the active S1/ExecPlan criterion. The numeric slowdown allowance is unchanged. Original baselines, failed evidence, five-run acquisition, contexts, callbacks, CDP throttling, seeded actions, waits and pagehide finalization remain unchanged. CLS acquisition and its existing requirements are outside this amendment. The public product LCP/INP targets remain unchanged.

No screenshot/Axe/Home-witness, CSP, privacy, content, route, budget, SDK or device criterion changes. The startup estimate remains a planning target while actual configured limits and failed qualification remain visible. The physical Samsung checkpoint and full/M0/M1/KIT_BUMP/M2/S0b obligations remain unearned until their actual required evidence passes.

## Implementation and validation

Apply exactly the reviewed R2 afterimages: two helper lines change the validity/direction predicate; existing safety controls and reporting remain intact. Existing comparison tests now accept a faster value and retain exact numeric boundaries, just-over-boundary regressions and nonfinite refusals. Two additional controls isolate negative current and negative original values; a separate finite-review successor adds an infinite-original control that directly catches omission of expected-value finiteness. The mixed Axe/PNG/timing case still observes every existing comparison, preserves unrelated failures and rejects its slower Conexiuni metric.

Use a justified `GATE-CHANGE:` commit. Targeted managed execution is pending; source acceptance alone is not a test or full pass. Record actual supported managed results before subsequent qualification.

## Actual targeted validation

At clean2a6e1bcc2b13bcc5e434fa83ba3ce6fb7039f5d5, the supported pinned owner shell ran the complete focused module once:43 unique tests passed, zero fail/skip/cancel/todo and empty stderr. Actual Node, source-bracket and wrapper exits were0. Helper/test/immutable baseline before/after hashes matched. Parent retained a small21-file/480960-byte source/mirror control bundle; independent actual review is clear. [Actual focused proof](../reviews/gui-normalized-react/vitals-regression-policy-focused-pass.json) and raw TAP retain the result. This proves the policy/refusal controls, not new browser timings or full/device/milestone acceptance.
