# ADR-0068: Repair Contexto common-word feedback and require unique targets

- Status: accepted
- Date: 2026-07-30

## Context

The strict V44 Fable/Codex replay found a shipped gameplay failure hidden by graph-wide
validation: all 71 concrete V30–V33 beginner nodes are inbound-only meshes. They can be
reached from mature concepts but cannot reach any of the 199 unique approved Contexto
targets, so exact familiar guesses and 43 existing projected terms always returned the
coldest unreachable result. Adding reverse graph edges would also change Lanț routes,
Alchimie recipes, target histograms, and derived behavior.

The same review found three approved Contexto records that repeat an already-selectable
target under a later ID/difficulty, while two long-held pending targets passed fresh,
exact-byte C1–C6 review. Romanian lexical review also separated true synonyms from
related, narrower, polysemous, or accent-folding-colliding forms.

## Decision

1. Apply a Contexto-only, explicit scorer proxy to exactly the 71 V30–V33 beginner nodes.
   Map them to 26 mature anchors supported by authored paths of at most three hops. Keep
   the submitted node's public ID and label; bypass proxying for an exact target; prevent
   proxy and projection guesses from winning; and apply at most one total approximation
   rank. Use the same effective scoring transformation for guesses, typo help,
   suggestions, played-anchor exclusion, and warmer-clue ranks.
2. Keep shared graph topology and target mining unchanged. Add 12 independently unanimous
   exact aliases to the shared resolver. Add 11 related forms only to the non-winning
   Contexto projection, bringing it to 453 terms across the same 26 domains. Retarget
   `sac de gunoi` directly to `Casă`. Rejected or disputed forms remain absent.
3. Promote the fresh bound dossiers for `ct_literatura_298` (`Capra cu trei iezi`) and
   `ct_viata_de_roman_299` (`Abecedar`). Keep the three later duplicate records approved
   for provenance, but exclude `ct_sport_315`, `ct_sport_316`, and `ct_sport_317` through
   a mirrored V44 reserve sidecar. Their canonical records remain selectable.
4. Supersede ADR-0042 and ADR-0045's fixed 444-term clauses with the reviewed 453-term
   inventory and shared effective-scoring rule. Supersede ADR-0066 only where it made
   `ct_sport_315` and `ct_sport_317` selectable; its other promotions, reserve model, and
   frozen-derived decisions remain in force.

## Consequences

Cald sau Rece has 201 selectable records and 201 unique targets. The original pack has
608 approved / 220 pending records and 447 selectable boards across its four games.
The KG remains 2,364 nodes / 9,217 edges / 180 puzzles and grows from 7,440 to 7,452
aliases. Lanț and Alchimie topology is unchanged. The frozen derived `boards` payload
remains 336 records; its digest-bound metadata is regenerated for the new pack, KG, and
ranking hashes.

The proxy inventory is intentionally closed: adding another scorer proxy, alias, projected
surface, or target requires the same collision, semantic-anchor, non-winning, reachability,
and exact-binding tests. A custom fixture missing a reviewed mature anchor falls back to
the submitted node's ordinary graph behavior.
