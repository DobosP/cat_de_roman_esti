# Task Result — land V52 household morphology

## Outcome

- Created `feat/v52-typed-vocabulary` directly from landed V51 `b4d8252`.
- Reviewed one fixed 50-surface household case-form funnel twice. Forty-eight exact
  genitive/dative forms passed both reviews; `păturile` and `păturilor` were rejected
  because accent folding also makes their keys ordinary forms of `pat`. No quota was used.
- Accepted forms serve typed Contexto guesses and otherwise-legal Lanț hops. Contexto's
  non-winning projection is unchanged.
- Preserved all nodes, edges, puzzles, game records, ranking rows, derived boards, holds,
  sessions, accounts, frontend, privacy, and deployment state.

## Quality and provenance

- ADR-0076 binds additions to exact forms with unanimous normalized ownership. The review
  archive binds all 50 candidates, two complete/disjoint dispositions, 25 lexical sources,
  normalized-key uniqueness, collision evidence, and the final 48/0/0/2 partition.
- The rollback-safe authoring path updated both KG mirrors and the public mobile snapshot.
- V51's exact-alias/non-winning-projection boundary, V49's 104 directed rejection pairs,
  and V48's archived-evidence/current-live provenance split remain intact.

## Files changed

- Added the V52 data/applier, ADR-0076, lexical review archive, and focused regression
  contract; superseded ADR-0075 only for its fixed V51 inventory/build counts.
- Updated both KG mirrors, mobile snapshot, README/current status, ranking/derived wrapper
  mirrors, and current digest/version pins in affected historical contracts.
- No frontend source or bundle changed.

## Bound artifacts

- Candidate funnel SHA-256:
  `21bf03bc35819a0957d98cbef23a060daf8abf63c5afdaed5c0a53a9d7b7a535`.
- KG SHA-256: `ea4c45a0ef07b63a845a0d723de58ef4ef468ad47ea8b3303cafc22bb90c9b5d`.
- Pack SHA-256 remains `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking SHA-256: `8f7dc148d849e8fdbdddd7f72d251ca26a63b45930c2b6f7fc978ac3a091edf6`;
  its board payload remains `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`.
- Derived SHA-256: `94ab0afa16cc9d1ce5dba0de387df6ddda822322349801c84a79a7b560510b98`;
  its frozen board payload remains `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
- V49 ledger SHA-256 remains
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.

## Verification

- Backend: 775/775; accounts-on: 53/53; sessions: 16/16; V52 contract: 6/6.
- Affected V33/V44/V47–V52 and app-pack/Contexto gates: green.
- Games-pack, KG, ranking, and derived validators: green; strict real Lanț pending sweep:
  three checked, zero flagged and zero FAIL findings.
- Ruff and `git diff --check`: green. Frontend was untouched, so no frontend gate ran.

## Sequencing and residual risk

- V52 is committed and landed on `main`, with `origin/main` synchronized. No production
  deployment is included.
- Rejected folded keys and all earlier deferred/rejected vocabulary stay out of runtime.
  Another paradigm, collision-policy, projection, topology, or board wave needs a fresh
  bounded review.
