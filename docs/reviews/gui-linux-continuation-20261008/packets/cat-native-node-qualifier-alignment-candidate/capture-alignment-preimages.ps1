$ErrorActionPreference='Stop'
$repoRoot='C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$packetRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-native-node-qualifier-alignment-candidate'
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
function Save([string]$relative,[string]$text){
 $absolute=Join-Path $packetRoot $relative
 [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($absolute)) | Out-Null
 [System.IO.File]::WriteAllText($absolute,$text,$utf8)
}
if((Git-Text @('rev-parse','HEAD')) -ne $pin -or (Git-Text @('status','--porcelain')) -ne ''){throw 'Relevant source sequencing drift; stop without writes'}
$priorGuards=[ordered]@{
 'SEAL.json'='a5e90bd370c1659a3164a011467a7bef396d129a9cf1b75293f535bd4ea9d57b';
 'SHA256SUMS'='6fc8a9bfa8bb7d51686221bfe767196ae1d2e63e52b8715136368b4bc0603a71';
 'source-bindings.json'='fa99393d5a653309600e5bca62637c53ee15fd043fa78e0be23ba85b179949d6'
}
foreach($file in $priorGuards.Keys){
 if((Sha ([System.IO.File]::ReadAllBytes((Join-Path $priorRoot $file)))) -ne $priorGuards[$file]){throw ('Closed predecessor identity mismatch: '+$file)}
}
if((Sha ([System.IO.File]::ReadAllBytes((Join-Path $analysisRoot '2026-10-08-node-qualification-source-analysis.txt')))) -ne 'a8c591e662ce824fb74975a5363543ff1bec259f6ac725432ba5e936c861bcc6'){throw 'Closed accepted analysis report drift'}
if((Sha ([System.IO.File]::ReadAllBytes((Join-Path $analysisRoot 'SHA256SUMS.txt')))) -ne '17230e995663e620545e621da625169189a41a7bdee2434f1ce001a1d99f0179'){throw 'Closed accepted analysis seal drift'}
$dependent=[ordered]@{
 'README.md'='5aafd3aab31a8d0476aff309d54e04bf3cf27e9861d02629fa6e61bca647fcef';
 'docs/agent-testing.md'='4f2551c1853f9c1cea4c1e07edf635466e586b6808c1758fc19717b32be1245d';
 'docs/STATUS.md'='3605b9ca92227e11aab5210bae511f7ba2a242c3560412278e13ce7ce68cfa2e';
 'docs/execplans/s1-cat.md'='84ec1dc6edba7670ef1a0b3225d4874c7f382dd9d42dde53f688aebb4a84effa'
}
$rows=@()
foreach($path in @('scripts/qualify_go_toolchain.sh','docs/NATIVE_TOOLCHAIN.md')+@($dependent.Keys)){
 if($dependent.Contains($path)){
  $sourcePath=Join-Path $priorRoot ('after/'+$path)
  $raw=[System.IO.File]::ReadAllBytes($sourcePath)
  if((Sha $raw) -ne $dependent[$path]){throw ('Dependent exact afterimage mismatch: '+$path)}
  $mode='100644'; $blob=Git-Text @('hash-object','--no-filters',$sourcePath)
  $provenance='EXACT CLOSED Cat9-doc afterimage; not raw main; apply after predecessor'
 }else{
  $meta=Git-Text @('ls-tree',$pin,'--',$path)
  $match=[regex]::Match($meta,'^(\d{6}) blob ([0-9a-f]{40})\t')
  if(!$match.Success){throw ('Fresh Git metadata absent: '+$path)}
  $mode=$match.Groups[1].Value; $blob=$match.Groups[2].Value
  $raw=Git-Bytes @('cat-file','blob',($pin+':'+$path))
  if((Sha $raw) -ne (Sha ([System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))))){throw ('Raw/working fresh preimage differs: '+$path)}
  $provenance='FRESH exact raw main59a9 Git preimage'
 }
 if($path -eq 'scripts/qualify_go_toolchain.sh' -and ($mode -ne '100755' -or $blob -ne '48032f620f260148362d37a409353181b0ccd481' -or $raw.Length -ne 4065 -or (Sha $raw) -ne 'c7e65ad67627e5060a154f3aef6091e46057562456a6d704d7d1e7a85d90ab11')){throw 'Qualifier exact expected source guard failed'}
 foreach($tree in @('before','after','check-tree')){
  $destination=Join-Path $packetRoot ($tree+'/'+$path)
  [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($destination)) | Out-Null
  [System.IO.File]::WriteAllBytes($destination,$raw)
 }
 $rows += [ordered]@{path=$path; provenance=$provenance; condition='exact raw bytes/SHA/Git blob and declared mode; dependent source layer must already be integrated'; before=[ordered]@{mode=$mode;blob=$blob;bytes=$raw.Length;sha256=(Sha $raw)}}
}
$inputs=@()
foreach($path in @('.nvmrc','frontend/.nvmrc','frontend/package.json','frontend/.npmrc','docs/adr/0184-native-spa-toolchain-and-managed-output.md','docs/adr/0168-qualify-complete-native-toolchain.md','docs/GUI_MIGRATION_HANDOFF.md')){
 $raw=Git-Bytes @('cat-file','blob',($pin+':'+$path))
 $inputs += [ordered]@{path=$path; metadata=(Git-Text @('ls-tree',$pin,'--',$path));bytes=$raw.Length;sha256=(Sha $raw);scope='hash/literal source only; never modified'}
 if($path -eq '.nvmrc' -or $path -eq 'frontend/.nvmrc'){
  if($utf8.GetString($raw).Trim() -cne '26.10.0'){throw 'Selected Node pin differs'}
 }
}
$binding=[ordered]@{schema=1;state='SOURCE ALIGNMENT CANDIDATE; UNAPPLIED; UNQUALIFIED; ALL RUNTIME NOT RUN';pin=$pin;pin_git_tree=(Git-Text @('rev-parse',($pin+'^{tree}')));observed_porcelain='';fresh_main_targets=2;dependent_prior_doc_targets=4;target_count=6;files=$rows;inputs=$inputs;predecessor=$priorGuards;accepted_analysis_report_sha256='a8c591e662ce824fb74975a5363543ff1bec259f6ac725432ba5e936c861bcc6';accepted_analysis_seal_sha256='17230e995663e620545e621da625169189a41a7bdee2434f1ce001a1d99f0179'}
Save 'capture-bindings.json' (($binding | ConvertTo-Json -Depth 12)+$lf)
Save 'capture-summary.txt' ('Captured2 fresh rawmain preimages and4 exact dependent CLOSED Cat9-doc afterimages; prior immutable seal/manifests/source bindings and accepted analysis checked. No repository/code execution. All runtime NOT RUN; no test authored. Script mode100755 preserved semantically in bindings/patch.'+$lf)
Write-Output 'Captured exactly6 preimages:2 rawmain +4 closed-doc afterimages. Prior closed packets untouched. Shared main clean.'
