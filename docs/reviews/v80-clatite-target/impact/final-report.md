Valid until: the V80 candidate, pack, rankings, derived catalog, or selector implementations change — then rerun this review.

# V80 Clătite independent selection and preservation review

## Verdict

Accept the bounded selection impact of promoting `ct_gastronomie_320`. This review found no cross-game or preservation blocker. It assesses deterministic selection, artifact preservation, public route privacy and scoring; it does not replace the separate factual/quality judgments or Romanian-player testing.

The final candidate contains 621 pack records: 613 approved and the same 8 pending holds. All 620 previous pack records are exact. Every previous ranking row keeps its game, status, familiarity, play-quality score, pilot score and eligibility. The new Clătite row scores 83, ranks 52, is eligible and has global selection weight 4. Exactly 158 old Contexto ordinal ranks move by +1. The only old global weight change is `ct_meme_net_064`, 4→3.

All 336 derived board rows and payloads are exact. Their artifact metadata changes only to bind the new pack and ranking hashes. The KG, mobile public contract, Lanț tombstones and Contexto impact reserve remain byte-exact.

The eligible Contexto gastronomie/ușor shelf grows from 8 to 9. Clătite enters at shelf rank 9 and effective filtered weight 1. Recomputed quintiles raise `ct_gastronomie_019` from 2→3 tickets and `ct_gastronomie_127` from 1→2; no existing shelf item loses tickets.

Across seeds 0–99 and September 1–30, 2026, repeated twice per artifact, all same-artifact sequences are exact. Alchimie, Conexiuni, Intrusul, Lanț and Perechi have zero changes across all 100 seeds and all 30 dailies. Contexto's pack-wide selector changes 65/100 seeded picks and 0/30 dailies. The gastronomie/ușor shelf changes 50/100 seeded picks and 3/30 dailies. Clătite is selected by pack-wide seeds 1 and 54, shelf seeds 20 and 46, and the shelf daily on September 18. These are deterministic ticket/rendezvous effects from the added eligible row and bounded weight changes.

Real Django route probes confirm shelf seeds 20 and 46 select the new private pack ID. Creation hides the answer. `Făină` is a non-winning distance-1/rank-2/Fierbinte guess and still hides the target; exact `Clătite` wins on attempt 2 with server score 940. V75 maintenance: seed 5 now selects `ct_gastronomie_300`, seed 6 still selects `ct_gastronomie_319`, and seed 19 is a replacement selector input for `ct_gastronomie_318`.

## Bound evidence

- `baseline.json` — exact raw pre-wave pack, rankings and derived records plus selections; SHA-256 `07232cc0228becbea98ce98b4c17969694b88fbaf274bad96ac56ad4d91382d5`.
- `candidate.json` — exact final candidate records plus selections; SHA-256 `d82edf7810bfd67b35eee2e0e01b196afa5c777e4d70eacaba6618b0a3de067c`.
- `comparison.json` — full row/rank/weight and selection delta; SHA-256 `0201c59c6aca80f95d1051f0625ce1c85a7ae26388d47923eb3696c5189d3ea0`.
- `public-api.json` — five creation probes and two full Clătite rounds; SHA-256 `7396adaa42bac50713ceb8ede14a43fbf43592d98eda04b6d429528a2fb6647b`.
- `baseline-tree/manifest.json` — reconstructable pre-wave artifacts at clean commit `9c208a96628b3d92910637fa634d4c998fe0e67d`; SHA-256 `475064cf0dd6bfaa100a4e41c348a824f69194c81858966ad1fbd88c2128ee57`.
- `final-receipt.json` is the compact fail-closed summary; it binds the full evidence and root's independent artifact delta; SHA-256 `7f06245d3e7348c892de07e9e8d68cb6bd50bbbbfb7b89e6b40de0febdd0fd19`.

The selector samples call production `GamesPack` and `DerivedCatalog` selection methods directly. Pack-wide scenarios intentionally apply no category, difficulty or account-history filters; Contexto also has the exact gastronomie/ușor filtered shelf. Derived seeded calls use `starter=False` and `balance_categories=False`. The two API rounds and three maintenance creations are separate route evidence. The 100 seeds and 30 dates are bounded release-impact samples, not an exhaustive distribution or enjoyment measure.

## Commands executed

From `/home/dobo/work/_worktrees/cat_de_roman_esti/content__v80-clatite-target`, the baseline capture ran before any mutation:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v80-clatite-target/impact/selection_impact.py capture --root /home/dobo/work/_worktrees/cat_de_roman_esti/content__v80-clatite-target --phase baseline --out /home/dobo/work/_temp/v80-clatite-target/impact/baseline.json
```

The final candidate, comparison, public route probe and receipt used:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v80-clatite-target/impact/selection_impact.py capture --root /home/dobo/work/_worktrees/cat_de_roman_esti/content__v80-clatite-target --phase final-promoted --out /home/dobo/work/_temp/v80-clatite-target/impact/candidate.json
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v80-clatite-target/impact/selection_impact.py compare --before /home/dobo/work/_temp/v80-clatite-target/impact/baseline.json --after /home/dobo/work/_temp/v80-clatite-target/impact/candidate.json --out /home/dobo/work/_temp/v80-clatite-target/impact/comparison.json
PYTHONPATH=. DJANGO_SETTINGS_MODULE=cat_de_roman_esti.web.settings /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v80-clatite-target/impact/public_api_probe.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v80-clatite-target/impact/build_final_receipt.py
```
