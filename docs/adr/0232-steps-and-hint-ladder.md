# ADR-0232 — Steps and the hint ladder

- Date: 2026-11-16
- Status: accepted by Paul; in implementation on `feat/redesign-v2`
- Amends the hint and scoring rules of all six games and the hint sections of
  [MOBILE_CONTRACT](../MOBILE_CONTRACT.md); keeps every operationId ([ADR-0003](0003-mobile-contract.md)).
- Companion: [ADR-0233](0233-redesign-v2-interface.md) (interface). Board comparison: ADR-0234 (reserved).

## Decision

Points stop being shown. A round's outcome is a count of **steps**. Hints become a ladder of at
most three rungs per round, available at any time, each costing one step and never a life.
Owner answers, 2026-11-16 (quoted): "Undo free, jumps still count"; "Count every new pair";
daily level "Ușor"; parity "Update the Python copy"; new parity count "Yes, new count is fine".

### Steps (normative)

| Game | Steps | Free | Perfect |
|---|---|---|---|
| Intrusul | wrong picks + hints | repeated pick | 0 steps on a win |
| Perechi | wrong pairs + hints | repeated wrong pair | 0 steps on a win |
| Conexiuni | wrong groups (incl. one-away) + hints | repeated combination | 0 steps on a win |
| Cald sau Rece | accepted guesses incl. the winning one + hints | unknown word, repeated word | none |
| Lanțul Cuvintelor | max(0, every accepted hop incl. later undone − shortest route) + hints | undo itself, rejected moves | 0 steps on a win |
| Alchimie | max(0, every new pair tried incl. fruitless − par) + hints | repeated pair | 0 steps on a win |

Counters are cumulative for the session: undo and reset never lower them. Only wins can be
Perfect; losses and give-ups report their steps with `perfect: false`.

### Hint ladder (normative)

| Game | Rung 1 | Rung 2 | Rung 3 |
|---|---|---|---|
| Intrusul | board theme | the three's link (group label) | none: a third rung would solve the board |
| Perechi | theme of one unsolved pair | that pair's link label | mark its two tiles |
| Conexiuni | redacted label pattern of one unsolved group | that group's full label | reveal one member of that group |
| Cald sau Rece | target category | a warm word, rank ≤ 150 | a warmer word, rank ≤ 25; never the target |
| Lanțul Cuvintelor | direction | two useful next words | one hop (backtrack hint as today) |
| Alchimie | next useful word to make | one ingredient of it | the full pair |

- A rung that is empty or already public (e.g. the theme in a themed round) is skipped at no
  charge; the next rung is served instead.
- A request after the last rung is rejected without changing the session.
- No rung may reveal a hidden answer beyond what the table states; each rung has a
  hidden-answer test.
- Conexiuni rung 3 supersedes the MOBILE_CONTRACT rule that clues never reveal membership,
  for that rung only.

### Daily boards

The daily board of Conexiuni, Cald sau Rece, Lanț and Alchimie uses difficulty Ușor and no
theme, so every player gets the same board. Free rounds keep the player's own options.

### API (additive)

Game responses gain `steps`, `perfect` (absent for Cald sau Rece), `hints_left` and
`hint_level`. `score` stays, computed as before, for account compatibility; the interface no
longer shows it. Server share texts lose point wording. The Rust reference stays on the
previous rules.

### Parity

Corpora gain an optional `rules_version` (absent = 1); selection uses content sources and rules
version. Rules-2 corpora are recorded from the Python oracle alone by a committed recorder, with
journeys for every rung, the rejected extra hint, undo, reset, resume and terminal states. The
case count changes from 1,206 to 1,332 (Paul: "Yes, new count is fine"). Mismatches are judged against
this ADR, never against either implementation.
