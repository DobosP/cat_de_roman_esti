$ErrorActionPreference='Stop'
$packetRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-native-node-qualifier-alignment-candidate'
$utf8=[System.Text.UTF8Encoding]::new($false)
function Replace-Once([string]$relative,[string]$before,[string]$after){
 $absolute=Join-Path $packetRoot ('after/'+$relative)
 $content=[System.IO.File]::ReadAllText($absolute,$utf8)
 $at=$content.IndexOf($before,[System.StringComparison]::Ordinal)
 if($at -lt 0 -or $content.IndexOf($before,$at+$before.Length,[System.StringComparison]::Ordinal) -ge 0){throw ('Exact unique anchor missing: '+$relative)}
 [System.IO.File]::WriteAllText($absolute,$content.Substring(0,$at)+$after+$content.Substring($at+$before.Length),$utf8)
}
Replace-Once 'scripts/qualify_go_toolchain.sh' '[[ "$(node --version)" == v24.* ]] || { printf ''Qualified Node 24 is required\n'' >&2; exit 2; }' '[[ "$(node --version)" == v26.10.0 ]] || { printf ''Selected Node 26.10.0 is required\n'' >&2; exit 2; }'
Replace-Once 'docs/NATIVE_TOOLCHAIN.md' 'Last verified: 2026-10-05' 'Last verified: 2026-10-08 — source/documentation review only; qualifier alignment UNAPPLIED, UNQUALIFIED, NOT RUN.'
Replace-Once 'docs/NATIVE_TOOLCHAIN.md' '[ADR-0165](adr/0165-native-source-build-and-qualification.md). Complete clean-source
qualification passes under [ADR-0168](adr/0168-qualify-complete-native-toolchain.md);
CI follows accepted manual policy (ADR-0164); native gates default, references opt-in. Current gates are in [STATUS](STATUS.md).' '[ADR-0165](adr/0165-native-source-build-and-qualification.md). [ADR-0168](adr/0168-qualify-complete-native-toolchain.md)
retains the historical complete clean-source Node 24 qualification. Selected Node 26.10.0/npm 12.2.0
follow [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md); the separate qualifier guard alignment is source-only and unqualified.
CI follows accepted manual policy (ADR-0164); native gates default, references opt-in. Current gates are in [STATUS](STATUS.md).'
Replace-Once 'docs/NATIVE_TOOLCHAIN.md' 'The complete integration entrypoint is `scripts/qualify_go_toolchain.sh`. It requires
`CDR_TOOLCHAIN_SCRATCH` under `~/work/_temp/`, an explicit disposable fixture in
`CDR_NATIVE_TEST_DSN`, qualified Go 1.27.1 and Node 24, and a `PATH` containing the native
build/Git/shell utilities with Python/Rust absent. It runs source/operator/builder checks,' 'The standalone integration entrypoint is `scripts/qualify_go_toolchain.sh`. After guarded integration of
this separate alignment, its prechecks require exact Go 1.27.1 linux/amd64 and selected Node 26.10.0 per ADR-0184.
It retains `CDR_TOOLCHAIN_SCRATCH` under `~/work/_temp/`, an explicit disposable fixture in
`CDR_NATIVE_TEST_DSN`, and a `PATH` containing native build/Git/shell utilities with Python/Rust absent.
Its retained command sequence includes source/operator/builder checks,'
Replace-Once 'docs/NATIVE_TOOLCHAIN.md' 'supplied disposable database. Provider mocks remain local; production flags are unchanged.' 'supplied disposable database. Provider mocks remain local; production flags are unchanged.

