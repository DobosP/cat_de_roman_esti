$ErrorActionPreference='Stop'
$packetRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-native-node-qualifier-alignment-candidate'
$repoRoot='C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$priorRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$analysisRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-node-qualification-source-analysis'
$pin='59a9a568c445654f69215d735091c9b3e0405831'
$utf8=[System.Text.UTF8Encoding]::new($false)
$lf=[string]([char]10)
function Sha([byte[]]$bytes){return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()}
function Git-Bytes([string[]]$arguments){
 $start=[System.Diagnostics.ProcessStartInfo]::new('git')
 $start.WorkingDirectory=$repoRoot; $start.UseShellExecute=$false; $start.CreateNoWindow=$true
 $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true; $start.Environment['GIT_OPTIONAL_LOCKS']='0'
 foreach($arg in $arguments){$start.ArgumentList.Add($arg)}
 $process=[System.Diagnostics.Process]::Start($start); $memory=[System.IO.MemoryStream]::new()
 $process.StandardOutput.BaseStream.CopyTo($memory); $stderr=$process.StandardError.ReadToEnd(); $process.WaitForExit()
 if($process.ExitCode -ne 0){throw ('Read-only Git failed: '+$stderr)}
 return ,$memory.ToArray()
}
function Git-Text([string[]]$arguments){return $utf8.GetString((Git-Bytes $arguments)).TrimEnd([char]13,[char]10)}
function Save([string]$path,[string]$text){[System.IO.File]::WriteAllText((Join-Path $packetRoot $path),$text,$utf8)}
if(Test-Path -LiteralPath (Join-Path $packetRoot 'SEAL.json')){throw 'Packet already sealed; never rewrite'}
if((Git-Text @('rev-parse','HEAD')) -ne $pin -or (Git-Text @('status','--porcelain')) -ne ''){throw 'Source sequencing drift before seal'}
foreach($path in @('scripts/qualify_go_toolchain.sh','docs/NATIVE_TOOLCHAIN.md')){
 $before=[System.IO.File]::ReadAllBytes((Join-Path $packetRoot ('before/'+$path)))
 $raw=Git-Bytes @('cat-file','blob',($pin+':'+$path))
 $working=[System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))
 if((Sha $before) -ne (Sha $raw) -or (Sha $before) -ne (Sha $working)){throw ('Fresh source drift: '+$path)}
}
if(!(Git-Text @('ls-tree',$pin,'--','scripts/qualify_go_toolchain.sh')).StartsWith('100755 blob 48032f620f260148362d37a409353181b0ccd481')){throw 'Script mode/blob drift'}
$guards=[ordered]@{
 'SEAL.json'='a5e90bd370c1659a3164a011467a7bef396d129a9cf1b75293f535bd4ea9d57b';
 'SHA256SUMS'='6fc8a9bfa8bb7d51686221bfe767196ae1d2e63e52b8715136368b4bc0603a71';
 'source-bindings.json'='fa99393d5a653309600e5bca62637c53ee15fd043fa78e0be23ba85b179949d6'
}
foreach($name in $guards.Keys){if((Sha ([System.IO.File]::ReadAllBytes((Join-Path $priorRoot $name)))) -ne $guards[$name]){throw ('Closed predecessor drift: '+$name)}}
foreach($path in @('README.md','docs/agent-testing.md','docs/STATUS.md','docs/execplans/s1-cat.md')){
 $before=[System.IO.File]::ReadAllBytes((Join-Path $packetRoot ('before/'+$path)))
 $prior=[System.IO.File]::ReadAllBytes((Join-Path $priorRoot ('after/'+$path)))
 if((Sha $before) -ne (Sha $prior)){throw ('Dependent source drift: '+$path)}
}
if((Sha ([System.IO.File]::ReadAllBytes((Join-Path $analysisRoot '2026-10-08-node-qualification-source-analysis.txt')))) -ne 'a8c591e662ce824fb74975a5363543ff1bec259f6ac725432ba5e936c861bcc6'){throw 'Accepted analysis changed'}
if((Sha ([System.IO.File]::ReadAllBytes((Join-Path $analysisRoot 'SHA256SUMS.txt')))) -ne '17230e995663e620545e621da625169189a41a7bdee2434f1ce001a1d99f0179'){throw 'Accepted analysis seal changed'}
Save 'source-review-rationale.md' 'Valid until: any exact bound source/predecessor byte, selected pin or authorized scope changes — then treat as history.

