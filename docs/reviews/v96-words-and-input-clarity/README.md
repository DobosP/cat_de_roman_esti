Valid until: bound content, runtime or interface inputs change — then repeat affected checks.

V96 completes the drafts started at `15e7561`, from landed V95 main `1457786`.
The owner requested landing V96 and starting V97. Current verification/publication state
belongs in [STATUS](../../STATUS.md); [ADR-0154](../../adr/0154-expand-content-and-clarify-input-recovery.md)
records the implementation decisions. Original kickoff drafts, source notes and critique
remain historical evidence; their unapproved status describes that earlier stage.

| Game | Accepted V96 additions |
|---|---|
| Conexiuni | One normal board: parents/grandparents, drinks, opening for passage and sharpening |
| Cald sau Rece | Covor, with useful floor/home/vacuum-cleaner approaches |
| Lanț | Vanilie → Brânză through Poale-n brâu or Pască |
| Alchimie | Ostropel and Salată de fructe, two recipes each; an onward vegetable-patty sandwich recipe |
| Intrusul | Atmospheric phenomena versus the Moon |
| Perechi | Leaf–branch, dog–cat, banana–fruit and wheat–flour |

## Content and preservation

Three pack drafts passed independent factual/quality review, pending staging, exact
allocated-ID judgments and strict promotion. [Final public playthroughs](integration/pack/independent-final-api.json)
select all three normally and win, including both Lanț routes, with wrong/repeat/hint/GET
recovery checks. The new Lanț round has a wide beginner corridor; its captions remain
generic. No private edge explanation was mistaken for displayed text. Covor's missing
mobilă/textil/parchet/mochetă guesses remain vocabulary debt, not invented aliases.

The pack has 713 records, 705 approved and eight unchanged pending, with 543 eligible.
All 710 previous records are exact. Conexiuni gains seven per-game word exposures.
The 105 rejected Lanț records, 101 custom captions and shared KG remain exact.

[Quick installation](integration/quick/installation-receipt.json) preserves all 336 core
boards and 81 previous authored records/scores. The supplement now has 83 boards:
227 Intrusul and 192 Perechi in total. Both additions qualify as starters; fresh word
exposures are three Intrusul and four Perechi. Independent final audits cover all 83
winning replays and wrong/repeat/hint/GET recovery plus natural starter selection for
the additions. These are per-game exposures, not new shared KG nodes.

[Alchimie installation](integration/alchimie/installation-receipt.json) grows 247→249
concepts, 342→347 recipes and 143→145 discoveries. Alternative-result count grows 97→99;
intermediates 63→64. Chiftele de legume gains an onward use; both new results are terminal.
Every old concept/recipe and the eight starters, 96 supplies, twelve tiers and 32 goals
remain exact. Eight historical saved books retain earned progress.

Review found that an earlier Gourmandelle excerpt did not substantiate sandwich assembly.
The final factual reviewer directly inspected Daniela Niculi's original cooked-patty and
bread assembly; Gourmandelle is retained only for cooking support. The original recipe's
vegan title conflicts with eggs/dairy in its body, so the game makes no vegan claim.
Chiftele marinate remains excluded because it shadows an existing KG alias.

The existing eight-compatible-book limit is now full. V97 must settle a compatibility
design before further recipe changes; old saves cannot be dropped or limits silently raised.

## Input and recovery

Unknown Cald sau Rece guesses now clearly say that the word is outside the game's
vocabulary and no attempt was lost. Advisory spelling variants fill/focus the field;
they do not submit. Additional displayed-label checks reject remote alias-based matches
such as fier→fluier and reparație→pârâu. Exact meanings, confident corrections, reviewed
projections, ranking, scoring and target/proxy privacy are unchanged.

The initial similarity-only rule also removed useful Nuci and Prafzz suggestions. The
refined rule retains one substitution, adjacent transposition, an entire displayed word
plus one/two trailing keystrokes, or normalized similarity of at least 0.82. All 174
focused input/feedback cases pass; original failures and their resolution are preserved.
The filter can still withhold a useful alias-based hint, an explicit conservative tradeoff.

Alchimie restores the activated usable ingredient after a lost combine response is read
back successfully. When inputs are depleted, focus moves to the collection. A player who
moved focus elsewhere keeps it. Focus queues only after successful adoption, retaining
save-ownership, game/generation and request-lock checks. Mutations are never replayed,
and V95's cached acknowledgments retain synchronous centering.

[Independent UI review](integration/alchimie/independent-ui-review.json) records 60 backend
cases, 12 desktop/mobile journeys and direct API probes over both new and preserved
suggestions. It checks committed/uncommitted response loss, moved focus, depleted inputs
and 320px doubled text. An initial test matched the visible message and hidden announcer;
the corrected locator targets the visible card. Browser evidence does not establish
physical-device acceptance or human enjoyment.

## Evidence

[Five core artifact inverses](artifact-delta.json) restore exact V95 bytes before historical
checks. [Target-profile proof](integration/contexto-profile-delta.json) preserves all 263
old profiles and adds only Covor. The browser seed snapshot changes only Lanț.
[Closure audit](integration/closure-audit.json) checks catalogs, approvals, runtime bindings,
three V2 dossier reconstructions, historical preservation and unchanged kickoff evidence.

[Integration archive](integration/archive-manifest.json) records exact source/archive
bytes, with lossless compressed logs and Python scripts retained as text. Environments,
browser caches and unbound trace ZIPs remain scratch. [Final verification](integration/verification.json)
records the assembled tests and exact installed artifacts. [Initial kickoff verification](kickoff-verification.json)
and [original archive](archive-manifest.json) remain separate from final acceptance.
Production remains the existing anonymous V91 deployment; landing is not deployment.
