# Source7 native coverage partitions

Valid until: I1200, code/embed/fixture inputs, owned SDK/cache, or the paused-scope authorization changes.

Source-only proposal under `go-source7-native-coverage-scope.json` dd32f9aedde87dfed16c81831ce1a220768a42c3618edee53a13bbc714107bac. No Go, CLI, imports, lists, compilation, tests, network or I changes were executed. Current Source6 remains live; Source7 is uninstalled.

The accepted backend metadata identifies **38 base packages: 27 test-bearing and 11 without tests**. This is package coverage, not binary case coverage. All 38 still belong in required vet/build coverage; no-test packages must not disappear from the inventory. Root's next reviewed batch can use the two previously unrun imported-package metadata commands and the existing current HTTP test binary's full case list. Failed universal `go list -m all` remains failed/optional and is not resumed or fetched.

| Immediate producer | Eligible operation | Meaning |
|---|---|---|
| Shared auth metadata | Owned Go `-C I/shared-go/authcore list -deps -test -json ./...` | Imported test/production closure for the one consumer module; errors stop, no `-e`. |
| Local Webkit metadata | Owned Go `-C I/go-backend/third_party/webkit list -deps -test -json ./...` | Eleven parent-module packages; nested `sample/go.mod` is outside `./...`. |
| Existing current HTTP binary | Legitimate cwd `I/go-backend/internal/httpapi`; binary9f `-test.list .` | Complete top-level test/example/fuzz/benchmark inventory from this compiled package. Prior list selected only two names. This does not execute their bodies. |

Use current exact SDK, complete module cache, legacy GOPATH, qualified native PATH, offline/readonly flags, Go2, fresh owned temp/output paths and unchanged reviewed397686 guard. Fresh admission, raw producer log/receipt keeper plus external SHA must precede parsers/consumers. Unknown actual case IDs/counts freeze only after the producer. List every actual case; no hand-authored successful count, omission, filtered-away failure or foreign module fallback.

## Reusable current binaries and completed evidence

- **contentbuild** `T/current-source7-installed-history-tests-r1/contentbuild.test`: SHA30de6a4cac26e09191a7b739f706ae6e9913b6565eb7f5fdac52045fcf812973,17,725,490 bytes. Rehashed exact. Compiler keeper3b574cb850b81eb739018515578ea3697952f75124094627abc6720414bf8898 binds actual producer. Completed unfiltered R4 evidence has all21 top-level/53 including subtests, zero failures/skips and race: raw manifest41fcced25a2f1e9a95145fa781fa871d64c0c05263cb1c68e782f92d014ba372, actual21-case digest53585404e4bcde81ef683ed5316ee4fef709fbac551ac36b8176bb7a7f00fe35, complete keeper13e72f380af9fe58fc5beab15b1faf91b7e1ba9576243b48c4aec86c87dbe28c. Reuse that result; do not compile/list/run it again merely for current docs.
- Source proof includes all16 contentbuild Go/embed-rule files and its **full backend-module compile closure:57 Go files/21 packages**, including contentbuild's test import of httpgolden→httpapi and its production dependencies. Every file remains identical to the authenticated834 inventory883ac745908bab07b86841e84355b6027535fe5a0c3768fc8e7110770025047b. Current graph differential and two HTTP input `_test.go` additions are dependency test files and are excluded from contentbuild compilation. No changed contentops production code is imported. Conservative replacement-module input checks additionally cover all9 authcore and17 local-Webkit non-test files present in I (nested sample excluded), each exact old834. Imported external cache/SDK identities remain required prior producer bindings; pending new shared/Webkit metadata is not fabricated here. Complete canonical relative-path/hash closure digest: 67f2bde6095e5b923c7ac773b91fe96db845071837fb6623bad111e098ae90ba.
- All834 old files were compared against actual I: only contentops README/command and two optional Python test modules differ. Serving fixtures, source/review/history inputs, embedded exports and module files remain exact. The additional files do not alter explicit contentbuild read paths; there is no contentbuild glob/walk/read-dir discovery. This supports reuse of the completed current-source/history result, not a new whole-module qualification. Preserve prior producer/source/input keeper checks before relying on it.
- **httpapi** `T/go-source7-input-contracts-r1/native/httpapi.test`: SHA9f02153a9079e48fb6c3240789bbca05477bc9387f93e1cca5b61ba8327a9f05,41,168,643 bytes. Rehashed exact. Complete output keeper69fdf763a8317cc10055af3ed91b2302dd0bc23ab75b1e14b0b4c3467a61eacb binds this full-package compile; only two selected parents/69 subtests were listed/run successfully. Reuse binary for complete listing, not a claim that all HTTP cases passed.
- Previous graph/contentops race binaries embedded genuine Source6. Their accepted source-algorithm proofs remain historical; they do not establish current sealed Source7 package execution. Compile their current packages if fresh candidate package qualification is required.

## Startup and side effects

Static declaration scan over actual I backend/shared sources, including local Webkit, found **no local `TestMain` or explicit `init` function**. This is a local-source fact, not a universal dependency-initializer audit. Current9f already started successfully in its two-test lane. Account test globals register empty flags only. `newFixture`/`newArcadeFixture` call `t.Skip` before any database pool/schema operation when `-accounts.database`/`-arcade.database` is absent. Neither case-listing nor default invocation silently selects a DSN. Do not pass those flags or activate PG/providers.

