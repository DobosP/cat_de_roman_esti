Valid until: draft content or the baseline changes — then repeat affected checks.

V96 starts from landed V95 main `14577863038378c734c7b2e0e8b33ea8158f318b` after the
owner asked to land V95 and start the next version. [V95 CI passed](https://github.com/DobosP/cat_de_roman_esti/actions/runs/35026423470).
This is an initial creation and
critique session. Drafts are unapproved and do not change the served inventory.

The starting inventory is 710 curated pack records, 417 quick boards and an Alchimie
world with 247 concepts, 342 recipes and 143 discoveries. All previous review gates,
wording/source checks, saved-progress guarantees and capacity limits still apply.
Only nine Alchimie concept slots remain below the existing 256-concept limit.

The content work starts with concrete drafts for Conexiuni, Cald sau Rece and Lanț,
plus Alchimie recipes/concepts and new Intrusul/Perechi boards. Novelty checks include
served content, previous raw proposals and durable rejection records. Natural selection
and actual displayed descriptions matter alongside mathematical solvability.

The interface critique focuses on two remaining observed issues: ordinary guesses that
Cald sau Rece does not recognize, and keyboard focus returning to the page body after
some Alchimie recovery paths. The latter predates the V95 stale-focus fix. Candidate
improvements need fresh interaction evidence and a comparison with relevant official
interfaces/rules before implementation choices are settled.

## Initial content queue

| Game | Unapproved draft |
|---|---|
| Conexiuni | Parents/grandparents, drinks, purpose-qualified opening and sharpening groups |
| Cald sau Rece | Covor, with floor, home and vacuum-cleaner opener checks |
| Lanț | Vanilie → Brânză through Poale-n brâu or Pască |
| Alchimie | Ostropel and Salată de fructe, two routes each; one proposed onward Sandviș recipe |
| Intrusul | Atmospheric phenomena versus the Moon |
| Perechi | Leaf–branch, dog–cat, banana–fruit and wheat–flour |

[Pack authoring](pack/README.md) records source checks, novelty and conditional selection.
Those in-memory playthroughs do not establish installed serving or independent approval.
[World/quick authoring](content/draft-notes.md) records two concepts and five recipes,
plus one board for each quick game. Chiftele marinate was excluded because it already
resolves to the existing Chiftele identity. The vegetable-patty sandwich generalization
still needs independent factual review. The new world would require an eighth saved-book
compatibility generation and would retain seven free concept slots.

These drafts must pass separate factual/quality reviews and final runtime audits before serving.
Current publication and verification state belongs in [STATUS](../../STATUS.md).


## Interface queue

[The fresh critique](critique/README.md) compares all six games with relevant official
interfaces/rules and records three priorities:

1. Say clearly that unsupported Cald sau Rece words cost no attempt, and avoid weak
   spelling suggestions that imply an unrelated intended word.
2. Restore deliberate keyboard focus after Alchimie reconciles a lost response.
3. Add independently reviewed descriptions for the eight earned links in V95's new
   Lanț rounds, without revealing later steps.

All six mobile starts already keep their main controls visible. The critique does not
justify another general menu rebuild. Missing vocabulary cannot be repaired by mapping
unrelated words to existing identities. Browser emulation is not physical-device or
human-enjoyment acceptance.

## Evidence and continuation

[Baseline receipt](baseline.json) binds the ten unchanged landed artifacts and verified
V95 cleanup. [Archive manifest](archive-manifest.json) binds the draft and critique files.
[Kickoff verification](kickoff-verification.json) confirms those bytes and unchanged serving artifacts.
Next work is independent raw review, resolution of the documented source/wording questions,
and concrete implementation of the selected interface improvement. No pending draft is
silently treated as approved, and no V96 branch publication is authorized by this kickoff.

[V95 publication verification](v95-ci.json) records all three successful GitHub jobs on
the landed main commit. V96 remains local and its drafts remain unapproved.