2026-10-08 closed source rationale — native Node qualifier alignment

Existing decision, bounded implementation
ADR0184 already selects Node26.10.0/npm12.2.0 and Go1.27.1. Root/frontend .nvmrc both contain26.10.0; existing frontend engines and engine-strict require the selected graph. Raw standalone qualifier12 admittedv24.* before its later npm-ci. The accepted CLOSED analysis identified a source inconsistency, not an observed runtime failure or canonical GUI-wrapper failure.

Exactly one script line changes: v24.* becomes exactv26.10.0, and the diagnostic says Selected Node26.10.0 is required. The Bash form/failure exit2 remains. Raw4065B before SHA256c7e65ad67627e5060a154f3aef6091e46057562456a6d704d7d1e7a85d90ab11 becomes4072B SHA256912e18cdf2e2101cdd2ba8906139515173eb45e5dd689452282c71c78cf5022d. Literal inverse replacement reproduces every original byte. Mode100755 before/after is bound to rawGit and the portable patch index. No broader support policy, new parser, npm predicate, command rewrite, test or assertion relaxation is introduced.

Every other script byte remains exact: Go1.27.1 linux/amd64 check; disposablePG and confined task scratch; Python/Rust exclusion; source/operator/docs/race/vet/explicitPG/parity/smoke/benchmark/Node/browser checks; command order/static-root; no-skip/failure/privacy flags; final GREEN line reachable only after actual successful future commands. No such result exists here.

Six exact paths with two provenance classes
Fresh rawmain59a9: scripts/qualify_go_toolchain.sh (100755), docs/NATIVE_TOOLCHAIN.md (100644).
Dependent exact CLOSED Cat9-doc AFTERIMAGES, all100644: README.md, docs/agent-testing.md, docs/STATUS.md, docs/execplans/s1-cat.md. They are not rawmain preimages. Cat9 predecessor SEAL/SHA256SUMS/source-bindings and each of four exact afterimage SHA256s were checked before capture; no predecessor file was written.

Current guides describe the prepared alignment as SOURCE ONLY/UNAPPLIED/UNQUALIFIED/NOT RUN, link existing ADR0184/nativeguide, and retain historical ADR0168 Node24 proof. No new ADR or framework/toolchain decision. Expired GUI handoff, every historical ADR body/receipt/archive/baseline and every earlier code/doc/review packet remains untouched. Core/teacher/social docs are not targets.

CLOSED independent read-only reviews
build_identity_api: exactly one Node line, all other bytes retained, selected diagnostic accurate;100755 preserved.
build_identity_contract: source-only qualification boundaries, historicalADR0168/E3/device/phase constraints and integration order are accurate; no prose blocker.
build_identity_tests:2rawmain and4dependent closed-doc preimages exact; only STATUSline5 changes with119 other lines exact; STATUS120/agent-testing78; all12 plan headings/old checked records/history preserved. No preservation blocker.

Native literal checks and scratch-only git apply --check --whitespace=error-all passed. Windows scratch check uses core.filemode=false only for host representation; portable index declares100755 and Linux integration must verify the exact semantic mode. Patch never applied. No product/doc parser, compiler, validator, formatter, generator, test, build, Docker, setup or version/environment probe ran. No low-value mirror tests were authored.

Unresolved qualification facts remain explicit
This fixes only the version predicate inconsistency. Existing command order and historical static-root do not supply managed current/legacy asset proof; selected-kit lint/owning context and full native/PG/browser qualification remain future actual obligations. Standalone qualifier is separate from canonical GUI unit/full, trust/GREENunit/KIT_BUMP. No new installed-version observation, qualification/gzip/image/release identity or metric exists.

All numeric budgets, AccountBar source amendment/test dispositions, startup gzipUNACQUIRED, React19/UI0.3 throughM1, core1.2 immutable release/tag, Source6/Source7 inventory/pins/counts, E3 formal budget-red limits, owner/device/M2/S0b/teacher/social/live/soak and production holds remain. No product/repository/index/object/stage/commit/merge/push/reset/cleanup or other-owner worktree operation.

Integration: original38 source -> separate2 eager accounting -> CLOSED Cat9 docs -> separate core2 docs -> this6-path alignment after independent manager acceptance and exact provenance checks. Existing packets stay immutable; no combined patch or new qualified identity.
'
Save '2026-10-08-portable-node-alignment-continuation.txt' 'Valid until: guarded integration, relevant source/predecessor drift, selected-pin change or superseding owner dispatch — then treat as history.

