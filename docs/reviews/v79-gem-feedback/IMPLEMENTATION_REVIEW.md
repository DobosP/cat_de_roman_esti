# V79 bounded `gem` feedback-neighborhood implementation review

Valid until: proposal `cde39575f4b3ac13a3139f00216af79f2e2edcfcfc9d7735286c7a213bf615b5`, either bound source, test, impact receipt, or bound content artifact changes — then treat as history.

Date: 2026-09-06

## Verdict

Approve the bounded implementation. No actionable source, privacy, mechanics, or test finding remains.

The earlier global Dulceață substitution remains rejected: it made 13 approved targets newly warm, including misleading feedback for Murături and Grătarul de 1 Mai. The final source keeps the existing Miere anchor in the 473-row projection inventory and adds one private neighborhood policy for `gem`. Dulceață is selected only for itself or a directed, non-distractor Dulceață-to-target edge whose strongest traversable edge is at least 0.60; missing, weak, reversed-only, distractor, indirect, and unrelated cases retain Miere.

## Source and behavior

`_projection_anchor_id` implements the proposal literally through `WordGameService.link`, whose default graph view excludes distractors and preserves direction. Both accepted projection guesses and typo-suggestion privacy call this helper. The subsequent existing scorer still enforces projection nonwinning and the one-rank penalty. The response keeps the surface-derived public ID and label; neither the effective anchor nor hidden target is serialized.

The helper selects Dulceață for exactly six of 2,364 current nodes: Dulceață, Papanași, Magiun de Topoloveni, Conserve de iarnă, Clătite, and Fruct. Socată's 0.45 seasonal edge remains on Miere. The test inventory pins this exact set and the full KG hash, so a future topology edit cannot silently extend it.

The independent real-route sweep covered all 207 approved Contexto targets and all 203 eligible rows. Exactly one served row changes: Papanași moves from distance 5/rank 1291/Foarte rece/44 to distance 1/rank 13/Fierbinte/99. The other 206 responses are exact, no cross-category target becomes newly hot, all target values remain hidden, and a forced-default replay matches the original baseline. All 473 projection rows and the KG, pack, rankings, and derived artifact hashes remain unchanged.

## Verification

- Independent focused run: `tests/test_v79_gem_feedback.py` plus `tests/test_v44_contexto_common_words.py` — 25 passed.
- Final V79 file alone: 13 passed.
- Scoped Ruff: passed.
- `git diff --check`: passed.

Coverage includes exact policy fields, the 0.60 boundary, direction, distractors, missing local anchor, all six current effective targets, Socată and savory fallbacks, public payloads, repeat/resume, nonwinning against Dulceață, secret-aware suggestions for Miere and Dulceață, Lanț isolation, and immutable content artifacts.

## Residual limit

The strength floor is safe for the bound KG because every current qualifying edge was reviewed. It is not a universal semantic rule. The exact-set and fixture-hash tests should remain hard gates whenever the graph changes. This review makes no human-playtest or target-promotion claim.
