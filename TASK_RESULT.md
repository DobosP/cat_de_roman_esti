# Task Result — V43 strict board rebuild

## Outcome

- Replayed the Fable 5 board workflow across all 67 original demotions, 268 groups,
  full approved/pending stock, replacement candidates, and the derived-game artifacts.
- Hardened generation/import/critique against full-inventory exact, three-of-four, and
  half-board reskins; durable rejection tombstones; surface/type shortcuts; mirrors;
  label leaks; vague predicates; projected overuse; stale/partial review artifacts; and
  transactional failure.
- Ran exact-byte factual and independent play-quality reviews without quotas. The final
  cultural pool retained 0/2; the everyday intersection retained 2/9 temporarily.
- Fresh real-ID critics rejected both temporary replacements, unanimously demoted
  `cx_personalitati_339` and `cx_sport_355`, and kept `cx_stiinta_356`. The strict rebuild
  therefore added no new selectable board.
- The reserve sidecar now has 75 IDs. Rejection tombstones contain 43 boards / 172 groups.
- Corrected current KG facts and removed two false e-SIGUR edges. The KG is
  2,364 nodes / 9,217 edges / 7,440 aliases / 180 puzzles.
- Intrusul and Perechi now turn unreadable or invalid derived catalogs into stable
  Romanian 503 responses. Regenerated healthy catalogs serve normally.

## Release artifacts

- Pack: 828 = 606 approved + 222 pending; Conexiuni 311 = 232 + 79.
- Ranked runtime: 448 eligible total / 74 Conexiuni.
- Derived catalog: 336 = 183 Intrusul + 153 Perechi.
- Frozen `boards` payload SHA-256 stayed
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
- Rankings, both derived copies, the pinned digest, legacy content digests, and the mobile
  contract were regenerated/restamped.

## Durable evidence

- `docs/reviews/v43-demotion-pattern-audit.{md,json}`
- `docs/reviews/v43-release-board-rebuild.md`
- `docs/reviews/v43-release-funnel.json`
- `docs/reviews/v43-final-gate/conexiuni_verdicts.json`
- `docs/adr/0067-durable-rejection-debt-and-unanimous-board-gate.md`
- `docs/STATUS.md`

## Verification

- Backend: 679 collected; full rerun green.
- Accounts: 53/53 green.
- Session store: 16/16 green (only the known pytest config warning in the auxiliary venv).
- Frontend: 152/152 green; ESLint and TypeScript green.
- Production bundle: 118.03/120 KiB gzip; Romanian font-subset gate green.
- Pack, KG, ranking, derived-catalog, mobile-contract, and exact-board gates green.
- Ruff, workflow syntax, and `git diff --check` green.

## Compatibility

Session TTL (7,200 seconds), per-game cap (1,000), hidden answers, scores, operation IDs,
and the frozen Intrusul/Perechi board payload are unchanged. Repository landing does not
deploy production.
