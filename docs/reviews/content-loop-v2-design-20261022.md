# V2 content loop design — all six games' boards (2026-10-22)

Valid until: the V2 procedure lands in CONTENT_LOOP.md — then treat as history.

Approved by Paul on 2026-10-22 with its defaults (section 9 recommendations), with landing B1 (four Lanț chains) first. The test-pin packet rule (decision 2) and the Go 1.27.3 fix (decision 13) are already in the stage-0 procedure ([ADR-0210](../adr/0210-curation-waves-and-staged-stock-landing.md)). Read-only design: three independent designs, a judge and a critic synthesis. Paths and line numbers refer to main d9c89887 and the stage-0 branch.


## 1. Summary

Boards become the product. Each V2 batch mines the current KG for playable boards in the thinnest category x difficulty cells of all six games, screens them mechanically, has a blind gameplay critic try to break them, then sends the survivors through the existing two-reviewer gate and the full landing cascade. Vocabulary is added only when a named board candidate needs it, and the 1,083 reviewed packages are consumed through ADR-0210 curation waves, at least one in every three landings. One batch at a time may be between freeze and landed; a batch that waits more than 7 days expires. Every landing pays one rail regeneration and one HTTP corpus whatever its game mix, so batches are multi-game (up to 24 boards) after a 4-board first landing that measures the cost. Every landing also produces a test-pin packet, because three live `_test.go` pins go red on any content change (verified below); the owner rules once on who writes those pins.

## 2. Lanes and per-game board specs

| Lane | Item | Writes | Install path | Review |
|---|---|---|---|---|
| B-pack (cx, ct, lt) | one pack record, `nodes: []`, `edges: []` | `games_pack.json` | PACK_ONLY two rounds, then cascade class P (§4) | factual + quality, dossier-bound |
| B-al | Alchimie pack book | pack | same, own review batch + `audit-projections` (ADR-0129) | same + `projection_audit_sha256` |
| B-quick (iq, pq) | authored quick board in `authored-v13.json` (next; v12 is highest in `go-backend/internal/contentrails/sources/`) | rail source | 4c-4e quick, then class P tail | rail reviews + native audit |
| V vocab-gap | the minimum nodes/edges a *named* rejected board needs; `board_ref` mandatory; becomes `integrate` if the lemma is in stock | KG | full 4a-4i | as curation wave |
| C curation | ADR-0210 stage (consolidated module from the 1,083 stock) | KG | full 4a-4i | fresh dual review, reviewer-chosen sources |

Out of V2 scope until a new decision: widening the 123-source derived freeze (`contentops/derive.go:13-15`), new discovery-world concepts (252/256, `alchimie_explore/service.go:18`), repairing the 83 FAIL-lint Conexiuni boards.

| Game | Mine from | Mechanical floor | Blind critic check |
|---|---|---|---|
| Conexiuni | 4 typed hubs (`is_a` 81 with >=4 same-type children, `part_of` 45, `located_in` 25, `associated_with` 22) | `validate-pack`; `critique --strict` FAIL-clean (tile_fairness, red_herring_budget, duplicate_groups vs 488 tombstone groups, board_reskin, member_overuse >8); cross-links usor 0-1, normal/greu 1-3 | solves 16 shuffled tiles without labels; fail on a different or second valid partition; writes "each tile ___" per group; 3 of 4 recognizable |
| Cald | 1,087 non-target nodes with >=5 predecessors (515/356/165 by salience band) | reachable >=120, responsive >=40; `contexto_incoming_floor` FAIL; `salience_floor`; no new gastronomie targets (54/265) | 5 openers before seeing distances; >=1 within 2 hops; one dominant sense |
| Lanț | in-category pairs, normal 3-4 / greu 4-6 hops; usor is saturated (79 two-hop) | BFS optimal, >=2 first hops, layers >=2; caption on every optimal edge; >=50% typed edges on the route (proposed); tombstones 105 | plays from captions only; must explain each step; reaches target within par+2 |
| Alchimie | closure mining; greu first in the 7 empty greu categories | 5-7 seeds, exact par, >=2 openings; productive-pair cap ~40% (proposed); live `audit-projections` | plays audited openings; target inferable; no free pair |
| Intrusul | hub trio + sibling-hub intruder of the same type (ADR-0052 rules as authoring) | quick shape (`shape.go:58-80`); >=2 of 3 member links >=0.60; intruder has no link to members | picks the intruder blind and names the predicate; fail if any other tile is arguably odd under a natural predicate |
| Perechi | 4 edges >=0.60 | intended pairing is the unique max-weight perfect matching of the 105, margin >=0.15 (proposed); 24 cross-links <0.60; starter: 0 real cross-links | pairs 8 tiles blind; fail on a different pairing or an ambiguous tile |

