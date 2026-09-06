# ADR-0114: Reviewed food batch with exact-dish tripe feedback

- Status: accepted
- Date: 2026-09-06

## Context

V82 screens eight familiar food targets over the V81 graph: Cozonac, Pască, Muștar,
Mujdei, Ciorbă de burtă, Urdă, Friptură and Bulz. The initial actual-API screen finds
several legible openers for each, but the existing `burtă` body-domain approximation
gives cold feedback for the soup whose defining ingredient it names. DEX's definition
of [ciorbă de burtă](https://dexonline.ro/definitie/burt%C4%83) explicitly names cattle stomach.

## Decision

Extend the existing projection-neighborhood policy with an explicit exact-target-only
mode. For normalized `burta`, borrow `n_gas_ciorba_burta` only when that exact soup is
the target; do not traverse its neighbors. Every other target keeps the original body
approximation. Gem keeps its previously reviewed neighborhood behavior. The original
projection surface, identity, domain, anchor and penalty remain unchanged in the vocabulary
inventory. This association does not make the ingredient a synonym or an exact answer.

The ingredient guess must remain nonwinning, rank at least two, with a hidden target and
private anchor. Repeats and resumed rounds retain ordinary behavior; unknown-input hints
must suppress secret-bearing proxies. Missing-anchor/custom fixtures retain their original
fallback. No graph topology, scoring formula, session field, cache or bounds change.

Promote all eight reviewed records `ct_gastronomie_321`–`328` in the order above: four
`usor` and four `normal` rounds. Each passed independent factual/quality screening, strict
critique and the complete bound analyst/verifier gate. Preserve earlier game records and
frozen boards while regenerating pack-bound artifacts through the existing builders.
The accepted list and remaining input limitations are recorded in the
[V82 review](../reviews/v82-playable-content-batch/README.md).

## Consequences

This batch combines an enabling feedback repair with playable targets under ADR-0113.
Future additions need their own factual and gameplay evidence; the exact-target mode
is not permission to assign arbitrary heat or treat body and culinary meanings as synonyms.
The integrated gate must cover public selection, useful guesses, privacy, repeat/resume,
exact wins, legacy projection boundaries and complete pre-wave artifact reconstruction.
