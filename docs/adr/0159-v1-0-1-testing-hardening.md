# ADR-0159: Harden V1 as 1.0.1 before physical-device testing

Date: 2026-09-23
Status: accepted

## Context

An independent review of the V1 testing release ([ADR-0158](0158-v1-testing-release.md))
covered flow, recovery, layout, backend selection, content, tester documentation, tests
and release plumbing. Each finding was re-judged by separate verifiers; 51 survived.
The most visible: a first lost round was celebrated as a record, enlarged text produced
ragged three-column word boards, the circuit's daily intent never expired, the tester
guide had no way to reach a local server from phones, and a failed optional account
chunk replaced the whole lobby with a game error.

## Decision

Ship the fixes as package version **1.0.1**, still an anonymous local testing release.

- A round that scores 0 points (a loss) is never a record. Stored 0-point bests are
  ignored when scores load; history keeps every result.
  A first daily attempt keeps its per-board row even at 0 points, so the daily circuit
  still counts it after many later plays.
- Circuit intent is single-use: the first intro action removes `challenge=daily` from
  the URL, and only today's resumed daily uses it up. A saved free round resumed from
  the circuit shows one notice instead of the usual resume toast, and the Intrusul/Perechi
  result then offers that day's challenge until a new round actually starts.
- The Conexiuni, Intrusul and Perechi boards use only 4, 2 or 1 columns, chosen by
  container queries in rem so enlarged text still trades columns; a 2-column grid is the
  fallback. This replaces ADR-0158's auto-fit reflow for those boards. Lanț stacks its
  route on phones (below 30em), and the Alchimie inventory uses one column for enlarged
  phone text (below 19.9em, so 320 px phones at default text keep two columns and every
  starting word above the fold), so long words are not split.
- Optional chrome has its own error boundary and renders nothing when it fails. The route
  boundary blames a game only on game routes.
- The release reserve loads at startup, so a damaged manifest fails the boot. A reserve
  failure during quick-game creation returns that game's JSON 503. The SPA shell
  revalidates on every load; hashed assets stay immutable.
- Quick-game tile labels are capitalised when served, except a reviewed allowlist of
  lowercase names. Stored labels, ids and matching are unchanged.
- Lanț offers an explicit give-up and announces the current word. Cald sau Rece names
  its reveal action. Each screen uses one noun per concept (greșeli, salturi) with
  correct singular forms.
- The lobby badge shows the exact version (V1.0.1). A test keeps every version field
  equal. This amends ADR-0158's plain "V1" label.

The review's content findings are deferred to one reviewed content wave, because each
change to the graph, pack, rankings or reserve re-pins several digests. They cover
missing diacritics in some descriptions, the false Toma Caragiu–Reconstituirea casting
edge, a Lanț board solvable only through generic nodes, off-theme single-board
Conexiuni shelves and label spellings. Alchimie Greu start latency on shelves with no
curated board is documented, not bounded, because a time cutoff would break
deterministic dailies.

## Consequences

Testers see fewer false signals (records, layout cues, stale actions), and organizers
can run a same-Wi-Fi phone session from the guide. Content defects already known are
listed in the guide, so testers need not report them. Physical-device and human testing
remain the next gate; browser emulation does not replace them.
