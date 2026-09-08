# ADR-0117: Food input forms and bounded feedback in one playable batch

- Status: accepted; exact-target inventory extended-by ADR-0123
- Date: 2026-09-07

Partially supersedes ADR-0110 only for the two additional exact-target Gem associations.

## Context

V82 deferred five familiar targets because core filling, salt, oil or pepper guesses were
cold. It also found missing ordinary grammatical forms. These are related player-input
problems that fit one batch under ADR-0113 rather than separate versions for every repair.

## Decision

Add exactly 24 independently reviewed grammatical/qualified forms across eight existing
food concepts using the shared V24 transaction. Preserve earlier bare-form exclusions and
all existing surface owners; count these as forms, not new concepts or synonyms. Keep the
graph's nodes, edges and puzzles unchanged apart from alias additions and build metadata.

Use six explicit Contexto-only, exact-target associations: Gem to Cornulețe/Gogoși, Ulei to
Gogoși/Cartofi prăjiți, Sare to Telemea, and Ardei to Ardei umpluți. Preserve each submitted
identity and exact-self win; the existing scorer keeps these associations nonwinning with
rank at least two. Do not traverse the targets' neighbors or extend these facts to unrelated
targets. Ordinary baked/no-oil and unfilled variants remain disclosed recipe exceptions.
Existing native/projection fallback, Gem's reviewed preserve neighborhood, Nucă and Burtă
policies, private answers and all session/cache bounds remain protected.

Promote the five frozen batch records `ct_gastronomie_329`–`333` after fresh source, input,
gameplay and complete independent dossier-bound reviews unanimously accepted each member. Preserve all
old pack records, approval/eligibility and frozen boards; record the resulting selection
changes. The candidate names are Cornulețe, Gogoși, Telemea, Cartofi prăjiți and Ardei umpluți.

## Consequences

The accepted content outputs are five playable rounds, six corrected feedback pairs and
24 forms. Full integration remains a separate completion gate; quantities do not justify
accepting weak content. Native exact-target associations and explicit projection target lists are closed
reviewed data, not synonym mappings or a general permission to assign arbitrary heat.
