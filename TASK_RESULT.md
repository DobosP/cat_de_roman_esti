# Task Result — V59 bounded human-anatomy morphology

## Summary

- V58 landed and was pushed at `9e1011b`; V59 starts directly from it on
  `feat/v59-human-anatomy-morphology`.
- The fixed funnel contains 50 normalized-unique case surfaces for 25 existing
  human-anatomy concepts. Its disposition calls for 48 qualified exact aliases across 24
  owners; `creierului` and `creierelor` remain rejected because the bare forms do not have
  one safe owner.
- The worktree fixture is `fixture-v59-human-anatomy-morphology`: 2,364 nodes, 9,217
  edges, 7,874 aliases, and 180 puzzles.
- V59 changes no projection, node, edge, puzzle, game record, hold disposition, or derived
  board. Pack bytes, topology, board payloads, sessions, accounts, frontend, privacy, and
  deployment behavior remain unchanged.
- V59 is implemented but remains uncommitted and unlanded pending a clean complete backend
  run or CI.

## Implementation scope

- Add the bounded V59 data module and transactional apply wrapper.
- Archive both complete reviews of the fixed 50-surface funnel and record ADR-0083.
- Add the focused V59 regression contract, including every historical rejected surface.
- Regenerate only alias-bearing KG/mobile/ranking/derived wrappers and update their current
  V59 build, count, and digest pins; keep topology and board payloads byte-stable.
- Update `README.md`, `docs/MOBILE_CONTRACT.md`, and `docs/STATUS.md` for V59.

## Review and artifact evidence

- Candidate-funnel digest:
  `606386a07e33909759a6f644e265bc5f20c956bb64fb992b7a64a355a6380500`.
- KG: `22e1f7345f9af8d67b9b5aafb769f6d42919c775ff577c3fc865f0d82215da38`;
  games pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper:
  `662c966c29be77e536cc73579c94b930ed3424dc99e4aa903c7a58a34d0f8773`;
  derived wrapper: `196b7a5f5fbf88c5de4e31762b238b9ce426d4d95329c38d675265e53626fa86`.
- Mobile snapshot:
  `49af5e2c9ed2a1ce00e7dfc511a8b3408bb7fad4e0a5a4a95e8cad8bac6fa22a`;
  Lanț rejection ledger:
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- The ranking-board payload remains
  `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`;
  the derived-board payload remains
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Verification

- Source assertions, both independent 48-accept/2-reject reviewer partitions, transaction
  dry-run, exact resolution, and inherited rejection checks passed.
- Focused V59: 6 passed. V31 + V32 + V59 compatibility: 20 passed. The expanded affected
  V31–V33/V44/V47–V59 run: 137 passed. Accounts-on: 53 passed. Session store: 16 passed.
- Ranking and derived read-only checks, pack and KG validators, strict Lanț sweep, fixture
  mirror equality, Ruff, and whitespace checks passed.
- The complete backend collected 817 tests and reported four failures while unrelated OCR
  jobs saturated the host: two unchanged Alchimie timing ceilings (30.8027 s > 30 s and
  62.0167 s > 45 s), plus exact-alias assertions in V31 and V32. The V31/V32 compatibility
  assertions were repaired, and both their targeted run and the expanded 137-test affected
  rerun are green. A clean complete backend rerun remains pending; the complete gate is not green.

## Risks and manual review

- Both rejected brain forms remain absent from exact, projection, and fuzzy paths after all
  48 accepted aliases are applied.
- No inherited V52–V58 rejected surface gains a route through the V59 additions.

## Merge recommendation

Do not land V59 until a clean complete backend run or remote CI is green.
