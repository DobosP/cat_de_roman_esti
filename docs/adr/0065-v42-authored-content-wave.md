# ADR-0065: V42 gated content wave and its owner-decision queues

- Status: accepted
- Date: 2026-07-29

## Context

V42's audit (V42_DESIGN_VERDICT, owner request of 2026-07-26) found content, not mechanics,
to be the main fun bottleneck: rubric-violating boards inside the served pool, four empty
Ușor Conexiuni shelves, single-board category shelves, and 222 ungated pending items. The
owner authorized running the ADR-0023/0025 analyst/verifier review and delegated final
judgment to the orchestrating session.

## Decision

1. **Gate runs.** The critique-games fleet (Sonnet critique → adversarial Opus verify with
   section-F web checks) processed: all 36 pending Contexto/Alchimie items (full coverage),
   79 pending Conexiuni, 107 pending Lanț, a 132-board sweep of served stock, and the new
   authored wave. Usage-limit interruptions were recovered by workflow-cache resumes; where
   several runs produced conflicting *verified* verdicts, the orchestrator arbitrated per
   item on the recorded evidence (arbitrations: ct_sport_314 keep, cx_viata_de_roman_312
   keep, cx_stiinta_310 keep, cx_geografie_305 promote) and assembled per-game batch
   artifacts from the verified union; `apply_rereview.py` then re-validated bindings and
   playability fail-closed as usual.
2. **Authored wave.** 78 new KG nodes and 98 edges (everyday-culture, retro-brand, customs,
   landmark concepts) plus 32 instances were authored in-session, factually web-verified by
   an Opus fleet **before** import (which caught 21 duplicate nodes, wrong Brifcor/DN1/Arc
   descriptions, three duplicate Contexto targets, and a factually false KG edge later
   confirmed at gate: Dem Rădulescu never co-starred with Pellea/Caragiu), quality
   pre-screened, imported via `import_candidates.py`, and lint-fixed to zero deterministic
   FAILs before gating.
3. **Shipped outcome.** 36 promotions / 11 rejections. Approved: Conexiuni 215, Contexto
   198, Lanț 94, Alchimie 78; eligible 129/198/94/78 (499 zero-FAIL served boards). Each
   formerly empty Ușor Conexiuni shelf has ≥1 eligible board again.
4. **Derived catalog stays pinned.** `build_derived_catalog_v38.py` now excludes the six
   new eligible sources explicitly (`V42_DEFERRED_SOURCES`) so Intrusul/Perechi remain the
   frozen 336-board pilot catalog per ADR-0054; widening them is a post-pilot decision.

## Owner-decision queues (ADR-0019 — never auto-applied)

- **Near-duplicate-held boards** (gate `keep`, quality largely verified fine, held because a
  group re-skins served stock): cx_gastronomie_296/297/298/300/301, cx_geografie_302/303/304,
  cx_stiinta_308/310/311, cx_viata_de_roman_312/314, cx_limba_307, ct_muzica_311,
  ct_sport_314/315/317. Approving 2–3 per shelf reaches the 8-board daily-pool target from
  V41's deferred ask.
- **Sweep proposals** on served stock: 67 verified `demote`, 6 `revise`, 4 `keep`
  (55 unswept) — archived in the ops scratch `SWEEP_PROPOSALS.md`.
- **Deferred applies**: the verified pending-pool verdicts for Conexiuni (1 promote / 34
  reject / 42 keep) and Lanț (4 promote — one failing playability re-derivation — / 77
  reject / 10 keep) could not be applied after the Contexto/Alchimie apply staled their
  dossier bindings; artifacts and journals are archived, and a post-release re-gate from
  fresh dossiers is the sanctioned path.

## Consequences

- Quantity growth is real but conservative: every shipped item carries a live adversarial
  verification; near-duplicate calls stay with the owner.
- The gate exposed systemic freshness debt in the approved pool (canonical quads re-served
  up to eight times; member overuse well past the >8 threshold for Caragiale/Enescu/Dunărea
  class nodes). The sweep queue is the cleanup vehicle.
- Authoring practice must census served quads before design, not only the KG (the wave's
  main authoring error, caught by the verifiers' pack censuses).
