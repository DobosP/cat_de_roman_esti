$ErrorActionPreference='Stop'
$packetRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-native-node-qualifier-alignment-candidate'
$repoRoot='C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$priorRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$pin='59a9a568c445654f69215d735091c9b3e0405831'
$utf8=[System.Text.UTF8Encoding]::new($false)
$lf=[string]([char]10)
function Sha([byte[]]$bytes){return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()}
function Git-Call([string]$working,[string[]]$arguments,[int[]]$allowed=@(0)){
 $start=[System.Diagnostics.ProcessStartInfo]::new('git')
 $start.WorkingDirectory=$working; $start.UseShellExecute=$false; $start.CreateNoWindow=$true
 $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true; $start.Environment['GIT_OPTIONAL_LOCKS']='0'
 foreach($arg in $arguments){$start.ArgumentList.Add($arg)}
 $process=[System.Diagnostics.Process]::Start($start); $memory=[System.IO.MemoryStream]::new()
 $process.StandardOutput.BaseStream.CopyTo($memory); $stderr=$process.StandardError.ReadToEnd(); $process.WaitForExit()
 if($allowed -notcontains $process.ExitCode){throw ('Read-only/scratch Git failed: '+$stderr)}
 return [pscustomobject]@{bytes=$memory.ToArray();stderr=$stderr;exit_code=$process.ExitCode}
}
function Git-Text([string]$working,[string[]]$arguments){return $utf8.GetString((Git-Call $working $arguments).bytes).TrimEnd([char]13,[char]10)}
function At([string]$relative){return [System.IO.File]::ReadAllText((Join-Path $packetRoot $relative),$utf8)}
function Save([string]$relative,[string]$text){[System.IO.File]::WriteAllText((Join-Path $packetRoot $relative),$text,$utf8)}
if((Git-Text $repoRoot @('rev-parse','HEAD')) -ne $pin -or (Git-Text $repoRoot @('status','--porcelain')) -ne ''){throw 'Relevant main sequencing drift'}
$oldNode='[[ "$(node --version)" == v24.* ]] || { printf ''Qualified Node 24 is required\n'' >&2; exit 2; }'
$newNode='[[ "$(node --version)" == v26.10.0 ]] || { printf ''Selected Node 26.10.0 is required\n'' >&2; exit 2; }'
$beforeScript=At 'before/scripts/qualify_go_toolchain.sh'
$afterScript=At 'after/scripts/qualify_go_toolchain.sh'
if($afterScript.Replace($newNode,$oldNode) -cne $beforeScript -or $afterScript -cne $beforeScript.Replace($oldNode,$newNode)){throw 'Qualifier has any change outside exact Node line'}
if(($beforeScript.Split([char]10).Length) -ne ($afterScript.Split([char]10).Length)){throw 'Qualifier lines changed'}
$scriptMeta=Git-Text $repoRoot @('ls-tree',$pin,'--','scripts/qualify_go_toolchain.sh')
if(!$scriptMeta.StartsWith('100755 blob 48032f620f260148362d37a409353181b0ccd481')){throw 'Qualifier executable/Git blob guard changed'}
$paths=@('scripts/qualify_go_toolchain.sh','docs/NATIVE_TOOLCHAIN.md','README.md','docs/agent-testing.md','docs/STATUS.md','docs/execplans/s1-cat.md')
$dependent=@('README.md','docs/agent-testing.md','docs/STATUS.md','docs/execplans/s1-cat.md')
$rows=@()
foreach($path in $paths){
 $beforePath=Join-Path $packetRoot ('before/'+$path)
 $afterPath=Join-Path $packetRoot ('after/'+$path)
 $before=[System.IO.File]::ReadAllBytes($beforePath)
 $after=[System.IO.File]::ReadAllBytes($afterPath)
 if($after -contains 13 -or ($after.Length -ge 3 -and $after[0] -eq 239 -and $after[1] -eq 187 -and $after[2] -eq 191)){throw ('Afterimage not rawLF/UTF8-noBOM: '+$path)}
 $mode=if($path -eq 'scripts/qualify_go_toolchain.sh'){'100755'}else{'100644'}
 $beforeBlob=Git-Text $repoRoot @('hash-object','--no-filters',$beforePath)
 $afterBlob=Git-Text $repoRoot @('hash-object','--no-filters',$afterPath)
 if($dependent -contains $path){
  $ancestor=[System.IO.File]::ReadAllBytes((Join-Path $priorRoot ('after/'+$path)))
  if((Sha $before) -ne (Sha $ancestor)){throw ('Dependent beforeimage drift: '+$path)}
  $provenance='EXACT CLOSED Cat9-doc AFTERIMAGE; dependency must be integrated; NOT rawmain'
 }else{
  $raw=(Git-Call $repoRoot @('cat-file','blob',($pin+':'+$path))).bytes
  if((Sha $before) -ne (Sha $raw) -or (Sha $before) -ne (Sha ([System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))))){throw ('Fresh rawmain preimage drift: '+$path)}
  $provenance='FRESH rawmain59a9 beforeimage, exact blob/mode/bytes'
 }
 $rows += [ordered]@{path=$path;provenance=$provenance;condition='exact beforeimage blob/SHA/raw bytes and declared mode required';before=[ordered]@{mode=$mode;blob=$beforeBlob;bytes=$before.Length;sha256=(Sha $before)};after=[ordered]@{mode=$mode;blob=$afterBlob;bytes=$after.Length;sha256=(Sha $after)}}
}
$afterNames=@([System.IO.Directory]::EnumerateFiles((Join-Path $packetRoot 'after'),'*',[System.IO.SearchOption]::AllDirectories) | ForEach-Object{[System.IO.Path]::GetRelativePath((Join-Path $packetRoot 'after'),$_).Replace('\','/')})
if($afterNames.Count -ne 6 -or @($afterNames | Where-Object{$paths -notcontains $_}).Count -ne 0){throw 'Unexpected product path scope'}
$beforeStatus=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'before/docs/STATUS.md'),$utf8)
$afterStatus=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'after/docs/STATUS.md'),$utf8)
if($beforeStatus.Count -ne 120 -or $afterStatus.Count -ne 120){throw 'STATUS budget changed'}
for($i=0;$i -lt 120;$i++){if($i -ne 4 -and $beforeStatus[$i] -cne $afterStatus[$i]){throw ('Protected dependent STATUS line changed: '+($i+1))}}
$agentCount=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'after/docs/agent-testing.md'),$utf8).Count
if($agentCount -gt 80){throw 'agent-testing line budget exceeded'}
$beforePlan=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'before/docs/execplans/s1-cat.md'),$utf8)
$afterPlan=[System.IO.File]::ReadAllLines((Join-Path $packetRoot 'after/docs/execplans/s1-cat.md'),$utf8)
$beforeHeadings=@($beforePlan | Where-Object{$_.StartsWith('## ')})
$afterHeadings=@($afterPlan | Where-Object{$_.StartsWith('## ')})
if($beforeHeadings.Count -ne 12 -or ($beforeHeadings -join $lf) -cne ($afterHeadings -join $lf)){throw 'Twelve plan sections changed'}
$historicalChecked=@($beforePlan | Where-Object{$_.StartsWith('- [x]')})
foreach($line in $historicalChecked){if($afterPlan -cnotcontains $line){throw 'Historical checked Progress record changed'}}
$allowedChangedPlan=@($beforePlan | Where-Object{$_.StartsWith('The future Linux integration order is ') -or $_.StartsWith('Current 2026-10-08 Windows continuation is ')})
if($allowedChangedPlan.Count -ne 2){throw 'Unexpected plan current-state anchors'}
$cursor=0
foreach($line in $beforePlan){
 if($allowedChangedPlan -ccontains $line){continue}
 while($cursor -lt $afterPlan.Length -and $afterPlan[$cursor] -cne $line){$cursor++}
 if($cursor -ge $afterPlan.Length){throw 'Historical/other plan line lost or reordered'}
 $cursor++
}
$diffCall=Git-Call $packetRoot @('-c','core.autocrlf=false','-c','core.safecrlf=false','diff','--no-index','--binary','--src-prefix=a/','--dst-prefix=b/','before','after') @(0,1)
$diffLines=$utf8.GetString($diffCall.bytes).Split([char]10)
$insideScript=$false
foreach($index in 0..($diffLines.Length-1)){
 $line=$diffLines[$index]
 if($line.StartsWith('diff --git ')){
  $line=$line.Replace('a/before/','a/').Replace('b/after/','b/')
  $insideScript=($line -ceq 'diff --git a/scripts/qualify_go_toolchain.sh b/scripts/qualify_go_toolchain.sh')
 }elseif($line.StartsWith('--- ') -or $line.StartsWith('+++ ')){
  $line=$line.Replace('a/before/','a/').Replace('b/after/','b/')
 }elseif($insideScript -and $line.StartsWith('index ')){
  if(!$line.EndsWith(' 100644')){throw 'Unexpected Windows scratch script mode header'}
  $line=$line.Substring(0,$line.Length-7)+' 100755'
 }
 $diffLines[$index]=$line
}
$patchText=$diffLines -join $lf
$scriptHeader='diff --git a/scripts/qualify_go_toolchain.sh b/scripts/qualify_go_toolchain.sh'+$lf
$headerAt=$patchText.IndexOf($scriptHeader,[System.StringComparison]::Ordinal)
if($headerAt -lt 0 -or !$patchText.Substring($headerAt+$scriptHeader.Length).StartsWith('index ')){throw 'Script portable patch header missing'}
if($patchText.Contains('old mode ') -or $patchText.Contains('new mode ')){throw 'Unexpected mode mutation'}
Save 'conditional-native-node-qualifier-alignment.patch' $patchText
$patchPath=Join-Path $packetRoot 'conditional-native-node-qualifier-alignment.patch'
$check=Git-Call (Join-Path $packetRoot 'check-tree') @('-c','core.autocrlf=false','-c','core.safecrlf=false','-c','core.filemode=false','apply','--check','--whitespace=error-all',$patchPath)
Save 'scratch-apply-check.txt' ('PASS: scratch git apply --check --whitespace=error-all, core.filemode=false for Windows representation only; patch never applied. Portable script index declares100755, independently bound to raw Git mode; Linux integration must verify100755.'+$lf+'stdout:'+$lf+$utf8.GetString($check.bytes)+'stderr:'+$lf+$check.stderr)
$patchBytes=[System.IO.File]::ReadAllBytes($patchPath)
$predecessorFiles=[ordered]@{}
foreach($name in @('SEAL.json','SHA256SUMS','source-bindings.json')){
 $predecessorFiles[$name]=Sha ([System.IO.File]::ReadAllBytes((Join-Path $priorRoot $name)))
}
$sourceBindings=[ordered]@{
 schema=1;state='SIX-PATH EXISTING-DECISION SOURCE ALIGNMENT; UNAPPLIED; UNQUALIFIED; ALL RUNTIME NOT RUN';
 pin=$pin;pin_git_tree='63a846a9974463ba360b4083cc53d0249f92fee7';observed_head_finish=(Git-Text $repoRoot @('rev-parse','HEAD'));shared_porcelain=(Git-Text $repoRoot @('status','--porcelain'));
 target_count=6;fresh_main_preimages=2;dependent_prior_doc_afterimages=4;files=$rows;
 predecessor=[ordered]@{packet='cat-accepted-calculation-doc-candidate';identity=$predecessorFiles;closed_payload_files=42;closed_payload_bytes=879190;mutation='NONE; dependent preimages copied without rewriting any predecessor';dependency='Apply Cat9 docs before these4 follow-on documentation hunks'};
 integration_order=@('original38 source packet','separate2 eager-accounting packet','CLOSED Cat9 docs packet','separate core2 docs packet, manager-owned external repository','this separate6 qualifier alignment packet after independent acceptance/exact guards');
 patch=[ordered]@{path='conditional-native-node-qualifier-alignment.patch';bytes=$patchBytes.Length;sha256=(Sha $patchBytes);scratch_check='PASS; no application';windows_filemode='scratch check disables Windows filemode comparison only; portable patch/script binding preserve100755'};
 single_line_script_change=[ordered]@{old=$oldNode;new=$newNode;old_bytes=([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'before/scripts/qualify_go_toolchain.sh'))).Length;new_bytes=([System.IO.File]::ReadAllBytes((Join-Path $packetRoot 'after/scripts/qualify_go_toolchain.sh'))).Length;every_other_script_byte_unchanged=$true;mode_before='100755';mode_after='100755';no_new_parser_or_support_policy=$true;no_npm_guard_or_other_command_change=$true};
 literal_preservation=[ordered]@{status_lines=120;status_only_changed_line=5;other119_status_lines_exact=$true;source6_source7_all_pins_receipts_counts_preserved=$true;agent_testing_lines=$agentCount;plan_sections=12;historical_checked_progress_records_preserved=$true;every_other_plan_line_preserved_except_current_state_and_future_order=$true;no_new_adr=$true;no_product_handover_path=$true};
 selected_pins=[ordered]@{node='26.10.0';npm='12.2.0, existing ADR0184 selection; no new script predicate';go='go version go1.27.1 linux/amd64, unchanged';provenance='existing ADR0184 and root/frontend .nvmrc literal source; engine-strict existing'};
 qualification=[ordered]@{source_application='UNAPPLIED';qualified='NO';tests_authored=0;tests_run=0;installed_version_observation='UNACQUIRED';standalone_result='UNACQUIRED';managed_output_proof='NOT EARNED';startup_gzip='UNACQUIRED';new_qualified_identity='NONE'};
 independent_review='draft reviews pending; closure recorded separately before seal';
 unchanged_rails='all other script bytes, failure exit2/no-skip, Go/scratch/disposablePG/Python-Rust/privacy/native/browser checks, static-root/order, every numeric budget, frozen/historical evidence, core1.2/release/tag, E3/device/M2/phase/S0b/owner holds';
 forbidden_execution=@('product code','tests','parsers','validators','generators','compilers','formatters','builds','Docker','setup','environment probes');
 repository_writes='NONE; no product/index/object/stage/commit/merge/push/reset/cleanup'
}
Save 'source-bindings.json' (($sourceBindings | ConvertTo-Json -Depth 14)+$lf)
Save 'literal-preservation-checks.txt' ('PASS native literal checks only:6 exact targets;2fresh main+4CLOSED-doc afterimage preimages; exactNode line inverse reproduces all4065 original script bytes;100755 portable metadata unchanged; STATUS120/all119 other lines exact; agent-testing'+$agentCount+'; all12 plan headings/checked records/otherhistorical lines preserved. No test or product/doc parser/validator executed.'+$lf)
Write-Output ('Prepared6-path patch '+(Sha $patchBytes)+'; qualifier4065->'+$sourceBindings.single_line_script_change.new_bytes+' bytes;100755 unchanged; STATUS120/agent-testing'+$agentCount+'; scratch check PASS.')
if($check.stderr.Length -gt 0){Write-Output ('Scratch Git stderr: '+$check.stderr)}
