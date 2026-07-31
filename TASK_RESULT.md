# Task Result — V48 strict Alchimie live-recipe gate

## Outcome

- Rebuilt current-bound dossiers for the exact 21 pending Alchimie records and audited
  E1–E5 against both the broad graph and the sparse private recipe books players receive.
- Deterministic graph checks found zero failures and three salience warnings, but the new
  runtime projection audit found seven boards with only one live opening. It binds the
  exact IDs, source rows, pack, KG, rubric, dossiers, runtime sources, and generator.
- Two independent reviews synthesized fail closed to one promotion, 17 rejections, and
  three mandatory A5 keeps. Promoted only `al_literatura_097` (`Făt-Frumos`).
- Kept `al_gastronomie_026`, `al_gastronomie_030`, and `al_viata_de_roman_092` pending and
  unserved because every route depends on alcohol content covered by ADR-0019.
- Removed 17 weak, arbitrary, filler-heavy, or recycled records. Three reviewer promotion
  disagreements were rejected because promotion was not unanimous.
- Alchimie is now 82 records = 79 approved/selectable + 3 pending. The original-game pack
  is 618 = 610 approved + 8 pending / 449 eligible.
- Added no board, alias, projection term, node, edge, or KG content. Regenerated rankings
  and derived metadata without changing the frozen 336-board Intrusul/Perechi payload.
  No deployment was performed.

## Files changed

- Content: both game-pack mirrors, both ranking sidecars, both derived-catalog metadata
  copies, the runtime derived digest pin, and seven historical pack digest pins.
- Workflow: `scripts/audit_alchimie_projections.py` generates replayable private-recipe
  evidence; `scripts/apply_rereview.py` now requires both reviewers to bind that evidence,
  replays the full artifact, and verifies its source against the untouched pre-apply pack.
- Gate evidence: 21 exact dossiers, deterministic report, live-projection audit, complete
  two-reviewer artifact, review report, ADR-0072, and the current STATUS.
- Contracts: six V48 regressions plus unit coverage for missing, stale, and structurally
  unreproducible projection evidence; historical lifecycle/count/profile assertions now
  preserve removed records through the V48 archive.
- Unchanged: KG, frontend, scoring, hidden answers, session semantics, and derived boards.

## Verification

- Full backend: 726/726 green.
- Accounts-on: 53/53 green; bounded session store: 16/16 green under both the repository
  environment and the prescribed shared environment.
- Alchimie/runtime/V48 targeted gate: 55/55 green; V48 exact contract: 6/6 green.
- Intrusul/Perechi/derived-catalog gate: 56/56 green.
- Ruff, `git diff --check`, pack, KG, ranking, and derived-catalog validators: green.
- Pack mirrors: 618 records, 610 approved / 8 pending, 449 runtime-eligible.
- Alchimie: 82 records, 79 approved / 3 pending, 79 selectable.
- Frozen derived boards: 183 Intrusul / 153 Perechi, unchanged SHA-256
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

The prescribed session command emitted only its existing warning that the shared
`romania_scraper` environment does not recognize the Django pytest option; all 16 tests
still passed. Frontend gates were not required because no frontend file changed.

## Risks and manual review

Alchimie has no generic rejection ledger. The committed source records, record digests,
dossiers, reviewer bindings, projection audit, ADR, and regression tests preserve all 17
removals. Any repair must consult that archive, materially change the named defect, and
pass a fresh source-bound E1–E5 gate.

The three A5 holds still require explicit owner disposition. The projection artifact
intentionally pins the reviewed runtime and generator; a future recipe-runtime change must
refresh evidence rather than silently inheriting these judgments. Production remains V43
at `38da2f4`; V48 deliberately does not alter deployment state.

## Merge recommendation

Green to commit, land, and push on `main`. Do not deploy V48 as part of this content gate,
and retain the task worktree/branch until the owner explicitly authorizes deletion.
