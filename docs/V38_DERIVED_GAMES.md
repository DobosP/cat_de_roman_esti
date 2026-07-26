# V38 derived games and ranking

ADR-0052 adds two short modes from a finite private catalog. This document is the maintainer
contract for regenerating and interpreting that artifact; it is not player-facing copy.
The product decisions and rejected alternatives remain in
[`ADR-0052`](adr/0052-derived-beginner-games.md).

## Inventory

| Mode | Strict candidates | Source boards | Kept boards | Starter boards |
|---|---:|---:|---:|---:|
| Intrusul | 800 | 66 | 183 | 24 |
| Perechi | 9,164 | 51 | 153 | 26 |

The source pool is exactly the 123 V37 `pilot_eligible` Conexiuni boards. A source may yield
many valid combinations, but the generator keeps at most three. It greedily prefers visible
concepts not already used by that source's retained variants, then standard score, mechanic
quality, familiarity, and stable candidate ID.

## Strict gates

Association strength is the strongest traversable, non-distractor edge in either direction.

- **Intrusul:** the three members and intruder have one node type; at least two member-member
  edges are at least 0.60; the intruder has no real edge to any member. The authored source
  group label is the only explanation.
- **Perechi:** one pair comes from each authored source group; all four intended strengths
  are at least 0.60; every unintended link among the eight visible nodes is below 0.60. The
  threshold graph therefore has one intended perfect matching.

These checks establish consistency with the reviewed KG and source partition. They do not
prove that every human interpretation is unique, so player feedback remains necessary.

## Scores and selection

Visible-word familiarity uses KG salience while retaining the weakest-word signal. Mechanic
quality rewards in-group cohesion for Intrusul and intended-pair strength plus cross-pair
separation for Perechi.

```text
standard_score = round_half_up(0.60 * familiarity + 0.40 * quality)
starter_score  = round_half_up(0.75 * familiarity + 0.25 * quality)
```

Starter eligibility is a separate gate: every visible word must clear salience 0.35; the
weakest intended link must clear 0.70; Perechi additionally requires zero unintended real
links. Runtime chooses a source first, then one of its retained variants. Scores map to fixed
1–5 ticket bands, so two equal scores always have equal weight. Stored ranks use competition
ranking (`1, 1, 3` for a two-way tie); they are audit metadata and do not replace the fixed
ticket bands. Daily selection uses the same two-stage shape with deterministic rendezvous
tickets. V37 selection code, its hash namespaces, and all existing daily assignments are
unchanged.

## Bounded session play

- **Intrusul:** four tiles; the player finds the intruder. Three distinct wrong taps end the
  game, repeated wrong taps are free, and one group-label hint unlocks after the first
  mistake. A win scores `max(100, 1000 - 200 × mistakes - 150 × hint)`; a loss scores zero.
- **Perechi:** eight tiles; four correct pairs lock one at a time. Six distinct unordered
  wrong pairs end the game, repeats are free, and one hint unlocks after two mistakes and
  reveals one unresolved pair without solving it. A win scores
  `max(100, 1000 - 100 × mistakes - 150 × hint)`; a loss scores zero.

Both games use the shared 7,200-second sliding session TTL and 1,000-entry per-game cap.
Session mutation is atomic. Answers remain hidden until a terminal state, apart from a
solved pair or explicitly earned hint, and non-daily replay memory retains at most four
distinct private source IDs.

## Private fields

The catalog row's source ID, derived ID, familiarity, quality, scores, eligibility, ranks,
and all selection weights are server-only. Before terminal state, APIs also hide the
intruder, trio membership, and unresolved pair mapping. A used hint or solved pair is earned
information and may be returned. Shares and local/browser score history must never contain a
source/catalog ID or ranking component.

## Check and regenerate

```bash
PYTHONPATH=. python scripts/build_derived_catalog_v38.py
PYTHONPATH=. python scripts/build_derived_catalog_v38.py --write
PYTHONPATH=. python -m pytest tests/test_v38_derived_rankings.py tests/test_v38_ranked_catalog.py -q
```

The default command recomputes all candidates and compares both committed fixture copies.
`--write` is a reviewed maintainer action. Runtime also checks the artifact's pinned digest
and its pack, KG, critique-rubric, and V37-ranking bindings. Any `CAT_GAMES_PACK`,
`CAT_KG_FIXTURE`, or `CAT_BOARD_RANKINGS` runtime override deliberately fails closed because
V38 has no neutral derived-content fallback. Loading a non-bundled catalog also requires its
explicit matching SHA-256 digest.
