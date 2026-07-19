# Task Result — V29 extended basic words

## Summary

- Added 17 first-class easy concepts, 66 collision-safe inflections, and 64 explicit
  directed semantic links through the rollback-safe common-word applier.
- The historical beginner benchmark remains 234/234; the separate extension is 17/17
  and combined eligible coverage is 251/251.
- Generated fixture inventory: 2,216 nodes / 8,909 edges / 7,143 aliases / 180 puzzles.
- Curated pack remains byte-identical: 794 = 572 approved + 222 pending, SHA-256
  `2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023`.
- Session behavior is unchanged: two-hour sliding TTL and 1,000-entry cap.

## Product files changed

- `scripts/basic_words_v29_data.py`
- `scripts/apply_basic_words_v29.py`
- `tests/test_v29_basic_words.py`
- additive updates to `tests/test_v28_basic_words.py`
- both generated KG fixture mirrors and the generated Cat mobile contract
- `docs/adr/0037-extended-basic-word-concepts.md`
- `docs/STATUS.md`

`v29-review/` and this result are review artifacts and must remain outside the product
commit.

## Verification

- Applier dry-run: GREEN (17 nodes / 64 edges / 253 probes / 64 link probes).
- Applier transaction: GREEN; canonical content hash
  `sha256:dc239bb161a6cd05d4c679fe69b9b15a467ee4fa97411703140c6af3e58cbaf7`.
- V25/V28/V29 focused pytest: 23 passed.
- V24/app-pack/data/session pytest: 46 passed.
- Full project pytest: 362 collected and passed using the project Django environment.
- Ruff: GREEN.
- Fixture and games-pack validators: GREEN.
- Workflow syntax and `git diff --check`: GREEN.
- Exact critique: 33 checked / 0 flagged / 0 FAIL.
- Full pending critique: 222 checked / 147 flagged / 143 existing FAIL records; before
  and after reports are byte-identical at SHA-256 `122e35c819f6bdacbbcf95b7dcbac09bf5b2a3de56314487df187493ac86919a`.

The first full pytest attempt used the documented lightweight scraper environment, which
lacks Django and stopped during collection; the required project environment then passed
the complete suite. No product failure was involved.

## Risk / review notes

- Deterministic regeneration changes 30 legacy puzzle records.
- Lanț and Alchimie topology metrics do not change. Contexto shortens 305 old-node
  distance cells across 82/207 targets by at most two hops; no validator or critique
  finding changes. In the exact review set, `Mâncare` gains `Cuțit` and `familie` gains
  `Weekend` as intuitive strong neighbors.
- Every new node has at least four distinct neighbors, two same-category neighbors, two
  outgoing choices, and one incoming cue. Existing endpoint fanout increases by at most 3.
- Production remains release `2746be3`; V29 has not been committed, merged, pushed, or
  deployed.

## Recommendation

Ready for review and an explicit commit/land decision. Do not combine the separate
board-remediation queue or analyst promotion proposals with this graph wave.
