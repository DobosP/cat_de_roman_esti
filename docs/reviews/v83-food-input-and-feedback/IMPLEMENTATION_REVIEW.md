# V83 independent implementation and preservation review

Valid until: the reviewed runtime, content artifacts, inverse helpers or journey tests change — then treat as history.

Reviewed on 2026-09-07 by the independent `iteration_overhead_audit` agent against
`38f0d62ff1cd72003ae94ed691db4c44eb78c794`. No blocking implementation or
preservation defect found. The final full integration matrix remains separate
evidence; this review does not certify human enjoyment.

- Four native ingredient/dish pairs and Gem's two named pastry targets are closed
  exact-target rules. Native rules require both nodes; Gem's extensions require
  the existing neighborhood anchor and target. No neighboring or reverse route is
  admitted. Prior Gem, burtă and walnut policy defaults remain intact.
- Accepted ingredients retain their own identity and cannot win through the
  borrowed anchor. The shared scorer retains a nonwinning rank and the private
  anchor; existing fuzzy/suggestion filters and warmer clues use that same
  transformation. The new tests cover exact boundaries, missing anchors,
  nonwinning feedback, privacy, repeats, resume and deterministic clue replay.
  No session field, capacity, lifetime or search bound changes.
- An independent direct comparison with Git found exactly **24 added forms**,
  with all other node fields, **9,223 edges** and **180 puzzles** unchanged. The
  old and new services directly resolved all **13,180 prior authored surfaces**
  to identical owners. All **629 prior pack records** and **336 frozen boards**
  are exact; precisely five Contexto records are added. Of the old ranking rows,
  142 change only `rank` and/or `selection_weight`.
- All four inverse helpers reconstructed the complete V82 KG, pack, ranking and
  derived artifacts byte-for-byte against actual Git content, independently of
  the receipts' claims. Prior review archives are unchanged. V76's original
  resolution assertion excludes only later additions and retains its original
  count/hash; historical reconstruction assertions remain literal.
- The shared manually authored snapshot refactor retains its earlier acceptance
  in `PIN_REFACTOR_REVIEW.md`. The current snapshot still reads no fixtures to
  calculate expectations. The additional current Contexto profile pin is distinct
  from historical profile evidence.
- `tests/content_scenarios.py` searches at most 1,000 deterministic seeds using
  current public selection rules. It neither injects a target nor skips failure.
  Named-round journeys still create through the real API and verify the intended
  answer, useful guesses, repeat/resume and wins. Historical seed receipts remain
  untouched; the helper makes no cross-version seed-stability claim.

Independent focused execution:

```text
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -q -o addopts='' tests/test_v79_gem_feedback.py tests/test_v82_burta_feedback.py tests/test_v75_contexto_food.py tests/test_v80_clatite_target.py tests/test_v82_playable_content.py tests/test_v81_history.py
53 passed in 3.60s
```

The runtime correction receipt's baseline and current source hashes were checked
against Git and working files. Its 884-input comparison and omitted-form outcomes
remain the producing agent's bounded evidence; this reviewer did not independently
repeat that entire capture. No heavy suite, source/fixture modification, push or
deployment was performed by this reviewer.

## Browser reload assertion addendum

The original Perechi failure trace showed a recovery GET starting before reload
and completing after navigation began. The URL-only response waiter captured that
old response, then attempted to read its body after navigation. The actual new
document's GET subsequently returned the correct state. These observations came
from transient task traces; no preserved trace artifact or trace hash is claimed.

The narrow `frontend/e2e/lifecycle.spec.mjs` fix was reviewed on 2026-09-07 and is
accepted. `reloadState` installs its request waiter and navigation listener before
reload, accepts only a matching GET issued after main-frame navigation, and reads
that specific request's response body concurrently with reload. It checks the
response status and always removes the navigation listener. Both reload journeys
retain their complete state-equality and visible-progress/playability assertions.
No timeout or product behavior was relaxed.

This reviewer inspected the test-only diff without running a browser. The fresh
browser matrix and the orchestrator's unchanged-threshold timing retry are separate
verification evidence, not results independently reproduced in this addendum.