The exact Node predicate/diagnostic alignment and dependent guide corrections are **SOURCE ONLY,
UNAPPLIED, UNQUALIFIED and NOT RUN**. No new toolchain policy or qualification result is recorded.
The standalone recipe is separate from the owning GUI wrapper. Genuine Linux version/selected-kit lint
context, all native/PG/browser checks and managed current/legacy asset proof remain future obligations.
Its existing command order and `--static-root cat_de_roman_esti/web/static` argument are unchanged;
this guard correction supplies no managed-output, canonical GREEN unit/KIT_BUMP or device/phase proof.'
Replace-Once 'README.md' 'The standalone qualifier also needs source alignment (Node 24 precheck versus selected
Node 26/npm-ci); it is separate from the owning GUI wrapper.' 'The separate standalone qualifier alignment prepares the exact Node 26.10.0 guard per ADR-0184;
it is **UNAPPLIED, UNQUALIFIED and NOT RUN**, and separate from the owning GUI wrapper.
Its retained checks and pending qualification are described in [NATIVE_TOOLCHAIN](docs/NATIVE_TOOLCHAIN.md).'
Replace-Once 'README.md' 'The standalone native-only recipe `scripts/qualify_go_toolchain.sh` currently awaits
selected-toolchain source alignment; explicit task scratch/PG and independent native
obligations remain.' 'The separate source alignment of `scripts/qualify_go_toolchain.sh` follows the exact selected Node 26.10.0 pin
([ADR-0184](docs/adr/0184-native-spa-toolchain-and-managed-output.md)); application, execution and complete qualification remain pending.
Explicit task scratch/PG and all independent native obligations remain; see [NATIVE_TOOLCHAIN](docs/NATIVE_TOOLCHAIN.md).'
Replace-Once 'docs/agent-testing.md' 'Standalone `scripts/qualify_go_toolchain.sh` still requires Node 24 before a later npm-ci step that needs selected Node 26; source alignment is pending.
It is separate from the owning GUI wrapper and cannot currently qualify ADR-0184 tooling; disposable PG/task scratch and all native/privacy/browser obligations remain.
[ADR-0168](adr/0168-qualify-complete-native-toolchain.md) retains historical Node 24 proof; [NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md) describes the stale standalone recipe. No missing required gate becomes a skip.' 'The separate `scripts/qualify_go_toolchain.sh` source alignment prepares exact Node 26.10.0 per [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md); **UNAPPLIED, UNQUALIFIED, NOT RUN**.
It remains separate from the owning GUI wrapper; actual Linux/version/lint context, disposable PG/task scratch and all native/privacy/browser qualification obligations remain.
[ADR-0168](adr/0168-qualify-complete-native-toolchain.md) retains historical Node 24 proof; [NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md) records the pending aligned recipe. No missing required gate becomes a skip.'
Replace-Once 'docs/STATUS.md' 'Frontend120KiB/canonical JS40960/30720 unchanged.' 'Frontend120KiB/canonical JS40960/30720 unchanged. Separate qualifier exactNode26.10.0 [ADR-0184](adr/0184-native-spa-toolchain-and-managed-output.md)/[native guide](NATIVE_TOOLCHAIN.md) alignment SOURCE ONLY/UNAPPLIED/UNQUALIFIED/NOT RUN;'
Replace-Once 'docs/execplans/s1-cat.md' '## 3. Surprises & Discoveries' '- [x] 2026-10-08 — prepared the separate six-path qualifier alignment under existing [ADR-0184](../adr/0184-native-spa-toolchain-and-managed-output.md): only the exact Node26.10.0 predicate/diagnostic changes in scripts/qualify_go_toolchain.sh, preserving100755 and every other byte. Two fresh main preimages plus four dependent CLOSED Cat9-doc afterimages are bound. Source application/execution/qualification remain UNAPPLIED/UNQUALIFIED/NOT RUN; [native guide](../NATIVE_TOOLCHAIN.md) records retained obligations.
- [ ] Qualifier Linux validation — obtain genuine selected-version/owning-context evidence and all applicable native/PG/browser checks after guarded integration, preserving command order/static-root and every failure. The guard correction alone proves no managed assets, standalone GREEN result, canonical GUI unit/KIT_BUMP, device or phase qualification.

## 3. Surprises & Discoveries'
Replace-Once 'docs/execplans/s1-cat.md' 'The future Linux integration order is original38-path source packet, separate2-path accepted startup-accounting amendment, then this separate documentation amendment.' 'The future Linux integration order is original38-path source packet, separate2-path accepted startup-accounting amendment, CLOSED Cat9-path documentation, separate core2-path documentation, then this six-path qualifier alignment. Its script/native-guide preimages are exact raw main59a9; README/agent-testing/STATUS/S1-plan preimages are exact prior Cat9-doc afterimages, not raw main files.'
Replace-Once 'docs/execplans/s1-cat.md' 'Earlier Linux-active paragraphs below are historical context, not Windows execution authority.' 'The separately prepared exactNode26.10.0 standalone guard alignment and four dependent documentation corrections are also UNAPPLIED/UNQUALIFIED/NOT RUN; current managed-output and complete qualification remain pending. Earlier Linux-active paragraphs below are historical context, not Windows execution authority.'
Write-Output 'Authored exactly6 scratch afterimages; only one qualifier line changed; no source execution/test/new policy.'
