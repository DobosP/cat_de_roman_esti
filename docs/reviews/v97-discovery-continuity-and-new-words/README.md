Valid until: reviewed content or implementation inputs change — then repeat affected checks.

V97 completes the owner-requested content and game-quality session from landed V96
`fd3ca7c78b6bee774c283d873d400abf4a8e7d65`. Five new rounds/targets, two Alchimie
preparations with four recipes, and twelve clearer Lanț captions passed independent
review and guarded installation. Current release and landing state belongs in
[STATUS](../../STATUS.md); production deployment is separate.

The [original kickoff](kickoff-README.md) remains preserved. Its initial `36db143`
baseline has identical content/runtime bytes to `fd3ca7c`; the intervening V96 change
corrected a browser interception test. All 65 records in the original
[archive manifest](archive-manifest.json) remain exact. Original drafts and conditional
probes are historical authoring evidence, not the final approval receipts below.

## Reviewed additions

| Game | Installed addition |
|---|---|
| Conexiuni | Male family roles, facial parts, filled recipes and electric variants |
| Cald sau Rece | ușă; seven native predecessors, useful home/bathroom/intercom/key openers |
| Lanț | Cacao→Lapte through Înghețată or Chec; both shortest routes win |
| Alchimie | Supă de roșii and Mâncare de spanac, two recipes each |
| Intrusul | Frate/Soră/Unchi versus Vecin |
| Perechi | Perete–Tavan, Metrou–Tramvai, A găti–Bucătărie, Examen–Lecție |

The pack now has 716 records: 708 approved and eight earlier pending holds. All 713
previous records are exact. Conexiuni gains nine fresh per-game exposures; Intrusul
gains four and Perechi eight. These are new uses of existing KG words, not new graph
nodes. All 264 earlier Contexto distance profiles and all 105 rejection-ledger records
remain exact. The [five-artifact inverse](artifact-delta.json) restores exact V96 bytes.

The quick catalog has 421 boards, including 85 authored boards. All 83 previous
authored records/scores and all 336 core boards remain exact. Both new boards qualify
as starters. Independent public replays cover all 85 wins plus the new starter,
wrong-answer, repeat, hint and GET recovery journeys.

## Saved progress and clearer connections

Alchimie now has 251 concepts, 351 recipes and 147 discoveries. All 249 earlier concepts
and 347 recipes remain exact. Nine complete historical books preserve earned progress;
the finite limit increases from eight to sixteen under [ADR-0155](../../adr/0155-preserve-discovery-history-and-explain-food-links.md).
The 2 MiB cap remains and is checked before generator writes. The installed artifact is
818,957 bytes. No history is evicted; all other capacities remain unchanged.

The final world audit covers 351 recipes, 33 free/goal runs and 1,009 saved prefixes
across all nine histories. It rejects 347 attempts to claim newer recipes under old
books. Independent tests exercise sixteen valid histories, reject a seventeenth and
check the exact byte boundary without replacing existing files.

Twelve reviewed food captions explain the two representative routes in each earlier
round `lt_gastronomie_243`, `244` and `245`. All 101 earlier captions stay exact. The
phrases bind complete edge snapshots; fourteen existing directions display them and
ten nonexistent reverse directions stay unavailable. Recipe variants and optional
ingredients remain qualified. Browser checks cover choices, keyboard use, earned paths,
GET/reload and 320px screens with doubled text.

## Evidence and limits

Final factual/quality receipts, allocated analyst/verifier dossiers, guarded installation
receipts and public API audits are archived under [integration](integration/archive-manifest.json).
Integration test counts and exact gate inputs are recorded in
[verification.json](integration/verification.json). Initial failed development assertions
remain archived alongside their corrections; they are not reported as passing checks.

Four plausible Ușă guesses—intrare, toc, balama and lemn—are still missing vocabulary;
they cost no attempt. The new Cacao→Lapte round still has four generic captions.
Chec→Lapte is supported as serving together, not asserted as a universal ingredient.
Both new Alchimie dishes are terminal; five concept slots remain under the existing
bound. These are concrete V98 review priorities. No older pending queue is silently
approved, and automated journeys do not establish human enjoyment.

## Linux resumption and final verification

The September 22 pickup found the earlier root integration unfinished: its browser run had
485 passes and 67 failures. The reviewed content remains exact. [Resumption evidence](resumption/README.md)
records the browser history-bound fix and one-time persistent-error reveal, including
preserved failures and independent review. The final assembled candidate passes 2329
backend/53 accounts on both Python versions, 214 native frontend and 552 browser checks.
The old static-caption receipt remains historical; the complete current browser suite
covers the rebuilt assets. V97 is verified locally and remains unlanded.

## Local landing (2026-09-23)

V97 application and evidence commit `f783a97e6eabaf59cd6360853723956b58a5aac6`
is merged into local main. The owner confirmed starting V98 afterward. The earlier
candidate publication flags describe their capture time; [landing.json](landing.json)
records the actual local merge and unchanged verified inputs. No push or deployment
is included. Only this merged task's worktree, branch and scratch are cleaned.
