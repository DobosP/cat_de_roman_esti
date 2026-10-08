$ErrorActionPreference = 'Stop'
$packetRoot = 'C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$repoRoot = 'C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$pin = '59a9a568c445654f69215d735091c9b3e0405831'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$lf = [string]([char]10)
function Save([string]$path,[string]$content) { [System.IO.File]::WriteAllText((Join-Path $packetRoot $path),$content,$utf8) }
function Sha([byte[]]$bytes){ return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
function Git-Bytes([string[]]$arguments) {
 $start=[System.Diagnostics.ProcessStartInfo]::new('git')
 $start.WorkingDirectory=$repoRoot; $start.UseShellExecute=$false; $start.CreateNoWindow=$true
 $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true; $start.Environment['GIT_OPTIONAL_LOCKS']='0'
 foreach($arg in $arguments){ $start.ArgumentList.Add($arg) }
 $process=[System.Diagnostics.Process]::Start($start); $memory=[System.IO.MemoryStream]::new()
 $process.StandardOutput.BaseStream.CopyTo($memory); $stderr=$process.StandardError.ReadToEnd(); $process.WaitForExit()
 if($process.ExitCode -ne 0){ throw ('Read-only Git failed: '+$stderr) }
 return ,$memory.ToArray()
}
function Git-Text([string[]]$arguments){return $utf8.GetString((Git-Bytes $arguments)).TrimEnd([char]13,[char]10)}
if(Test-Path -LiteralPath (Join-Path $packetRoot 'SEAL.json')){ throw 'Packet already sealed; never rewrite' }
if((Git-Text @('rev-parse','HEAD')) -ne $pin -or (Git-Text @('status','--porcelain')) -ne ''){ throw 'Source changed before closure; stop sequencing' }
foreach($absolute in [System.IO.Directory]::EnumerateFiles((Join-Path $packetRoot 'before'),'*',[System.IO.SearchOption]::AllDirectories)){
 $path=[System.IO.Path]::GetRelativePath((Join-Path $packetRoot 'before'),$absolute).Replace('\','/')
 $before=[System.IO.File]::ReadAllBytes($absolute)
 $current=Git-Bytes @('cat-file','blob',($pin+':'+$path))
 $working=[System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))
 if((Sha $before) -ne (Sha $current) -or (Sha $before) -ne (Sha $working)){ throw ('Relevant doc drift before seal: '+$path) }
}
$adrPath='docs/adr/0185-accepted-eager-startup-bundle-accounting.md'
if(Test-Path -LiteralPath (Join-Path $repoRoot $adrPath)){ throw 'NewADR absence guard failed' }
if([System.IO.File]::ReadAllText((Join-Path $repoRoot 'docs/adr/README.md'),$utf8).Contains('0185')){ throw 'NewADR index guard failed' }
$refs=@((Git-Text @('for-each-ref','--format=%(refname)')).Split([char]10,[System.StringSplitOptions]::RemoveEmptyEntries))
foreach($ref in @($pin)+$refs){
 foreach($name in (Git-Text @('ls-tree','-r','--name-only',$ref,'--','docs/adr')).Split([char]10,[System.StringSplitOptions]::RemoveEmptyEntries)){
  if($name.StartsWith('docs/adr/0185-',[System.StringComparison]::Ordinal)){ throw 'NewADR ref claim appeared; stop' }
 }
}
Save 'source-review-disposition.md' 'Valid until: any bound source, accepted rule, exact packet byte or relevant ADR claim changes — then treat as history.

2026-10-08 closed source review — accepted calculation documentation

Owner acceptance: Paul directly instructed “accept this new calculation update all documentation with this new calculation and continue”, recorded 2026-10-08T13:12:38.2521563Z. This establishes the calculation decision, not source application, a new measurement or runtime qualification.

Exactly nine product paths are proposed: README.md; frontend/README.md; docs/STATUS.md; docs/PROGRAM.md; docs/execplans/s1-cat.md; docs/agent-testing.md; docs/adr/README.md; docs/adr/0020-bound-launch-runtime-and-first-load.md; new docs/adr/0185-accepted-eager-startup-bundle-accounting.md. Eight exact raw preimages/modes and one new-path absence are bound. ADR0185 was absent in34 observed refs plus pinned HEAD, current index and working ADR directory. Recheck before integration.

Independent read-only source reviews are CLOSED:
- build_identity_api: ADR0020 Date/body/evidence remain exact after Status-only replacement. Calculator/default-helper/font/limit/qualification prose accurate. The one route-loading wording issue is corrected to route-lazy.
- build_identity_contract: PROGRAM4.6-only additive clarification, all12 plan sections and historical metrics/lines, E1/E3/phase/device/green-unit holds and38→2→docs order retained. No handover path.
- build_identity_tests: STATUS120 lines and agent-testing78; STATUS changes only lines3,5,120 with all117 other lines exact, including Source6/Source7. Current standalone qualifier source alignment, Docker recipe pending qualification and manual/opt-in CI facts are corrected. Final recheck found no remaining wording blocker.
Root also checked native literal spans/order and raw hashes. These are source reviews, not executed product/doc validators or runtime tests.

The PROGRAM_CLARIFICATION.md literal block is identical and portable for the manager''s separate core PROGRAM amendment. Its decision reference is repository-qualified Cat text; Cat-local Markdown links sit outside it. No whole-file mirror or core/teacher/social source path is included.

Preservation: no historical ADR body, expired GUI_MIGRATION_HANDOFF.md, frozen original30/archive/report/baseline, accepted immutable code packet or other owner worktree was modified. Source6/Source7 current evidence remains unchanged. All numeric limits, font policy, React19/UI0.3 throughM1, immutable core1.2 release/tag, E3 budget-red/formal qualification, same-final-SHA trust -> GREEN unit -> KIT_BUMP, device/M2/S0b/teacher/social/live/soak and production holds remain.

Current source-only state: original38-path code packet, separate2-path calculator and this9-path documentation proposal are UNAPPLIED and UNQUALIFIED. The amended4+7=11 bundle contracts are authored NOT RUN. Fresh Vite manifest/mandatory AccountBar-inclusive inventory/per-file gzip9 sum is UNACQUIRED. No product bytes, savings, measured total or budget PASS is claimed. Default helper, gui-baseline per-key closures and gui-assets initial_gzip_bytes keep static-only scope.

Known next bounded source task: scripts/qualify_go_toolchain.sh requiresNode24 before later npm-ci of selectedNode26 source; standalone source alignment remains pending and separate from the owning GUI wrapper. This documentation packet states that fact; no code repair is included. NATIVE_TOOLCHAIN''s retained recipe remains a source-alignment follow-up, not fresh selected-toolchain qualification.

Runtime/product code/tests/parsers/compilers/validators/generators/formatters/builds/Docker/setup/environment probes: ALL NOT RUN. Repository apply/index/stage/commit/merge/push/reset/cleanup: NONE. Main59a9a568c445654f69215d735091c9b3e0405831 remains clean.
'
Save '2026-10-08-portable-doc-continuation.txt' 'Valid until: guarded integration, a relevant source/ADR claim change, or a superseding accepted calculation — then treat as history.

2026-10-08 portable accepted-calculation documentation continuation

This dated continuation exists only inside the new _temp packet. No new repository dated handover is proposed; expired docs/GUI_MIGRATION_HANDOFF.md stays byte-for-byte. Current source decision and pending obligations are carried by STATUS and the living S1 plan.

Base: Cat main59a9a568c445654f69215d735091c9b3e0405831, Git tree63a846a9974463ba360b4083cc53d0249f92fee7, empty porcelain. Exactly8 existing doc preimages and1 newADR0185 path; metadata/hashes/modes in source-bindings.json. SOURCE ONLY, UNAPPLIED, UNQUALIFIED. Parent manager acceptance of this documentation packet remains pending.

Portable layers, in order:
1. Original sealed linux-source-packet, exactly38 product paths; source-bindings SHA256845e7941ffb646c85c7778a1797cc388943e2c8b5072f8f40cb4dd8f8164ac3a.
2. Separate sealed cat-eager-bundle-accounting-candidate, exactly2 paths; patch SHA256e971934f6c57f59d8ca1fd4167bc19d5734898eac063c64be278fee09ce4fda1.
3. This separate9-path documentation packet and exact conditional-accepted-calculation-docs.patch.
Do not rewrite or combine those immutable packets. Verify manifests, exact preimage blobs/modes/raw bytes and new-path/ADR-index absence before applying any layer. Stop for owner sequencing on relevant drift; preserve current Source6/Source7 facts rather than overwriting a later status. No merged40-path patch or qualified identity is created here.

The accepted method is the deduplicated union of all entry/static JS/CSS and immediately mounted AccountBar recursive STATIC JS/CSS. Required root/import/output failures refuse. Dynamic descendants/game routes remain outside this bounded set. Build checker has fixed required root; default collector and frozen reports remain static-only. Frontend default122880B and canonical JS40960B/30720B target plus separate CSS/font policy remain.

All11 amended bundle contracts are authored NOT RUN, and current manifest/startup gzip is UNACQUIRED. Paul will execute/refine on Linux through current authorized owner admission and evidence preservation. Acquire genuine current manifest/root key/file inventory/per-file gzip9 measurement and execute all applicable existing lanes; retain any real120KiB or40KiB failures. No native/doc validator, compiler, parser, test, build, Docker, setup or environment probe ran here.

After actual application/validation, update living current-state docs from genuine observations before a product commit; this unapplied checkpoint is not a qualified result. Preserve all historical baselines, ADR bodies, old failed/pass receipts, core1.2 immutable release/tag, E3 budget-red/phase/device/M2/S0b/production holds and same-final-SHA trust -> GREEN unit -> canonical KIT_BUMP.

Manager separately copies only PROGRAM_CLARIFICATION.md''s literal paragraph into core PROGRAM and updates core current status. Cat-local adjacent links are outside that block; its repository-qualified ADR reference is valid in both owner contexts. No core/teacher/social file is a product target here.

Known pending source alignment: standalone Node24 qualifier versus selectedNode26/npm-ci; separate from GUI wrapper. Manager dispatches bounded alignment after this docs/core sequence. No source fix is invented or bundled.

Scratch-only git apply --check --whitespace=error-all passed; patch was not applied. All runtime NOT RUN. Repository/main/index/branches/worktrees and existing immutable packets were never written.
'
$bindingPath=Join-Path $packetRoot 'source-bindings.json'
$binding=[System.IO.File]::ReadAllText($bindingPath,$utf8)
$old='"independent_review": "draft review requested; recorded separately before sealing"'
$new='"independent_review": "CLOSED three-agent source reviews; corrected route-lazy/current qualifier/README facts; final rechecks found no blocking wording; all runtime NOT RUN"'
if(!$binding.Contains($old)){throw 'Source review binding anchor missing'}
[System.IO.File]::WriteAllText($bindingPath,$binding.Replace($old,$new),$utf8)
$receipt='Valid until: any bound source or packet changes — then treat as history.'+$lf+$lf+
 '2026-10-08 final source-only closure. HEAD '+$pin+'/tree63a846a9974463ba360b4083cc53d0249f92fee7; empty porcelain; all8 raw doc preimages/current working bytes reverified; newADR absence/index/ref guard rechecked across'+$refs.Count+' refs plus pinned HEAD. Existing GUI handoff and sealed code layers unchanged. No repository/index/object/branch/worktree write. All runtime/tests/product parsers/compilers/validators/formatters/generators/builds/Docker/setup/environment probes NOT RUN. STATUS120/agent-testing78; source review closed.'+$lf
Save 'closing-repository-receipt.txt' $receipt
$paths=[string[]]@([System.IO.Directory]::EnumerateFiles($packetRoot,'*',[System.IO.SearchOption]::AllDirectories) | ForEach-Object { [System.IO.Path]::GetRelativePath($packetRoot,$_).Replace('\','/') } | Where-Object { $_ -ne 'SHA256SUMS' -and $_ -ne 'SEAL.json' })
[System.Array]::Sort($paths,[System.StringComparer]::Ordinal)
$manifestLines=[System.Collections.Generic.List[string]]::new()
$totalBytes=[long]0
foreach($relative in $paths){
 $bytes=[System.IO.File]::ReadAllBytes((Join-Path $packetRoot $relative))
 $manifestLines.Add((Sha $bytes)+'  '+$relative); $totalBytes+=$bytes.Length
}
Save 'SHA256SUMS' (($manifestLines -join $lf)+$lf)
$patchSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'conditional-accepted-calculation-docs.patch')))
$bindingSha=Sha ([System.IO.File]::ReadAllBytes($bindingPath))
$manifestSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'SHA256SUMS')))
$programSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'PROGRAM_CLARIFICATION.md')))
$seal=[ordered]@{
 schema=1; kind='closed nine-path accepted-calculation portable documentation proposal';
 pin=$pin; pin_git_tree='63a846a9974463ba360b4083cc53d0249f92fee7'; target_paths=@('README.md','frontend/README.md','docs/STATUS.md','docs/PROGRAM.md','docs/execplans/s1-cat.md','docs/agent-testing.md','docs/adr/README.md','docs/adr/0020-bound-launch-runtime-and-first-load.md',$adrPath);
 existing_targets=8; new_targets=1; payload_files=$paths.Count; payload_bytes=$totalBytes;
 sha256sums_sha256=$manifestSha; patch_sha256=$patchSha; source_bindings_sha256=$bindingSha; program_clarification_sha256=$programSha;
 native_literal_status_lines=120; native_literal_agent_testing_lines=78; historical_records_preserved=$true;
 owner_calculation_decision='ACCEPTED'; applied=$false; qualified=$false; new_measurement='UNACQUIRED'; amended_contracts_authored=11; amended_contracts_run=0;
 independent_source_reviews='CLOSED; no remaining wording blocker'; independent_manager_acceptance='PENDING';
 scratch_apply_check='PASS; check only, never applied'; shared_porcelain=''; existing_code_packet_mutations=0;
 not_run=@('product code','tests','parsers','compilers','validators','generators','formatters','builds','Docker','setup','environment probes','runtime qualification');
 no_product_handover_target=$true; no_repository_write=$true
}
Save 'SEAL.json' (($seal | ConvertTo-Json -Depth 8)+$lf)
$sealSha=Sha ([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'SEAL.json')))
Write-Output ('CLOSED '+$paths.Count+' payload files / '+$totalBytes+' bytes')
Write-Output ('PATCH '+$patchSha)
Write-Output ('SOURCE_BINDINGS '+$bindingSha)
Write-Output ('PROGRAM_BLOCK '+$programSha)
Write-Output ('SHA256SUMS '+$manifestSha)
Write-Output ('SEAL '+$sealSha)
Write-Output 'Main clean; nine documentation targets only; source proposals unapplied/unqualified; all runtime NOT RUN. Packet is now immutable.'
