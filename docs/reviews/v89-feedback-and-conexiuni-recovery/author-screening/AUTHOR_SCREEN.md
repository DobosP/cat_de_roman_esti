# Household target author screen

Valid until: final bound V89 judgments supersede these proposals — then treat as history.

Author: `v89_household_author`; checked 2026-09-08. These are eight private-target
BFF screens, not public selection, approval or human acceptance. No graph, scorer,
pack or generated fixture was edited by the author. The complete first-guess screen
uses 32 ordinary/control words per target. Eight journeys additionally check private
initial state, three unrelated guesses, a warmer clue, clue resume, a natural opener,
uppercase repeat, history resume, exact win and terminal score persistence.

## Initial results and proposals

| Target | Direct neighbors | Defining approaches in actual BFF | Author disposition |
|---|---:|---|---|
| Făraș | 5 | Mătură #4, Podea #2; projected Praf #2256 frozen | Potential easy round after dust feedback repair |
| Mop | 6 | Podea #2, Găleată #8, Detergent #10, Apă #7, Mătură #6 | Strong core; include dust repair (#1528 very cold) |
| Aspirator | 5 | Podea #2, Mătură #4, Covor #36; projected Praf #2022 frozen | Potential easy round after dust feedback repair |
| Burete de vase | 5 | A spăla #3, Detergent #4; Farfurie #212 lukewarm | Hold unless dish-specific neighborhood is repaired and reviewed |
| Mătură | 4 | Făraș #4; Praf #2256 frozen | Hold: four neighbors, dust cue missing |
| Găleată | 4 | Apă #2, Mop #6 | Hold: only four direct neighbors |
| Detergent | 4 | A spăla #3, Burete de vase #4, Apă #5 | Hold: only four direct neighbors |
| Taburet | 4 | Scaun #2189 frozen; Pian #2 | Hold: expected chair cue fails, four neighbors |

The first four clear recognition and salience screens, but C3 is a legibility
requirement as well as a count. Făraș/Aspirator share weak generic cleaning edges
with Burete de vase; these are not five equally defining incoming cues. Most floor
inputs are still mediated by the existing Podea proxy, and Burete/Detergent by
A spăla. Those actual responses, rather than raw one-hop claims, inform the screen.
No broad Casa/Aspirator mapping is proposed.

The exact `praf` projected surface currently uses the Pământ landscape anchor.
It therefore misses the everyday settled-dust sense directly described by the
Făraș and Aspirator labels. A bounded, nonwinning dust neighborhood for all three floor tools is a supported
repair proposal; it must keep the existing projected ID and Pământ fallback for
other targets. This proposal does not transfer all earth, soil or powder cues.

Bare `curățenie`, `burete`, `vase`, `gunoi`, `perie` and `motor` are unresolved in
this screen. Unresolved `burete` is not a reason to steal an alias: dictionary senses
include fungi, marine sponges and absorbent cleaning material. The qualified
Burete de vase label has a clear household sense; weak dish feedback is its blocker.

All eight technical journeys pass. Floor-tool warmer clues are Podea; sponge and
detergent show A spăla; bucket shows Apă. Taburet shows Dinu Lipatti #4 before the
chair opener stays frozen, so successful completion cannot establish fair gameplay.
Mop's unrelated Sarmale #52 warm and room/furniture noise remain disclosed; no claim
is made that the graph approximates human semantic rankings uniformly.

## Primary factual and recognition sources

- **Făraș:** the [CADE definition (1926–1931)](https://dexonline.ro/definitie/f%C4%83ra%C8%99/1341866)
  describes the small collecting scoop used after sweeping. Current
  [Leifheit dustpan-and-brush instructions](https://leifheit.ro/ro/acasa/164-leifheit-set-maturafaras.html)
  describe collecting fine dust and storing the two implements together. These two
  signals support enduring ordinary household recognition, Mătură and dust approaches.
  They do not make a sponge a defining dustpan part.
- **Mop:** [DEX 2009 and DOOM 2005/2021](https://dexonline.ro/definitie/mop)
  independently establish the named household floor-washing tool and normal plural.
  Current [Vileda Turbo](https://www.viledaromania.ro/spin-mops/turbo-spin-mop)
  directly describes a mop, bucket, rinsing and hard-floor use.
  [Vileda's cleaning instructions](https://www.viledaromania.ro/turbo) confirm water
  and optional cleaning solution. These substantiate the core approaches without
  claiming every mop requires detergent or a bucket (steam/spray variants exist).
- **Aspirator:** [DEX 1998/2009 and older dictionaries](https://dexonline.ro/definitie/aspirator)
  document the dust/smoke/gas suction apparatus. Current
  [Kärcher household vacuum description](https://www.karcher.com/ro/ro/home-garden/aspiratoare.html)
  specifically describes dust collection, hard floors and carpets. Ordinary household
  sense dominates this category, although industrial and nasal uses exist. Covor is
  a valid approach; water is not a universal requirement of ordinary dry vacuums.
- **Burete de vase:** [DEX 2009](https://dexonline.ro/definitie/burete) distinguishes
  biological/fungal meanings from porous absorbent cleaning objects, motivating the
  existing qualified label. Current
  [Vileda PUR Active Colors](https://www.viledaromania.ro/ScourersAndSponges/Vileda-Bure%C8%9Bi-PUR-ACTIVE-Colors-4-1-/p/149444)
  names dishes, cookware, cutlery, sink rinsing, water and soap.
  [Vileda PurActive](https://www.viledaromania.ro/ScourersAndSponges/Vileda-Glitzi-PUR-Active-pentru-cl%C4%83tire-/p/129706)
  independently specifies kitchen pans/pots and absorbency (same manufacturer, not
  a second independent recognition signal). Genuine Farfurie/Chiuvetă cleaning links
  would be worth considering on their own; the current five-node count is not enough.
- **Dust sense:** [DEX 1998/2009 and DLRLC 1955–1957](https://dexonline.ro/definitie/praf/definitii)
  distinguish fine particles suspended in air or settled on things from qualified
  powders. This supports home dust while preserving the landscape association elsewhere.

Recognition is an evidence-backed editorial judgment from longstanding dictionary
entries and current first-party household usage, not measured population familiarity.
No polls, pageview measurements, classroom tests or Romanian-player sessions were run.

## Tooling correction and evidence

The first author script incorrectly supplied the requested category as `_build_session`'s
third positional `daily` argument and counted responsive distances through four hops.
The actual runtime responsive limit is five. The first journey therefore received a
category clue and stopped at the author's warmer-stage assertion. No production or
runtime code failed. Original scripts and first-guess output are preserved under
`initial-*-wrong-private-setup.*`; corrected scripts use `daily=None` and the explicit
`category='viata_de_roman'` keyword and retain complete, source-bound fresh outputs.
Only the corrected 256 observations and eight successful journeys count as baseline
acceptance evidence. The earlier 256 are diagnostic history, not additive coverage.
