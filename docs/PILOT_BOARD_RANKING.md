# V37 pilot board ranking

ADR-0051 defines this as an **editorial pre-playtest estimate**, not measured fun or a
test of any player's Romanian knowledge. The committed sidecar
`cat_de_roman_esti/fixtures/board_rankings_v37.json` contains one private row for every
curated pack record; no ranking field is returned by a game API.

## What the numbers mean

All component values are rounded integers from 0 to 100.

| Field | Meaning |
|---|---|
| `romanian_familiarity` | Recognition proxy over the concepts needed to play the board. Node salience is the KG's blend of Romanian corpus frequency, centrality, and structured-source prior. |
| `play_quality` | Game-specific structural estimate from the same bounded evidence used by critique dossiers. |
| `pilot_score` | `60% × romanian_familiarity + 40% × play_quality`. |
| `rank` | Unique ordinal inside one game over approved and review inventory, sorted by score then stable ID. |
| `pilot_eligible` | `true` only for an approved, payload-valid record with no deterministic critique `FAIL`. |
| `selection_weight` | One to five tickets from the eligible approved board's within-game quintile; ineligible rows remain at one. |

Status and eligibility are intentionally separate from score. A pending record may score
well and remain unservable; a familiar but unfair board cannot outrank its way through the
critique gate.

## Familiarity aggregation

- **Conexiuni:** all 16 tile scores, their lower quartile, and the strongest four-tile
  group mean. The lower tail matters because one obscure tile can block a partition.
- **Cald sau Rece:** target familiarity plus recognizable strong direct neighbors. A known
  target with familiar warm anchors is easier to approach by association.
- **Lanț:** both endpoints plus the distinct intermediate concepts on bounded representative
  shortest routes. The weakest endpoint remains visible in the result.
- **Alchimie:** seeds, target, and the intermediate results in one minimum-action recipe.
  The weakest seed is retained so filler does not disappear inside a high mean.

## Structural quality aggregation

- **Conexiuni:** foreign-group pulls, contested tiles, raw entanglement, mirrored/type-mixed
  groups, repeated groups, and non-distinctive region links. Any deterministic `FAIL`
  removes pilot eligibility independently of the numeric penalty.
- **Cald sau Rece:** strong and familiar inbound neighbors, target incoming degree, and the
  bounded reachability floor, with a penalty for non-distinctive regional associations.
- **Lanț:** credible first hops, the narrowest shortest-path layer, average path width, and
  semantic strength along representative shortest routes.
- **Alchimie:** productive-opening density, minimum-recipe semantic strength, action par
  fit for the declared difficulty, and noisy multi-result opening pressure.

The exact integer formulas live in `scripts/rank_games_pack.py` and are unit-tested. The
sidecar binds normalized SHA-256 digests for `games_pack.json`, `kg_sample.json`, and
`docs/CRITIQUE_RUBRIC.md`; changing any input makes the check fail closed.

## Check and regenerate

```bash
PYTHONPATH=. python scripts/rank_games_pack.py
PYTHONPATH=. python scripts/rank_games_pack.py --write
```

The first command checks committed bytes and prints a short per-game audit. `--write` is
the explicit maintainer action after a reviewed pack, KG, rubric, or formula change. Both
fixture copies must stay byte-identical, and `scripts/validate_games_pack.py` plus the
critique gate still run independently.

## Pilot interpretation

Weighted selection increases exposure to stronger eligible boards while keeping every
eligible board reachable. Approved ineligible stock is reserve content only when the
eligible shelf is empty or below its daily minimum. This does not make a causal claim about
enjoyment. A later calibration needs server-authored aggregate starts, terminal outcomes,
hints, and action counts keyed only by internal board ID. Identities, session IDs, raw
guesses, free text, and client-authored public scores are outside V37.