Rubric gap: no section I (Intrusul) or J (Perechi) and `critique-games.js` maps only B-E. Doc sections need the owner; the JS mapping is a separate code task.

## 3. Loop state machine

- **M0 Baseline.** Worktree from `main` by SHA; LOOP step-0 gates; need map (eligible per cell, floor 4 per ADR-0063; today 164/252 cells short); rebuild `compat-index@<sha>.json` (deny/defer/collision/fuzzy/owner_hold plus board signatures: quads, Lanț pairs, Cald targets, Intrusul and Perechi sets). Red validate/export/ops check = BLOCKED.
- **M1 Mine.** Read-only miner from `_temp/content-loop/miner/`, 3 candidates per target slot, quota by deficient cell, 503-cells first (Perechi gastronomie and meme_net, the 10 empty Conexiuni cells). Max 2 mining ticks; shrink the batch rather than loop.
- **M2 Static screen.** Compat index, tombstones, holds, demotions, reserve. Cites `file:line`, never a count.
- **M3 Lint pre-screen.** `validate-pack` and `critique --strict` on a scratch pack copy. **Never an import dry run here**: `import-candidates` reads `verify_factual.json`/`verify_quality.json` first (`contentops/import.go:45-49`).
- **M4 Gameplay critic.** Blind solves per §2; one line per failure; its log goes into the frozen bundle. Pre-review filter, not a signer (decision 3).
- **M5 Freeze.** `candidates.json` per category, SHA recorded; refuses to freeze if any cited evidence capture is missing or hash-mismatched.
- **M6 Review round 1.** `factual-v2-NN` (web, adversarial) and `quality-v2-NN` judge the whole batch once, bound to the SHA.
- **M7 Stage and review round 2.** `import-candidates --pack-only --write`; `critique --dossier --write`; `audit-projections` for Alchimie; analyst + verifier on the dossiers; `build-review`; `apply-review --write` (`docs/PACK_ONLY_CONTENT_WAVES.md:16-38`). Quick boards: rail candidate, reviews, proposal, audit, finals.
- **M8 Land** (§4). **M9 Record:** count table, rejects to tombstones, retrospective <=10 lines, <=3 proposals.
- **Budgets.** Batch <=24 boards (first landing 4); <=24 ticks, <=20 commits; one sub-step per tick, burst <=4; research caps unchanged (12 items/tick, 300 s/item, >=2 s dictionary spacing, phases serialized); fails-twice = `waiting`.
- **Roles.** Author (never reviews), factual verifier, quality analyst, gameplay critic, landing reviewer; all distinct, fixed names per batch; critic and factual verifier on different ladder tiers.
- **Independence, mechanical.** Reviewers get only the frozen bundle (candidate, dossiers, critic log, audit). Author sources sealed (hashed) until both sign; each judged item cites >=1 URL outside the author's set (set difference over normalized URLs). Separate directories; both `signed_at` must exist before either reads the other; build-review checks the ordering. A review with >20% identical rationale strings is rejected. A reviewer name in any M1-M5 artifact voids that review.

## 4. Landing cadence and gates

- **Land or expire** replaces `unlanded-pool` (POLICY:5). One batch at a time between M5 and landed; no M1 for N+1 until N lands or expires; expiry after 7 days waiting or when a main KG change invalidates dossier bindings. Expired candidates return to the pool and need fresh M3-M6.
- **Honest cascade per class.** There is no light path. `cat-content export` runs `validateQuick` (`contentbuild/build.go:125` -> `catalogs.go:466-472`), which requires `quick_games_v92.json` bindings to equal the live `games_pack.json`, `kg_sample.json` and `derived_catalog_v38.json` digests; the extensions rail binds pack and KG too (`contentrails/extensions.go:44-52`). I recomputed: quick and extensions `bindings.pack` = `e24eb362…` = live pack sha. So:
  - **Class P (pack, quick):** 4b `rank --write`, `derive --write` (payload stays 336); 4c copy `authored-v12` -> `authored-v13`; 4d-4e quick and extensions with `inherited: true` where untouched, re-signed finals; 4f pins + export; 4g corpus; 4h authorities for quick and extensions; 4i gates + each new board played once over HTTP. World rail inherited (binds KG only, `world.go:164`).
  - **Class G (V, C):** full 4a-4i.
  - Never KG and boards in one landing; Alchimie is its own review batch inside a landing.
