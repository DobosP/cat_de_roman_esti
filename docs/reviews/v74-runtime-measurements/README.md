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

The highest-value follow-up is **Alchimie create variance**: nine warm creates had a 29.076 ms
median but a 263.526 ms maximum/p95. Its bounded recipe search is the likely investigation
target before adding concurrency or a latency commitment. This is not a release blocker or
a proposed threshold: one nine-round local sample cannot set an SLO. Lanț actions are the
next highest warm median (4.779 ms), still measured without network or contention.

Contexto's finite guess-history path remains a separate capacity concern. A session can
retain up to the stated 2,836 known guess IDs. The historical nine-round report uses ten
distinct terms per session (90 stored guesses), not repeated submissions. The current
harness rejects `--contexto-guesses > 10`, its fixed distinct-term corpus, and reports both
the total and maximum distinct attempts rather than inferring them from successful replies.
Existing protection is the 7,200-second sliding TTL and 1,000-entry cap **per game** in
`SessionStore`; those stores also require the one-worker deployment constraint in
[DEPLOY.md](../../DEPLOY.md).

### Bounded 100-session Contexto sample

The follow-up sample is archived in `contexto-100-sessions.json`, run offline
with 100 deterministic sessions and ten distinct terms each. It retained **100 sessions /
1,000 distinct guesses**, measured 64,360,448 bytes process RSS growth from 45,633,536 to
109,993,984 bytes, create median/p95/max **6.964 / 8.231 / 325.589 ms**, and action
median/p95/max **0.539 / 1.174 / 2.461 ms**. At measurement the machine had load averages
**8.072 / 7.432 / 7.508** (1/5/15 minutes), CPython 3.12.3, Linux 6.8.0, and 32 logical
CPUs. This still includes fixture/Django initialization in the RSS delta and is neither a
per-session memory value nor a 2,836-history worst case; it deliberately avoids a
thousands-heavy-session allocation.

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
round. `--rounds` is positive and `--contexto-guesses` is explicitly bounded to the ten
distinct supplied terms. Before Django starts, the script forces accounts off, clears the
RO-EDU URL/key, pins `CAT_KG_FIXTURE` to the bundled fixture, and sets the exact Django
settings module; inherited service configuration cannot change the workload. It uses only
public response fields to form tile and move actions; its fixed Contexto words are ordinary
guesses, not answers or test hints.

## Anonymous V72 release and rollback check

This is a local checklist for releasing a new candidate from the last documented anonymous
V72 deployment; it does not provision infrastructure or contact production.

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

## Integrated V75 candidate sample

`v75-candidate-measurements.json` repeats the bounded workload against integrated backend
and V75 content at `c50b059` on 2026-09-06. The machine's load averages were
16.177 / 18.758 / 13.901, substantially above the earlier sample. Warm create median/p95
in milliseconds were Alchimie 59.914/435.617, Intrusul 0.495/36.648, Perechi 0.430/2.108,
Conexiuni 0.417/1.767, Contexto 10.331/12.476 and Lanț 3.437/5.633. Warm action medians
ranged from 0.375 ms (Perechi) to 7.982 ms (Lanț). Each cold sample was one fresh process;
all inputs used public response fields and the same fixed ordinary Contexto guesses.

These are local workload observations, not a controlled before/after speed comparison:
host load differed, and Contexto's expanded pool changes selected targets for some seeds.
No latency threshold was relaxed. Use the archived samples to choose a controlled
concurrency measurement before setting a production latency or capacity commitment.
