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
