# Content-loop read-only review (2026-10-22)

Valid until: the stage-1 curation wave lands — then treat as history.

Independent Claude Code review of the V1.8–V1.42 content loop, five dimensions with refutation passes and a final adjudication. No source module was run, no content was installed and no web request was made. Paths are on the reviewing host.

Post-review note: Paul approved and landed `d9c89887` (CONTENT_LOOP on go1.27.3) on 2026-10-22, closing the TOOL-1 approval question; his stage decisions are recorded in [ADR-0210](../adr/0210-curation-waves-and-staged-stock-landing.md).


## 1. Verdict on the source work

**YES, with exceptions.** The accepted stock (1,083 packages, 29 unlanded waves V1.14–V1.42) is trustworthy *as reviewed source*: every hash, ref, pool→module binding and headline count reproduces; no held/rejected item leaks into any payload; no accepted item was shown to be factually wrong. The exceptions are evidence-tier, not content:

| Tier | Waves | Why |
|---|---|---|
| Full-strength (bounded briefs, retained evidence, dual fresh review) | V1.38–V1.42 | `context_policy` first appears in v1-38 pool; captures retained and hash-verified |
| Reviewer pre-exposed (reviewers audited author drafts before signing) | V1.17–V1.37 | reviewer-named `*-audit.json` files in `_temp/content__v1-*/` (V1.35–37 under `step1/`, `research*/`) |
| Single verifiable fresh review | V1.14, V1.15, V1.21 | V1.14 quality used cached records ("no new DEX request"); V1.15 quality has no request ledger; V1.21 pruned bodies |
| Evidence not retained | V1.33 | all 275 cited bodies lived in `/tmp/v133-research` (gone since reboot 2026-10-20 21:15); 0 html in `_temp`; 361 `/tmp` references in `source-provenance.json` |

Nothing is installed; `application_allowed=false`; player-visible delta 0/0/0. Confirmed.

## 2. Confirmed findings

### Source-correctness / review integrity

| id | sev | path | evidence | recommendation |
|---|---|---|---|---|
| EW-01 | high | `/home/dobo/work/_worktrees/cat_de_roman_esti/content__v1-33-familiar-celebration-and-traditional-objects/docs/reviews/v1-33-familiar-celebration-and-traditional-objects/source-provenance.json` | `ls /tmp/v133-research` → No such file; README:50 "No historical raw artifact tree was pruned." is misleading | Mark V1.33 (30 items/170 keys/114 claims) "raw evidence not retained"; fresh verification before any qualification; never cite `/tmp` again |
| CI-1 | medium | `/home/dobo/work/cat_de_roman_esti/tests/test_v84_graph_and_games.py:68` | `"sucitoare"` in EXCLUDED (V84 review: "avoids the bird noun"); v142-sucitor has `prior_hold_decisions=[]`; CONTENT_LOOP step 1 forbids reading pre-V1.8 reviews, which hid it | Owner rules: keep V84 exclusion (qualify 20 keys) or explicitly override + NEEDS-OWNER test change. Add `tests/` + `docs/reviews/*/graph-candidates.json` exclusion greps to step-1 screen |
| EW-02 | medium | `.../content__v1-34-familiar-service-and-journey-objects/docs/reviews/.../caption-wording-amendment.json` | factual amendment (18:28:48Z) adopts quality's exact wording 67 s before quality signed (18:29:55Z); contradicts policy line 21 | Keep v134-trecere-de-pietoni (final = quality's signed text) but mark amendment non-independent; never reuse the reviewer-to-reviewer channel |
| EW-03 | medium | `/home/dobo/work/_temp/content__v1-33-.../research-tick2-factual-audit.json` et al. | pre-review audits by the named reviewers exist V1.17–**V1.37** (verifier widened from V1.34) | Record independence tier per wave in canonical stock (table above) |
| EW-04 | medium | `.../content__v1-14-animals-and-habitats/docs/reviews/.../graph-quality-review.json` | "cached ... no new DEX request was made"; V1.15 quality: 0 `requested_at`; V1.21 `raw_body_tree_pruned_after_verification: true` | Annotate as single verifiable fresh review; fresh verification at qualification |
| V142-05 | low | `.../content__v1-42-.../scripts/familiar_food_materials_and_selected_inputs_v1_42_data.py` | Șerbet `is_a` Desert; only source is DEX "preparat ... din sirop de zahăr" (no dessert-course claim) | Consider `related_to` at curation; module frozen now |
| BS-3/V142-04 | low | `.../content__v1-42-.../review/second-source-role-binding-correction.json` | `before_sha256 afb575f2…`/`after_sha256 54e580bd…` match no retained file; builder is `732b39da…` | Name the artifact and retain before/after bytes; signed verdicts unaffected |
| V142-02 | low | `.../content__v1-42-.../review/factual/fetch_item.py` = `quality/fetch_item.py` (sha `569884e8…`) | both reviewers re-fetched the author's URL list; bytes fresh, selection not | Handover wording: "fresh re-captures of author-navigated sources"; V2: ≥1 reviewer-chosen source per item |
| EW-06 | low | V1.33 factual review | 30/30 items share one rationale string; V1.29 42/44, V1.21 32/46 | Tier as lower-evidence; per-item rationale tied to capture ids |

