$ErrorActionPreference = 'Stop'
$repoRoot = 'C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$packetRoot = 'C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$pin = '59a9a568c445654f69215d735091c9b3e0405831'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$lf = [string]([char]10)
function Git-Bytes([string]$working,[string[]]$arguments,[int[]]$exitCodes=@(0)) {
 $start = [System.Diagnostics.ProcessStartInfo]::new('git')
 $start.WorkingDirectory=$working; $start.UseShellExecute=$false; $start.CreateNoWindow=$true
 $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
 $start.Environment['GIT_OPTIONAL_LOCKS']='0'
 foreach($arg in $arguments){ $start.ArgumentList.Add($arg) }
 $process=[System.Diagnostics.Process]::Start($start)
 $memory=[System.IO.MemoryStream]::new()
 $process.StandardOutput.BaseStream.CopyTo($memory)
 $stderr=$process.StandardError.ReadToEnd(); $process.WaitForExit()
 if($exitCodes -notcontains $process.ExitCode){ throw ('Read-only/scratch Git failure: '+$stderr) }
 return ,$memory.ToArray()
}
function Git-Text([string]$working,[string[]]$arguments){ return $utf8.GetString((Git-Bytes $working $arguments)).TrimEnd([char]13,[char]10) }
function Sha([byte[]]$bytes){ return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
function Text-At([string]$relative){ return [System.IO.File]::ReadAllText((Join-Path $packetRoot $relative),$utf8) }
function Save([string]$relative,[string]$content){ [System.IO.File]::WriteAllText((Join-Path $packetRoot $relative),$content.Replace([string]([char]13)+[char]10,$lf),$utf8) }
if((Git-Text $repoRoot @('rev-parse','HEAD')) -ne $pin){ throw 'Relevant sequencing HEAD drift' }
if((Git-Text $repoRoot @('status','--porcelain')) -ne ''){ throw 'Shared repository changed; stop/report without modifying it' }
$paths=@('README.md','frontend/README.md','docs/STATUS.md','docs/PROGRAM.md','docs/execplans/s1-cat.md','docs/agent-testing.md','docs/adr/README.md','docs/adr/0020-bound-launch-runtime-and-first-load.md','docs/adr/0185-accepted-eager-startup-bundle-accounting.md')
$rows=@()
foreach($path in $paths){
 $afterPath=Join-Path $packetRoot ('after/'+$path)
 $after=[System.IO.File]::ReadAllBytes($afterPath)
 if($after -contains 13){ throw ('Afterimage notLF: '+$path) }
 $afterBlob=Git-Text $repoRoot @('hash-object','--no-filters',$afterPath)
 $beforePath=Join-Path $packetRoot ('before/'+$path)
 if(Test-Path -LiteralPath $beforePath){
  $before=[System.IO.File]::ReadAllBytes($beforePath)
  $current=Git-Bytes $repoRoot @('cat-file','blob',($pin+':'+$path))
  $working=[System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))
  if((Sha $before) -ne (Sha $current) -or (Sha $before) -ne (Sha $working)){ throw ('Relevant preimage drift: '+$path) }
  $meta=Git-Text $repoRoot @('ls-tree',$pin,'--',$path)
  $match=[regex]::Match($meta,'^(\d{6}) blob ([0-9a-f]{40})\t')
  if(!$match.Success -or $match.Groups[1].Value -ne '100644'){ throw ('Mode mismatch: '+$path) }
  $beforeBinding=[ordered]@{ mode='100644'; blob=$match.Groups[2].Value; bytes=$before.Length; sha256=(Sha $before) }
  $condition='exact raw beforeimage, Git blob and100644 mode'
 }else{
  if(Test-Path -LiteralPath (Join-Path $repoRoot $path)){ throw 'New ADR path became present' }
  if((Git-Text $repoRoot @('ls-tree',$pin,'--',$path)) -ne ''){ throw 'New ADR is present at pinned source' }
  $beforeBinding=$null; $condition='new-path absence; ADR0185 unclaimed in34 observed refs/pinned HEAD/index'
 }
 $rows += [ordered]@{ path=$path; condition=$condition; before=$beforeBinding; after=[ordered]@{ mode='100644'; blob=$afterBlob; bytes=$after.Length; sha256=(Sha $after) } }
}
$afterNames=@([System.IO.Directory]::EnumerateFiles((Join-Path $packetRoot 'after'),'*',[System.IO.SearchOption]::AllDirectories) | ForEach-Object { [System.IO.Path]::GetRelativePath((Join-Path $packetRoot 'after'),$_).Replace('\','/') })
if($afterNames.Count -ne 9 -or @($afterNames | Where-Object { $paths -notcontains $_ }).Count -ne 0){ throw 'Unexpected documentation target scope' }
$beforeStatus=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'before/docs/STATUS.md'),$utf8)
$afterStatus=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'after/docs/STATUS.md'),$utf8)
if($beforeStatus.Count -ne 120 -or $afterStatus.Count -ne 120){ throw 'STATUS line budget or source length changed' }
for($i=0;$i -lt 120;$i++){ if(@(2,4,119) -notcontains $i -and $beforeStatus[$i] -cne $afterStatus[$i]){ throw ('Protected STATUS line changed: '+($i+1)) } }
$oldStatus='Status: partially superseded by ADR-0184 for tooling/lint and generated-output handling; bounded session/input and120KiB acceptance remain'
$newStatus='Status: partially superseded by ADR-0184 for tooling/lint and generated-output handling, and ADR-0185 for first-load JS/CSS accounting; bounded session/input limits and the 120 KiB default ceiling remain'
if((Text-At 'after/docs/adr/0020-bound-launch-runtime-and-first-load.md').Replace($newStatus,$oldStatus) -cne (Text-At 'before/docs/adr/0020-bound-launch-runtime-and-first-load.md')){ throw 'ADR0020 body changed' }
$program=(Text-At 'PROGRAM_CLARIFICATION.md').TrimEnd([char]10)
$programAdded=$program+$lf+$lf+'Cat decision and pending application: [ADR-0185](adr/0185-accepted-eager-startup-bundle-accounting.md) and [S1 plan](execplans/s1-cat.md). Historical measurements retain their captured scopes.'+$lf+$lf
if((Text-At 'after/docs/PROGRAM.md').Replace($programAdded,'') -cne (Text-At 'before/docs/PROGRAM.md')){ throw 'PROGRAM contains changes outside narrow4.6 clarification' }
$beforePlan=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'before/docs/execplans/s1-cat.md'),$utf8)
$afterPlan=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'after/docs/execplans/s1-cat.md'),$utf8)
$cursor=0
foreach($line in $beforePlan){
 while($cursor -lt $afterPlan.Length -and $afterPlan[$cursor] -cne $line){ $cursor++ }
 if($cursor -ge $afterPlan.Length){ throw 'Historical ExecPlan line lost or reordered' }
 $cursor++
}
$beforeHeadings=@($beforePlan | Where-Object { $_.StartsWith('## ') })
$afterHeadings=@($afterPlan | Where-Object { $_.StartsWith('## ') })
if($beforeHeadings.Count -ne 12 -or ($beforeHeadings -join $lf) -cne ($afterHeadings -join $lf)){ throw 'Twelve-section plan changed' }
$agentLines=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'after/docs/agent-testing.md'),$utf8).Count
if($agentLines -gt 80){ throw 'agent-testing budget exceeded' }
if(!(Text-At 'after/docs/adr/README.md').StartsWith((Text-At 'before/docs/adr/README.md'),[System.StringComparison]::Ordinal)){ throw 'Existing ADR index history changed' }
$diff=$utf8.GetString((Git-Bytes $packetRoot @('-c','core.autocrlf=false','-c','core.safecrlf=false','diff','--no-index','--binary','--src-prefix=a/','--dst-prefix=b/','before','after') @(0,1)))
$diffLines=$diff.Split([char]10)
for($i=0;$i -lt $diffLines.Length;$i++){
 if($diffLines[$i].StartsWith('diff --git ') -or $diffLines[$i].StartsWith('--- ') -or $diffLines[$i].StartsWith('+++ ')){
  $diffLines[$i]=$diffLines[$i].Replace('a/before/','a/').Replace('b/after/','b/').Replace('a/after/','a/')
 }
}
Save 'conditional-accepted-calculation-docs.patch' ($diffLines -join $lf)
$checkRoot=Join-Path $packetRoot 'check-tree'
$patch=Join-Path $packetRoot 'conditional-accepted-calculation-docs.patch'
$checkOutput=$utf8.GetString((Git-Bytes $checkRoot @('-c','core.autocrlf=false','-c','core.safecrlf=false','apply','--check','--whitespace=error-all',$patch)))
Save 'scratch-apply-check.txt' ('PASS: git apply --check --whitespace=error-all against scratch raw preimages/new ADR absence only. No patch applied, no repository/index/object write.'+$lf+$checkOutput)
$inputs=@()
foreach($path in @('docs/GUI_MIGRATION_HANDOFF.md','docs/adr/0184-native-spa-toolchain-and-managed-output.md','frontend/package.json','frontend/vite.config.ts','frontend/src/App.tsx','scripts/qualify_go_toolchain.sh','run.sh','AGENTS.md')){
 $raw=Git-Bytes $repoRoot @('cat-file','blob',($pin+':'+$path))
 if((Sha $raw) -ne (Sha ([System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))))){ throw ('Input changed: '+$path) }
 $inputs += [ordered]@{ path=$path; bytes=$raw.Length; sha256=(Sha $raw); condition='hash only; unchanged; never a patch target' }
}
$sourcePackets=@()
foreach($packet in @('linux-source-packet','cat-eager-bundle-accounting-candidate')){
 $sourceRoot=Join-Path ([System.IO.Path]::GetDirectoryName($packetRoot)) $packet
 foreach($file in @('source-bindings.json','SEAL.json')){
  $bytes=[System.IO.File]::ReadAllBytes((Join-Path $sourceRoot $file))
  $sourcePackets += [ordered]@{ packet=$packet; file=$file; bytes=$bytes.Length; sha256=(Sha $bytes); mutation='NONE; existing sealed source layer preserved' }
 }
}
$patchBytes=[System.IO.File]::ReadAllBytes($patch)
$binding=[ordered]@{
 schema=1; state='OWNER ACCEPTED CALCULATION; DOC SOURCE CANDIDATE; UNAPPLIED; UNQUALIFIED; ALL RUNTIME NOT RUN';
 pin=$pin; pin_git_tree=(Git-Text $repoRoot @('rev-parse',($pin+'^{tree}'))); observed_head_finish=(Git-Text $repoRoot @('rev-parse','HEAD')); observed_porcelain_finish=(Git-Text $repoRoot @('status','--porcelain'));
 target_count=9; existing_targets=8; new_targets=1; files=$rows; unchanged_inputs=$inputs; immutable_source_layers=$sourcePackets;
 patch=[ordered]@{ path='conditional-accepted-calculation-docs.patch'; bytes=$patchBytes.Length; sha256=(Sha $patchBytes); scratch_check='PASS, check only; no application' };
 literal_preservation=[ordered]@{ status_lines=120; status_only_changed_lines=@(3,5,120); other117_status_lines_exact=$true; source6_source7_preserved=$true; agent_testing_lines=$agentLines; adr0020_only_status_metadata=$true; program_only4_6_addition=$true; every_historical_execplan_line_preserved_in_order=$true; execplan_section_count=12; historical_gui_handoff_unchanged=$true; no_new_product_handover_path=$true };
 owner_acceptance=[ordered]@{ direct_request='accept this new calculation update all documentation with this new calculation and continue'; recorded_at='2026-10-08T13:12:38.2521563Z'; source_application='UNAPPLIED'; qualification='UNQUALIFIED'; new_measurement='UNACQUIRED'; amended_contracts_authored=11; amended_contracts_run=0 };
 integration_order=@('original38-path linux-source-packet','separate2-path cat-eager-bundle-accounting-candidate','separate9-path accepted-calculation documentation packet');
 numeric_requirements=[ordered]@{ frontend_default_combined_js_css_bytes=122880; canonical_js_limit_bytes=40960; canonical_js_target_bytes=30720; changes='NONE' };
 adr0185_guard='No0185 filename in34 observed refs plus pinned HEAD; exact new path absent; working/index claim absent. Recheck immediately before Linux integration; stop on relevant drift.';
 no_runtime=@('product execution','tests','parsers','compilers','validators','generators','formatters','builds','Docker','setup','environment probes');
 repository_mutation='NONE; no apply/index/stage/commit/merge/push/cleanup'; independent_review='draft review requested; recorded separately before sealing'
}
Save 'source-bindings.json' (($binding | ConvertTo-Json -Depth 15)+$lf)
Save 'literal-review-checks.txt' ('PASS native literal metadata/span checks only:9 exact paths, STATUS120 and117 unchanged lines, agent-testing'+$agentLines+', ADR0020 Status-only, PROGRAM4.6-only additive paragraph, every historical ExecPlan line in order/all12 sections, old ADR index prefix exact, handoff/source layers unchanged. No product/doc parser or validator executed.'+$lf)
Write-Output ('Prepared9-path portable patch '+(Sha $patchBytes)+'; scratch apply --check PASS; STATUS120/agent-testing'+$agentLines+'; no repository writes or runtime.')
