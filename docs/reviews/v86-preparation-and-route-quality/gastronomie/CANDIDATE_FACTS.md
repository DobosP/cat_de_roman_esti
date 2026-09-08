# V86 raw-candidate factual screen

Valid until: the raw candidates or applied graph change — then treat as history.

Reviewed 2026-09-08. Candidate SHA-256:
`5feb68e6782b735650ccc99a28ccae0e0dab8a1013b57105bafab3e034b91648`.
All six raw references have factual coverage in `verify_factual.json`. This reviewer
helped author the graph but did not select or author this root-selected raw pack
batch. Final separate dossier-bound analyst/verifier judgments remain mandatory.
This is a factual approval for pending staging, not an automatic promotion.

## Concrete targets and source support

| Ref | Target | Direct incoming count | Factual core |
|---|---|---:|---|
| contexto[0] | Brânză | 14 | Milk-derived food, known cheese types and familiar filled preparations |
| contexto[1] | Lapte | 14 | Ordinary food, dairy associations, glass and school/family-food contexts |
| contexto[2] | Savarină | 5 | Soaked cofetărie pastry whose defining new clue is whipped cream |
| contexto[3] | Frișcă | 5 | Sweet cream, cold storage, optional vanilla/powdered sugar and mixer |
| contexto[4] | Cremă de vanilie | 5 | Five actual ingredients: milk, sugar, vanilla, starch and yolk |

The live service verified all five target payloads without validation errors.
Counts use actual directed predecessors, not undirected degree. The labels are
concrete foods or fillings; Brânză and Lapte are ordinary generic food nouns, not
abstract category names substituted for a hidden thing. Generic cheese remains
distinct from the existing Telemea/Urdă targets; cream remains distinct from vanilla.

- **Brânză:** [the dictionary food definition](https://dexonline.ro/definitie/br%C3%A2nz%C4%83/325603)
  describes cheese prepared from coagulated milk. [The Pască recipe](https://jamilacuisine.ro/pasca-cu-aluat-de-cozonac-reteta-video/)
  and [Poale-n brâu recipe](https://jamilacuisine.ro/poale-n-brau-pas-cu-pas-reteta-video/)
  independently demonstrate familiar sweet-cheese filling contexts. This does not
  assert that every cheese is salty or that every type uses the same coagulant.
- **Lapte:** [the dictionary's food entry](https://dexonline.ro/intrare/lapte/30512)
  establishes the ordinary culinary sense; the same longstanding pastry recipes
  use milk as an ordinary ingredient without specialist explanation. The current
  freezer link is deliberately qualified: [Arctic's storage guide](https://www.arctic.ro/blog/idei-practice/congelarea-alimentelor-ce-mancare-se-poate-congela)
  lists selected milk variants and cautions that whole milk can change texture.
  No storage duration, health or infant-feeding advice is carried into the target.
- **Savarină:** [the original2013 recipe](https://jamilacuisine.ro/savarine-de-casa-reteta-video/)
  identifies the soaked pastry and whipped-cream decoration; [the later giant-savarina recipe](https://jamilacuisine.ro/savarina-uriasa-reteta-video/)
  continues that recognizable combination. The target's0.55 salience is below the
  easy warning floor and must be explicitly judged. Neither a low prior nor an
  agent's source check is evidence of human enjoyment.
- **Frișcă:** [Hendi's preparation guidance](https://www.hendi.ro/blog/cum-se-face-frisca-iata-cele-mai-simple-metode)
  distinguishes suitable sweet cream, chilling and beating from fermented sour
  cream. [The tested Chantilly recipe](https://www.dulceromanie.ro/mix-and-match/crema-chantilly)
  uses powdered sugar and actual vanilla seeds. These are flavored/sweetened
  variants; neither sugar nor vanilla nor a machine is mandatory for all whipped
  cream. The longstanding savarina recipe independently shows its familiar use.
- **Cremă de vanilie:** [the original Dr.Oetker recipe](https://www.oetker.ro/retete/r/crema-de-vanilie-cu-amidon)
  explicitly lists each of the five ingredient neighbors. [The original eclair recipe](https://jamilacuisine.ro/eclere-pas-cu-pas-reteta-video/)
  corroborates its familiar filling use. Egg-free or flour-thickened variants remain
  possible; the graph labels say some recipes rather than declaring universals.

No new target adds adult framing or alcohol-dependent value. Some historical pastry
recipes mention flavor extracts; those are not the defining graph route or the
content value offered to the anonymous Romanian audience.

## Refrigerator route: explicit refutation attempt

`lant[0]` is Frigider→Înghețată, optimal2. The live graph gives precisely two shortest
intermediates, with profile `(2 first hops, 2 minimum layer width, 2 intermediates)`:

1. Frigider → Frișcă → Înghețată: a stored chilled ingredient is used in a named
   ice-cream preparation. Hendi supports the first link; [the original caramel ice-cream recipe](https://www.auchan.ro/inspiratie-si-savoare/retete-cu-imagini/inghetata)
   folds beaten cream into the cold base before freezing.
2. Frigider → Congelator → Înghețată: some refrigerator models include a freezer
   compartment, which stores frozen dessert. [The original Beko manual](https://documents.beko.com/Refrigerator/7202947607/ro-RO/3450429551106844043.html)
   explicitly separates refrigerator/freezer shelves and names ice cream for the
   frozen compartment. The first edge says “unele modele”; it is not universal.

I challenged whether this merely hides a plausible direct refrigerator association.
In ordinary speech, an entire combined appliance can be called “frigider”, and a
player might therefore expect ice cream to connect immediately. That ambiguity
must remain explicit. The route does **not** establish the false claim that an
appliance called a refrigerator can never contain ice cream. The two-link optimum
counts authored direct relations under the game's existing rule; it is not an
absolute semantic distance or a physical-storage theorem.

I accept its factual eligibility for pending staging because the two intermediates
are distinct recognizable things, their links are specific and truthful, and the
freezer-compartment distinction is directly supported by the original manual.
Neither route depends on an invented intermediate or a false ingredient claim.
Final D2/D4 reviewers must still judge whether the ordinary-language ambiguity is
fair in play. If they reject it, keep the candidate out of approved stock rather
than broadening the graph solely to force this round through.

This file makes no claim about final selector eligibility, graded ranks, all-game
compatibility or new public round IDs. Those require the post-import dossiers,
independent judgments and actual public-API journeys.