### Integration / landing readiness

| id | sev | path | evidence | recommendation |
|---|---|---|---|---|
| **TOOL-1** (merges BS-1, BS-2, V142-01, SC-8, EW-12, CI-6) | high | `/home/dobo/work/cat_de_roman_esti/docs/CONTENT_LOOP.md`, `/home/dobo/work/_temp/content-loop/state.json`, `/home/dobo/work/_temp/content-loop/owner-source-policy.md:30` | main = origin/main = **d9c89887** (not e531358c as the brief says); its body says "Draft for owner approval; not landed." yet it is pushed; host `go version` = go1.27.3; CONTENT_LOOP:38/96/372 now pin go1.27.3; policy line 30 still "go1.27.1"; state.json `procedure_rev 17b97a2b`, `secondary_main e531358c`, `primary_feature feat/gui-cat-m3` (fb829aaa, fully merged ancestor, 16 behind) | Owner: (a) confirm d9c89887 is approved, (b) amend policy line 30, (c) rebind primary → main d9c89887 in state/current-stock/policy, (d) treat all 8 baseline PASS lanes as historical, (e) only then ADR-0037-clean feat/gui-cat-m3 |
| CI-2 | high | `/home/dobo/work/cat_de_roman_esti/go-backend/internal/httpgolden/golden.go:141-163` + `docs/CONTENT_LOOP.md:195` | all reviewed corpora require 1207 except V1.13 (1206); 4g says "expect 1207"; V1.14 exception declined | Owner edits 4g (1206 or per-wave count) before *any* install; every scope hits this gate |
| SC-3 | medium | `/home/dobo/work/cat_de_roman_esti/scripts/{contexto_common_words_v44,basic_words_v30,basic_words_v33,basic_words_v32}_data.py` | spot-checked: `"sofa"` v44:39 + collision pair :50; `"bol"` v30:250; `"iepuraș"` v30:243; `"lavoar"` v33:283; `"covoraș de baie"` v33:300 **and** DEFERRED_V33_CONCEPTS :334 while canonical says `deferred_current=False` | 10 families / 62 keys need explicit owner decision against the recorded rejections; add a static main-side compatibility layer (BLOCKED/COLLISION/FUZZY_DENY/DEFERRED) to canonical stock |
| BS-4 | medium | `/home/dobo/work/cat_de_roman_esti` | 29 `content/v1-*` + consolidation branch have no upstream, exist only on this host | `ops publish` or SHA-verified NAS bundle before anything else |
| CI-4 | medium | `selections/v1-43-curation-first.json` | slice = 5 families < min 10/20; spans modules e4c011e5 (V1.41) + 931799a3 (V1.42) | Owner names module strategy (per-wave drop vs new module + fresh step-3) or folds into a ≥20-family batch |
| CI-9 | medium | `go-backend/internal/contexto/content_v1_3_test.go` | 2,556-entry pinned inbound map; +855 nodes (+33%), +3,426 edges (+34%), +5,737 keys | Full landing = multi-wave program with per-wave NEEDS-OWNER expectation changes |
| EW-05 | medium (gameplay) | V1.33 `reviewed-module.py:63` | Ie aliases `['iei','ii',…]`; `î→i` folding makes pronoun `îi` / verb `iei` resolve to Ie; frequency hit was `îi` rank 131 | Judge as homograph keys at qualification; note misattributed frequency |
| EW-07 | low | `.../content__v1-14-animals-and-habitats` | branch carries applied `bundled.json`/pins from a base 187 behind main | Never merge the branch; re-apply the 54 items via cascade |
| CI-5 | low (gameplay) | `go-backend/internal/graph/service.go:384-426` | adding `sucitoarele` drops fuzzy `scriitoarele→Scriitor` (gap .0395 ≤ .06) | 4i playthrough must include fuzzy-neighbour probes |
| CI-3 | low | `continuations/v1-41.json`, `v1-42.json` | Mănăstire (2 recipe boards) and Sucitor (`discovery_world`) force snapshot rebuilds | Annotate per-family snapshot deps in the slice |
| CI-8 | low | `httpgolden/testdata/python-http-parity-v1-13.json.gz` | corpus has no typed free text; corpus churn ≠ alias behaviour | Treat 4i logs as the evidence for alias scopes |
| SC-7 | low | `current-stock.json` continuation | two first-slice proposals coexist (21-key and 19-key) | Mark `small_existing_owner_candidate_scope` superseded |
| BS-5/BS-6 | low | `current-stock.json`, `state.json` | `observed_at_utc` predates 4 in-place edits; state.json 2036 B of 2048 cap | last-amended ref; compact `owner_decisions` before next write |

