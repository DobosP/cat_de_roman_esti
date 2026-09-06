# V79 Gem feedback

Valid until: the reviewed projection policy, Contexto routes or bound content changes — then treat as history.

V79 gives the existing guess **Gem** useful feedback for a small reviewed
fruit-preserve neighborhood. It follows [ADR-0110](../../adr/0110-use-fruit-preserve-feedback-for-gem.md).
No new target, alias or graph edge is added.

## Player-facing result

| Fixed target | Before: hops / rank / temperature | V79 |
|---|---|---|
| Papanași — currently eligible `ct_gastronomie_128` | 5 / 1291 / Foarte rece | 1 / 13 / Fierbinte |
| Clătite — still deferred as a target | 6 / 1699 / Înghețat | 1 / 8 / Fierbinte |
| Dulceață | Projected Gem never wins | Still nonwinning; direct Dulceață wins normally |
| Cozonac — still deferred | Gem 4 / 504 / Rece; Nucă 4 / 504 / Rece | Unchanged |
| Socată — weak seasonal association | 4 / 663 / Rece | Unchanged |

Gem retains its public ID `ctxp_fab0f46e7bcd5932442e`, label, normalized surface,
ingredient domain and one-rank penalty. Repeats remain free and resume retains
progress. The private scoring anchor and hidden target are not exposed.

## Bounded policy and rejected experiment

All 473 original projection terms, including Gem's Miere default, remain exact.
Only Gem has an additional authored neighborhood. It borrows Dulceață when the
hidden target is Dulceață itself or when a **directed, non-distractor** edge from
Dulceață to the target has strength **at least 0.60**. Otherwise it retains Miere.
The current six qualifying concepts are Dulceață, Papanași, Magiun de Topoloveni,
Conserve de iarnă, Clătite and Fruct. The threshold bounds the individually
reviewed relations; it does not establish semantic quality for future content.

The first trial replaced Gem's anchor globally. It made 13 currently eligible
food targets newly warm, including unrelated Grătarul de 1 Mai, Murături and
savory dishes. Independent reviewers rejected it despite green local regression
checks. Limiting borrowing to one hop still included Socată through a generic
0.45 seasonal edge. The final strength boundary excludes that route.

One helper selects the effective private anchor for both scoring and typo
suggestions. It uses the existing direct-edge lookup, adds no graph search or
session cache, and preserves the fallback when the local concept is absent.
For `gemm`, Gem remains a fill-only suggestion in a Clătite round; it is suppressed
when Miere or Dulceață is the secret. The rule never creates an exact alias or
Lanț move. Nucă, Alună, Unt and Miere are unaffected.

## Independent evidence

- `proposal-bounded.json`, `FACTUAL_REVIEW.md`, `factual-review.json`: the exact
  final policy and independent lexical/culinary review of all six associations.
- `impact/final-report.md`, `impact/final-receipt.json`: independent acceptance,
  complete source/content bindings and baseline reproduction proof.
- `impact/bounded-comparison.json`: all **207 approved / 203 eligible** targets
  exercised through the real Django guess API. Only Papanași changes; the other
  **206 responses are exact**. All 2,364 known nodes were checked for effective
  anchor selection, yielding exactly the six reviewed targets.
- The impact captures preserve the original pre-edit baseline, rejected global
  trial and final bounded trial. A forced-default replay exactly reproduces the
  original 207 response rows and three shared fixed controls. Metadata and five
  additional audit controls are explicitly outside that equality claim.
- `openers-delta.json`: replay of V78's ordinary 68-probe list. Only the Clătite
  Gem response changes; **67 responses and both neighborhoods remain exact**.
  The full baseline remains in the immutable V78 archive and its hash is bound.
- `implementation-review.json` / `IMPLEMENTATION_REVIEW.md`: independent final
  source, test, privacy and impact review. `rejected-global/` retains the separate
  earlier rejection and source/test snapshot; it is not the landed implementation.
- `preservation.json`: nine graph/pack/derived/mobile/ledger artifacts match
  baseline main `010cfd176dcaa78aac660aea71e154691bd010f3` byte-for-byte.
- `verification.json`, `review-manifest.json`: exact checks and archive hashes.

The 13 focused regressions cover the complete original term table, exact six-node
borrow set, edge-strength boundary, direction, distractors, missing anchors,
private/nonwinning guesses, useful versus suppressed typo suggestions, repeat/
resume, cold savory controls, Socată fallback, Lanț rejection and artifact pins.

## Reproduction and preserved scope

Copy the archived `impact/*.py.txt` runners into a task scratch directory, removing
`.txt`. `impact/final-report.md` records the capture/compare commands. The receipt
builder uses the original scratch/root paths; adjust those paths for another
checkout and retain the recorded baseline files. Sessions are temporary and
removed after each probe. Reproducing the rejected global trial requires its
archived projection source with the baseline Contexto route, in an isolated
worktree; never apply the trial over the final runtime.

All 620 pack records (612 approved, eight pending), 620 board-ranking rows,
336 frozen derived boards, 180 puzzles and 8,450 aliases remain exact. Selection
sources, score rules, session limits and frontend assets are unchanged. The served
KG remains V77. There is no promotion of Cozonac or Clătite, and the bread route
remains deferred. A fresh Clătite review is the next content step.

The reviews are independent Codex-agent judgments with source checks, not human
Romanian playtests. No push, deployment, production re-verification or accounts
enablement occurred. External beta gates remain in [BETA_CANDIDATE](../../BETA_CANDIDATE.md).