- **Test-pin packet (every landing, both classes).** Verified live at `d9c89887`: `go test ./internal/httpgolden -run 'TestV113|TestV112' -count=1` is green (5.8 s), and `v113_selection_test.go:59-61` asserts the live bundle's source tuple equals V1.13's; `contentops/check_test.go:133` pins 716 boards and `contentops_test.go:614` pins 709 approved, both over `repoRoot(t)`. Every landing therefore emits one packet: new `vNNN_selection_test.go` + predecessor "did not move past" edit, the 716/709 bumps, and for class G the Cald inbound-map diffs (`contexto/content_v1_3_test.go`, 2,556 entries). Needs an amendment of LOOP:233 ("never new or edited `_test.go`"); see decision 2.
- **HTTP corpus.** Record the count actually captured. The Stage-0 branch already rewrites LOOP:195 to "the case count of the previous reviewed corpus block, 1206 since V1.13; any other count is NEEDS-OWNER" — V2 adopts it verbatim and attaches the case-list diff. Never BLOCKED, never edited to fit; capture stays independent (`httpgolden/testdata/README.md`).
- **Landing review + owner GO** before `merge --ff-only`; push per ADR-0014.

## 5. How the 1,083 packages flow in

- **Integration lane = ADR-0210 curation waves**, as already specified on the Stage-0 branch (CONTENT_LOOP.md "Curation wave" section: >=20 items from final module payloads, re-screened against current main, consolidated module, one dual review, steps 4-5 unchanged). V2 adds only ordering and demand rules:
  - **Debt service:** while stock > 0, at least 1 of every 3 landings is a curation wave.
  - **Board-yield ordering** within a stage: a `_temp` simulation merges each family/concept into an in-memory fixture copy and re-runs the miner; items that unlock boards (a Cald target crossing 5 *main-served* predecessors, today 3/852; a Perechi edge in an empty cell; a Lanț normal/greu route) go first. Items unlocking nothing after Stage 3 are parked `vocabulary-only`.
  - **`vocab-gap` becomes `integrate`** whenever the lemma is already in stock; no new V1-style research while matching stock exists.
  - **After every class-G landing** the queued board candidates are re-screened (Lanț optimal and Alchimie par re-derive).
  - Tier order and rulings are ADR-0210's (V1.38-42 first; V1.33 only after re-sourcing; V1.14 re-applied never merged; bare `sucitoare` stays excluded; Ie never gets `ii`/`iei`).

## 6. Automation and owner touchpoints

- Heartbeat stays paused until approval, then rebinds as `cat-content-v2`: one sub-step per tick, burst <=4, silent on unchanged waits, elapsed time never approves (POLICY:29-32), reread LOOP when `procedure_rev` differs.
- `state.json` pointers only (<=2 KB); decisions in an append-only `decisions.jsonl` beside it.
- Evidence under `~/work/_temp/content-loop/evidence/<landing>/` with SHA manifest, copied to the NAS SHA-verified before any cleanup; never `/tmp`.
- Owner touchpoints: approve V2 once; per landing a go/drop table (<=24 rows) after M6, the test-pin packet, the corpus NEEDS-OWNER if any, landing GO; A5 adult/alcohol items; monthly cell-target review.

## 7. CONTENT_LOOP.md: changes vs stays (relative to the Stage-0 branch text)

Already done on `docs/content-loop-stage0` (do not re-decide): "today 12" (so v13 next), step-1 greps of `tests/` and `docs/reviews/*/graph-candidates.json`, evidence under `_temp`, reviewers blind to drafts and each other, reviewer-chosen source per item, 4g count rule, the Curation wave section. Still stale there: POLICY:30 "go1.27.1" (host is go1.27.3).

| Section | Change |
|---|---|
| Scope `:6-10`, `:275-277`, `:332-334` | boards/targets for all six games are the product; "rounds path untested" removed |
| `:25-33` fence | add: landing emits a test-pin packet; owner-approved pin edits are allowed in a named "pins" commit (amends `:233`) |
| Step 1 `:114-127` | becomes M0 need map + M1 mining + M2 compat index with board signatures |
| Step 2 | authoring from existing KG; vocabulary only as `vocab-gap` with `board_ref` |
| Step 3 `:137-148` | adds gameplay critic, sealed author sources, set-difference URL check, 20% rationale rule, name-in-artifact voiding |
| Wave size `:82-97` | 40-60 floor retired for board batches; cap 24, first landing 4 |
| Step 4 | class P vs G cascade named; 4a conditional; 4d-4e `inherited: true` rules |
| 4i | HTTP playthrough per new board; fuzzy-neighbour probe + Cald guess per new alias |
| Landing mode | `unlanded-pool` -> land-or-expire, one batch, 7 days |
| Backlog `:309-336`, heartbeat `:338+` | need map replaces themes; prompt rewritten |

Stays: authority (ADR-0188 + ADR-0210), BLOCKED/NEEDS-OWNER semantics, 4b-4i command text, quality bar `:285-307`, hash-bound chain, fixed-name reviewers, dictionary spacing, holds never leaking, tick/commit discipline, improvement loop `:263-283`, Python suite not a gate.

## 8. First three V2 landings