## 3. Count reconciliation

**Confirmed (reproduced from canonical layers and static AST of module literals, by ≥2 reviewers):** 1,741 records = 218 integrated + 1,083 accepted + 439 held + 1 rejected; 855 new concepts + 228 families (201 owners); 370 pending holds + 69 historical; 5,737 unique keys = 5,737 owner-key pairs = 4,807 + 930 = 5,734 ordinary + 3 display-only; 3,426 directed claims (3,417 unordered); predecessor distribution {0:386,1:36,2:25,3:168,4:195,5:32,6:13} → 810/45; 117 Cald projection hits; 49 snapshot-dependent families; lanes 88/164 and 140/766; 0 collisions with main's 14,685-key resolver (bundle `bbdf1f31` identical on fb829aaa, e531358c, d9c89887); V1.42 35 accepted (14+21) / 5 held, 153 keys (72+81), 56 edges; slice 21 keys (4+5+5+4+3); 29 unlanded waves; 2,584 nodes / 10,141 edges on main.

**Corrected / qualified:**
- 5,734 "reviewed dictionary inputs" → **4,968 single-token + 766 multiword** (6 classified component-composed, 760 unclassified).
- 45 numeric incoming-floor passes → **45/810 only if whole waves co-land; 3/852 counting main-served predecessors only**.
- 370 pending holds → **≥10 are overlap holds whose lemma is accepted elsewhere**; 439 total includes 20 later superseded (3 accepted in V1.15, 17 integrated V1.9–13). Record counts, not concepts.
- "21 ordinary morphology families" in V1.42 → 6 in the morphology lane + 15 selected-sense lane; 4 same-lemma families (Rude, Interfon, Chiftele, Vecini) sit in the selected-sense lane. Interfon (slice member) is one.
- Snapshot-dependent families: current-stock/selection say 49; older manifest and owner-handoff say **40** → use 49.
- secondary_main: brief and state say e531358c → **d9c89887**.
- Host Go: brief says go1.27.1 → **go1.27.3** (`/usr/local/go1.27.1` retained).
- Minor: V1.41 has 16 `n_v1_41_*` nodes (finding CI-4 said 15); "author's 146 URLs" is 161 entries/123 unique.

**Unverifiable:** V1.33 per-item claim support (EW-01); correction hashes `afb575f2…/54e580bd…`; attribution of pre-baseline commits ba7f62b0/fc65926e in the 14-commit counter; the 9,520 stored-forms figure; reviewer spawn/context records for V1.33–V1.37.

## 4. Landing readiness

**Must happen before anything lands (all owner-level):**
1. **Authority:** confirm d9c89887 ("Draft for owner approval; not landed" but on origin/main) is approved; amend `owner-source-policy.md:30` to go1.27.3 (new sha); rebind `state.json` (`procedure_rev`, `secondary_main`) and `current-stock.json` to main d9c89887; retire feat/gui-cat-m3 as primary and close the secondary-observation chain with a terminal note. ADR-0037 cleanup of feat/gui-cat-m3 only *after* rebinding.
2. **Preserve:** `ops publish` (or verified NAS bundle) for the 29 `content/v1-*` refs + `docs/content-consolidation-v1-8-to-v1-32`.
3. **Procedure edits (CONTENT_LOOP):** 4g expectation 1207→1206/per-wave; min-wave-size override path for curation slices; step-1 screen gains greps over `tests/` and `docs/reviews/*/graph-candidates.json` exclusions and a static main-side block/deferred/collision/fuzzy-deny layer; evidence retention under `~/work/_temp` only; "authored-v13 is next" (not "today 6").
4. **Rulings:** bare `sucitoare` vs V84; the 10 BLOCKED_ALIAS_FORMS families (62 keys); `ii`/`iei` for Ie.
5. **Stock annotations (canonical write):** independence tiers; V1.33 evidence-not-retained; 4968/766 and 3/852 figures; supersede the 19-key scope.
6. **Re-baseline:** step 0 on d9c89887 under go1.27.3; all current PASS lanes historical.

