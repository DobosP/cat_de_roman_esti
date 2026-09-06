# V81 independent implementation review

Valid until: the V81 proposal, implementation sources, data module, generated artifacts, tests, historical reconstruction, ADR-0112 scope, or bound impact receipt changes.

Reviewer: `session_refactor`

Role: independent implementation reviewer

Verdict: **accept**, with no actionable finding.

## Binding

This review evaluates baseline `dbbcf6e8b810fb990c9acffb42d6426138551637` and the exact proposal SHA-256 `0612129b282feb6124c2992078178efc17fa088b0b425dbccf3291ee10b34d8a`. The machine-readable companion records complete source, test, generated-artifact, factual-review, impact, and ADR bindings.

The core source hashes are:

- `contexto_feedback.py`: `05a1075ba93c4ca2d00da0819c9d4f541330ba727e4b71f556d346a647131f24`
- `contexto.py`: `be73a3aaedfb8a3164643fd350052e12560dc52d6df21225d99d2c0e82688dd5`
- `contexto_projection.py`: `da816f4038ab01b619662409e0a5f20cfad8a81a2e5b1544fe8dbf517b060ec1`
- data module: `daea0d654ecd7f05fde467b7eccfad00e76d597f67b0a4106554a3de52004f07`
- applier wrapper: `7338e31899c31b5243da8d568b719cf7b5b67ffbe9742b575d249be8a541c824`
- V81 behavior tests: `0095e936a034ab2b4e2c9c4d51fc2a22e570a977b5455edd85e513d152e5fb77`
- history helper/tests: `4c310c66dcb6b74c731e6d33b7326065dcc93322219c09cbdcc14d9f2554214b` / `8eafa04f0618fdc4da5a836c08b5815f09ce9f7fb26db4bc920b456a425a1afa`
- canonical impact receipt: `c680aaaaa38ce641bee07d345ae430b9a437c7e0bc9265337847336084234070`

## Findings

The implementation matches the proposal exactly: one `Nucă` concept, sole alias `nucile`, and four forward, non-distractor `part_of` edges labeled `ingredient pentru` at strengths 0.97, 0.97, 0.95, and 0.90. The generated edges are `de8557` through `de8560`; the node has no predecessor, no reverse edge, and no pack occurrence. The wrapper uses the existing supported V24 transaction. It adds no applier or sparse-density exception.

The Contexto rule is narrow and direction-sensitive. Exact self returns before any fallback. Native scoring then requires the Nucă node, a direct forward non-distractor edge, exact relation and label, and the 0.90 floor. Fixtures verify the weak, reverse, distractor, wrong-relation, and wrong-label boundaries. Source inspection confirms that a custom graph without Miere falls back to native behavior. Everywhere else in the shipped graph, Nucă keeps its prior Miere approximation.

The privacy and win behavior is sound. A changed anchor is always penalized to rank 2 or worse and feedback distance 1 or worse. Exact `Nucă` or `nucile` wins only for a Nucă target. The public response keeps the submitted Nucă identity and never returns the private Miere anchor. Guess scoring, fuzzy confirmation, unknown suggestions, and warmer clues share the same helper. True Nucă typos cannot disclose hidden Nucă or Miere through confirmation; ambiguous `nuci` remains an uncounted advisory suggestion and is suppressed for either hidden anchor. A focused real-route test confirms Baclava receives Nucă as a playable rank-2 warmer clue, replay remains nonwinning and private, and a hidden Nucă target is excluded. Direct scorer inspection gives the same playable rank for all four reviewed recipe edges and a penalized nonwinning Miere proxy.

The alias boundary stays conservative. Ordinary normalization accepts accented and accentless canonical singular forms and case variants. `nucile` is the only authored alias. The ambiguous tree/fruit forms `nuci`, `nucii`, and `nucilor`, tree singular forms, `miez de nucă`, and `nucă de cocos` remain unresolved and do not fuzzy-score.

The generated delta is exact: 2365 nodes, 9223 edges, 180 puzzles, and 8451 aliases. No old edge changes. Only the four recipe target nodes change, by degree +1. The 621-row pack and 180 puzzles are byte-exact, and all 336 frozen derived board payloads are exact. Baclava gains one familiarity, quality, and pilot-score point and moves from rank 121 to 117; four displaced rows move by one. Status, eligibility, and selection weights remain unchanged.

The independent actual-route sweep found no cross-game blocker. Only the valid Baclava target changes from cold to Nucă at rank 2/Fierbinte; the other 207 approved Contexto targets retain their prior Nucă fallback distance and temperature. Conexiuni, Lanț, Alchimie, derived boards, puzzles, and the bounded selector sample are unchanged. Adding one reachable leaf necessarily shifts many old Contexto ordinals by one and moves 121 guesses across percentile boundaries, but changes no old semantic distance. The impact receipt records this limited global normalization effect explicitly.

The reconstruction helper checks the full V81 after-state before rebuilding the immutable pre-wave KG, rankings, derived metadata, and retired projection row. The historical tests then verify the exact old hashes, unchanged pack, and 180 puzzles. ADR-0112 scopes the four-edge exception solely to this Nucă node while keeping the normal density rule and barring broader aliases, reverse links, or old-node fan-out changes.

## Verification and limits

The focused V81, V81 history, V77, and V79 run passed 45 tests. Ruff on the reviewed source, scripts, helper, and tests passed, as did `git diff --check`.

I did not run the full suite. The selection audit covers 100 seeds and 30 September daily values per game and the Contexto gastronomie/usor shelf. Nucă is not a current pack target, so exact-self and non-packed recipe checks use controlled private sessions; human playtesting and any future target review remain separate gates.
