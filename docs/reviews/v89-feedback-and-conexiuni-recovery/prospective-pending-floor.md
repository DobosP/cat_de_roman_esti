# Prospective C3 lint — existing pending-rail check

Valid until: the bound pack, graph or critique contract changes — then remeasure.

**The proposed numeric incoming floor would leave the current eight-item pending
rail green.** Both existing pending Contexto owners exceed five unique incoming
non-distractor nodes. No exemption, threshold change or owner decision is needed to
preserve this specific rail. This is a measured planning conclusion, not an implemented
lint or a new quality judgment.

| Pending record | Target ID | Incoming count | Incoming at strength ≥0.6 | Existing disposition |
|---|---|---:|---:|---|
| `ct_meme_net_238` | `n_v3mem_shitpost` | 8 | 8 | A5 owner hold; cross-generational recognition concern |
| `ct_societate_257` | `n_v2soc_industrie` | 13 | 13 | A5 near-duplicate owner hold; abstract-target C1 concern |

Counts use `svc.predecessor_ids`, unique IDs and exclusion of the target itself over
the runtime non-distractor graph. Complete IDs, labels, strengths and record bytes
are in the accompanying JSON. The numeric pass says nothing new about recognition,
uniqueness or suitability for public play. Both items remain pending and unserved.

The [V47 exact verdict artifact](../v47-contexto-pending-gate/contexto_verdicts.json)
records the same incoming counts, 8 and 13. Shitpost's profanity-derived wording and
cross-generational concern triggered the owner boundary. Industrie would fail C1 on
quality alone and overlaps the served Industria românească field; A5 required the
owner hold. [ADR-0071](../../adr/0071-gate-contexto-by-feedback-legibility.md) preserves
both dispositions. A numerical C3 pass must not erase those findings or become an
automatic promotion.

I ran the actual current command once:

```text
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/critique_pack.py --status pending --strict
critique_pack: 8 item(s) checked, 0 flagged, 0 FAIL finding(s)
  member_overuse       WARN x65
  nondistinctive_region_link WARN x16
```

Exit status was 0. The inventory warnings already exist and do not mean a pending
item failed. The CLI selects every pending item when `--ids` is omitted and returns
1 for `--strict` only if a selected item's finding is FAIL. Warnings are displayed
without changing this exit status. The current pending breakdown is Contexto2,
Lanț3, Alchimie3 and Conexiuni0. A Contexto-only numeric floor adds **zero** findings
to these two records and cannot affect the six other-game records.

There is no present conflict with the proposed rule. The genuine contract to keep
explicit before implementation is that a numeric diagnostic and an editorial hold
are different decisions: a future A5-held item with fewer than five predecessors
would still trigger an unconditional pending FAIL and make the global strict rail
red. It must not be silently exempted, auto-rejected contrary to A5, or rescued by
fabricated links. Any future conflict would need an explicit supported disposition
or separately reviewed gate-contract decision. Do not invent that exception now.

Tests should protect these exact two holdings as numeric passes while leaving their
pending status untouched, and separately require a synthetic pending target with
four incoming nodes to fail even if it has many outgoing neighbors. Recognition
above the numeric floor remains with judges. Before implementation, inspect whether
new approved-stock WARN findings affect ranker scores or eligibility; a warning must
not indirectly demote old stock without the separately reviewed stock decision.
This note preserves the original
`prospective-scout.md/json` hashes; no application, lint, graph or status was edited.