**Staged plan:**

| Stage | Scope | Churn | Risk |
|---|---|---|---|
| 0 Bookkeeping | items 1–5 above; no content | docs/state/policy only | low |
| 1 First slice | alias-only batch of **≥20 `existing_lemma_morphology` families from V1.38–V1.42** (best tier), excluding the 10 blocked families; include Avion/Cinematograf/Interfon; Mănăstire/Sucitor only if owner accepts snapshot rebuild + sucitoare ruling. One consolidated module with fresh step-3 dual review (the only way to keep review binding across modules) | full 3-rail cascade, authored-v13, new 1206 HTTP block, world/extensions regen; `test_v84` red if bare sucitoare included | medium — fuzzy shifts need 4i probes; otherwise small |
| 2 Families | remaining morphology lane (to 88/164), then selected-sense families (140/766) in ≥20-family batches; per-batch rulings on blocked families and the 49 snapshot deps | repeated cascades; projection_terms (117 Cald hits) touched here | medium-high |
| 3 Concepts | whole-wave co-landing (so 810/45 holds), 20–60 items per wave, V1.38–V1.42 first, V1.17–V1.37 next, V1.14/15/21 with fresh verification, V1.33 only after re-sourcing; V1.14 re-applied via cascade, never merged | Cald pinned maps (`content_v1_3_test.go`) red every wave → NEEDS-OWNER; Lanț routes, rankings, boards, Alchimie world regenerated; 3 display-only labels | high; effectively a multi-wave program |

## 5. Inputs for a V2 discovery loop (all boards)

**Keep:** hash-bound chain (pool → frozen module → signed reports → canonical stock) that reproduces end to end; two fixed-name reviewers signing before seeing each other (V1.38+ bounded briefs are the model); ≥2.1 s dictionary spacing with serialized phases; holds preserved and never leaked; canonical consolidation with per-wave continuations; graph-skeleton pre-selection (fixed the V1.34/V1.37 hold ratios); `application_allowed=false` as a hard fence; tick/commit budgets.

**Structural limits to design out:**
- *Source-only vocabulary*: it produces aliases, nodes and edges, never targets, rounds or boards; "45 numeric passes" is the only board-adjacent signal and it is unapproved. V2 must select against board/round needs (Alchimie boards, Cald projection terms, Lanț routes, discovery_world) and record each candidate's snapshot dependencies at selection time, not at integration.
- *Per-theme waves* on a fixed primary that was already merged: the primary/secondary model went stale on 2026-10-19 unnoticed. V2 binds to main by blob at each wave start.
- *No cross-module compatibility layer*: main-side BLOCKED/DEFERRED/collision lists are only asserted wave-locally, and step 1's pre-V1.8 review blindness hid V84's `sucitoare` exclusion. V2 builds one static main-side deny/defer index and screens every hypothesis against it.
- *Reviewer source selection = author's*: require ≥1 reviewer-chosen second source per item and full dexonline entry inspection.
- *Evidence in `/tmp`* lost a whole wave; V2 retains bodies under `_temp/<slug>/` and the canonical record stores the retention path.
- *Counts are record-level and lane axes are mixed*: V2 publishes concept-level and key-level figures, per-key before/after resolver outcome (exact/fuzzy/none), and fuzzy-neighbour shifts as a mechanical check.
- *Landing granularity*: minimum wave size vs small curation slices has no defined path; V2 defines the co-landing unit (module) up front so incoming-floor and review bindings survive partial landings.
- *State at the 2 KB cap* with owner decisions inline; move decisions to the protected handoff.

**Not checked by any dimension:** NAS copies of the refs or V1.33 bodies; reviewer spawn records V1.33–V1.37; fuzzy shifts across all 930/4,807 keys; V1.16–V1.20, V1.22–V1.32, V1.35 packets beyond mechanical checks; any Go/Python execution of Cat code; anything on origin beyond local remote-tracking refs.