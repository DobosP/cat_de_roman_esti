# V4 landing queue

The C1–C5 rows record the historical local fast-forward at 2026-11-10T06:50:28.709546+00:00
to product `1eb2e7682675bb967b11e267b965b7bec2cd9eef`. Paul approved those exact pins
under [ADR-0227](../adr/0227-owner-qualified-test-pin-delegation.md). Shared main was clean
before and afterward. Shared words and names were unchanged.


| Cohort | Exact qualified source SHA | Added boards/routes | Gate and independent-review receipt | Status |
| --- | --- | --- | --- | --- |
| C1 | `8a275f53665c9fc19d8549e622d518247d28a2b2` | Conexiuni +2 (Istorie/Societate), Lanț +2 (Făină→Salată de boeuf; Jiu→Marea Neagră); other games +0 | `c1/qualification.json`: build11/4i10/unit27/full37, 859 browser, fresh GO | Landed in product prefix above. |
| C2 | `2af8f7d358443dd86033fd77c068b6f9157159a0` | Conexiuni +2 (Limbă); other games +0 | `c2/qualification.json`: build11/4i10/unit27/full37, 859 browser, fresh GO | Landed in product prefix above. |
| C3 | `409e6b2c339fc028e16621477a236ef5c156897e` | Conexiuni +1 (Societate), Cald +1 (Muzeu); other games +0 | `c3/qualification.json`: build11/4i10/unit27/full37, 859 browser, fresh GO | Landed in product prefix above. |
| C4 | `7d0b11c9a5023177f136e57cc5d81deb23408a74` | Conexiuni +1 (Film TV); other games +0 | `c4/qualification.json`: build11/4i10/unit27/full37, 859 browser, fresh GO | Landed in product prefix above. |
| C5 (C10 intake) | `1eb2e7682675bb967b11e267b965b7bec2cd9eef` | Conexiuni +1 (Știință); other games +0 | `releases/c5/qualification.json`: build11/4i10/unit27/full37, 859 browser, fresh GO | Landed in product prefix above. |
| C6 (C11 intake) | `cc905fbb1908c2368cf7837195cb98819dcac48b` | Lanț +1 Aragaz→Lingură, gastronomie/normal, par 3. Other games +0. | `releases/c6/qualification.json` records build 11, unit 27, fresh 4i 10, full 37, 859 browser cases, 1,206 parity cases and PostgreSQL 12/302. Fresh GO is `911601a4…`. | Landed locally at 2026-11-10T09:05:37.981813+00:00 by clean fast-forward from `75b1b9bd`. |
| C7 (C12 intake) | `26ebaf39bd642d9778c9c9d7d09159f1297c0dfa` | Conexiuni +1 household-properties board. Eight existing nodes gain first Conexiuni exposure. Other games +0. | `releases/c7/qualification.json` records build 11, unit 27, fresh 4i 10, full 37, 859 browser cases, parity 1,206 and PostgreSQL 12/302. Fresh GO is `d9835f6b…`. | Landed locally at 2026-11-10T11:50:52.426278+00:00 by clean fast-forward from `6c295e57`. |

Receipts are relative to `~/work/_temp/content__v4/`. `owner/landing.json` records the actual
command, operator and UTC; `owner/landed-delta.json` records the product delta.
`owner/landing-record/` freezes the exact receipts and reproduces the twenty registry
transitions from immutable Git baseline `6b67eaa4b9f92dab60f96f7b03b8fa617d881aed`.
All ten prefix boards won and reloaded over HTTP; every cohort's independent corpus matched
1,206 cases. All 79 Conexiuni locks and all 87 owner-held rows remain unchanged.
Later loop staging is separate from this landed product inventory.
The [V4 procedure](../CONTENT_LOOP.md) governs future cohorts. Historical V3 landings are in
[ADR-0225](../adr/0225-retire-v3-content-loop-artefacts.md).

