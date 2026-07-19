# V30 working scope — farm, wardrobe, and kitchen essentials

Status: implemented and gate-green in `feat/basic-words-v30`; intentionally uncommitted,
unmerged, unpushed, and undeployed.

## Landed baseline

V30 starts from Cat main `a2e9fd5` (`fixture-v29-extended-basic-words`): 2,216
nodes / 8,909 edges / 7,143 aliases / 180 puzzles. The curated pack remains 794
records at SHA-256 `2c7d2eb…023`. Exact critique is 33/33 clean; the full 222-pending
baseline report is SHA-256 `122e35c8…19a`.

## Implemented bounded wave

| Domain | First-class concepts |
|---|---|
| Farm animals | Vacă, Cal, Oaie, Capră, Iepure |
| Clothing | Pantaloni, Rochie, Fustă, Pantof, Șosetă, Geacă |
| Kitchen/table | Farfurie, Lingură, Furculiță, Oală, Tigaie, Cană, Castron |

All 18 canonical labels are unresolved. The exact catalog below contains 60
conservative aliases: 78 distinct normalized label/alias surfaces, with zero existing
or intra-wave collision.

```text
Vacă: vaci, vacile, vacii
Cal: calul, calului
Oaie: oaia, oile, oii
Capră: capre, caprele, caprei
Iepure: iepurele, iepuri, iepurii, iepurelui

Pantaloni: pantalon, pantalonul, pantalonii, pantalonilor
Rochie: rochia, rochii, rochiile, rochiei
Fustă: fuste, fustele, fustei
Pantof: pantoful, pantofi, pantofii, pantofului
Șosetă: șosete, șosetele, șosetei
Geacă: geci, gecile, gecii

Farfurie: farfuria, farfurii, farfuriile, farfuriei
Lingură: linguri, lingurile, lingurii
Furculiță: furculițe, furculițele, furculiței
Oală: oale, oalele, oalei
Tigaie: tigaia, tigăi, tigăile, tigăii
Cană: căni, cănile, cănii
Castron: castronul, castroane, castroanele, castronului
```

## Sense guardrails

- Do not add `cai` or `caii`: accent folding conflates them with `căi` and `căii`.
- Do not add bare `oi`: it is also a common auxiliary/interjection.
- Feminine definite forms such as `vaca`, `capra`, `fusta`, `geaca`, `lingura`, and
  `cana` normalize to their canonical labels and would be redundant claims.
- Animals do not absorb `vită`, `armăsar`, `miel`, `ied`, or `iepuraș`.
- Clothes do not absorb `blugi`, `încălțăminte`, `ciorap`, `jachetă`, or `ie`.
- Cookware does not absorb `vas`, `bol`, or `cratiță`. `Cană` becomes a separate node;
  V29 correctly refused to make it an alias of `Pahar`.
- Keep `Duș`, `Pod`, `Spate`, and `Umăr` outside this wave pending sense review.

## Edge and critique contract

- The final graph has 36 local links and 18 legacy-to-V30 bridges. Every new node has
  exactly two outgoing choices, at least four distinct non-distractor neighbors, and a
  responsive inbound target pool.
- All bridges enter one of three strongly connected local meshes; no V30 edge returns to
  the legacy graph. This makes the meshes one-way sinks and preserves old-to-old paths.
- Predicates and Romanian labels are explicit, never `related_to`; no legacy endpoint
  gains more than three new neighbors.
- The 207 old Contexto targets retain every score cell; all 201 Lanț and 98 Alchimie
  profiles are unchanged. Both critique reports remain byte-identical.
- Add no curated board and perform no promotion. Preserve both pack copies byte-for-byte.
- Preserve the 7,200-second sliding session TTL and 1,000-session cap.
- The final 33 bound dossiers are in `v30-review/dossiers`; the public mobile contract is
  synchronized and verified in its own worktree.

## Verification outcome

- Fixture: 2,234 nodes / 8,963 edges / 7,203 aliases / 180 puzzles; combined eligible
  beginner probes resolve 269/269.
- New targets: inbound reachability 2,221–2,223; responsive 1–5-hop band 161–1,632;
  outgoing degree exactly two.
- Pack: 794 records at SHA-256 `2c7d2eb…023`, unchanged and unpromoted. Exact critique
  remains 33/33 clean; full pending remains 222 checked / 147 flagged / 143 FAIL.
- Tests: focused 30, support contracts 46, full backend 369; Ruff, both validators,
  workflow syntax, and whitespace green. Mobile importer 4 and full verify 227/26 green.

## Next queue, not V30

Low-risk later candidates: Prosop, Săpun, Genunchi. Continue deferring Duș and Pod;
review Spate and Umăr as explicit multi-sense concepts before adding them.
