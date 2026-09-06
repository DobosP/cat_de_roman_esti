# V80 Clătite target

Valid until: the bound candidate, game content or relevant runtime changes — then treat as history.

V80 promotes **Clătite** as `ct_gastronomie_320`, an easy gastronomie Contexto
round using the existing graph node. It follows [ADR-0111](../../adr/0111-promote-reviewed-clatite-target.md)
and the [pack-only workflow](../../PACK_ONLY_CONTENT_WAVES.md).

## Acceptance and remaining limits

V75 and V78 deferred this target because flour and Gem gave misleading feedback.
V77 repaired flour; V79 repaired Gem through a bounded private scoring policy.
A fresh one-row candidate, factual screen, quality screen and strict pending
critique now pass. Independent analyst and adversarial verifier judgments both
say `promote`, bound to the same pending dossier and current rubric.

| Ordinary guess | Hops / rank / feedback |
|---|---|
| Făină | 1 / 2 / Fierbinte |
| Ou | 1 / 5 / Fierbinte |
| Desert | 1 / 3 / Fierbinte |
| Dulceață / Gem | 1 / 7 and 8 / Fierbinte |
| Zahăr | 2 / 11 / Fierbinte |
| Lapte / Brânză / Smântână | 2 / 40, 30 and 22 / Cald |

The fresh capture includes 28 Clătite word probes, five Papanași controls and a
repeat/resume sequence. Incoming neighbors number nine, including the directed
Făină edge; the eight outgoing neighbors do not include Făină. Singular, plural,
accentless and inflected food answers win correctly. Public create seeds 20 and
46 select the new round, hide its answer, accept an ordinary warm guess and finish
with a server-scored win. These seed observations identify this artifact version.

Reviewers explicitly considered the remaining frozen Unt/Ulei/Miere/Nucă routes
and unresolved ciocolată/aluat. Those are still limitations. They judged that the
specific batter, filling, dairy and dessert paths now form a coherent easy round;
this is not a claim of complete vocabulary coverage or human enjoyment.

## Preserved content and selection impact

Pack stock grows **620→621**, approved **612→613**, with all eight existing pending
holds intact. Contexto stock becomes 210 total / 208 approved / two pending and
**204 eligible**. All 620 pre-existing rows, their quality scores/status/eligibility,
and all 336 frozen Intrusul/Perechi boards remain exact. KG nodes, edges, aliases,
180 puzzles, mobile payload, game/session logic and frontend assets do not change.
Only generated pack/ranking/derived metadata and the trusted catalog digest advance.

The new ranking row is global rank 52, score 83, weight 4. It moves 158 existing
Contexto ordinal ranks by +1 and changes only `ct_meme_net_064`'s global weight from
4 to 3. On the gastronomie/usor shelf, eligibility grows 8→9; Clătite has shelf
rank 9/weight 1, while the existing `ct_gastronomie_019` and `ct_gastronomie_127` weights rise 2→3 and 1→2.
These are private selection estimates, not human difficulty or enjoyment scores.

| Repeated selection sample | Changed between V79 and V80 |
|---|---|
| Other five games | 0/100 seeds and 0/30 September daily dates |
| Contexto, unfiltered | 65/100 seeds and 0/30 daily dates |
| Contexto, gastronomie/usor | 50/100 seeds and 3/30 daily dates |

All repeated runs against the same artifacts matched exactly. These samples measure
release-to-release selection changes, not repeat rates or every possible future
seed. V75's currently served Mici smoke uses seed 19 after seed 5 changed; Salată de
boeuf still uses seed 6. Historical review files and their original seeds are intact.

## Bound evidence and reproduction

- `gastronomie/candidates.json`, `verify_factual.json`, `verify_quality.json` and
  `FACTUAL_REVIEW.md`: frozen one-row batch and independent pre-staging screens.
- `analyst-review.json`, `verifier-review.json`, `VERIFIER_REVIEW.md` and
  `verdicts/`: raw independent judgments, exact pending dossier and serializer-built
  V2 promotion artifact. The importer staged one pending row; the applier promoted one.
- `runtime-openers.json`, `runtime-report.md`, `runtime-independent.json`,
  `runtime-probes.py.txt`: actual fixed-target API observations and reproduction.
- `artifact-delta.json`: only the new record, old metadata, exact weight change and
  before/after digests. The new tests reverse that delta and reconstruct all three
  complete prior artifacts by their original SHA-256, preserving older wave tests.
- `impact/final-receipt.json`, `impact/final-report.md`, captures and runners:
  independent preservation, deterministic selection and public API evidence.
- `IMPLEMENTATION_REVIEW.md`, `implementation-review.json`: independent acceptance
  of the artifact/provenance/test changes, with no remaining findings.
- `verification.json` and `review-manifest.json`: actual checks and source/archive hashes.

The candidate SHA-256 is
`87e8b3b4133a82c83542070f6f3228d7482b8e775d66fed660574148220e67dd`.
The pending dossier binding is
`sha256:dfa63711feac4a57e664e72420e73ae4d1a775382056e9c1e78f575fc06234b9`.
The current accepted record is approved; the archived pending dossier preserves
what the reviewers judged before the applier changed its status.

To reproduce the wave, use baseline commit `9c208a96628b3d92910637fa634d4c998fe0e67d`
in an isolated task worktree and follow the pack-only import, serialize/apply,
ranking, frozen-catalog and mobile export commands. Update the trusted catalog
pin only after proving the 336-board payload exact. Archived runner `.py.txt` files
can be copied to scratch as `.py`; adjust their recorded original paths. The
baseline-tree manifest identifies the exact files to restore from that commit.

The reviewers are independent Codex agents with Romanian source checks, not human
playtest participants. Cozonac and bread remain deferred; honest nut feedback is a
separate investigation. Public-beta external gates remain in [BETA_CANDIDATE](../../BETA_CANDIDATE.md).
No push, deployment, accounts enablement or production re-verification occurred.
