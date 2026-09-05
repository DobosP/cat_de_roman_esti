# V74 offline runtime measurements

Valid until: the next runtime-affecting game or deployment change — then remeasure.

`runtime-measurements.json` is evidence from `f75a75c` on 2026-09-06. It exercises the
six anonymous games through their real Django routes with the bundled offline fixture,
not game helpers, a remote service, or a listener. The test client covers routing, body
parsing, response serialization, session stores, and game work; it does **not** represent
TLS, Caddy, network, concurrent users, container CPU limits, or a production process.

## Workload and result

Each cold row is one fresh CPython process and one create/action sequence. Warm rows run
nine deterministic seeds (`10000..10008`) in one initialized process. Contexto makes ten
ordinary typed attempts per round without reading the private target; all nine rounds
accepted ten distinct attempts. Times are milliseconds; the JSON retains median/p95/max
and median/max response bytes for every create/action sample. RSS uses current Linux
`VmRSS`, before and after each bounded sample; it is not a per-session allocation claim.

| Route cost | Cold create (median) | Warm create median / p95 | Warm action median / p95 |
|---|---:|---:|---:|
| Alchimie | 269.163 | 29.076 / 263.526 | 0.418 / 0.577 |
| Intrusul | 302.650 | 0.302 / 23.368 | 0.240 / 0.471 |
| Perechi | 269.303 | 0.341 / 1.507 | 0.271 / 0.377 |
| Conexiuni | 271.631 | 0.325 / 1.401 | 0.278 / 0.481 |
| Cald sau Rece | 310.594 | 6.350 / 8.503 | 0.453 / 0.793 |
| Lanțul Cuvintelor | 282.629 | 1.844 / 3.781 | 4.779 / 4.985 |

The run used CPython 3.12.3 on Linux 6.8.0, x86_64, with 32 logical CPUs and no deliberate
parallel load. Cold creates added about 49 MB RSS, principally Django and fixture/service
initialization. In the warm process, the first Alchimie sample added 60.9 MB RSS while
later game samples added at most 1.1 MB; do not divide these process-level deltas into a
session-size estimate.

The highest-value concern is **Alchimie create variance**: nine warm creates had a 29.076 ms
median but a 263.526 ms maximum/p95. Its bounded recipe search is the likely investigation
target before adding concurrency or a latency commitment. This evidence proposes no new
threshold: one nine-round local sample cannot set an SLO. Lanț actions are the next highest
warm median (4.779 ms), still measured without network or contention.

Contexto's finite guess-history path remains a separate capacity concern. A session can
retain up to the stated 2,836 known guess IDs; this run deliberately stopped at ten per
round (90 accepted entries across nine short-lived sessions) and did not allocate hundreds
or thousands of heavy sessions. The result is an extrapolation boundary, not proof of
worst-history memory or latency. Existing protection is the 7,200-second sliding TTL and
1,000-entry cap **per game** in `SessionStore`; those stores also require the one-worker
deployment constraint in [DEPLOY.md](../../DEPLOY.md).

## Reproduce locally

From a worktree, with no production access and accounts explicitly off:

```bash
PYTHONPATH=. CAT_ACCOUNTS_ENABLED=0 /home/dobo/work/cat_de_roman_esti/.venv/bin/python \
  scripts/measure_wordgames_runtime.py \
  --report docs/reviews/v74-runtime-measurements/runtime-measurements.json
/home/dobo/work/cat_de_roman_esti/.venv/bin/python -m json.tool \
  docs/reviews/v74-runtime-measurements/runtime-measurements.json >/dev/null
```

The default is intentionally small: nine rounds per game and ten Contexto attempts per
round. `--rounds` and `--contexto-guesses` are positive, explicit overrides. The script
uses only public response fields to form tile and move actions; its fixed Contexto words are
ordinary guesses, not answers or test hints.

## Anonymous V72 release and rollback check

This is a local checklist for a release candidate already deployed in anonymous V72 mode;
it does not provision infrastructure or contact production.

1. Run the local runtime command above and the release's required validators/tests. Record
   the candidate commit, image digest, manifest hash, benchmark JSON, machine/load details,
   and that `CAT_ACCOUNTS_ENABLED=0` was used.
2. Before a server update, preserve the running V72 image with the exact commands and
   release tag in [DEPLOY.md](../../DEPLOY.md#6-updates-and-rollback). Keep one uvicorn
   worker: stores are in process and cannot span workers.
3. Update only after the local record is complete. Verify the documented anonymous health
   and public API checks; submissions must remain unavailable and accounts/debug off.
4. If a release smoke or runtime symptom fails, restore the recorded V72 commit/image by
   the same DEPLOY rollback procedure, then re-run its health checks. Do not use `down -v`
   or Docker pruning because that can remove the preserved rollback image or named data.
