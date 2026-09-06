Valid until: the Contexto projection policy, Contexto guess route, KG, games pack, rankings, or derived catalog changes — then rerun this review.

# V79 independent Gem feedback impact review

## Verdict

Accept the bounded candidate bound to `contexto_projection.py` SHA-256 `d6b80f7cb7abcce77c64d04d94ff2cf7e178ffd6bb1d48cbd7b4a9e441fd9cb1` and `contexto.py` SHA-256 `bdef59b96dd7f3b06321b20463987e7d4140625e60b07bc043383cd3caf3282f`.

The real Django endpoint sweep covers all 207 approved Contexto targets, including all 203 eligible rows. Exactly one response changes: eligible `ct_gastronomie_128` Papanași moves from distance 5/rank 1291/Foarte rece/44 to distance 1/rank 13/Fierbinte/99. The authored directed Dulceață→Papanași edge is strength 0.70 and says `se toarnă peste papanași`, so this is a specific, useful correction. The other 206 target responses remain exact, and no cross-category target becomes newly hot.

All 473 public projection mappings remain byte-for-byte equivalent as structured rows. Gem keeps its Miere default anchor, public ID `ctxp_fab0f46e7bcd5932442e`, rank penalty 1, non-winning behavior, and hidden private target. Both accepted guesses and typo-suggestion filtering use the same effective-anchor helper. Exact Dulceață, Miere, and target guesses still win under their KG IDs.

The helper selects Dulceață for exactly 6 of 2,364 known target nodes: Dulceață itself plus the five directed, non-distractor neighbors at or above the 0.60 threshold: Papanași 0.70, Magiun de Topoloveni 0.60, Conserve de iarnă 0.80, Clătite 0.70, and Fruct 0.85. Every other known node uses Miere. Socată's only direct Dulceață edge is the weak 0.45 `preparate de casă sezoniere` relation, so it correctly remains on Miere at distance 4/rank 663/Rece/71. The helper honors graph direction, ignores distractors through `WordGameService.link`'s default view, and falls back when the neighborhood anchor is unavailable.

The KG, games pack, rankings, and derived catalog hashes are unchanged. This wave changes only Gem feedback. It does not promote Clătite or Cozonac, change Nucă or Alună, or conflate Gem with exact Dulceață.

## Baseline proof

The pre-edit baseline is `baseline.json` SHA-256 `79ca578f1380264d8d6b82dad07c06bf24fdccbbbd5af6fb00354d3654150c0f`. A fresh capture through the final route with only `_projection_anchor_id` forced to return each term's existing default anchor produced `baseline-bounded-replay.json` SHA-256 `d5fda11a6a0e8a0ba6611bb847cbb1dc9268075bd04d0313985c0524c9af0b70`. Its 207 endpoint rows exactly match the original baseline. Its three shared fixed controls—Miere, Dulceață, and Clătite—also match exactly. The replay adds five later audit controls and neighborhood metadata, which are excluded from this equality claim.

The final receipt is `final-receipt.json` SHA-256 `8f8c53dbbaf6590fe05cf04098f40118cb1be487ea631d1a6e2be85b1cc29144`. The bounded candidate and comparison are `bounded-candidate.json` SHA-256 `1eed3edf4480a1102b5cc72b156b4bfda248c701402bd9fbfdecbec1057d8d40` and `bounded-comparison.json` SHA-256 `154f491d7ad625665b7ec07ee6e278d527680f56c8c23e63688b50510b9aa1f8`.

The rejected global-anchor evidence remains separately preserved. It changed feedback for all 207 targets and made 13 eligible gastronomie targets newly warm, including misleading Cald feedback for Grătarul de 1 Mai and Murături. A distance-only direct-neighbor rule was also rejected because it would include Socată's weak 0.45 relation.

## Reproduction

Run from `/home/dobo/work/_worktrees/cat_de_roman_esti/fix__v79-gem-feedback` with the intended candidate source present:

```bash
PYTHONPATH=. DJANGO_SETTINGS_MODULE=cat_de_roman_esti.web.settings /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v79-gem-feedback/impact/gem_feedback_impact.py capture --phase baseline-replay --force-default-anchor --out /home/dobo/work/_temp/v79-gem-feedback/impact/baseline-bounded-replay.json
PYTHONPATH=. DJANGO_SETTINGS_MODULE=cat_de_roman_esti.web.settings /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v79-gem-feedback/impact/gem_feedback_impact.py capture --phase bounded-candidate --out /home/dobo/work/_temp/v79-gem-feedback/impact/bounded-candidate.json
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v79-gem-feedback/impact/gem_feedback_impact.py compare --before /home/dobo/work/_temp/v79-gem-feedback/impact/baseline-bounded-replay.json --after /home/dobo/work/_temp/v79-gem-feedback/impact/bounded-candidate.json --out /home/dobo/work/_temp/v79-gem-feedback/impact/bounded-comparison.json
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/v79-gem-feedback/impact/build_final_receipt.py
sha256sum /home/dobo/work/_temp/v79-gem-feedback/impact/{baseline.json,baseline-bounded-replay.json,bounded-candidate.json,bounded-comparison.json,final-receipt.json}
```

`build_final_receipt.py` fails if the forced-default replay's 207 rows or the original three fixed controls differ from the pre-edit baseline, if the candidate policy shape differs, if any sweep secret leaks, or if a bound content artifact changes.
