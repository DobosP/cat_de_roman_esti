# Status — cat_de_roman_esti

Last verified: 2026-09-22 — V97 candidate verified locally on Linux; not yet landed.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- Local and remote main are V96 `fd3ca7c`; CI 35158602720 passed after the test-only
  interception correction. V97 remains in `feat/v97-discovery-continuity-and-new-words`.
- The September 22 owner request resumes testing and version work from current docs and
  the Windows handoff. The existing V97 candidate is preserved. No arcade-specific new
  skill page was found locally; the exact skill name/path remains a clarification.
- V97 adds five rounds/targets: one each for Conexiuni, Cald sau Rece, Lanț, Intrusul and
  Perechi. Fresh per-game exposures are nine Conexiuni words, four Intrusul and eight
  Perechi words, all using existing shared KG nodes.
- Ușă has seven native predecessors and useful home/bathroom/intercom/key openers.
  Lanț connects Cacao→Lapte through Înghețată or Chec. Conexiuni covers family roles,
  facial parts, filled recipes and electric variants; quick games add family/neighborhood
  discrimination and four reviewed everyday pairs.
- Alchimie adds Supă de roșii and Mâncare de spanac with two recipes each: **251 concepts,
  351 recipes,147 discoveries**. All 249 old concepts/347 recipes and eight starters,
  96 supplies, twelve tiers/32 goals remain exact. Both new results are terminal.
- Nine complete historical books are retained; the bounded compatibility list grows
  eight→sixteen with a pre-write 2 MiB guard, under ADR-0155. Nothing is evicted. The
  browser now uses the same 16-history limit: its old 8 limit broke the next write of a
  fresh ninth-book collection. Tests cover 9/16 updates, current catalog and 17 rejection.
- A failed start/replay now reveals its full persistent error once inside the existing
  scrollport without changing focus. This prevents an expiring outertoast notification
  from moving the error above the visible game. Mutations are never replayed.
- Twelve reviewed food captions clarify routes in three earlier Lanț rounds. All 101
  earlier captions remain exact; fourteen existing directions get text and ten nonexistent
  reverse directions remain unavailable. Optional recipe ingredients stay qualified.
- Decisions/evidence: ADR0155 and `docs/reviews/v97-discovery-continuity-and-new-words/`.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 245 | 245 | 0 | 87 eligible |
| Cald sau Rece | 265 | 263 | 2 | 259 eligible |
| Lanțul Cuvintelor | 123 | 120 | 3 | 120 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 228 | 228 | 0 | 189 preferred |
| Perechi | 193 | 193 | 0 | 153 preferred |

Pack **716 = 708 approved + 8 pending**, 546 eligible. All 713 previous records remain exact.
Quick supplement 85; all 83 previous authored records/scores and 336 core boards remain exact.
All 105 Lanț rejections, 264 prior Contexto profiles and shared KG/mobile bytes stay exact.
KG: `fixture-v90-household-discovery`,2416 nodes/9459 links/8641 forms/180 puzzles.
Sessions retain 7200-second sliding TTL, 1000 entries/game,locks,64 KiB requests and bounded
histories/caches. Exploration stays≤256 concepts/512 recipes/256 saved crafts,128 observed
empty pairs/session; quick supplements≤256 boards/2 MiB. Recipes/routes/answers stay private.

## Current artifact pins

- alchimie_discovery_world_v92.json: `0b3fea2c30b4c729cbe8398bc467e5a4f7e6a443ff886023a07d9bf0e40e9f44`
- alchimie_recipe_extensions_v92.json: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- quick_games_v92.json: `804fcf446487e9925158598c4663f0d61f4508574ad14b2fc4e93a5ba8fe6803`
- games_pack.json: `4162c8db2205ac4f250e29e6e94ec1e0212036d6c38de5660991a8bd010204de`
- board_rankings_v37.json: `23421501b0e4bc391a62d25a577ed9d08c935a9eb48a550ab0e5b2f0e8367acb`
- derived_catalog_v38.json: `fe88e7265c68a79884eabb257912630722980dccd7238f3a834c6796aa65b400`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- cat_mobile_app_pack_contract.json: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`

## Verification

- Final assembled gates are GREEN: **2329 backend/53 account tests on Python 3.12 and
  Python 3.14; 214 native frontend/552 browser checks**, two browser workers and zero retries.
  Validators, Ruff, frontend lint/typecheck/build,docs and whitespace pass; gzip 119.23/120 KiB.
- Independent resumption audit verifies all 65 kickoff/139 integration archive records,
  mirrors, earlier content preservation and distinct factual/quality approval bindings.
  No missing approval was found. Nine complete historical books retain earned progress.
- The original browser run: 485 pass/67 fail is preserved. 66 Alchimie failures came from
  the browser eight-history limit; one Lanț mobile replay error escaped view after toast expiry.
  Focused correction checks pass 93 V97 backend, 19 save-validation, 84 Alchimie browser and
  26 shared start/replay cases. Real-clock geometry confirms the notice and retry stay visible.
- Two new focus assertions initially sampled before the disabled pending render; waiting
  for that state resolves the test race. The original 24 pass/2 fail and earlier lint failure
  are retained. No timeout increase, retry or product behavior was used to hide a failure.
- Independent fix review verifies 34 source/static bindings and 87 evidence hashes with no
  mismatch. The final 552-case suite covers every game and the rebuilt caption screens.
- Inherited backend/data/scripts/tests remain exact through today's frontend corrections;
  the final receipt binds 522 candidate inputs plus archived raw logs and historical reviews.
  Evidence: reviews/v97-discovery-continuity-and-new-words/integration/verification.json.
- Human enjoyment and physical-device acceptance remain unrun. The requested Windows
  skill page/name remains unidentified; repo docs and the existing V97 work were used.

## Production and next work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`.
  Today's work does not deploy, push, merge or restart the recurring loop; shared main is clean.
- V97 is verified on its local task branch. Clarify the next-version scope and specific
  Windows skill reference before further version work. Ușă still
  lacks intrare/toc/balama/lemn; the new Cacao→Lapte round still has four generic captions.
  Both new dishes need useful onward uses; only five concept slots remain under the bound.
- Earlier Caraiman/museum/Dem/Ateneul descriptions, Neagu labels and pending A5 holds stay
  open. Human playtesting/device acceptance remain unrun; accounts stay off until DEPLOY gates.

## Doc map

- README/AGENTS: orientation; agent-map/agent-testing: routes/gates.
- ADRs (newest 0155), reviews and WORKLOG: decisions, evidence and history.
