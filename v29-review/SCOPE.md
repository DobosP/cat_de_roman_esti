# V29 working scope — extended beginner words

Status: V29 graph implemented and final-bound; no board or promotion changed.

## Freeze point

V28 is committed and landed on both local mains. V29 remains isolated on
`feat/basic-words-v29`; its 17-concept breadth wave must stay separate from the pending
board-remediation queue below.

## Proposed bounded wave

Keep the historical v24 benchmark at 234/234 and add a separate 17-term extension:

| Domain | First-class concepts |
|---|---|
| Animals | Câine, Pisică, Porc, Găină |
| Clothing | Haină, Cămașă |
| Kitchen/table | Cuțit, Pahar |
| Body | Gât |
| Time/routine | Minut, Secundă, Noapte, Weekend, Calendar |
| Everyday society | Cumpărături, Coleg, Trotuar |

The final catalog has 66 conservative inflection aliases: 83 normalized canonical
and alias surfaces in total, with no collision against v28 and no intra-wave collision.
Accentless spellings remain resolver-normalized rather than duplicated as aliases.

## Sense guardrails

- Keep animal nodes distinct from meat, dishes, titles, and composite meme/story nodes.
- `Haină` does not claim adjective `hain`; `Cămașă` does not absorb `Ie`.
- `Cuțit` is the tool, not a TV-title alias; `Gât` excludes bottle/idiom senses.
- `Coleg` does not imply `Prieten`; `Calendar` does not absorb bare `Dată`.
- Defer `Somn`, `Duș`, `Pod`, `Burtă`, and `Braț` because normalization or ordinary
  homonymy cannot select one honest sense.

## Acceptance contract

- Resolve the 17 canonical terms exactly and all 66 aliases to one declared owner.
- Give every node at least four incident links, two same-category links, two forward
  choices, and one incoming cue; all 64 links pass, with no generic `related_to`.
- Add no curated board and perform no promotion. Keep both 794-item pack mirrors
  byte-identical at SHA-256 `2c7d2eb…023`.
- The exact-33 and full-222 JSON reports are byte-identical before/after; the two reviewed
  Contexto targets that gain a strong neighbor do so through `Mâncare → Cuțit` and
  `familie → Weekend`, with no finding.
- Preserve the two-hour sliding session TTL and 1,000-session cap.
- Regenerate and independently verify the public mobile contract if the graph changes.

## Review baseline

The final V29 graph produced 33 version-bound dossiers under `dossiers/`; deterministic
critique is 33 checked, 0 flagged, 0 FAIL. These are a regression baseline, not promotion approval.
The analyst pass also tracks generic Lanț route labels and arbitrary Alchimie recipes as a
separate remediation queue so v29 does not hide existing frustration behind added breadth.

A separate read-only topology audit identified 30 explicit directed links and 22 safe
normalized alias keys for existing weak-route concepts. Its simulation introduced no
finding across the exact 33 or all 222 pending items, but `A scrie → Creion` has a broad
Contexto-distance effect and needs aggregate reprofiling. Keep that catalog as a follow-up
queue; do not silently combine it with the 17-node wave before the v29 scope is reviewed.
