# Independent linguistic and safety review: `Paște` / `paștele`

Valid until: the V76 Romanian input-sense implementation lands — then treat as history.

## Scope and verdict

This review covers only whether the explicit accented Romanian forms `Paște` and `paștele` may bind the existing gastronomy node `n_v3gas_paste` (`Paste`, aliases `paste făinoase`, `pastele`), and the code paths needed to enforce that distinction consistently.

**Verdict: approve the bounded proposal, with the implementation conditions below.** The accented forms must not resolve, score, or move as the pasta node. The accentless forms `paste` and `pastele`, and qualified compound aliases such as `paste făinoase`, must continue to resolve normally. `Paște` must not be proxied to `Masa de Paște`, because a holiday and a holiday meal are different concepts. Adding a holiday node is outside this wave.

## Linguistic evidence

The source-specific DOOM 3 entry records the religious holiday as **Paște/Paști**, with articulated forms **Paștele/Paștile**. The same entry gives holiday uses such as “De Paște” and “Paștele cade…”. This establishes that `Paște` and `paștele` are legitimate accented forms, but for the holiday sense rather than pasta:

- DOOM 3 (2021), `Paște`: https://dexonline.ro/definitie/pa%C8%99te/1258487

The source-specific DOOM 3 entry for **pastă** gives the plural **paste**, without `ș`. DEX '09 likewise defines **pastă**, plural **paste**, and identifies **paste făinoase** as wheat-flour dough food products:

- DOOM 3 (2021), `pastă`: https://dexonline.ro/definitie/past%C4%83/1280847
- DEX '09, `pastă`: https://dexonline.ro/definitie/past%C4%83/866867

The broader dictionary record also assigns `Paște/Paști` to the religious holiday and, in some dictionary senses, consecrated bread/pască. Neither accented sense denotes the `Paste` pasta node:

- DEX/DOOM entries for `paștele`: https://dexonline.ro/definitie/pa%C8%99tele

Thus Romanian diacritics distinguish the relevant concepts here:

| Input | Legitimate sense relevant to this review | Pasta-node result |
|---|---|---|
| `Paște`, `paștele` | religious holiday; dictionaries also record a consecrated-food sense | reject as `n_v3gas_paste` |
| `paste`, `pastele` | plural / articulated plural of `pastă` | preserve |
| `paste făinoase` | explicit pasta compound | preserve |

`paște` may also occur as a form of the verb *a paște*. That additional ambiguity reinforces the conclusion: the accented token is not evidence for the pasta sense.

## Current behavior reproduced

The repository's general normalizer decomposes Unicode, removes combining marks, case-folds, and collapses whitespace. Consequently, all of these currently collapse to the pasta lookup keys and resolve to `n_v3gas_paste`:

- NFC `Paște` and `paștele`
- uppercase `PAȘTE`
- decomposed `Pas\u0326te`
- legacy cedilla `Paşte` and `paştele`

The ordinary forms `paste`, `pastele`, and `paste făinoase` also resolve to the pasta node, as intended. `pastele de dinți` resolves to its separate toothpaste node, showing why the exclusion must match the complete input surface rather than a prefix.

The exact reproduction inputs and outputs are saved in [current-behavior.json](./current-behavior.json); the small read-only harness is [reproduce.py](./reproduce.py.txt).

No standalone holiday node is present. The graph contains `Masa de Paște`, which is not a semantically valid substitute for the holiday. A rejected `Paște` input should therefore remain unknown and should not change game state.

## Required implementation boundaries

The existing accent-folded `normalize()` result cannot distinguish `paște` from `paste`, so the current normalized-key fuzzy-denial mechanism is not sufficient. Use a narrow raw-surface sense check that preserves Romanian diacritics while canonicalizing representation:

1. Apply NFC or NFKC, case-folding, and existing whitespace trimming/collapse.
2. Treat Romanian legacy cedilla `ş/Ş` as equivalent to comma-below `ș/Ș`.
3. Match only the complete canonical surfaces `paște` and `paștele`.
4. Do not prefix-match or deny their accentless forms.

The guard must run before every actionable resolution route:

- ordinary exact resolution;
- fuzzy resolution, before its accent-insensitive exact-index lookup;
- Contexto projection or fallback suggestions, so rejection by the KG resolver cannot fall through to an unrelated projected concept;
- Lanț visible-neighbor/local disambiguation, including `_resolve_neighbor`, which currently compares accent-folded labels before generic resolution and can move to the pasta node from valid predecessors.

The advisory path needs the same semantic boundary. Current suggestions for `Paște` include `Paste`, and projection fallback can offer unrelated approximate words. For either denied accented surface, the bounded safe response is an unknown result with no pasta suggestion and preferably no fallback suggestions. Suggesting `Paste` asks the player to change the spelling into another sense.

## Behavioral acceptance matrix

| Case | Expected behavior |
|---|---|
| `Paște`, `paștele` | unknown; no score, guess, history, or move mutation |
| `PAȘTE`, mixed case | same rejection |
| decomposed comma-below spelling | same rejection |
| legacy cedilla `Paşte`, `paştele` | same rejection |
| `paste`, `pastele` | resolve to pasta as before |
| `paste făinoase` | resolve to pasta as before |
| other compounds such as `pastele de dinți` | preserve their existing whole-input resolution |
| Contexto advisory response for denied forms | do not suggest `Paste` or an unrelated projection as a substitute |
| Lanț with pasta as a visible/legal neighbor | denied accented forms do not select or move to pasta |
| `Masa de Paște` | preserve its existing exact node resolution |

Tests should exercise the actual game routes for non-mutation as well as resolver units. Lanț needs an explicit route or state-level regression because its local visible-choice path bypasses the ordinary resolver. Uppercase, composed/decomposed Unicode, and comma/cedilla spellings should all be covered.

## Limitations

This is an independent agent review based on authoritative Romanian dictionary editions and the current repository code and fixture. It is not a human Romanian-language SME judgment. The DOOM 3 evidence was accessed through dexonline's source-specific permanent entries because the direct `doom.lingv.ro` search interface did not render successfully in the available tooling. No repository files were edited, no implementation was tested, and no broader policy for Romanian diacritics was evaluated.
