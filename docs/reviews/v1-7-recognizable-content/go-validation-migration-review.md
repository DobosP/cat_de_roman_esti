Valid until: reviewed source or owner validation policy changes — then treat as history.

# Independent Go validation migration review

Reviewer: `/root/v17_research_quality`; reviewed 2026-10-09 04:59 UTC.
Source cutoff: 2026-10-09 05:06:04 UTC; deadline 05:09:04 UTC.

**Verdict: ACCEPT the exact source implementation and authorized policy migration for separately admitted native qualification. No blocking code defect found.** No Go/Python/Rust tools, compilation, tests, imports, formatting or data mutation were executed by this reviewer. Whole-source RSS remains unmeasured.

The owner's new authorization explicitly supersedes the old mandatory Python ordered-object/full-suite gate. ADR-0186 records the decision; the original 4a/552 failures and partial passes remain historical failures. This review does not retarget a12 or any old acceptance to new code. Source6 remains live; candidate I1194 and generated fixtures are unchanged.

The read-only command is appropriately scoped:

- `check --write` is rejected before source loading, including an absent-root refusal test. Check calls no transaction or writer.
- Existing strict decoding, byte-exact KG/pack mirrors, immutable source snapshots and runtime inventory remain. Snapshots/inventory are checked before validation and again on every return.
- Graph structure/path/reference/alias/count checks use existing native validators. Pack validation uses actual `PackBytes`, rather than the loader's in-memory high-water reconciliation.
- `Rank(false)` and `Derive(false)` recompute complete native values and preserve array order, source bindings, scores, eligibility, weights and canonical numeric distinctions. Native physical sidecar bytes are additionally required; format drift refuses with the supported regeneration command. No fixture is silently rewritten.
- The new refusal tests exercise value/binding/array/type/duplicate-key/format drift, graph reference/type/identity mutations, mirror drift, source byte/mode/inventory changes and write refusal. Native temporary fixtures are produced through the existing builders in owned test roots.
- Native generation is not an independent oracle by itself. Frozen observed evidence 23865943372abf957a82b4a74dc2c01706dcbe4539fd50118a259b8a5dccc402 independently establishes equal typed values and ordered arrays for all 716 current rows. The scoring algorithms are unchanged; the optional Python test retains complete generated-value parity and exact physical mirrors, while testing its own renderer order separately.
- The new all-pair graph test reconstructs reverse adjacency directly from authenticated raw nodes/edges, excludes distractors/missing endpoints, expands bidirectional edges and uses an independent string-map/queue BFS. Independently sorted IDs, every pair, identity/unreachable and unknown-target behavior are checked. It does not call another distance wrapper as its oracle. Workspace is linear; no all-pair matrix is stored.
- That graph test covers **unweighted** distances on the content actually authenticated by its built binary. An R build currently embeds Source6; do not claim a new Source7 seal from it. Weighted-distance and existing gameplay/normalization/corpus contracts remain separate.

CI retains source/export, all-authority rails, mobile, docs, native race/vet and the other existing native gates; it routes rank/derive checking through the stronger composed command. Python/Rust remain opt-in references. Current docs honestly mark implementation qualification pending; STATUS is 120 lines and agent-testing 77. README delegates the policy decision to ADR-0186.

Rust assessment is appropriately bounded: its current filtered graph test still compiles the server library and 129-package lock closure, requires the unqualified pinned 1.98.1 toolchain, and supplies no standalone authoring-validator CLI. Existing Go dense algorithms plus the independent differential test and measured benchmark are the appropriate immediate scope. No Rust installation, FFI, dependency extraction or performance claim is approved here.

Required before qualification/adoption:

