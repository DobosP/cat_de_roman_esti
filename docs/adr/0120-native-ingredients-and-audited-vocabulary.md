# ADR-0120: Replace approximate ingredient guesses with reviewed native concepts

- Status: accepted
- Date: 2026-09-07

## Context

V84 still makes cinnamon hotter for bread than apple pie, and maps cocoa through coffee.
Butter is cold for apple pie despite ordinary pastry variants. The owner requested a
similar V85 batch of quality improvements, new concepts and realistic graph links.

## Decision

Add eight reviewed culinary concepts, 25 accepted forms and 40 specific links through
the shared graph transaction. Keep variant qualifications and authored direction explicit.
Retire only the synthetic Scorțișoară and Cacao rows; their accepted words now resolve to
real, distinct nodes. No replacement broad food/coffee scoring proxy is added. Preserve
unrelated projected surfaces, exact native owners and deliberate ambiguous-input exclusions.

Change the inherited ADR-0042 vocabulary-floor clause from at least 14 synthetic entries
per domain to at least 14 accepted, audited surfaces per domain. This is a change of the
audited representation, not a claim that synthetic-only coverage stays unchanged: the
ingredient projection count falls to 13. Explicit immutable native-replacement tuples
name the original domain and exact owner for Nucă, Drojdie, Scorțișoară and Cacao.
Every counted native word must resolve to that owner, have no synthetic collision and
contribute one unique normalized key. Native entries cannot invent a new unaudited domain.
The metadata has no runtime resolution or scoring role. Keep the former synthetic-only
471-row inventory and 14-word floor tested on restored V84 history.

Replace the exact existing Mucenici/Moldova relation whose description incorrectly calls
the Moldavian variant boiled. The reviewed replacement says baked, retaining endpoints,
relation type, strength and both directions. This is one factual correction in addition
to the 40 new links, represented by 41 added edge IDs and one removed ID.

Promote four Contexto rounds (Ecler, Amandină, Halva and Înghețată) and the Stafide→Brânză
Lanț round only after measured native feedback, independent bound judgments and the
existing critique/promotion gates. Four salience warnings receive explicit familiarity
justifications; no salience values are changed. The Lanț round has two real routes through
Pască or Poale-n brâu. Node additions are not automatically targets, recipes or boards.
Preserve session/request bounds and private answers; keep the eight previous pending holds.

## Consequences

Domain coverage survives a word's upgrade into the graph without manufacturing filler
projections. Specific ingredient paths replace known approximations, while remaining rank
noise and recipe variants stay disclosed. Historical evidence remains exact; current
expectations use the reviewed snapshot. Agent checks do not establish human enjoyment.