2026-10-08 portable native Node qualifier continuation

NEW separately sealed cat-native-node-qualifier-alignment-candidate only. No repository dated handover; expired docs/GUI_MIGRATION_HANDOFF.md stays unchanged. Parent independently reviews these CLOSED bytes before Linux application. Independent manager acceptance remains pending.

Source base Cat59a9a568c445654f69215d735091c9b3e0405831/tree63a846a9974463ba360b4083cc53d0249f92fee7, empty porcelain. Exactly6 paths:
- scripts/qualify_go_toolchain.sh and docs/NATIVE_TOOLCHAIN.md:2 exact rawmain preimages.
- README.md, docs/agent-testing.md, docs/STATUS.md, docs/execplans/s1-cat.md:4 exact prior CLOSED Cat9-doc AFTERIMAGE preimages, not rawmain. source-bindings.json records bytes/modes/blobs/SHA and dependency.
Preserve script100755. Beforeblob48032f620f260148362d37a409353181b0ccd481; afterblob485ca13f9dad8dc6ffc7bd3e29ddaa295d15e6ea. The sole script delta is exactselectedv26.10.0/SelectedNode26.10.0 diagnostic; every other script byte remains.

Required layered order:
1 original38-path source packet;
2 separate2-path eager-accounting packet;
3 CLOSED Cat9-path documentation packet;
4 separate core2-path documentation, manager-owned;
5 this6-path qualifier alignment after acceptance/exact checks.
Do not overwrite/recombine previous source/doc/review packets. Verify each exact beforeimage blob/mode/raw SHA and prior-doc afterimage identity before integration. On relevant drift stop for owner sequencing rather than recapturing/rebasing over current Source6/Source7 truth. No new qualified identity.

Cat9 predecessor identities: SEALa5e90bd370c1659a3164a011467a7bef396d129a9cf1b75293f535bd4ea9d57b; SHA256SUMS6fc8a9bfa8bb7d51686221bfe767196ae1d2e63e52b8715136368b4bc0603a71; source-bindingsfa99393d5a653309600e5bca62637c53ee15fd043fa78e0be23ba85b179949d6. These and the4 dependent afterimage hashes remain exact, unchanged.
Accepted analysis reportSHAa8c591e662ce824fb74975a5363543ff1bec259f6ac725432ba5e936c861bcc6/sealSHA17230e995663e620545e621da625169189a41a7bdee2434f1ce001a1d99f0179 were checked; no report mutation.

CLOSED source reviews found no blocker. Native literal inverse-script/hash/mode/doc-history/budget checks and scratch-only git apply --check passed; Windows mode representation is disabled only for scratch applicability, with100755 separately bound and preserved in the portable index. No patch applied.

All execution/tests/parsers/validators/generators/compilers/formatters/builds/Docker/setup/environment/version probes remain NOT RUN. No new test authored. Qualifier/source/doc proposals UNAPPLIED and UNQUALIFIED; actual installed versions, standalone qualifier result, managed-output proof and current startup gzip remain UNACQUIRED. The Node guard fix alone does not qualify retained command order/static-root/context, native/PG/browser lanes or canonical GUI proof.

Paul will execute/refine on Linux through actual current authorization/context and evidence preservation, retaining real failures and every existing required check. Obtain actual selected Node/npm/exactGo and genuine selected-kit lint context; no skip/bypass/fabricated context. Current/legacy managed assets and standalone/full qualification remain future evidence, without hidden source/order rewrites here. Keep separate canonical GUI trust -> same-final-SHA GREENunit -> KIT_BUMP and E3/device/M2/phase/production holds.

Record actual application/check results in living status/plan before any future product commit. Do not relabel ADR0168 Node24 historical proof or this source packet as selected-toolchain qualification. Main remains clean; no product/index/object/branch/worktree writes or cleanup.
'
$bindingPath=Join-Path $packetRoot 'source-bindings.json'
$binding=[System.IO.File]::ReadAllText($bindingPath,$utf8)
$old='"independent_review": "draft reviews pending; closure recorded separately before seal"'
$new='"independent_review": "CLOSED three-agent source/prose/preservation reviews; no blocker; no writes or runtime execution"'
if(!$binding.Contains($old)){throw 'Review binding anchor differs'}
[System.IO.File]::WriteAllText($bindingPath,$binding.Replace($old,$new),$utf8)
$receipt='Valid until: exact source/predecessor or packet bytes change — then treat as history.'+$lf+$lf+
 '2026-10-08 closure: shared main'+$pin+'/tree63a846a9974463ba360b4083cc53d0249f92fee7; empty porcelain.2fresh rawmain and4dependent Cat9-afterimage guards reverified; prior immutable SEAL/SHA/source-bindings/analysis guards exact. Source script100755 preserved;4065->4072 bytes, onlyNode line. STATUS120/agent-testing78/all12sections/historical records retained. All product/runtime/tests/parsers/validators/generators/compilers/formatters/builds/Docker/setup/probes NOT RUN. No product/index/object/branch/worktree write/apply/commit/merge/push/reset/cleanup.'+$lf
