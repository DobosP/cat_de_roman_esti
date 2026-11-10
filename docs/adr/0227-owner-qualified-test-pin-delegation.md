# ADR-0227: Owner-qualified test-pin delegation

Date: 2026-11-10
Status: accepted (Paul, 2026-11-10).
Decider: Paul Dobos.

## Context

V4 C1–C5 passed their existing exact-SHA gates and fresh independent landing reviews.
ADR-0210 still required Paul to approve each separate expectation-pin commit before landing.
The owner receipt below approves the five exact commits and delegates future qualified pins.
It supplements the original V4 owner log without changing any earlier quoted ruling.

## Decision

1. Accept the five separate test-pin commits and the qualified local prefix through
   `1eb2e7682675bb967b11e267b965b7bec2cd9eef`:

   | Cohort | Exact test-pin commit |
   | --- | --- |
   | C1 | `8a275f53665c9fc19d8549e622d518247d28a2b2` |
   | C2 | `2af8f7d358443dd86033fd77c068b6f9157159a0` |
   | C3 | `409e6b2c339fc028e16621477a236ef5c156897e` |
   | C4 | `7d0b11c9a5023177f136e57cc5d81deb23408a74` |
   | C5 | `1eb2e7682675bb967b11e267b965b7bec2cd9eef` |

2. Delegate future **separate test-expectation commits** only when expectations are regenerated
   from independent oracles, every existing gate passes on the exact candidate SHA, and a fresh
   independent landing reviewer clears that candidate. Keep the old-to-new pin list and exact
   source/corpus bindings. This narrow delegation replaces the per-commit owner approval step;
   it grants no authority to weaken validators, assertions, seeds, runtime or source policy.
3. A corpus case-count change remains **NEEDS-OWNER**, with a case-list diff under ADR-0186.
   A self-capture still cannot establish independent expected evidence. All source controls,
   item and cohort gates, factual/quality independence and blind gameplay checks remain.
4. Keep all 79 held Conexiuni boards and all other recorded/owner-held rows unchanged. Keep
   bare *sucitoare* excluded, keep *ii*/*iei* off Ie, and require Paul's explicit go for
   Mănăstire/Sucitor. Minors remain excluded from names; living-person proposals go to Paul.
   Local Git only remains the landing scope. Main pushes, production and accounts require
   their existing owner authorization. No source-policy, clinical or privacy ruling changes.

## Supersession

Only ADR-0210's operator for the separate test-pin approval step is superseded.
ADR-0226's retention of that owner step is amended by this decision. Every other boundary in
ADR-0210, ADR-0186, ADR-0226 and the [V4 procedure](../CONTENT_LOOP.md) remains in force.

## Actual landing

Operator `agent:codex` ran `git merge --ff-only 1eb2e7682675bb967b11e267b965b7bec2cd9eef`
at `2026-11-10T06:50:28.709546+00:00`, from clean local main
`1e3a04eb70d58770315be2b65fa22759cb6cfe11`; main was clean afterward.
The product prefix adds seven Conexiuni boards, two Lanț routes and one Cald target (Muzeu).
It adds no shared KG concepts, names, edges, accepted forms or legacy puzzle IDs.
The subsequent documentation/registry commit is not a newly qualified product SHA.

## Owner receipt

Receipt received at `2026-11-10T06:50:27.299154+00:00`; source: Paul's user message containing
`request_user_input_async` replies. Compact original receipt and actual fast-forward proof:
`~/work/_temp/content__v4/owner/qualified-prefix-and-pin-delegation.json` and `owner/landing.json`.
Frozen qualification and application proof: `owner/landing-record/` in the same scratch root.
The question describes main immediately **before** the recorded fast-forward.

Earlier approval scopes and selected answers, verbatim from the same receipt:

Scope:

```text
C1 8a275f53665c9fc19d8549e622d518247d28a2b2 and C2 2af8f7d358443dd86033fd77c068b6f9157159a0 exact test pins
```

Selected answer:

```text
Approve both exact pin commits (Recommended)
```

Scope:

```text
C1–C4 qualified prefix through exact 7d0b11c9a5023177f136e57cc5d81deb23408a74
```

Selected answer:

```text
Approve C1–C4 through exact 7d0b11c9 (Recommended)
```

Latest question, verbatim:

```text
Main additions remain 0 words, names and boards in all six games. Five qualified cohorts contain seven Conexiuni boards, two Lanț routes and one Cald board targeting Muzeu. ADR-0210, retained by V4, requires your approval of their separate test-pin commits before local landing. Approve the qualified prefix through exact 1eb2e7682675bb967b11e267b965b7bec2cd9eef? The recommended option also delegates future separate test-expectation commits regenerated from independent oracles and cleared through every existing gate and fresh landing review. Review [C1 pins](/home/dobo/work/_temp/content__v4/c1/seed-rebind/revised-pins.diff), [C2 pins](/home/dobo/work/_temp/content__v4/c2/http/pins.diff), [C3 pins](/home/dobo/work/_temp/content__v4/c3/http/pins.diff), [C4 pins](/home/dobo/work/_temp/content__v4/c4/http/pins.diff) and [C5 pins](/home/dobo/work/_temp/content__v4/releases/c5/http/pins.diff).
```

Selected answer, verbatim:

```text
Approve five + delegate future qualified test pins (Recommended)
```
