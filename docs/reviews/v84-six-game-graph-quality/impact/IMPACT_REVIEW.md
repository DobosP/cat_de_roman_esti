# V84 graph impact review

Valid until: the bound graph or runtime scoring/projection code changes — then treat as history.

Reviewed against shared main `83538809d4913c4b22f36cf92c4f1502f50f83f3` in independent
Python processes. The same 15 proposed labels plus Biscuit/Măr were first-guess API probes
against all 221 old approved Contexto records: 3,757 observations per checkout. The probe
does not mutate content, promote candidates or relax validators. Later pack-only additions
are outside this snapshot's inventory counts and do not alter its old-target observations.

## Retained game behavior

- All 82 old Alchimie recipe projections remain byte-equivalent after canonical serialization:
  recipes, routes, par and opening counts are unchanged. Every target remains reachable,
  every payload validates, and route/pair/concept/result/par bounds pass.
- All 97 Lanț payloads, exact distances and branch profiles are unchanged and valid.
- All 232 Conexiuni records remain exact and its 74 eligible boards are retained.
- All 183 Intrusul and 153 Perechi frozen boards, including metadata, remain exact.
  Preferred pools remain 144 and 113; starter pools remain 24 and 26.
- All 217 old runtime-eligible Contexto records remain eligible. All 221 approved targets
  still satisfy target validation. All 17 audited inputs are accepted with their native IDs
  on every old approved target, with zero accidental wins.
- All 67 directions allowed by the 57 newly authored edges win a one-hop Lanț API journey.
  None was a valid direct move before; 64 referenced at least one not-yet-existing concept.

## Meaningful feedback gains

- Drojdie now resolves to its own native concept. Its old Mâncare projection is retired.
  Only Drojdie overlapped projection vocabulary among all 15 new labels and 42 forms.
  Biscuit/Măr already had native identities and no legacy feedback proxies to retire.
- In the old approved target set, Drojdie's hot results are now Cozonac and Gogoși.
  Its former hot Sarmale, Mici, Ciorbă de burtă, Urdă, Friptură and Ardei umpluți results
  are no longer hot. Sarmale changes from rank 8/distance 1 to rank 246/distance 3, Rece.
- Actual API checks also show Biscuit→Salam de biscuiți and Măr→Plăcintă cu mere at
  rank 3/distance 1; Zer→Urdă rank 4/distance 1; Saramură→Telemea rank 5/distance 1.
  These guesses stay nonwinning and retain the submitted concept identity. The biscuit
  and apple targets are not in the old 221 approved records, so their separate exact-target
  probes are recorded in `core-associations.json` rather than counted as old-round coverage.
- The new hot associations within old rounds are culinary relationships: whey/urdă,
  brine/pickles or telemea, dough/cornulețe or gogoși, oven or baking tray/cozonac or
  cornulețe, mălai/mămăligă and food rennet/telemea.

## Scope of numeric movement and remaining limits

The graph expansion intentionally changes 3,712 of 3,757 compact observations; 45 are exact.
This is largely the addition of native acceptance for 14 previously unknown concepts and the
retirement of the one broad Drojdie identity, not thousands of individually reviewed repairs.
The graph also changes Biscuit on 197 old targets (38 hop-distance and 31 temperature changes)
and Măr on 200 (35 hop-distance and 18 temperature changes); neither creates a hot old target.
Both retain input identity on every record. Rank changes alone are not quality improvements.

Drojdie→Telemea remains vaguely warm (Caldut, rank 203, distance 3), illustrating that broader
graph ranking still has noise. These checks establish playability, boundaries and specific
feedback gains; they are not player enjoyment testing or a claim of perfect semantics.

## Reproduction

Run `capture.py.txt` separately with `--root` set to the stable baseline and candidate checkouts,
`--inputs inputs.json`, `--baseline-pack baseline-pack.json`, and distinct `--out` paths.
Use the repository's Python 3.12 web interpreter. `compare.py.txt baseline.json candidate.json
comparison.json` produces the complete changes plus a compact stdout summary. Every capture
binds the graph, pack, ranking, derived catalog and relevant runtime source hashes.

Archived evidence: `summary.json`, `quality-summary.json`, `core-associations.json` and
`capture-receipt.json`. The receipt binds the full raw captures and successful logs; duplicate
raw dumps remain in task scratch and can be reproduced from the retained scripts and Git baseline.
