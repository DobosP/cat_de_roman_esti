# Task Result — land V49–V51 typed vocabulary

## Outcome

- Landed V49 at `b70640f`, V50 at `2d45c06`, and V51 on `main`; pushed `main` to
  `origin`. Shared main is clean and synchronized.
- Created `feat/v51-typed-vocabulary` directly from landed V50. Two independent reviews
  classified one fixed 50-surface funnel; only their unanimous subset entered runtime.
- Added 32 normalized-unique grammatical forms of previously accepted exact aliases and
  eight Contexto-only, rank-penalty-one common guesses. Seven surfaces remain deferred,
  including disputed `amicii`; three are rejected. No quota was used.
- Preserved all nodes, edges, puzzles, game records, ranking rows, derived boards, owner
  holds, sessions, accounts, frontend, privacy, and deployment state.

## Quality and provenance

- ADR-0075 preserves V50's typed lexical boundary: exact same-referent forms may enter the
  shared Contexto/Lanț resolver; related terms remain non-winning Contexto projections.
- The review archive binds all 50 candidates, complete/disjoint reviewer dispositions,
  exact projection tuples, lexical sources, normalized-key uniqueness, and the final
  32/8/7/3 partition. Reviewer disagreement fails closed to defer.
- Only normative `Wi Fi` is authored. `Wi-Fi`, `wifi`, and bare `email` remain absent and
  are tested through resolver, projection, and Contexto behavior so spellings cannot create
  duplicate semantic attempts.
- The rollback-safe authoring transaction updated both KG mirrors and the mobile snapshot.
  V49's 104 directed rejection pairs and V48's historical/archive versus current-live
  Alchimie provenance boundary remain intact.

## Files changed

- Added the V51 data/applier, ADR-0075, exact lexical review archive, and focused regression
  contract; marked ADR-0074 superseded only for its fixed V50 inventory counts.
- Added eight terms and exact anchors to the Contexto projection; updated both KG mirrors,
  the canonical mobile snapshot, README/current status, and ranking/derived wrapper mirrors.
- Updated runtime and historical regression pins to distinguish current wrapper bytes from
  unchanged ranking rows, topology, pack bytes, and frozen derived-board payloads.

## Bound artifacts

- Candidate funnel SHA-256:
  `36eb871f07de3dde7169a896585031598791367af2c184b6dd6d15262933e416`.
- Exact projection binding SHA-256:
  `c0b8cb8fb6d464ab9536a8d11c26311a93de69d6031ac729e67bc49f5a06491b`.
- KG SHA-256: `db236736caee6dc8a00874939f52cba2082ef9a73ea1c40d9826a25099ef7e3a`.
- Pack SHA-256 remains `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking SHA-256: `265696defbefd31adf1bc2da46511a69083361721207ad4b8833d8b22bc4133b`;
  its board payload remains `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`.
- Derived SHA-256: `ee0bfd5ed51ff24a2e3ed8ea8ce32612548d9a418f138dacad2464d6bfd48b3d`;
  its frozen board payload remains `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
- V49 ledger SHA-256 remains
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.

## Verification

- Backend: 769/769; accounts-on: 53/53; sessions: 16/16; V51 contract: 10/10.
- Affected V33/V44/V47–V50 and app-pack/Contexto regressions: 150/150.
- Games-pack, KG, ranking, and derived validators: green; strict real Lanț pending sweep:
  three checked, zero flagged and zero FAIL findings.
- Ruff and `git diff --check`: green. Frontend was untouched, so no frontend gate ran.

## Sequencing and residual risk

- V51 is committed and landed on `main`, with `origin/main` synchronized. No production
  deployment is included.
- Deferred/rejected forms and unauthored spelling variants remain outside runtime. A later
  morphology, projection-attempt alias, topology, or board wave needs a new bounded review.
- Anonymous production remains unchanged on V48 `d59caed`; owner-only holds remain pending.
