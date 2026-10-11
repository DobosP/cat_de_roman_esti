# ADR-0191 — Image-backed browser concurrency experiment

Date: 2026-10-11
Status: Source accepted; actual full validation pending.

## Context

Paul asked for more parallel progress. The completed enforced b03 full used one Playwright worker: its900-case matrix took1984.340s, while the backend race stage took914.145s. Wrapper parallel2 controls Go concurrency and does not set browser workers. These are elapsed observations; no speedup is proven.

## Decision

The GUI config selects two workers only with the genuine GATE_APP_URL image-backed route. Image-less original/normalized GEN inherits original.workers. fullyParallelfalse, retries0, all900 identities, assertions/fixtures, benchmark throttles and separate serial CSP/baseline stages stay unchanged. The existing4CPU/6GiB managed resource bounds remain.

## Validation and limits

Exact one-path60-byte inverse and8622 other Git entries were independently reviewed. Runtime is NOT RUN at source327. The next real same-final-SHA/image full must preserve900 once/no skip/retry/flaky/global errors and all mandatory evidence before accepting this setting. Compare actual elapsed time without claiming causation or fastest-possible performance. Current route budgets remain red; formal adoption, KIT_BUMP and real Samsung qualification remain open. No budget or safety gate is relaxed.


## Actual bounded validation — 2026-10-11

Completed enforced full at b0edd76d9d2ee6a4897f3d79c756fed4ca78048c recorded workers2 and all900 identities once, zero retry/skip/flaky/global errors; the unchanged mandatory non-budget checks passed. Actual matrix1044.409s versus historical b03 workers1 1984.340s is an elapsed observation, not a causal speedup or optimality claim. [Current proof](../reviews/gui-normalized-react/full-b0-checkpoint.json) retains the FAIL201 aggregate and all20 red route-JS rows. Original/image-less GEN remains serial. Formal adoption/KIT_BUMP/device obligations remain open.
