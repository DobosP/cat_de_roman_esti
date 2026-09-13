# V92 — Larger Alchimie vocabulary

Valid until: changes to the catalog, provenance, compatibility history or bound serving sources — then treat as history.

The owner explicitly requested another substantial concept expansion. Baseline:
`8f97bd9`. Decision: [ADR-0147](../../adr/0147-grow-alchimie-with-reviewed-vocabulary.md).
Current integration state: [STATUS](../../STATUS.md).

## Playable content

| Measure | Before | After |
|---|---:|---:|
| Collectible concepts | 111 | 221 |
| Crafted discoveries | 58 | 117 |
| Initial starters | 8 | 8 |
| Later pantry supplies | 45 | 96 |
| Canonical recipes | 116 | 285 |
| Results with alternate recipes | 40 | 77 |
| Reusable crafted intermediates | 23 | 47 |
| Terminal crafted dishes | 35 | 70 |
| Productive initial pairs | 7 / 28 | 9 / 28 |
| Optional goals | 19 | 32 |

The 110 additions are **59 crafted results and 51 supplied ingredients/tools**. All
original concept records, recipes, supply tiers, starters and goals remain exact.
The [author invariants](author-invariants.json) and [live audit](live-audit.json)
record the inventory and complete reachability. These are combinatorial checks,
not measured player success rates or enjoyment scores.

New foundations include mayonnaise, choux pastry, laminated pastry, tomato sauce,
caramel, ganache, hummus, aubergine spread, mashed vegetables and pastry fillings.
They create longer useful chains. Both oven and pan make toast; cutting toast makes
croutons. Cooked cabbage precedes the Cluj dish, and Dubai chocolate requires the
distinctive pistachio/kataif filling. Generic tool-to-named-dish shortcuts were removed.

## Vocabulary provenance and review

The world contains **174 existing KG identities and 47 authored definitions**. The
latter fill missing ingredients and preparations inside Alchimie's catalog; they are
not inserted into the shared graph. The [base-stock delta](base-stock-delta.json)
confirms that KG/pack/mobile counts and content remain unchanged.

World-local definitions use `alw_food_` IDs, original Romanian wording, checked primary
reference URLs and exact snapshots. Their source is `authored:alchimie`; no third-party
redistribution license is inferred. KG records retain their original complete metadata.
Both the generator and runtime prevent identity shadowing and ambiguous labels.

[Candidate](candidate.json) SHA:
`da5a2a1df2790a2cd3f9db0806f8112c7b0ccdb63ed6d7d2e3f418542d4e209a`.
Both semantic reviews cover **285 recipe rows and 221 exact concept digests**:
[factual](reviews/factual-review.json), [quality](reviews/quality-review.json).
The 116 prior recipes and 111 prior concept records explicitly inherit byte-compared
judgments. New definitions require their own acceptance and factual source evidence.

Catalog SHA: `baafc2fc656dfe501dbe5be03ce2bd536e086b71f1711d0cf8c77ed56a03e1df`.
Two final reviews bind those exact bytes and [the runtime audit](live-audit.json)
before the atomic package write: [factual](reviews/final-factual-review.json) and
[quality](reviews/final-quality-review.json).

## Collection compatibility and verification

Both historical books are carried forward: the original 75-concept/39-craft collection
and the 111-concept/58-craft expansion. The server validates each checkpoint against
its original mechanics, then restores its discoveries into the current world. Unknown
fingerprints and newly invented recipes under older authority remain rejected.

The runtime audit completes free exploration and all 32 goals, validates KG/authored
provenance separately and restores all 39/58 historical prefixes. Independent factual
checks also complete 50 randomized worlds, 50 checkpoint restores, 100 historical
migrations and 100 live-session upgrades. A synthetic full 256-concept test separately
proves restoration above 128 earned crafts; the actual book contains 117 crafts.

Full commands, final results, source fingerprints and intermediate findings are in
[verification](verification.json). Final gates: **1837 backend, 53 accounts, 212 native
frontend and 446 browser checks pass**. Browser coverage includes both historical restores,
continuing from a completed old collection, retained journal/search/goal, and accessibility.
The save limit remains 64 KiB, now measured as UTF-8 bytes, with at most 256 craft pairs.

Review/testing caught a too-large draft supply tier and a missing runtime normalized-label
guard; both were fixed. The first browser focus caught the screen fade mid-transition
during contrast measurement. The audit now waits for the existing route opacity to settle,
as the other accessibility tests do, while retaining all contrast checks and UI colors.

The world remains finite and food-themed, and some recipe explanations intentionally
simplify preparation. No deployment, human playtest, physical-device acceptance or
cross-device account synchronization is established by these automated results.
