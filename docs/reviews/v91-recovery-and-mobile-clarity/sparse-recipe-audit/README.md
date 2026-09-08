# Sparse recipe expectation correction

Valid until: the reviewed patch or bound input changes — then treat as history.

2026-09-09: the two isolated failures are stale expectations after the accepted
Sport 083 seed revision. The first compares current Sport recipes directly to
V87; the second still expects the pre-V91 median strength. The blocked first
comparison also concealed the stale total/tied recipe counters.

Cold recomputation matches all 80 approved projections against both before and
candidate review archives. Only Sport 083 changes. V87 remains 550 recipes / 77
two-result recipes / median 0.66; V90 remains 555 / 77 / 0.67; V91 is 554 / 76 /
0.68. Per-board structural checks and the five weak fallback IDs still pass.

`sparse-recipe-expectations.patch` reconstructs the one old Sport projection from
the exact V90 inverse and asserts unchanged KG. It retains the V87 digest,
pins all 80 V90 and current projection rows, preserves the old 555/77/0.67 checks,
and updates the current expectations without relaxing any per-board invariant.

Initial isolated run: 2 failed, exit 1, 32.81 seconds. Scratch candidate: 2 passed,
exit 0, 33.91 seconds. One import-format correction followed; the two candidate
ASTs are identical and final repository-config Ruff and `git apply --check` pass.
All original logs and source snapshots are retained. `audit.json` binds them and
`metrics.json` records the full cold metrics. This reviewer edited no repository
source, tests, fixtures or existing evidence. Root owns patch application and
final matrix reruns. V91 remains the final authorized version.

Root packaging: the original `.py` snapshots named by `audit.json` are byte-identical members of `source-snapshots.tar.gz`; `packaging.json` records both archive and member hashes. The patch, metrics and logs remain alongside this note.

The original unified diff is stored as `sparse-recipe-expectations.patch.gz`; its decoded bytes and original audit hash are unchanged. `patch-packaging.json` records the wrapping needed to keep diff context spaces out of the repository whitespace gate.
