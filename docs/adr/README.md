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
| 0127 | [Recurring verified local version loop](0127-recurring-local-version-loop.md) | accepted |
| 0128 | [Recover uncertain Lanț actions](0128-reconcile-uncertain-lant-actions.md) | accepted |
| 0129 | [Portable projection-bound Alchimie reviews](0129-portable-alchimie-projection-reviews.md) | accepted |
| 0130 | [Closed native bread-family feedback](0130-closed-native-bread-family-feedback.md) | accepted |
| 0131 | [Everyday tools and cream-sense correction](0131-everyday-tools-and-cream-sense-correction.md) | accepted |

Earlier decisions affected by V88: [ADR-0039](0039-hygiene-anatomy-cleaning-word-meshes.md)
and [ADR-0068](0068-contexto-common-word-feedback-and-unique-targets.md) are partially
superseded by ADR-0131 for the six cleaning-node topology boundary; their other scope remains.
