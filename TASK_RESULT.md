# Task Result — V46 strict Conexiuni pending cleanup

## Outcome

- Rebuilt current-bound dossiers for the exact 79 pending Conexiuni records and compared
  them with the full approved, pending, owner-demoted, and rejected inventory.
- The deterministic gate found 438 failures across 76 records. The three lint-clean
  records still failed adversarial unique-partition and clue-arc review.
- Promoted and kept no board. Gameplay rejected all 79; inventory rejected 38 and held 41
  under a cautious owner-boundary reading, so the fail-closed synthesis rejected all 79.
- Removed only dormant pending stock. Conexiuni is now 232 approved / 0 pending / 74
  eligible; the original-game pack is 645 = 608 approved + 37 pending, with 447 eligible.
- Appended all 79 exact records to the rejection ledger, now 122 boards / 488 groups.
  Legacy named group keys are normalized deterministically inside the ledger without
  changing original record digests or partitions.
- Regenerated ranking and derived metadata without changing the frozen 336-board
  Intrusul/Perechi payload. No deployment was performed.

## Files changed

- Content: mirrored game pack, rankings, derived catalog, rejection ledger, pack digest
  pins, and runtime derived-catalog pin.
- Gate: 79 exact dossiers, deterministic report, complete v2 two-reviewer artifact, and
  the human-readable audit under `docs/reviews/v46-conexiuni-pending-gate/`.
- Workflow: legacy group-key normalization in `scripts/apply_rereview.py` with rollback
  and provenance regression coverage.
- Contracts: ADR-0070, `docs/STATUS.md`, V46 regression tests, and historical tests updated
  to model retired records rather than require a real pending Conexiuni fixture.

## Verification

- Full backend: 711/711 green.
- Accounts-on: 53/53 green; bounded session store: 16/16 green.
- Exact targeted Conexiuni/pack/critique gate: 138/138 green.
- Affected historical/content matrix: 241/241 green.
- Intrusul/Perechi/derived-catalog gate: 68/68 green.
- Ruff, `git diff --check`, pack, KG, ranking, and derived-catalog validators: green.
- Pack mirrors: 645 records, 608 approved / 37 pending, 447 runtime-eligible.
- Rejection ledger: 122 boards / 488 groups; every V46 row cross-bound to its exact
  dossier, gate artifact, record digest, and group partition.
- Frozen derived board payload: unchanged at 183 Intrusul / 153 Perechi, SHA-256
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Risks and manual review

Ten Conexiuni category/difficulty shelves remain empty by design; no failed record was
promoted to fill a quota. Future boards must be materially new because the larger ledger
blocks exact, three-of-four, and board-level reskins. The generic apply command still
requires ranking and derived-metadata regeneration as a separate release step; V46's
committed regression verifies the completed chain. Session TTL/caps, deterministic
selection, graph/KG, frontend, scoring, and hidden-answer behavior are unchanged.

## Merge recommendation

Green to commit, land, and push on `main`. Do not deploy V46 as part of this content gate,
and retain the task worktree/branch until the owner explicitly authorizes deletion.
