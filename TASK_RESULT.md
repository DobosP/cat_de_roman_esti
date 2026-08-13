# Task Result — V57 bounded creative-arts morphology

## Summary

- V56 landed on `main` and was pushed as `0394bc5`; `feat/v57-typed-vocabulary` starts
  directly from that commit.
- Two independent reviews covered a fixed 50-surface funnel: two Romanian
  genitive/dative forms for each of 25 existing creative-arts concepts.
- Forty-eight normalized-unique surfaces were accepted as exact aliases for 24 existing
  owners. `tabloului` and `tablourilor` were rejected because ordinary artwork,
  table/chart, theatre-division, technical-panel, and array senses do not have one safe
  owner.
- The bundled fixture now identifies itself as
  `fixture-v57-creative-arts-morphology` and contains 2,364 nodes, 9,217 edges, 7,778
  aliases, and 180 puzzles.
- V57 adds no Contexto projection, node, edge, puzzle, game record, hold disposition, or
  derived board. Pack and board payloads, frontend, sessions, accounts, privacy, and
  deployment behavior are unchanged.
- The first reviewed set exposed a cross-wave fuzzy regression: `corului`/`corurilor`
  made V56's rejected `corpului`/`corpurilor` autocorrect to the choir node. Two fresh
  audits replaced that row with qualified folk-ballad forms and restored all inherited
  rejection boundaries.
- V57 is green and remains intentionally uncommitted and unlanded for owner review.

## Files changed

- Added the bounded data and application scripts:
  `scripts/contexto_common_words_v57_data.py` and
  `scripts/apply_contexto_common_words_v57.py`.
- Added the two-reviewer evidence under
  `docs/reviews/v57-creative-arts-morphology/`.
- Added ADR-0081 and superseded ADR-0080 only for the V56 alias-count/build pins.
- Added `tests/test_v57_creative_arts_morphology.py` for funnel completeness, exact
  resolution, rejected-surface absence, typed Contexto/Lanț behavior, topology and
  payload invariants, mirror equality, the mobile contract, and the V49 ledger.
- Updated both KG fixtures and their bound ranking, derived-catalog, and mobile-contract
  mirrors; updated `README.md`, `docs/MOBILE_CONTRACT.md`, and `docs/STATUS.md` for the V57
  build and alias count.

## Review and artifact evidence

- Candidate funnel SHA-256:
  `1637e4c45028f6aa07ce3fb87dbb1d774174edd09c54c41b89a65bf18bf03d39`.
- KG fixture SHA-256:
  `7098d7fb2178656209b72c779dc73583c442bbb601c7eaf08d42920367834d4d`.
- Games pack SHA-256, unchanged:
  `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper SHA-256:
  `0bfd99fba8f3f85fb125fbd5fca8e8b72c60c5b1dcb2bc2e362d5ecad4d4f29b`;
  unchanged `boards` payload SHA-256:
  `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`.
- Derived wrapper SHA-256:
  `dcdf298e4fb39b42696249b272e9c210b145ea6f9539a20ea402b7b8a0a1b5d2`;
  unchanged `boards` payload SHA-256:
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
- V49 Lanț rejection-ledger SHA-256, unchanged:
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- Mobile contract SHA-256:
  `519fece9f718791e9582750e119e07e1baa89b1d45aa599b36b17b9db2b77565`.

## Verification

Completed checks:

- All 50 candidates had no exact or Contexto-projection owner before application.
- Both rejected _tablou_ forms also had no fuzzy runtime owner.
- Both independent reviewer partitions are complete: 48 exact-alias accepts, no
  projection accepts or deferrals, and the same two rejects.
- All 14 morphology rejections from V52–V57 remain absent from exact, projection, and
  fuzzy runtime paths after the collision repair.
- Current artifact digests and package/test mirror bytes match the values recorded above.
- Backend: 805/805; accounts-on: 53/53; sessions: 16/16; V57 contract: 6/6.
- Affected V33/V44/V47–V57 contracts: 111/111.
- Games-pack, KG, ranking, and derived validators: green; strict Lanț pending sweep:
  three checked, zero flagged and zero FAIL findings.
- Package/test KG, pack, ranking, and derived mirrors are byte-identical.
- Ruff and `git diff --check`: green. Frontend was untouched, so no frontend gate ran.

## Risks and manual review

- The acceptance boundary is intentionally narrow: inflection alone does not create a new
  sense, while either _tablou_ surface would collapse several ordinary senses onto the
  artwork node. Future admission of those forms needs explicit disambiguation evidence or
  distinct modeled owners.
- No frontend build was required because V57 changes no frontend file.

## Merge recommendation

V57 is green, and the owner explicitly requested landing before V58 starts.
