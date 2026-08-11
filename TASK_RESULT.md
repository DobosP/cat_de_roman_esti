# Task Result — V49 durable Lanț rejection-debt workflow

## Outcome

- Started V49 as the ledger hardening explicitly left by V45/ADR-0069, instead of
  re-gating the eight unchanged owner/blocker holds or beginning privacy-sensitive pilot
  telemetry.
- Added a non-runtime Lanț rejection ledger seeded with exactly the 104 V45 rejects and
  104 unique directed start/target pairs. The three V45 keeps are excluded.
- Bound the seed to the pre-V45 pack commit/hash, sorted rejected-ID set, exact V45 gate,
  dossier review bindings, canonical record digests, and per-pair digests.
- Added fail-closed checks to candidate import, deterministic pending critique, and review
  apply. Import checks canonical post-alias pairs before mutation; critique compares the
  selected row with the full current inventory and ledger; future rejects append in the
  same transaction as pack mutation and roll back with it.
- Kept direction exact. Reverse pairs and merely similar corridors remain ordinary A1–A7
  and D1–D5 human-review evidence rather than inferred automated rejections.

## Quality conditions retained

- Exact sorted batch identity, fresh dossier/KG/rubric bindings, strict deterministic and
  runtime-real evidence, complete two-reviewer coverage, unanimous promotion, either
  rejection rejects, owner-only A5 holds, and no quota promotions remain the gate bar.
- Approved, pending, kept, unrelated, co-promoted, and same-batch-rejected Lanț rows all
  participate in exact-pair comparison; only the current row ID excludes itself.
- The V45–V48 archives remain immutable. V49 deliberately leaves the rubric digest,
  pack, rankings, derived wrapper, frozen derived payload, and runtime source pins at
  their V48 bytes.

## Evidence

- ADR: `docs/adr/0073-durable-lant-rejection-debt.md`.
- Review archive: `docs/reviews/v49-lant-rejection-ledger/README.md` and
  `seed-audit.json`.
- Ledger SHA-256:
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- V45 gate SHA-256:
  `4e976a185b27ccee2737542ed8321c6664b7b8c974ae8e793076571964af4458`.
- Pack/rankings/derived SHA-256 remain `05e80ab2…`, `0e2b5cda…`, and `87544c899…`;
  the frozen 336-board payload remains `71a2acef…`.
- Content remains 618 records = 610 approved + 8 pending / 449 selectable. No game row,
  KG node/edge/alias, content status, score, session behavior, account mode, frontend, or
  production deployment changed.

## Verification

- Full backend: **748/748**.
- Accounts enabled: **53/53**.
- Bounded word-game sessions: **16/16**; only the existing foreign-venv
  `DJANGO_SETTINGS_MODULE` warning appeared.
- V49 plus V45–V48, critique, and importer regressions: green (also included in the full
  backend result).
- The real Lanț pending sweep checked all three holds with the ledger/full-pair census:
  0 flagged items and 0 FAIL findings.
- Pack, ranking, derived-catalog, and KG validators: green.
- Ruff, all three edited workflow syntax checks, and `git diff --check`: green.
- Frontend checks were not rerun because no frontend or release-bundle file changed.

## Files changed

- Ledger/runtime tooling: `lant_rejection_tombstones.json`, `critique_pack.py`,
  `import_candidates.py`, and `apply_rereview.py`.
- Workflow prompts: `critique-games.js`, `game-audit-recon.js`, and
  `verify-authored-content.js`.
- Regression coverage: `test_v49_lant_rejection_ledger.py` and workflow assertions in
  `test_critique_pack.py`.
- Durable record: ADR-0073, the V49 review archive, `docs/STATUS.md`, and this result.

## Residual work

- The three Lanț holds still require their named blocker to change and then a fresh exact
  gate. The two Contexto and three Alchimie A5 holds still require explicit owner action.
- Broader corridor similarity has no approved deterministic threshold and remains a
  human D1–D5 judgment.
- The first genuine future ledger append must evolve the V49 exact-seed assertions while
  preserving all 104 V45 entries as an immutable subset.
- Production remains V48 at `d59caed`; V49 was not deployed.

## Handoff

The branch is green and ready for review/landing. No commit, push, merge, deployment, or
owner-hold disposition was performed.
