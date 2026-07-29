# 2026-07-29 — V42 owner decision queues (release go, held boards, sweep)

Valid until: Paul processes these queues or supersedes them — then treat as history.

V42 (ADR-0062..0065) is merged on main at `7e862b4`, all gates green. Three owner-only
queues remain; everything below is a proposal, nothing auto-applies (ADR-0019).

## 1. Release go — anonymous arcade v1

# V42 anonymous release checklist (working doc)
_Valid until: V42 ships or is abandoned — then treat as history._

Target: replace live fixture-v32 four-game deploy at cat-de-roman-esti.dobolabs.ro with
V42 six-game anonymous arcade (docker-compose.anon.yml, CAT_ACCOUNTS_ENABLED=0, no DB).

## Gates (all must be green before deploy; run in worktree, repo .venv)
- [ ] `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -q` (full backend)
- [ ] `CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 ... -m pytest tests/accounts -q` (accounts suite still green even though OFF)
- [ ] `scripts/validate_games_pack.py` + `scripts/validate_fixture.py`
- [ ] `scripts/rank_games_pack.py` regenerated + `scripts/build_derived_catalog_v38.py` rebuilt after content apply
- [ ] frontend: `npm run lint` + `npm run build` (tsc + vite + bundle budget ≤ 120 KiB) + `npm test`
- [ ] `git diff --check`
- [ ] mirrors byte-identical (fixtures vs tests/fixtures)

## Docs discipline (same commit as landing)
- [ ] docs/V42_REFINEMENT.md (what/why/how verified)
- [ ] ADR: V42 playability wave (2nd Conexiuni clue supersedes ADR-0007 economy line; Lanț normal cue extends ADR-0046; Alchimie nudge/daily floor amends ADR-0044 boundary; local streak/diploma — new ADR, notes ADR-0053 public-streak deferral untouched)
- [ ] ADR: V42 content wave (gate/sweep/authored batch, counts, ADR-0023 protocol references)
- [ ] docs/STATUS.md rewrite (new counts, V42 outcome, Last verified)
- [ ] README game modes list if changed

## Paul decisions needed before go-live (cannot be decided by the agent)
1. `CAT_LEGAL_OPERATOR` + `CAT_LEGAL_CONTACT_EMAIL` values (required even for anon stack).
2. Legal pages are DRAFT with [[PLACEHOLDER]]s (web/legal.py, docs/compliance/) — fill or accept for hobby release.
3. Sweep demote proposals on approved stock (owner-only per ADR-0019/0023).
4. The deploy `go` itself (DEPLOY.md procedure on the target host; rollback = previous image).

## Post-release (the anonymous pilot the docs call for)
- Aggregate pilot telemetry decision still open (privacy/retention) — ADR needed before any analytics.
- Score-curve changes + 7th game remain gated on pilot evidence (ADR-0054 boundary respected in V42).


## 2. Near-duplicate-held boards (gate `keep`, ADR-0065)

Approving 2–3 per shelf reaches the 8-board daily-pool target from V41's deferred ask:
cx_gastronomie_296 / 297 / 298 / 300 / 301, cx_geografie_302 / 303 / 304,
cx_stiinta_308 / 310 / 311, cx_viata_de_roman_312 / 314, cx_limba_307,
ct_muzica_311, ct_sport_314 / 315 / 317. Full verified evidence lives in the ADR-0023
verdict archives (session journals; see ADR-0065).

## 3. Sweep of served stock

# V42 sweep — owner proposals (ADR-0023 sweep mode; approved stock is never auto-demoted)

_Verified union across sweep runs of 132 served low-quality/WARN-flagged boards. demote = leave the served pool; revise = good bones, one swap fixes it; keep = fine. Every row had a live adversarial Opus verifier (or was a clean stable-sample skip per G3). Unverified critiques listed separately as unswept._