C6 receipts bind landed product `cc905fbb`. The earlier C1–C5 prefix remains historical.
The landed V4 prefix contains eleven boards, comprising seven Conexiuni, one Cald and three Lanț.
Other game additions and KG words, names, edges, forms and puzzles remain zero.
C6 raw gates remain retained. C12/C13 proposals and C7 staging are separate from this record.

The C1–C6 rows and earlier prefix paragraphs record their landing-time facts.
C7 receipts bind product `26ebaf39bd642d9778c9c9d7d09159f1297c0dfa`. The current landed prefix has twelve
boards, comprising eight Conexiuni, one Cald and three Lanț. Other game additions and
shared KG words, names, edges, forms and puzzles remain zero. Earlier C6 raw trees were
pruned under retention manifests. C7 owning raw gates remain retained at qualification.

## C8 landed locally, 2026-11-10

Exact product `8f9ff9188129a3026f1ea3bbd938dc2fc21a16af` fast-forwarded cleanly from `da7674dcfa263528623ce1eccc8393d31700e6bb`. The sole `cx_stiinta_383` passed build 11, unit 27, fresh 4i 10, full 37 and independent GO `8ffda23956a58b9b94af91d9349188904829a450bb2fb15193b0e53fcecce4f2`. All 859 browser cases, CSP 0/0, PG 12+302, parity 1,206 and nine PNGs/all 17 baseline outcomes passed. Normal HTTP won and reloaded with zero mistakes. ADR-0227 covers the five independently regenerated separate pins. One registry ID advances reviewed→qualified→landed. The landed prefix is nine Conexiuni, one Cald and three Lanț boards, with zero shared vocabulary additions. Limits and retained receipts are in [the C8 record](../reviews/v4-c8-science-conex/README.md).

## C9 landed locally, 2026-11-10

Clean main `94e8d175` fast-forwarded to qualified product `642f0c2f133786fcc0198f2f2b1440978632369a`. Separately reviewed operator-only child `12b9af3bf6222e0162a72e027be1cf30d0a6068f` then landed. The two existing-KG Lanț routes, `lt_societate_250` and `lt_stiinta_251`, passed exact build 11, unit 27, fresh 4i 10 and full 37, followed by independent GO `da74b8527b66db7f2d2f7b7aac20f2f63772f2f94afc2f006da31e46ed2bc625`. All 859 browser cases passed with zero skips, retries or flaky outcomes. Enforced CSP was 0/0; PostgreSQL accounts 12, HTTP API 302, parity 1,206 and nine PNGs with all 17 baseline outcomes passed.

Eleven normal public-text witnesses won and reloaded. Five chip-only witnesses won; six encountered UI omissions, with free-text fallback accepting the legal moves. Original blind evidence records prospective native-caption graph play. Four events advance only the two reviewed rows through qualified and landed: 3,351 → 3,355 events, 2,984 IDs unchanged and 13 → 15 landed boards. All other 2,982 rows and protected holds/guards remain exact. The prefix is nine Conexiuni, one Cald and five Lanț boards, with zero shared vocabulary additions. P9 inventory is 731 pack records, 724 approved, seven pending and 542 eligible; Lanț has 128 records, 126 approved and 126 eligible. T has its own operator tests and code review. P9 carries the product GUI gate qualification. C16, C17 and ADR-0228 policy/M2 state retain their separate scope. [C9 record](../reviews/v4-c9-postal-shirt-lant/README.md).


## C10 — 2026-11-11

Valid until: a relevant source/runtime change — then treat as history.

Product `4824609e5a8442beab43c762efdb3c859fc5bd9b` landed locally after build11/4i10/unit27/full37 and [fresh GO](../reviews/v4-c10-society-emoji/landing-review.json). Society `cx_societate_384` and Cald `ct_meme_net_379` won/reloaded on normal HTTP. Separate seven-file expectations `8c3b8835` satisfy ADR-0227; fixed corpus stays 1,206. The original P10 doc-inventory NO-GO, full I10 requalification, all292 attachments and9PNGs remain; no remote publication occurred.
