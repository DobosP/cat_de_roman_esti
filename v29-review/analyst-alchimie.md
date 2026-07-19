# V29 analyst pass — Alchimie (proposals only)

These are rubric-A/E quality proposals bound to the v28 dossiers. They do not mutate
the pack and are not promotion authority.

## `al_literatura_097`

- Binding: `sha256:b3bebc620ec0547ad1b9630698d29491dda1dcd708d21c4f90ae653f06a343f7`
- Proposal: `reject` and remint a narrower literature recipe.
- Recognition and theme are strong, and several story-pair openings are understandable.
  However all 15 possible seed pairs open, closure reaches 136 concepts, and the target
  appears at generation 2. This fails E5's bounded-choice requirement: almost any pair
  works, so the player discovers the graph's broad `Carte/Poveste/author` overlap rather
  than a purposeful recipe. The final `Tinerețe... + Poveste → Făt-Frumos` step is also
  generic rather than uniquely inferable (E3).
- Rescue: retain the fairy-tale theme but remint seeds/edges so only a few character or
  author predicates open and the Făt-Frumos route is specific.
- Verifier checks if reminted: cross-generational recognition and exact authorship of the
  chosen tales/characters.

## `al_viata_de_roman_098`

- Binding: `sha256:49782468132023176a56d2d71db79bd464f0e37f20907ea25ff5635233e15a8d`
- Proposal: `reject` and remint.
- The seeds are recognizable childhood games, but most productive pairs collapse into
  generic `Jocuri de copilărie` or `Copilăria anilor 90`. The last combination returns
  six unrelated nostalgia nodes, only one of which is the target. The recipe therefore
  is not inferable (E3), and closure 111 is noisy for one generation-2 target (E5).
- Rescue: require a communication/whisper/line-of-players route distinctive to
  `Telefonul fără fir`, not a generic nostalgia intersection.
- Verifier checks if reminted: sustained Romanian recognition of the selected games.

## `al_viata_de_roman_099`

- Binding: `sha256:09803278473a44f0e1f2602ce02879fbb58e3ecb7f518d83e86717d223a17feb`
- Proposal: `reject` and remint.
- The home/school seed mix contains obvious filler (E1). `A dormi + ușă → Dormitor` is
  arguable, but `Dormitor + ușă → Pernă` is arbitrary; the target route fails E3.
- Rescue: use `Pat`, `Saltea`, `Pătură`, `Cearșaf`, and `A dormi` with an explicit bedding
  predicate, then recheck that at least two openings are intuitive and no pair is free.

## `al_viata_de_roman_100`

- Binding: `sha256:c65b96a01d8abf3ac310e928238637f72e0467e94fd8a9516777254eb599ff66`
- Proposal: `reject` and remint.
- School items are filler, while the recipe uses `ușă` repeatedly to transform Dormitor
  into Pernă and then Pernă into Fotoliu. Those outcomes are not predictable (E1/E3).
- Rescue: use seating/living-room concepts with explicit `mobilier pentru șezut` and
  `se află în sufragerie` relations.

## `al_viata_de_roman_101`

- Binding: `sha256:d683a7b01909a67f0a62fe60571bed3513109dd1332b129780ed98ae902db697`
- Proposal: `reject` and remint.
- The target Sufragerie is familiar, but the mixed school/home seeds are incoherent and
  the route `Pat + ușă → Pernă`, then `Pernă + ușă → Fotoliu`, then
  `Fotoliu + ușă → Sufragerie` treats `ușă` as a magic ingredient (E1/E3).
- Rescue: compose the room from recognizable living-room furniture instead.

## `al_viata_de_roman_102`

- Binding: `sha256:e2043262c262e59e4cfbf7f88bde67bf3b11a4cf12241980e30fc5f69cf806d9`
- Proposal: `reject` current payload; remint from its promising school route.
- `Caiet + Creion → Temă`, `Clasă + Caiet → Lecție`, and `Temă + Lecție → Examen` form
  the strongest intuitive recipe in this batch. But `A dormi`, `Pat`, and `ușă` are
  irrelevant filler, failing E1 and making many openings unrelated to the target.
- Rescue: replace the three home fillers with `Elev`, `Profesor`, and `Carte`, then
  regenerate and re-evaluate closure, openings, and free-answer risk.

## `al_viata_de_roman_103`

- Binding: `sha256:f36ed2a31eb76cc00c77d8d0bb3da3b65a95b0b150ca63ccd385dc6de9bb16bf`
- Proposal: `reject` and remint.
- The final school chain toward Catalog școlar is plausible, but `A dormi`, Sufragerie,
  and `ușă` are filler and generate an unrelated home branch. Seed coherence fails E1.
- Rescue: keep the assessment chain and replace home fillers with school roles/objects;
  require a specific `Profesor/Elev/Note → Catalog școlar` final predicate.

## `al_viata_de_roman_104`

- Binding: `sha256:1b05d74d2dc5dda7a6d93adfcc03e92851888064b0a4840ccb225b959da92d7d`
- Proposal: `reject` and remint.
- Mixed school/home seeds fail E1. The only target recipe again relies on
  `Dormitor + ușă → Pernă` and `Pernă + ușă → Covor`, neither of which is inferable (E3).
- Rescue: use Floor, Cameră, Sufragerie, Mobilier, and textile/cleaning concepts with an
  explicit floor-covering route.

## Batch conclusion

All eight stay pending during v29 discovery. Seven have clear semantic/seed failures;
the literature item has excellent recognition but still fails bounded-choice and route
specificity. No web claim can rescue the current mechanical failures; web verification
belongs after reminting any candidate that survives.