1. **B1, class P, 4 Lanț boards** in empty normal/greu cells (gastronomie normal, limba normal, personalitati normal, societate greu), pack-only. Purpose: measure the real cascade (4c-4h quick+extensions regeneration, corpus capture time, resulting case count) and produce the first test-pin packet. Expected: 4 cells 0 -> 1, no cell crosses 4, 0 KG change, Cald pins green, `v113_selection_test` + 716/709 pins in the packet.
2. **C1 = ADR-0210 Stage 1**, class G: >=20 alias-only families from V1.38-V1.42 as one module, full 4a-4i, Cald inbound-map packet. Expected: first stock consumption (>=20 families), authored-v14, re-screen of B2's queue.
3. **B2, class P, up to 20 boards, multi-game:** 8 Perechi quick boards (gastronomie 4, meme_net 4, usor/normal: the two 503 categories), 8 Conexiuni in empty cells (arta_cultura u/g, societate u/g, sport u/n, film_tv u, geografie n), 4 Cald greu (literatura greu is empty; personalitati). Expected: Perechi 503s closed, 8 Conexiuni cells 0 -> 1, Cald literatura greu 0 -> 4 and preferred shelf +8.

## 9. Open owner decisions

1. **Approve V2 base** (graph-mining + grafts) and land-or-expire replacing `unlanded-pool`. Rec: yes.
2. **Who writes test pins** (`vNNN_selection_test.go`, 716/709 bumps, Cald maps). Rec: the landing agent writes them in a separate "pins" commit; the owner approves the packet; LOOP:233 amended to say so. Without this every landing is NEEDS-OWNER forever.
3. **Gameplay critic status.** Rec: pre-review filter whose log is in the frozen bundle; keep the ADR-0104 two-signature pair unchanged.
4. **Rubric sections I/J** and `critique-games.js` mapping. Rec: approve the doc sections with V2; the JS mapping is a separate code task; until then quick boards use §2 checks in the brief.
5. **Proposed numbers** (Perechi margin 0.15, Alchimie pair cap 40%, Lanț typed-edge >=50%, Conexiuni cross-link bands, Cald gastronomie freeze). Rec: WARN level for the first three landings, ratify after.
6. **Caps:** batch 24 / first 4, 7-day expiry, 1-in-3 debt ratio. Rec: adopt.
7. **Miner home.** Rec: `_temp/content-loop/miner/` read-only script now; port to `cat-content-ops mine` after B2 as a code task.
8. **Evidence home.** Rec: `_temp/content-loop/evidence/` registered as exempt from the ADR-0028 4-day sweep, NAS copy mandatory before any delete.
9. **Order B1 before C1.** Rec: B1 first (4 boards de-risk F1/F2 for the larger Stage 1).
10. **Derived-catalog freeze** (ADR-0067). Rec: keep frozen; revisit after Conexiuni eligible stock exceeds 150.
11. **Heartbeat.** Rec: rebind as `cat-content-v2` after approval, same burst rule.
12. **Per-game acceptance rule** (POLICY:26 open item). Rec: adopt §2 floors + critic checks as the rule.
13. **POLICY:30 go1.27.1 -> go1.27.3.** Rec: fix in the Stage-0 branch before it lands.

## Coverage and uncertainty

- **Executed:** `go test ./internal/httpgolden -run 'TestV113|TestV112' -count=1` on main (green, 5.8 s): the F2 pin is live. `python3 -I` recomputed quick and extensions `bindings.pack` = live `games_pack.json` sha (`e24eb362…`) and quick `kg_sha256` = live KG sha: F1 is real. Read-only git on the Stage-0 worktree (another session committed `54f590fb` during my run; I touched nothing).
- **Read and cited:** `golden.go:268-300`, `v113_selection_test.go:55-65`, `catalogs.go:462-476`, `build.go:120-130`, `extensions.go:40-56`, `world.go:160-168`, `check_test.go:91-136`, `contentops_test.go:15-22,600-616`, `import.go:40-62`, `derive.go:10-16`, `shape.go:57-60`, `alchimie_explore/service.go:17-19`, `CONTENT_LOOP.md:30-34,44-46,193-198,230-236`, `PACK_ONLY_CONTENT_WAVES.md:14-40,86-95`, REV §5, POLICY:4-6,26-32, ADR-0210 and the Stage-0 LOOP diff.
- **Taken from the judge, not re-derived:** deficit table, KG headroom counts, the 7 pending IDs, empty-cell lists.
- **Not run:** no Cat tool, no export after a simulated pack change (F1 is inferred from exact-digest comparison in `validateQuick`, high confidence), no corpus capture timing. Whether `rail extensions --check` fails before or after export only changes ordering.
- **Routing:** the critic was needed: the Stage-0 branch finding changes §5, §7 and §9, and none of the three designs or the judge saw it.