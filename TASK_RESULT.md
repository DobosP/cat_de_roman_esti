# Task Result — land V53 and start V54 people morphology

## Outcome

- Landed and pushed V53 on `main` at `9808b10`, then removed its verified-merged local
  branch/worktree.
- Created `feat/v54-people-morphology` directly from landed V53 `9808b10`.
- Reviewed one fixed 50-surface people/role case-form funnel twice. Forty-eight exact
  genitive/dative forms passed both reviews; `părintelui` and `părinților` were rejected
  because _părinte_ ordinarily denotes both a parent and a cleric. No quota was used.
- Accepted forms serve typed Contexto guesses and otherwise-legal Lanț hops. Contexto's
  non-winning projection is unchanged.
- Preserved all nodes, edges, puzzles, game records, ranking rows, derived boards, holds,
  sessions, accounts, frontend, privacy, and deployment state.

## Quality and provenance

- ADR-0078 binds additions to exact forms with unanimous normalized ownership. The review
  archive binds all 50 candidates, two complete/disjoint dispositions, 25 lexical sources,
  normalized-key uniqueness, collision evidence, and the final 48/0/0/2 partition.
- The rollback-safe authoring path updated both KG mirrors and the public mobile snapshot.
- V53's collision boundary, V51's exact-alias/non-winning-projection boundary, V49's 104
  directed rejection pairs, and V48's archived-evidence/current-live provenance split
  remain intact.

## Files changed

- Added the V54 data/applier, ADR-0078, lexical review archive, and focused regression
  contract; superseded ADR-0077 only for its fixed V53 inventory/build counts.
- Updated both KG mirrors, mobile snapshot, README/current status, ranking/derived wrapper
  mirrors, and current digest/version pins in affected historical contracts.
- No frontend source or bundle changed.

## Bound artifacts

- Candidate funnel SHA-256:
  `e826810d2b8a88b8034e21c28336faa7d6d55e2801d62bde4ec6dccfdd87a2bb`.
- KG SHA-256: `8fa5bd8d7f9169c21fc076a6310b085b1224fd68aca473b365143306608ff526`.
- Pack SHA-256 remains `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking SHA-256: `8adc1da531ca65fd23b653597886d93c7ecdad23477a44ba754365596041e900`;
  its board payload remains `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`.
- Derived SHA-256: `f23f4abf69217234a085525643f9d4d85109f260ec388421ac25961c9a0486ed`;
  its frozen board payload remains `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
- V49 ledger SHA-256 remains
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.

## Verification

- Backend: 787/787; accounts-on: 53/53; sessions: 16/16; V54 contract: 6/6.
- Affected V33/V44/V47–V54 and app-pack/Contexto gates: green.
- Games-pack, KG, ranking, and derived validators: green; strict real Lanț pending sweep:
  three checked, zero flagged and zero FAIL findings.
- Ruff and `git diff --check`: green. Frontend was untouched, so no frontend gate ran.

## Sequencing and residual risk

- V54 is intentionally uncommitted and unlanded on `feat/v54-people-morphology` for review.
  V53 is landed and `main`/`origin/main` are synchronized at `9808b10`. No production
  deployment is included.
- Rejected polysemes and all earlier deferred/rejected vocabulary stay out of runtime.
  Another paradigm, collision-policy, projection, topology, or board wave needs a fresh
  bounded review.
