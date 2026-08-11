# Task Result — V50 bounded typed vocabulary

## Outcome

- Reviewed a finite 50-surface Romanian vocabulary funnel twice and accepted only the
  unanimous subset: 8 exact shared aliases and 12 Contexto-only non-winning projections.
  Eight surfaces remain deferred and 22 are explicit rejects; no quota was used.
- Exact aliases improve typed Contexto input and eligible Lanț hops. Related/basic words
  have rank-penalty-one Contexto feedback only. Conexiuni, Alchimie, Intrusul, and Perechi
  receive no alias substitution.
- Preserved 2,364 nodes, 9,217 edges, 180 puzzles, all 618 game records, every ranking row,
  and the frozen 336-board derived payload. Alias count is 7,460; Contexto projection count
  is 465 across the existing 26 domains.
- Added no topology, board, promotion, pending-hold disposition, frontend, account, privacy,
  session, or deployment change.

## Quality and provenance

- ADR-0074 separates exact same-referent resolver aliases from approximate non-winning
  feedback. The 50 candidate rows, both verdicts, normalized-key census, lexical sources,
  exact projection-binding digests, and final partition are archived under
  `docs/reviews/v50-synonym-basic-word-funnel/`.
- The rollback-safe authoring transaction updates both KG mirrors and the mobile snapshot,
  validates normalization ownership, and preserves pack bytes.
- V48 Alchimie archives replay their embedded historical provenance after alias-only KG
  changes. Live gates require the current KG, rubric, runtime sources and manifest,
  generator, and source pack; V50 independently tampers with every input.
- V49's 104-pair Lanț rejection ledger, alias-aware import preflight, full-inventory
  critique, and transactional future appends remain intact after integration.

## Files changed

- Added the V50 data/applier, lexical review archive, ADR-0074, and focused regression test.
- Updated Contexto projection data, both KG mirrors, the mobile contract, README/status,
  and exact ranking/derived mirrors plus their runtime/test digest pins.
- Versioned historical dossier/Alchimie replay separately from current live-gate checks;
  aligned both mobile snapshot writers with the checked-in canonical JSON format.
- Marked ADR-0068 superseded only for its old fixed 453-term inventory clause.

## Bound artifacts

- KG SHA-256: `56b861ae4f6d611e70e87e27086a3a617ccfc8b6d69d51b100677df3dff4be7e`.
- Pack SHA-256 remains `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking SHA-256: `12c0971c60b6e93f5c4443776f46570b5f9ae29d10f7254d3a222e7a38eafd4e`;
  its board payload remains `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`.
- Derived SHA-256: `e987229417aea266e12f3223cb696f13aa740225aaab56cb2d55b084a4fad1ea`;
  its frozen board payload remains `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Verification

- Combined V49+V50 backend: 759/759; accounts-on: 53/53; sessions: 16/16.
- V49 contract: 22/22; V50 contract: 11/11; affected V33/V44/V45–V48 and critique/import
  regressions: green.
- Pack, KG, ranking, and derived validators: green; the real Lanț pending sweep is clean.
- Ruff, three workflow syntax checks, JSON/mirror integrity, and `git diff --check`: green.
- Frontend was untouched; V48's 28/28, lint, typecheck, and production build remain the
  latest frontend evidence.

## Sequencing and residual risk

- V49 landed first at `b70640f`; V50 is rebased directly on it and retains ADR-0073.
- Deferred and rejected vocabulary stays out of runtime. A later topology wave, wild-animal
  domain, alternate-spelling attempt identity, or disputed alias needs a fresh review.
- V51 starts only after V50 lands, from a separate branch and finite two-reviewer funnel.
- Anonymous production remains unchanged on V48 `d59caed`.

## Landing

The owner authorized landing. This V50 change is green for a fast-forward main update and
push after the recorded gate; no production deployment is included.
