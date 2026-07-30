# Task Result — bundled derived-catalog deployment fix

## Outcome

- Production smoke exposed that Compose's exact bundled `CAT_KG_FIXTURE` path was
  incorrectly treated as a custom runtime source, forcing Intrusul and Perechi to 503.
- The loader now distinguishes exact bundled paths from genuine source overrides.
- Custom pack, KG, and ranking paths still fail closed; catalog digests and source
  bindings remain mandatory.

## Files

- `cat_de_roman_esti/wordgames/derived_catalog.py`
- `tests/test_v38_ranked_catalog.py`
- `docs/V38_DERIVED_GAMES.md`
- `docs/DEPLOY.md`
- `docs/STATUS.md`

## Verification

- Catalog plus Intrusul/Perechi API contracts: 68/68 green.
- Exact Compose `CAT_KG_FIXTURE` environment: 42/42 Intrusul/Perechi API tests green.
- Complete backend: 688/688 green.
- Ruff and `git diff --check`: green.
- Independent blocker review: no blockers.
- Production redeployed at `38da2f4`: container catalog 183/153, health/manifest,
  accounts-off, 14 populated categories, frontend, and all six create endpoints green.
- Recent production app logs contained no 5xx/error entries after the final smoke.

## Risk

Narrow path-classification change only. The derived artifact, board payload, session
behavior, API responses, and Compose environment are unchanged.