- Fresh fixed resource admission; existing 17GiB start/16GiB remaining disk and MemAvailable, 2GiB sampled group RSS, 1GiB full-owned growth, 20-minute deadline and 180-second reserve remain unchanged.
- Run formatting and affected native tests/vet/checks under that admission. If gofmt changes bytes, freeze actual after-hashes and verify whitespace/AST equivalence before compile; preserve this pre-format receipt and do not consume stale source pins.
- Record benchmark setup separately from the timed ranking-generation loop. No measured speed or allocation result exists yet.
- New Go files/command and graph-test inventory change runtime bindings. Rebuild affected tools and refresh actual Source7 audits/finals/current-authority bindings after freezing runtime; old 130-entry audits cannot certify this implementation.
- Source/seal, independent factual/quality, graph caps/thresholds, private bounded gameplay/sessions/saves, installed history, full native/shared/HTTP/TCP/assets and assembled gates remain mandatory. Managed assets, paused frontend/GUI and explicit PG/provider/remote scope are not authorized by this migration.
- Report real missing native contracts or semantic disagreements promptly. This four-part check is not a blanket claim that every legacy reference assertion has been ported or that Source7 is adopted.

Exact reviewed SHA-256 bindings (relative to the V1.7 task root):

```text
956af6f43ba05b5764c1e02963f76151257cb8c2829710e74e5d5cd26b83d8e9  docs/reviews/v1-7-recognizable-content/go-validation-migration-scope.json
870664bb90887f9385748219b9e812e885f0c8cb0e6a919bd9e18cfc0fb4e7a3  docs/reviews/v1-7-recognizable-content/go-validation-migration-scope-extension.json
ca671211abe1fd7099d253ae1d3dcc8b4d51ade8eda1223350dec9ade19bb48a  docs/reviews/v1-7-recognizable-content/go-validation-graph-scope.json
05ad44ed3706e6bbfe4985a69e7cd69f29e7fd064489a3f9475f4f46732ae0f3  go-backend/internal/contentops/check.go
b4b8beb6b57c455a84b21fe4ef97e3973ffa6091b1c4442702d6d354b3a66966  go-backend/internal/contentops/check_test.go
54733010ac8f059d276a9ec0db9ad710216908f61712fa2dcb6c3bf57da03d7d  go-backend/internal/contentops/command.go
15ed7964d7270e91ef03bcef3cfcef89ef89440f4bb7d5a5e27b5d2911e9aea2  go-backend/internal/contentops/README.md
c555d21180f86621e032849a27aaf9a1e8cc465d9304110602a95d0b72cf7949  go-backend/internal/graph/dense_reference_test.go
babc3bd8113e9102482ad3cb06737e84bed8907de53eb268133bb76470aae367  tests/test_board_rankings_v37.py
966e09f8be1d591fd5bb9116ffaf091af3d5e7e8fb21712e88959dc1a6f95649  .github/workflows/ci.yml
adbcaaadf5621d0214eb4d8cb0a1dff320949ee57caeba7816aaad87bfa9df68  docs/adr/0186-go-authoritative-content-validation.md
b89240c658989c1b40d2e749a3eabe09e72d31ee3adcbe0f36cc44bd6dd7b36b  docs/adr/README.md
27f22566c1e12badd0966a9d082a0ca58600c1275707525a5848ee9aa0affc67  docs/adr/0165-native-source-build-and-qualification.md
b89bdedc82226d059ef59524d852509d977986536a357febacdcece0dd68f5da  docs/adr/0168-qualify-complete-native-toolchain.md
59fd944bc4d99278c19e52530efd245c545d6af195976983750b4eb0a0931c61  docs/STATUS.md
d105efe2977c6cfd1c605692684fbdaa62f324a083a0cb773c0682feca93204f  docs/agent-testing.md
6bf8dab1283f7fda3e5424bdbe585b8059b0cd0ca872d56961c9e2edaa14f110  README.md
837edadb75ef05371aa9f5baeaa708a12d7eb13fa722e7accfbaa36e6177dcf0  docs/reviews/v1-7-recognizable-content/README.md
1012d36c9874ece94be075ee9e35e00956b00f967220c3633cba942aca8dd019  TASK_BRIEF.md
eaef4017458e23202f985221e95a9e4a84a727583ce1c9fcfb7b1222981e029e  WORKLOG.md
b726a60b924dfbf862cbd4a738badac3388e4b773eb047df143ca5e8f92d326c  docs/reviews/v1-7-recognizable-content/go-validation-rust-assessment.md
```
