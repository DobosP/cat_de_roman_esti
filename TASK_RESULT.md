# Task Result — V68 Romanian-language and grammar morphology

## Summary

- V67 is landed and pushed on final `main` head
  `46cf65f05a39b001e429c9f0a14fe0bfb611cb38`. Exact feature run `32772547384`,
  evidence run `32773388527`, and landed-main run `32774376592` are green.
- Anonymous production remains on exact V65 app commit
  `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`.
- The fixed V68 funnel contains 50 normalized-unique Romanian-language and grammar case
  surfaces. It adds exactly 48 aliases across 24 existing owners while rejecting
  _punctului_ and _punctelor_ because neither ordinary form has one safely bounded
  punctuation sense.
- V68 remains intentionally uncommitted, unlanded, undeployed, and without CI.

## Frozen review contract

- Candidate-funnel digest:
  `ff4cee7a4ac2f39601a19efd3aad2a305e85303e282451ba606fe1c8b68b3377`.
- Build: `fixture-v68-romanian-language-and-grammar-morphology`.
- Fixture counts: 2,364 nodes / 9,217 edges / 8,306 aliases / 180 puzzles.
- Contexto projection: 473 terms across 26 domains.
- Exact delta: +48 aliases; no projection, node, edge, puzzle, game record, hold
  disposition, ranking row, or derived board.
- Earlier accepted inventories retain their owners; earlier rejected, deferred, held, and
  unauthored surfaces retain their prior absence or disposition.

## Implementation scope

- The worktree contains the reviewed V68 data module, rollback-safe apply wrapper,
  two-reviewer archive, ADR-0092, and focused regression contract.
- The first transaction rejected two six-word candidates and restored all artifacts. The
  corrected five-word _părții/părților de vorbire în română_ pair is triple-absent,
  source-backed, validator-compliant, and included in the recomputed digest.
- Regenerated the alias-bearing KG/mobile/ranking/derived wrappers and migrated current
  build/count/hash pins.
- Games-pack bytes, ranking rows, derived boards, projection inventory, V49 ledger,
  sessions, accounts, frontend, and deployment remain preserved by scope.

## Artifact evidence

- KG: `ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128`.
- Games pack:
  `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper:
  `b521d5d698a036aa81589ba059d7c04d731dbd69a2bf1a2f6b627e881a19bfe6`.
- Derived wrapper:
  `e7acd141a357409559a93f68514b977dbd697e19a97939afa9bb200d9d70dc97`.
- Mobile wrapper:
  `1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae`.
- V49 ledger:
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- Frozen V67 invariant hashes remain unchanged: nodes without aliases
  `c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0`, edges
  `f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0`, puzzles
  `3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc`, ranking rows
  `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`, and derived
  boards `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Verification state

- Focused V68 passed 6/6; affected V31–V33/V44/V47–V68 passed 191/191; accounts-on
  passed 53/53; sessions passed 16/16; exact full backend passed 871/871 in 569.61 seconds
  on stable CPU14 scheduler placement.
- Fixture/pack/ranking/derived validators, 618/449 ranking inventory, 336 derived boards,
  strict Lanț 3 checked / 0 flagged / 0 FAIL with 16 WARN, mirrors, exact-delta, inherited
  bindings, protected surfaces, immutable payloads, and source coupling are green.
- Ruff lint, new-file format, mirrors, exact-delta, inherited bindings, 49 protected
  surfaces, immutable payloads, source coupling, and whitespace are green.
- V68 has no commit and therefore no exact-head CI run.

## Production state

- The production host checkout remains clean at exact V65
  `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`; the healthy app image begins
  `sha256:71f3e2cc`, has zero restarts, and is tagged `release-aefcc2c64fed`.
- `rollback-1c42de0` preserves the previous V61 image `sha256:efa179af`. Caddy was not
  recreated; no env, DNS, TLS, database, OAuth, extra worker, or infrastructure changed.
- Accounts and debug are off, `CAT_SUBMISSIONS_DIR` is absent, and submissions return HTTP
  503. The public manifest continues to report the V65 build and counts 2,364/9,217/180.
- V68 changes no database, OAuth, worker, session, frontend, DNS, TLS, or infrastructure
  behavior and is not deployed.

## Risks and release result

- _Punctului_ and _punctelor_ must remain absent from exact, projection, and fuzzy
  resolution. Aliases must not create edges or broaden projection resolution.
- V68 is implemented, uncommitted, unlanded, and undeployed. Commit it and require exact
  feature CI before landing. Production remains on exact V65 app commit
  `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`.
