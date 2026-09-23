# Architecture decision index

The numbered files in this directory are the append-only decision history. Current
implementation and verification are recorded in [STATUS](../STATUS.md). Earlier decisions
are indexed by their filenames (0001–0097); new numbers are claimed here before parallel work.

| Number | Decision | Status |
|---|---|---|
| 0098 | [Real browser game journeys](0098-protect-real-browser-game-journeys.md) | accepted |
| 0099 | [Shared session endpoint transactions](0099-consolidate-session-endpoint-transactions.md) | accepted |
| 0100 | [Shared saved-game resume lifecycle](0100-extract-saved-game-resume-lifecycle.md) | accepted |
| 0101 | [Reliable saved-game recovery](0101-recover-saved-game-resume-failures.md) | accepted |
| 0102 | [Pack-only content waves](0102-pack-only-content-wave-workflow.md) | accepted |
| 0103 | [Keyboard-reachable game status](0103-make-game-status-keyboard-reachable.md) | accepted |
| 0104 | [Portable independent reviews](0104-portable-independent-review-artifacts.md) | partially superseded by 0129 |
| 0105 | [Idempotent local completion recording](0105-deduplicate-local-terminal-score-receipts.md) | accepted |
| 0106 | [Two reviewed Contexto food targets](0106-add-reviewed-contexto-food-targets.md) | accepted |
| 0107 | [Reviewed Romanian input senses](0107-preserve-reviewed-romanian-input-senses.md) | accepted |
| 0108 | [Bounded flour ingredient associations](0108-add-bounded-flour-ingredient-associations.md) | accepted |
| 0109 | [Defer dessert targets after fresh feedback review](0109-defer-dessert-targets-after-feedback-review.md) | accepted |
| 0110 | [Fruit-preserve feedback for Gem](0110-use-fruit-preserve-feedback-for-gem.md) | partially superseded by 0117 |
| 0111 | [Reviewed Clătite target](0111-promote-reviewed-clatite-target.md) | accepted |
| 0112 | [Reviewed walnut input](0112-add-reviewed-walnut-input.md) | accepted |
| 0113 | [Outcome-based version batches](0113-outcome-based-version-batches.md) | accepted |
| 0114 | [Reviewed food batch and scoped tripe feedback](0114-reviewed-food-batch-and-scoped-tripe-feedback.md) | accepted |
| 0115 | [Bounded reuse during Alchimie generation](0115-reuse-alchimie-pair-results-within-a-build.md) | accepted |
| 0116 | [Shared current-content test expectations](0116-share-current-content-test-expectations.md) | accepted |
| 0117 | [Food forms and exact-target feedback](0117-food-forms-and-exact-target-feedback.md) | accepted |
| 0118 | [Reviewed culinary graph corrections](0118-reviewed-culinary-graph-corrections.md) | accepted |
| 0119 | [In-round help and earned link explanations](0119-in-round-help-and-earned-link-explanations.md) | accepted |
| 0120 | [Native ingredients and audited vocabulary](0120-native-ingredients-and-audited-vocabulary.md) | accepted |
| 0121 | [Exact labels and stable board identities](0121-exact-label-corrections-with-stable-board-identities.md) | accepted |
| 0122 | [Visible alternative routes in Lanț](0122-visible-alternative-routes-in-lant.md) | accepted |
| 0123 | [Reviewed preparation and cooling concepts](0123-reviewed-preparation-and-cooling-concepts.md) | partially superseded by 0131 |
| 0124 | [Persistent game creation failures](0124-persist-new-game-creation-failures.md) | accepted |
| 0125 | [Reviewed snack concepts and defining biscuit cues](0125-reviewed-snack-concepts-and-biscuit-cues.md) | accepted |
| 0126 | [Authoritative Contexto action recovery](0126-reconcile-uncertain-contexto-actions.md) | accepted |
| 0127 | [Recurring verified local version loop](0127-recurring-local-version-loop.md) | superseded by 0137 |
| 0128 | [Recover uncertain Lanț actions](0128-reconcile-uncertain-lant-actions.md) | accepted |
| 0129 | [Portable projection-bound Alchimie reviews](0129-portable-alchimie-projection-reviews.md) | accepted |
| 0130 | [Closed native bread-family feedback](0130-closed-native-bread-family-feedback.md) | accepted |
| 0131 | [Everyday tools and cream-sense correction](0131-everyday-tools-and-cream-sense-correction.md) | accepted |
| 0132 | [Recover uncertain Conexiuni actions](0132-reconcile-uncertain-conexiuni-actions.md) | accepted |
| 0133 | [Closed dust and whipped-cream feedback](0133-closed-dust-and-whipped-cream-feedback.md) | partially superseded by 0135 |
| 0134 | [Directed Contexto incoming-neighbor floor](0134-directed-contexto-neighbor-floor.md) | accepted |
| 0135 | [Household discovery concepts and native Praf](0135-household-discovery-concepts.md) | accepted |
| 0136 | [Recover uncertain Alchimie actions](0136-reconcile-uncertain-alchimie-actions.md) | accepted |