Save 'closing-source-receipt.txt' $receipt
$paths=[string[]]@([System.IO.Directory]::EnumerateFiles($packetRoot,'*',[System.IO.SearchOption]::AllDirectories) | ForEach-Object{[System.IO.Path]::GetRelativePath($packetRoot,$_).Replace('\','/')} | Where-Object{$_ -ne 'SHA256SUMS' -and $_ -ne 'SEAL.json'})
[System.Array]::Sort($paths,[System.StringComparer]::Ordinal)
$rows=[System.Collections.Generic.List[string]]::new()
$totalBytes=[long]0
foreach($relative in $paths){
 $bytes=[System.IO.File]::ReadAllBytes((Join-Path $packetRoot $relative))
 $rows.Add((Sha $bytes)+'  '+$relative); $totalBytes+=$bytes.Length
}
Save 'SHA256SUMS' (($rows -join $lf)+$lf)
$patchSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'conditional-native-node-qualifier-alignment.patch')))
$bindingSha=Sha ([System.IO.File]::ReadAllBytes($bindingPath))
$manifestSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'SHA256SUMS')))
$seal=[ordered]@{
 schema=1;kind='closed six-path existing-decision native Node qualifier alignment candidate';
 pin=$pin;pin_git_tree='63a846a9974463ba360b4083cc53d0249f92fee7';
 target_paths=@('scripts/qualify_go_toolchain.sh','docs/NATIVE_TOOLCHAIN.md','README.md','docs/agent-testing.md','docs/STATUS.md','docs/execplans/s1-cat.md');
 fresh_main_preimages=2;dependent_closed_cat9_doc_afterimages=4;payload_files=$paths.Count;payload_bytes=$totalBytes;
 patch_sha256=$patchSha;source_bindings_sha256=$bindingSha;sha256sums_sha256=$manifestSha;
 script_mode_before='100755';script_mode_after='100755';script_before_bytes=4065;script_after_bytes=4072;script_after_sha256='912e18cdf2e2101cdd2ba8906139515173eb45e5dd689452282c71c78cf5022d';
 single_node_line_change_only=$true;every_other_script_byte_unchanged=$true;
 status_lines=120;agent_testing_lines=78;historical_source6_source7_and_plan_records_preserved=$true;
 independent_source_reviews='CLOSED; no blocker';independent_manager_acceptance='PENDING';
 applied=$false;qualified=$false;tests_authored=0;tests_run=0;installed_versions='UNACQUIRED';standalone_result='UNACQUIRED';managed_output_proof='NOT EARNED';startup_gzip='UNACQUIRED';
 scratch_apply_check='PASS only; never applied; Windows scratch filemode disabled while portable mode100755/rawGit binding preserved';
 integration_order='original38 -> separate2 eager -> Cat9 docs -> core2 docs -> this6 alignment after acceptance/exact guards';
 predecessor_mutations=0;new_adr=$false;new_product_handover_path=$false;repository_writes=0;shared_porcelain='';
 not_run=@('product execution','tests','parsers','validators','generators','compilers','formatters','builds','Docker','setup','environment/version probes','qualification');
 new_qualified_identity='NONE'
}
Save 'SEAL.json' (($seal | ConvertTo-Json -Depth 10)+$lf)
$sealSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'SEAL.json')))
Write-Output ('CLOSED '+$paths.Count+' payload files / '+$totalBytes+' bytes')
Write-Output ('PATCH '+$patchSha)
Write-Output ('SOURCE_BINDINGS '+$bindingSha)
Write-Output ('SHA256SUMS '+$manifestSha)
Write-Output ('SEAL '+$sealSha)
Write-Output 'Main clean;2rawmain+4closed-doc inputs;100755 preserved; onlyNode line changed; all execution NOT RUN. Packet is immutable.'