## DEMOTE — 67 verified proposals
- **cx_arta_cultura_003**: Verdict survives refutation, though two of six failure modes fall. Oedipe clears A1 (60+ years of ONB/Cluj/Iași staging) and the Folclor group satisfies its predicate — the critic overstated both. Wha
- **cx_arta_cultura_004**: Verdict stands; reasoning partly overturned. Refutation attempt: every lint is WARN, tile_fairness is clean (no unfair/contested tiles), and B2's type-agnostic escape could arguably cover "Pe șevalet,
- **cx_arta_cultura_005**: I overturned most of the critic's reasoning but not the verdict. All four flagged web claims fail: Delta Dunarii IS World Heritage (1991), so the UNESCO label is A3/A4-honest across its 3 World Herita
- **cx_arta_cultura_007**: Rubric and dossier read directly. B1/A3: each group is an "associated with X" bundle, not one checkable predicate — Brâncuși = man+medium+2 works; Grigorescu = man+work+influence+medium; Voroneț = mon
- **cx_arta_cultura_091**: Refute-first failed on the load-bearing findings. Pack scan (fixtures/games_pack.json, 288 approved conexiuni): "Enescu pe partitură și pe afiș" is an EXACT 4/4 quad reuse in cx_muzica_208 and cx_pers
- **cx_arta_cultura_092**: Refute-first failed. Keep argument (all tiles verified famous; director↔film mirror is type-distinct so no mis-sort) collapses: B5's own canonical examples (festivals↔host cities, hosts↔shows) are equ
- **cx_arta_cultura_094**: Refute-first partially succeeded on two sub-claims but not on the verdict. Group 1 is NOT a Bonțida B1 failure — all four tiles are node_type work and satisfy "Brâncuși at Târgu Jiu"; and the aviation
- **cx_arta_cultura_159**: Refute-first fails: the strongest pro-keep reading collapses on A4. "Proză de manual, fără cameră de filmat" asserts these school texts were never filmed — false for all four: Moromeții (1987, 2.22M v
- **cx_arta_cultura_161**: Critic's peripheral A1 doubts are refuted (Grigorescu's "Car cu boi" is canon; Brukenthal is nationally salient; the Aviation Museum is a permissible single B8 deep-cut). The board still fails. B6 is 
- **cx_arta_cultura_162**: Refute-first failed both ways. KEEP dies on A6: pack inspection of 209 approved boards shows G2 is an EXACT quad in cx_film_tv_169/cx_muzica_209/cx_societate_155 (+3-shared in two more), and G1's Aten
- **cx_arta_cultura_239**: Refute-first failed. Every recognition doubt (F-checks 1-4) resolves FOR the item — Enescu Festival, TNB, Mungiu all pass A1/A2; Oedipe is a legitimate single deep-cut. Recognition was never the faili
- **cx_arta_cultura_241**: Refutation succeeded on three of the critic's modes: labels are hidden until solved, so B9 "player sees the answer" is wrong (only a post-solve blemish); web checks clear Sburătorul, Lovinescu and Oed
- **cx_film_tv_008**: Refutation attempt failed. Pro-keep points do hold — all anchors are prime-time famous, Isoscel is web-confirmed iconic (critic's B8 reasoning overturned), fairness is clean (0 unfair/contested/raw). 
- **cx_film_tv_009**: Refute-first failed. B5 mirror confirmed: ro.wiki lists Caragiu (capitanul Panait), Radulescu, Papaiani, Constantin as the recurring Brigada Diverse cast, and "B.D. la munte si la mare" sits in Group1
- **cx_film_tv_011**: Refutation attempt failed. Independently reconfirmed from games_pack.json: g2 is an exact quad reuse of approved cx_film_tv_165; g4 shares 3 members with THREE approved boards (cx_arta_cultura_239, cx
- **cx_film_tv_013**: Critique upheld and strengthened. B9 fails 4/4 verbatim: every label IS a member tile ("Pro TV", "Prima TV", "Antena 1"; "TVR și Kanal D" names both). A pack-wide scan proves this is not an interpreti
- **cx_film_tv_165**: Refute-first partially succeeded on two sub-claims but not the verdict. Isoscel clears A1 (ro.wikipedia names it Buciuceanu-Botez's emblematic role; 5.5M-spectator film), and Bucuresti IS thematically
- **cx_film_tv_167**: Verdict stands; two of the critic's five modes fail. B1 REFUTED: "Aur fără bijuterie" predicate is orthographic ("conține AUR"), satisfied identically by all four — unlike Untold/Bonțida, where a sema
- **cx_film_tv_169**: Refute-first failed. Recognition (A1/B8) and facts (A4) all verify — including the suspicious "2026" end year. I also overturn the critic's strongest B1 sub-claim: Vacanța Mare's TV output *is* catchp
- **cx_gastronomie_171**: Verdict stands, on partly different grounds. CONFIRMED: (1) ro.wikipedia returns totalhits=0 for "Bucovina gastronomică" — an invented meta-label ("imagine culinară regională"), not a dish, seated bes
- **cx_geografie_028**: Recognition is not the problem — every anchor verified. Construction and freshness are. Pack inspection: cx_geografie_023 and cx_geografie_109 already carry the IDENTICAL quad Dunărea/Olt/Siret/Prut; 
- **cx_geografie_110**: Critic's verdict survives, but two of its five failure modes are refuted. A7/tile-tangling is WRONG: gameplay never leans on Barabulă→Moldova (regions and regionalisms are separate quads); tile_fairne
- **cx_geografie_177**: Refute-first succeeded on recognition and failed on everything else. Web checks overturn the critic's B7/B8 case: Resita (1771, Romania's oldest industrial unit), Galati (largest steelworks, 2/3 of th
- **cx_geografie_178**: Refutation succeeded only on B5/B3: all four strong cross-edges share one endpoint (Brâncuși), so they are not "≥3 disjoint" — mirrored_groups correctly did not fire; tile_fairness passed, contested_t
- **cx_geografie_252**: Refute-first failed on the two load-bearing points. (1) The best "keep" defense of "Locuri de litoral și deltă" is reading litoral as the Romanian seaside destination; ro.wikipedia shows it is a gener
- **cx_istorie_029**: Refute-first failed. Every web check came back PASS: all 16 tiles clear A1/A2 (Mărășești sustained + film-slogan footprint; Chișinău 27-Mar is annually commemorated canon, not politically loaded; Bucu
- **cx_istorie_030**: Verified in the pack, not the summary: "Dacia antică" is member- AND label-identical to cx_istorie_115's group; "Roma din poveste" is that board's "Roma în poveste" quad with one preposition changed —
- **cx_personalitati_064**: Refutation attempted and failed. Pack diff (cat_de_roman_esti/fixtures/games_pack.json) shows 4/4 groups already served: g1 = cx_arta_cultura_003.g1 exactly; g2 = cx_arta_cultura_004.g4 exactly; g4 = 
- **cx_personalitati_144**: Refute-first failed. Fairness is clean (no unfair/contested tiles, engine_unfair_raw 0, no cross-group strong edges) and I overturned three critic claims: Mungiu clears A1, Oedipe and Angela Gheorghiu
- **cx_personalitati_210**: Refute-first succeeded on fame: all 16 tiles clear A1/A4 (verified Liceenii's Mihai Marinescu/Bănică Jr., Pelișor↔Regina Maria, Târgu Jiu↔Brâncuși, Nadia's Montreal 10s, Enescu's Paris exile). A recog
- **cx_personalitati_213**: I overturned 2 of the critic's 4 failure modes (B8 and A7 — see web_checks), but the verdict survives on the other two, which I verified against the pack itself rather than the lint text.  A6: all FOU
- **cx_personalitati_214**: Refute-first failed. Recognition is clean — web checks OVERTURN four of the critic's sub-claims (Mica Antantă, Societatea Națiunilor, Efectul Coandă all pass A1; B8's "two deep-cuts" is wrong). The ve
- **cx_personalitati_275**: Refutation attempted on every axis and failed. Recognition is NOT the problem: web checks clear Balcic, Pelisor, Mica Antanta and Trianon (only the memoir is a true deep cut, permitted once on greu), 
- **cx_personalitati_276**: Recognition survives (Brăescu, Efectul Coandă, Davila all clear A1), so I overturned that axis — but the structural kill is stronger than the critic stated. Direct pack check: cx_stiinta_162 (also nor
- **cx_personalitati_277**: Critique upheld; refutation fails. B9 is dispositive alone: "Lumea teatrului românesc" contains member "Teatrul românesc" verbatim. ro.wikipedia shows doina is "cântat în singurătate", non-ceremonial,
- **cx_societate_065**: Refute-first, the keep case is real: no FAIL lint, tile_fairness passes, the partition is unique (no tile fits two predicates), and every tile clears A1/A2 easily. engine_unfair_raw=5 is largely benig
- **cx_societate_067**: Critique upheld; I could not overturn it. B5 is decisive and self-executing: the rubric's own canonical mirror example is "inventors ↔ their machines", and this board ships that mirror at 4/4 (0.90–0.
- **cx_societate_068**: Refute-first for keep fails. Best keep case: zero FAIL lints, tile_fairness/contested clean, and CEDO is web-verified as a genuinely distinct document (refuting the critic's sub-claim). All 16 tiles p
- **cx_societate_151**: Refute-first failed. Keep is untenable: B5 is 4/4, not 3-way — every city has its eponymous plant (0.88/0.88/0.86/0.86), stronger than the rubric's own festivals↔hosts example; once one pair falls, 8 
- **cx_societate_152**: Verdict direction survives, but not for the critic's stated reason — its reasoning ("test") and claim list are placeholders carrying no argument. I re-derived the kill from the pack itself (cat_de_rom
- **cx_societate_155**: Refute-first failed. Keep is untenable: g1 pairs the play with three of its own characters — the canonical B1 "is an X" vs "is associated with X" mix (Bonțida pattern), plus B2 person+work, which the 
- **cx_societate_216**: Pack inspection (games_pack.json) shows worse recycling than the critique: g2 is an exact repeat of cx_societate_065's "Administrație locală"; g4 an exact repeat of cx_societate_068/153's "Organizații
- **cx_societate_217**: Refute-first largely succeeded on recognition: web checks clear Puterea judecătorească, Avocatul Poporului and the "buletin lung" framing, no FAIL lints, tile_fairness clean, and engine_unfair_raw=5 r
- **cx_societate_220**: Read rubric A/B/F and the dossier directly, and pulled the 9 cited boards from fixtures/games_pack.json rather than trusting counts. A6 confirmed hard: the dish quad recurs under the identical predica
- **cx_societate_280**: Refute-first failed. A1 is NOT the problem: CEDO and ÎCCJ both clear the recognition floor (sustained ro.wiki pageviews, no spike), and "Norma Academiei" is school-canon-adjacent. So the critic's A1-a
- **cx_societate_290**: Read rubric A/B/F, the dossier, and the three cited boards in games_pack.json myself. A6 is confirmed on the actual quads, not aggregate counts: g1 {Alegeri, Protest, Societatea civilă, Drept de vot} 
- **cx_sport_072**: Critic's named mode B5 is REFUTED. `mirrored_groups` never fired, and recomputing max disjoint strong (>=0.6) cross-edge matchings from the dossier caps every group pair at 2: G4-G3 and G4-G2 and G4-G
- **cx_sport_073**: Refute-first failed. Pack inspection confirms A6 re-skin harder than the critic did: g1 = exact 4/4 re-serve of cx_sport_222, g4 = exact 4/4 of cx_sport_283, plus 3/4 overlaps with cx_sport_076/157/16
- **cx_sport_074**: Refute-first partly succeeded: three critic sub-claims are wrong. B7 has a clean uncontested anchor (România olimpică draws zero cross-group strong edges); B4 holds (contested_tiles empty, raw=2 < 4-m
- **cx_sport_076**: Refute-first failed. Two critic pillars collapse: Ghencea and Hagi's 'Regele' both pass A1 on web checks, US Open 1972 is factually correct and an allowed B8 deep-cut, fairness is clean (0 unfair/0 co
- **cx_sport_077**: Refute-first failed. Pro-keep case (no FAIL lints, engine_unfair_raw=0, one contested tile within budget, greu allows one deep cut, Mureșan and Țiriac/Madrid Open both clear A2) does not survive.  Dec
- **cx_sport_156**: Refutation attempts, and what survived. (1) "Duplication is symmetric — demote the other board instead" FAILS: cx_sport_156 is the strictly weaker twin every time. Recomputed overlaps directly from th
- **cx_sport_157**: Refute-first partly succeeds: the critic's B1/B2 kill is overstated — the "one famous moment" cluster (person+event+record+concept) is the approved house style of cx_sport_073/222/281 — and web checks
- **cx_sport_160**: Refute-first attempt at "keep" failed. All 16 tiles pass A1/A2 (web-verified) and fairness is clean (engine_unfair_raw 0, no contested tiles, no cross-group strong edges), but structure collapses. Pac
- **cx_sport_161**: Refute-first failed. Web checks clear A1/A4: the critic's own handball-CL doubt is refuted (substantial ro.wiki articles, CSM București 2016, Neagu 4x IHF), and every embedded fact verifies — Mureșan'
- **cx_sport_222**: Refute-first fails. Recognition/factual case is strong (F checks all pass; fairness clean: engine_unfair_raw 0, no contested tiles, B3-B7 fine) — but A6 kills it. Checked against games_pack.json direc
- **cx_sport_225**: Fame is not the problem — every web check passed, so I tried hardest to overturn toward keep/revise and failed on the pack itself. Reading games_pack.json directly: g2 {Patzaichin, canoe, delta_pagaia
- **cx_sport_226**: Refute-first failed. Keep case (all 16 tiles web-verified A1; tile_fairness passes; red-herring 2<4; group 1 excellent) collapses on predicate honesty. G3 "Cifre și metale olimpice": zero members are 
- **cx_sport_282**: Refute-first failed. I re-derived A6 from the pack itself: g4 {Patzaichin, Canoe, Pagaia din Deltă, Dunărea} is the FIFTH serving of one quad — identical nodes in cx_geografie_179 ("Delta la pagaiă"),
- **cx_sport_284**: KG edges make the critique's case stronger, not weaker: all FOUR groups pair a class/container node with its own instances. Năstase/Țiriac/Halep --is_a--> Tenis (0.94/0.90/0.95); Arena/Rapid/Dinamo --
- **cx_stiinta_083**: Refutation attempt failed. Web checks CONFIRM, not soften, group 2: "Procedeul Edeleanu" has no ro.wiki article at all (404); Edeleanu's own article shows zero Romanian commemoration; Nenițescu's fame
- **cx_stiinta_162**: Refute-first failed. Keep rests on "all lints are WARN, tile_fairness passes" — but the WARNs are the rubric's own kill patterns. B5: g1↔g2 is verbatim the canonical "inventors ↔ their machines" mirro
- **cx_stiinta_165**: Refute-first failed. "Nobelul lui Palade, pe scurt" is an association-bag (person + generic prize + its own subtype + research object) — the Bonțida failure — and the label names its own member (B9). 
- **cx_stiinta_167**: Refute-first for keep fails. I re-derived A6 from the shipped pack, not the lint text: g3 is a 4/4 exact quad of cx_geografie_023 "Lacuri cu poveste" (this label is that label plus "de teren") and of 
- **cx_stiinta_227**: Verified directly in cat_de_roman_esti/fixtures/games_pack.json (209 approved boards): g3 {Paulescu, Insulina, Hormon, Diabet} is identical in approved cx_stiinta_163, cx_stiinta_286 and 227; g1 share
- **cx_stiinta_285**: Refute-first failed. Pack comparison is decisive: cx_stiinta_285 shares 11/16 tiles and all four thematic axes with approved cx_stiinta_162 at the same `normal` difficulty (pioneers/their machines/fli
- **cx_viata_de_roman_238**: Refutation attempt (keep) fails. Keep's best case — every tile is A1/A2-solid, zero FAIL lints, engine_unfair_raw=0, no contested tiles — is irrelevant: recognition was never the defect, and the rubri

## REVISE — 6 verified proposals
- **ct_gastronomie_019**: Refute-first breaks the critic's only load-bearing argument. He passed the A7 WARN because "neither Moldova nor Transilvania appears among the top-10 strong_neighbors, so the edge is unlikely to surfa
- **ct_gastronomie_127**: Refute-first failed in both directions. Pro-keep: the best counter-source (ro.wiki Bucătăria moldovenească) calls mămăligă the best-known dish of Moldovan cuisine — but in the same clause says "precum
- **ct_geografie_030**: Rebuilt the inbound BFS over the non-distractor graph (reachable 2215 vs dossier 2216, model validated). Critic's gameplay case collapses: "Carpați" (salience 0.73) sits at distance 2, rank 2-8/2215; 
- **cx_gastronomie_173**: Refute-first: I tried to save the board by reading "Franta se vede pe eticheta" as one nameable trick — "the French is in the NAME." Its own members disprove it. Web-verified: salata de boeuf is Roman
- **cx_societate_278**: Refute-first held partially. The board is fair and playable: unfair_tiles empty, engine_unfair_raw 0, partition unique (ANAF is the only money-domain spare, and Poliție has no other home), all 16 tile
- **cx_sport_075**: Refute-first breaks the critic's load-bearing pillars. A6/A5: the duplicates are real (both source boards approved and served) but pool-typical — 82/209 approved boards carry >=2 exact-dup quads and 1

## KEEP — 4 verified proposals
- **ct_geografie_031**: The critique's decisive C3 argument rests on a tooling misread. `critique_pack.py:658-670` builds `strong_neighbors` from `predecessor_ids` with strength ≥0.6 — incoming edges only. The full KG (kg_sa
- **ct_istorie_139**: Refute-first attempt failed to demote, and instead broke the critic's one stated concern. The A7 WARN rests on two nodes the critic mischaracterized: KG n_lbax_regionalism_cucuruz is a limba node ("Re
- **ct_viata_de_roman_273**: Refute-first held. C1's literal noun-list omits sayings, but its stated rationale — "nobody free-associates their way to them" — is empirically false here: national media itself headlines the theme wi
- **cx_film_tv_243**: Refute-first killed the critic's two substantive charges. B8: sustained ro.wikipedia interest ranks Pistruiatul (1804/mo) and Toate pânzele sus (1719) ABOVE Lăzărescu (851) and Filantropica (890); Sec

## Unswept (no live verifier): 55
al_gastronomie_024, ct_gastronomie_022, ct_istorie_036, cx_arta_cultura_240, cx_film_tv_244, cx_geografie_179, cx_istorie_001, cx_istorie_034, cx_istorie_115, cx_istorie_117, cx_istorie_118, cx_istorie_181, cx_istorie_182, cx_istorie_183, cx_istorie_255, cx_limba_037, cx_limba_038, cx_limba_122, cx_limba_187, cx_limba_192, cx_limba_260, cx_literatura_040, cx_literatura_041, cx_literatura_043, cx_literatura_044, cx_literatura_126, cx_literatura_127, cx_literatura_128, cx_literatura_131, cx_literatura_193, cx_literatura_194, cx_literatura_198, cx_literatura_264, cx_literatura_266, cx_meme_net_045, cx_meme_net_048, cx_meme_net_137, cx_meme_net_201, cx_meme_net_204, cx_meme_net_267, cx_muzica_053, cx_muzica_138, cx_muzica_141, cx_muzica_143, cx_muzica_205, cx_muzica_208, cx_muzica_209, cx_muzica_273, cx_personalitati_059, cx_personalitati_063, cx_personalitati_145, cx_stiinta_081, cx_viata_de_roman_236, cx_viata_de_roman_288, test