| 0137 | [Finish V91 and stop automatic iteration](0137-finish-v91-and-stop-iteration-loop.md) | accepted |
| 0138 | [Owned Intrusul and Perechi action recovery](0138-owned-intrusul-perechi-recovery.md) | accepted |
| 0139 | [Visible mobile status and notices](0139-visible-mobile-status-and-notices.md) | accepted |
| 0140 | [Reviewed Sport seed revision](0140-reviewed-sport-seed-revision.md) | accepted |
| 0141 | [Alchimie workbench GUI rebuild](0141-rebuild-alchimie-workbench.md) | superseded by 0142 for interaction and default layout; safety boundaries retained |
| 0142 | [Direct Alchimie crafting with fewer actions](0142-direct-alchimie-crafting.md) | accepted; other-game scope expanded by 0143 |
| 0143 | [Simplify the five other game interfaces](0143-simplify-the-five-other-games.md) | accepted |
| 0144 | [Reviewed Alchimie recipe freedom](0144-reviewed-alchimie-recipe-freedom.md) | partially superseded by 0145 for exploration scope |
| 0145 | [Persistent Alchimie discovery world](0145-persistent-alchimie-discovery-world.md) | partially superseded by 0146 for expansion/upgrades and 0149 for optional controls |
| 0146 | [Expand Alchimie and preserve collections](0146-expand-alchimie-and-preserve-collections.md) | partially superseded by 0147 for larger vocabulary, bounds and history |
| 0147 | [Grow Alchimie with reviewed vocabulary](0147-grow-alchimie-with-reviewed-vocabulary.md) | accepted |

| 0148 | [Expand all game content with independent review](0148-expand-all-game-content-with-independent-review.md) | accepted |

| 0149 | [Review new levels and keep crafting feedback visible](0149-review-new-levels-and-keep-crafting-feedback-visible.md) | accepted; extended by 0150 |

| 0150 | [Expand vocabulary and clarify game controls](0150-expand-vocabulary-and-clarify-game-controls.md) | accepted |
| 0151 | [Expand game vocabulary and search earned recipes](0151-expand-game-vocabulary-and-search-earned-recipes.md) | accepted |
| 0152 | [Expand reviewed rounds and explain Lanț connections](0152-expand-reviewed-rounds-and-explain-lant-connections.md) | accepted |
| 0153 | [Expand discovery and remember attempted Alchimie pairs](0153-expand-discovery-and-remember-attempted-pairs.md) | accepted |
| 0154 | [Expand V96 content and clarify input recovery](0154-expand-content-and-clarify-input-recovery.md) | accepted |
| 0155 | [Preserve discovery history and explain food links](0155-preserve-discovery-history-and-explain-food-links.md) | accepted |
| 0156 | [Refine content and maintain an experimental discovery pool](0156-two-track-content-growth.md) | accepted |
| 0157 | [Start V99 with reviewed route explanations and a discovery pool](0157-start-v99-refinement-and-discovery.md) | accepted |
| 0158 | [Prepare V1 for mixed-age phone and desktop testing](0158-v1-testing-release.md) | accepted (amended by 0159) |
| 0159 | [Harden V1 as 1.0.1 before physical-device testing](0159-v1-0-1-testing-hardening.md) | accepted |

Earlier decisions affected by V88: [ADR-0039](0039-hygiene-anatomy-cleaning-word-meshes.md)
and [ADR-0068](0068-contexto-common-word-feedback-and-unique-targets.md) are partially
superseded by ADR-0131 for the six cleaning-node topology boundary; their other scope remains.

Earlier decisions affected by V92: [ADR-0052](0052-derived-beginner-games.md) and
[ADR-0054](0054-refine-derived-pilot-before-expansion.md) are partially superseded by
ADR-0148 for authored quick-game catalog expansion; their selection and safety rules remain.

[ADR-0043](0043-lant-visible-route-corridors.md) is also partially superseded by ADR-0149
for skipping generic direction hints; informative hint stages and route boundaries remain.

ADR-0153 also partially supersedes [ADR-0043](0043-lant-visible-route-corridors.md)
for casual easy-round sampling; daily preference and route-quality floors remain.

ADR-0154 partially supersedes [ADR-0021](0021-graded-similarity-and-fuzzy-suggestions.md)
for Contexto advisory display filtering and unknown-word feedback.

ADR-0159 partially amends [ADR-0158](0158-v1-testing-release.md) for the lobby version label
and the word-grid reflow; its release, reserve and content decisions remain.