Shared OAuth, backend ROEDU/hop tests and Webkit health tests use `httptest.NewServer` local fixtures in their test bodies. A future unit lane must explicitly admit bounded loopback fixture sockets; no real provider/ROEDU endpoint is needed. These bodies are not invoked by package metadata or binary listing. Nested Webkit sample has actual Node/Chromium subprocess and live-PG paths and is outside this plan. Its log-only no-DSN return is not PG acceptance.

Current contentops delta tests initialize a Git repository only in `t.TempDir`, remove inherited `GIT_*` from the child, and set empty templates/global config; their per-test environment pins private fixture paths. Later execution must preserve this isolation and expose qualified Git. Doccheck unit cases inspect finite text corpora; the separate actual doccheck operator invokes readonly Git `ls-files` and requires the real owning worktree, not a forged Git root in I. No default native test caller invokes Node/Go child tools in the parent backend/shared/Webkit scope found by this source scan.

## Complete future partition ledger

| Partition | Packages / handling |
|---|---|
| Reuse qualified current history | `internal/contentbuild` (1), result scope above. |
| Current operators/graph/rails | `internal/graph`, `internal/contentops`, `internal/contentrails`, `cmd/cat-content-rail` (4): fresh candidate compile/list, then unfiltered package race tests and vet under reviewed inputs. |
| Core games/services | `internal/alchimie`, `internal/alchimie_explore`, `internal/catalog`, `internal/conexiuni`, `internal/contexto`, `internal/intrusul`, `internal/lant`, `internal/perechi`, `internal/session`, `internal/strictjson`, `internal/pyrandom`, `internal/content` (12). |
| Other backend contracts | `cmd/cat-server`, `internal/apppack`, `internal/browserplan`, `internal/doccheck`, `internal/hopcli`, `internal/mobilepack`, `internal/roeduclient` (7). |
| Default accounts / separate PG | `internal/accounts` (1): list all names. Default documented PG skips stay visible and unqualified; explicit PG lane remains paused. |
| Current HTTP | `internal/httpapi` (1): reuse9f/list all; full body execution withheld while actual managed assets are missing. Keep all mandatory asset and explicit-PG names visible. |
| Independent corpus | `internal/httpgolden` (1): compile/list allowed; full package body run withheld because `ForSources` supports only original/V1.2–V1.6 and refuses current Source7. No synthetic Source7 identity/golden or historical wrapper for this current contract. |

These rows cover all27 tested backend packages exactly once. All11 no-test packages are `cmd/cat-browser-plan`, `cmd/cat-content`, `cmd/cat-content-ops`, `cmd/cat-doc-check`, `cmd/cat-hop`, `cmd/cat-mobile-pack`, `cmd/cat-qualify`, `cmd/cat-roedu`, `embedfs`, `internal/gameapi`, `internal/pack`; they remain in backend vet/build scope.

`TestManagedSPACompiledCurrentAndFrozenLegacy` requires actual embedded current/legacy index and Vite manifest; I has scaffolds only. Its synthetic sibling tests do not satisfy this actual-byte gate. Asset authorization remains unanswered; no asset generation or skip is proposed. `internal/httpgolden.TestCurrentIndependentHTTPParity` requires a genuinely independent exact Source7 corpus/selector; existing1207 Source6 records cannot be relabeled. Default whole-backend/zero-omission/assembled acceptance remains withheld.

## Shared/Webkit cases and resource admission

Shared source has **15 static top-level test declarations**, all pending actual binary inventory: TestDjangoDefaultLegacyHashers; TestOIDCSignedIdentityPKCEAndSingleUse; TestOIDCRejectsInvalidClaims; TestOAuthRejectsUnboundAndExpiredState; TestFacebookAppScopedTokenValidation; TestReturnPathRejectsExternalRedirect; TestProviderTransportBoundsResponses; TestConfigRequiresHTTPSAndPersistentStore; TestSignupLoginRotationAndLogout; TestCSRFFailsBeforeStoreOrHash; TestSessionExpiryAndUnknownToken; TestProvidersFailClosedWithoutCredentials; TestBoundedBodiesAndRateLimit; TestPasswordDjangoCompatibilityAndWorkBounds; TestExternalIdentityNeverLinksEmail.

Parent Webkit has **32 static `_test.go` declarations across11 test-bearing packages**: assets2,budget6,cmd/budget2,csp6,engine2,golden5,health4,island2,routes1,static1,tokens1. These are source counts, not actual binary cases or passes. Historical33 counted exported production helper `budget.TestRouteBudgets(t testing.TB,...)`; that helper is not a test entrypoint. Exact actual names/counts, build-tag/filename selection and subtests must come from the future metadata and each binary's complete list/run. Nested sample is a separate module and is excluded, with no concealed sample gate claim.

Compile/list current test packages serially in reviewed finite groups, actual keeper before each list. No full backend run while known blocked. Known race binaries are17.7MB and41.2MB; a naive27×41.2MB retention projection is about1.11GB before cache/temp/log growth, so compiling every package into one retained batch cannot be assumed to fit the1GiB growth bound. This is a projection, not a measured upper bound. Group admission must use actual baseline/headroom/cache state and preserve prior outputs; unchanged-source binaries should be reused. Native2GiB sampled groupRSS/1GiB fullS-R growth/20min/180reserve/Go2 limits remain; no quota or runner rewrite. Fresh actual growth/RSS and complete source/log/output checks decide acceptance. Source wholeRSS is unmeasured.

Preparation retained read-only missing-filename probes for nonexistent parity_test.go/corpus.go/source_test.go; corrected to actual source paths. No executable lane was started or retried.
