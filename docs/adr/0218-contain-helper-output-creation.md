# ADR-0218: Contain helper output creation

Date: 2026-10-26
Status: accepted; independent r5 static review passed on 2026-10-26; landed with
[ADR-0219](0219-land-portable-prospective-captions.md)

## Context

Independent r4 static review rejected helper v4 (SP12R4-1). Its lexical path checks were suitable
for the later descriptor-bound input opens, but outputs still used pathname mkdir and a final-leaf
no-follow open. A stable ancestor symlink could redirect public, private-key or comparison files
outside approved scratch. The separate r4 native PASS did not qualify that failed helper.

## Decision

- Create a distinct v5 helper, manifest and explicitly UNQUALIFIED author pin. Preserve every prior
  helper, branch, report, failed attempt and original baseline. Keep all v4 input snapshot,
  digest-before-parse, strict schema, source closure, limits and content/native validators intact.
- Open the pre-existing approved scratch root through component no-follow directory opens. Create
  missing output parents with directory-relative mkdir and open each with O_DIRECTORY|O_NOFOLLOW.
- Create every final public/key/comparison file via Linux openat2 over its complete relative path
  from that trusted root descriptor: RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS and
  O_CREAT|O_EXCL|O_NOFOLLOW, mode 0600. Never create a leaf through a potentially relocated parent.
  Unsupported APIs, kernels and architectures refuse; x86_64/aarch64 syscall 437 is supported.
  Ambiguous concurrent-rename EAGAIN refuses without retry or pathname fallback.
- Retain raw command/results before assertions. Exercise actual build public/key and compare paths
  with stable symlinks, parent relocation/replacement, missing parents, existing outputs and platform
  refusals. Use only owned nonsensitive fixtures and deliberately unsealed unit comparison keys.

## Guarantee and limitations

The trusted scratch-root directory must not itself be relocated by concurrent actors. Final-file
creation resolves the entire path beneath that anchor in one kernel operation. A held output parent
moved outside it cannot redirect creation; a new ordinary directory at the original inside-root path
may receive the output. Component mkdirat lacks an atomic beneath constraint: a hostile rename can
move or create empty directories outside the anchor before final-file creation refuses. No stronger
directory immobility guarantee is claimed. A created file can be moved while writes finish, and
arbitrary privileged mutation or moves after return are outside this creation-boundary guarantee.

The first author suite had three subtest failures because its mkdir mock changed capability-set
identity and never reached the intended hook; raw failure evidence remains. After correcting that
harness, 29 tests pass, including the preserved 21 input contracts and actual frozen-v4 escape
controls for all three output paths. Five targeted native race top-level tests have 12 pass events,
zero failures/skips: baseline serving caption parity, full-export source-pin refusal, native final
create relocation and command-specific flag guards. The regenerated prospective artifact has
17,499 captions/19 native production sources; the exact default-4096 lt_gastronomie_220 author flow
has 867 tiles/4,730 choices. No actual sealed key was reopened, parsed or rehashed.

These are author engineering results, never independent qualification or content/critic evidence.
Different fresh independent code review and native verification must both PASS before a fresh
controller metadata witness and WORKFLOWONLY pin. A separately independently reviewed executable
content-plan/input pin is still mandatory before any B13/content work. Everything stays UNLANDED;
no workflow, helper, source, content, serving, install, landing or production approval follows.

## Author command record

Actual argv, UTC, constrained environment, exit, full stdout/stderr and hashes are retained under
`/home/dobo/work/_temp/content-loop/source-pin-workflow-fix/author-r5/captures/` in the distinct
`producer-preview`, `helper-contracts` (failed harness), `helper-contracts-corrected`,
`exact-helper-flow`, `targeted-native-race`, `targeted-native-vet`, `native-doc-check` and
`whitespace-before-freeze` receipts. Go is `/usr/local/go/bin/go` 1.27.3 with
`GOTOOLCHAIN=local`, `GOPROXY=off` and existing caches only. Native race uses `-count=1 -timeout=30m`
and the exact five-name regex in its receipt. Targeted vet and native docs (62 files, empty
errors/budgets) pass, as does whitespace. No full gate, unchanged 103 protocol tests/27 probes,
materializer, compatibility, content gameplay, HTTP or production test was rerun or claimed.

Owned superseded author fixture trees were pruned after retaining compact manifests and all process
receipts: 95,516,078 plus 95,539,031 regular-file bytes (191,055,109 total). Their raw bytes are
unavailable; historical manifests do not assert current physical completeness. One latest bounded
reproducible source readset, helper/tests, native artifact, public task and sealed key remain.
No predecessor/frozen/signed/failed actor evidence or original source baseline was deleted.
