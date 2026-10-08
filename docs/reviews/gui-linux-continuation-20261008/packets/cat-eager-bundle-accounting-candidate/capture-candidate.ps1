$ErrorActionPreference='Stop'
$repoRoot='C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$packetBase='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008'
$packetRoot=Join-Path $packetBase 'cat-eager-bundle-accounting-candidate'
$utf8=[Text.UTF8Encoding]::new($false)
$pin='59a9a568c445654f69215d735091c9b3e0405831'
$targets=@('frontend/scripts/check-bundle-budget.mjs','frontend/tests/bundle-budget.test.mjs')
function HashBytes([byte[]]$bytes) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
function FileHash($file) { HashBytes ([IO.File]::ReadAllBytes($file)) }
function WriteBytes($relative,[byte[]]$bytes) {
  $file=Join-Path $packetRoot $relative
  [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($file)) | Out-Null
  [IO.File]::WriteAllBytes($file,$bytes)
}
function WriteText($relative,$value) { WriteBytes $relative ($utf8.GetBytes($value.Replace("`r`n","`n"))) }
function GitBytes([string[]]$arguments,[string]$cwd=$repoRoot,[int[]]$allowed=@(0)) {
  $start=[Diagnostics.ProcessStartInfo]::new(); $start.FileName='git'; $start.WorkingDirectory=$cwd
  $start.UseShellExecute=$false; $start.CreateNoWindow=$true; $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
  $start.Environment['GIT_OPTIONAL_LOCKS']='0'
  foreach($argument in @('-c','core.autocrlf=false','-c','core.safecrlf=false')+$arguments) { $start.ArgumentList.Add($argument) }
  $process=[Diagnostics.Process]::Start($start)
  $stream=[IO.MemoryStream]::new(); $process.StandardOutput.BaseStream.CopyTo($stream)
  $diagnostic=$process.StandardError.ReadToEnd(); $process.WaitForExit()
  if($allowed -notcontains $process.ExitCode -or $diagnostic.Trim()) { throw ('Read-only Git did not complete quietly: '+$diagnostic) }
  ,$stream.ToArray()
}
function GitText([string[]]$arguments) { $utf8.GetString((GitBytes $arguments)).Trim() }
$headStart=GitText @('rev-parse','HEAD')
if(GitText @('status','--porcelain')) { throw 'Shared checkout is not clean; do not alter it' }
$rows=@()
foreach($relative in $targets) {
  $treeLine=GitText @('ls-tree',$pin,'--',$relative)
  if($treeLine -notmatch '^100644 blob ([a-f0-9]{40})\t') { throw ('Unexpected source mode/blob: '+$relative) }
  $blob=$Matches[1]
  $before=GitBytes @('cat-file','blob',($pin+':'+$relative))
  $working=[IO.File]::ReadAllBytes((Join-Path $repoRoot $relative))
  $current=GitBytes @('cat-file','blob',('HEAD:'+$relative))
  $early=GitBytes @('cat-file','blob',('ff7fb05d8cb80518833f10ca410e2581ba0b4725:'+$relative))
  if((HashBytes $before) -ne (HashBytes $working) -or (HashBytes $before) -ne (HashBytes $current) -or (HashBytes $before) -ne (HashBytes $early)) { throw ('Source target drift: '+$relative) }
  WriteBytes ('before/'+$relative) $before
  WriteBytes ('check-tree/'+$relative) $before
  $afterPath=Join-Path $packetRoot ('after/'+$relative)
  $after=[IO.File]::ReadAllBytes($afterPath)
  $rows+=@{path=$relative;condition='exact raw beforeimage +100644 mode';before=@{bytes=$before.Length;sha256=(HashBytes $before);blob=$blob;mode='100644'};after=@{bytes=$after.Length;sha256=(HashBytes $after);blob=$utf8.GetString((GitBytes @('hash-object','--no-filters',$afterPath))).Trim();mode='100644'};matches_ff7_current_working_and_committed=$true}
}
# Literal source span checks preserve existing measurement/font/limit logic.
$beforeScript=$utf8.GetString([IO.File]::ReadAllBytes((Join-Path $packetRoot ('before/'+$targets[0]))))
$afterScript=$utf8.GetString([IO.File]::ReadAllBytes((Join-Path $packetRoot ('after/'+$targets[0]))))
$spans=@()
foreach($span in @(@('measureGzipFiles','export function measureGzipFiles(','export function parseLimitKiB('),@('parseLimitKiB','export function parseLimitKiB(','export function assertRomanianFontSubsets('),@('assertRomanianFontSubsets','export function assertRomanianFontSubsets(','export function checkInitialBundle('))) {
  $start=$beforeScript.IndexOf($span[1]); $end=$beforeScript.IndexOf($span[2])
  $newStart=$afterScript.IndexOf($span[1]); $newEnd=$afterScript.IndexOf($span[2])
  if($start -lt 0 -or $end -le $start -or $newStart -lt 0 -or $newEnd -le $newStart) { throw 'Literal invariant span is missing' }
  $old=$beforeScript.Substring($start,$end-$start); $new=$afterScript.Substring($newStart,$newEnd-$newStart)
  if($old -cne $new) { throw ('Preserved helper changed: '+$span[0]) }
  $spans+=@{name=$span[0];sha256=(HashBytes ($utf8.GetBytes($old)));bytes=$utf8.GetByteCount($old);unchanged=$true}
}
if(!$afterScript.Contains('export const DEFAULT_INITIAL_GZIP_LIMIT_KIB = 120;')) { throw 'Default ceiling changed' }
$beforeTests=$utf8.GetString([IO.File]::ReadAllBytes((Join-Path $packetRoot ('before/'+$targets[1]))))
$afterTests=$utf8.GetString([IO.File]::ReadAllBytes((Join-Path $packetRoot ('after/'+$targets[1]))))
$originalWithImport=$beforeTests.Replace('  assertRomanianFontSubsets,',"  assertRomanianFontSubsets,`n  checkInitialBundle,")
$additions=[IO.File]::ReadAllText((Join-Path $packetRoot 'additions-source.mjs'))
if($afterTests -cne ($originalWithImport+$additions)) { throw 'Original tests were rewritten instead of appended' }
$newNames=@('explicit eager account roots include recursive JS/CSS once and exclude game routes','explicit eager account roots reject missing or malformed chunk files','initial budget counts eager account bytes that the static-only closure misses','initial budget requires the account root even when the caller supplies empty eager roots','initial budget fails closed for missing account JS, CSS, or nested import output','eager root options require bounded own string keys and deduplicate repeated roots','eager account closure rejects malformed shared files, CSS, and static import edges')
foreach($name in $newNames) { if(!$additions.Contains('test("'+$name+'",')) { throw 'Expected additive test source missing' } }
$historicalRef='93066854f67245d4b70c0ea97dc2401445a3218c'
$historicalPath='cat_de_roman_esti/web/static/.vite/manifest.json'
$historicalBytes=GitBytes @('cat-file','blob',($historicalRef+':'+$historicalPath))
$manifestText=$utf8.GetString($historicalBytes)
if(!$manifestText.Contains('"src/components/AccountBar.tsx": {') -or !$manifestText.Contains('"src": "src/components/AccountBar.tsx"')) { throw 'Historical manifest source key missing' }
WriteBytes 'inputs/historical-vite-manifest.json' $historicalBytes
$inputs=@()
foreach($relative in @('AGENTS.md','docs/STATUS.md','docs/PROGRAM.md','docs/execplans/s1-cat.md','docs/adr/0184-native-spa-toolchain-and-managed-output.md','frontend/src/App.tsx','frontend/src/components/AccountBar.tsx','frontend/vite.config.ts','frontend/package.json','versions.lock.json','scripts/gui-assets.mjs')) {
  $bytes=GitBytes @('cat-file','blob',($pin+':'+$relative))
  $current=GitBytes @('cat-file','blob',('HEAD:'+$relative))
  if((HashBytes $bytes) -ne (HashBytes $current)) { throw ('Relevant source contract drift: '+$relative) }
  $inputs+=@{path=$relative;bytes=$bytes.Length;sha256=(HashBytes $bytes);matches_current_committed=$true;captured='hash only; literal relevant source read'}
}
$combinedBindingsPath=Join-Path $packetBase 'linux-source-packet/source-bindings.json'
$combinedBytes=[IO.File]::ReadAllBytes($combinedBindingsPath)
$combinedText=$utf8.GetString($combinedBytes)
foreach($relative in $targets) { if($combinedText.Contains('"path": "'+$relative+'"')) { throw ('Task overlaps sealed38-path packet: '+$relative) } }
$combinedSealPath=Join-Path $packetBase 'linux-source-packet/SEAL.json'
$combinedSealHash=FileHash $combinedSealPath
$combinedSumsHash=FileHash (Join-Path $packetBase 'linux-source-packet/SHA256SUMS')
$patchBytes=GitBytes @('diff','--no-index','--binary','--src-prefix=a/','--dst-prefix=b/','before','after') $packetRoot @(0,1)
$patchLines=$utf8.GetString($patchBytes).Split("`n")
for($index=0;$index -lt $patchLines.Length;$index++) {
  if($patchLines[$index].StartsWith('diff --git ') -or $patchLines[$index].StartsWith('--- ') -or $patchLines[$index].StartsWith('+++ ')) { $patchLines[$index]=$patchLines[$index].Replace('a/before/','a/').Replace('b/after/','b/') }
}
WriteText 'conditional-eager-accounting.patch' ($patchLines -join "`n")
$patchPath=Join-Path $packetRoot 'conditional-eager-accounting.patch'
$quiet=GitBytes @('apply','--check','--whitespace=error-all',$patchPath) (Join-Path $packetRoot 'check-tree')
$headFinish=GitText @('rev-parse','HEAD'); $finalStatus=GitText @('status','--porcelain')
if($finalStatus) { throw 'Shared repository changed; report rather than alter' }
if((FileHash $combinedSealPath) -ne $combinedSealHash -or (FileHash (Join-Path $packetBase 'linux-source-packet/SHA256SUMS')) -ne $combinedSumsHash) { throw 'Earlier packet seal changed during capture' }
$record=[ordered]@{
  schema=1;state='SOURCE ONLY; UNAPPLIED; UNQUALIFIED; ALL RUNTIME NOT RUN';pin=$pin;pin_git_tree=(GitText @('rev-parse',($pin+'^{tree}')));observed_head_start=$headStart;observed_head_finish=$headFinish;shared_porcelain=$finalStatus;
  target_count=2;files=$rows;patch=@{path='conditional-eager-accounting.patch';sha256=(FileHash $patchPath);bytes=([IO.File]::ReadAllBytes($patchPath)).Length;scratch_check='git apply --check --whitespace=error-all success only; no application'};
  invariants=@{default_limit_kib=120;preserved_helpers=$spans;original_tests_count=4;original_tests='every original body/name/assertion unchanged; only named checkInitialBundle import added';new_tests_count=7;new_test_names=$newNames;zero_skip_source=$true;fixtures='ordinary fixed arithmetic synthetic JS/CSS; actual future checker causal excess test; no production measurement'};
  eager_binding=@{key='src/components/AccountBar.tsx';current_source='App lazy import and unconditional mount outside Routes; AccountBar returns auth-dependent UI after module load';historical_ref=$historicalRef;historical_manifest_path=$historicalPath;historical_manifest_blob='274396be5ca03191ee229786e13009472ad36eea';historical_manifest_bytes=$historicalBytes.Length;historical_manifest_sha256=(HashBytes $historicalBytes);historical_only=$true;new_build_observation='NOT RUN';source_behavior='entry/default static behavior preserved; explicit eager closure first validates required file/CSS/static imports; cycles/files deduplicate; all unselected dynamic game edges excluded';production_requirement='private frozen AccountBar key list passed unconditionally by checkInitialBundle; no caller/environment eager-root opt-out'};
  input_bindings=$inputs;earlier_packet=@{path='linux-source-packet';source_paths=38;source_bindings_sha256=(HashBytes $combinedBytes);seal_sha256=$combinedSealHash;checksum_manifest_sha256=$combinedSumsHash;disjoint_targets=$true;integration='may apply original38-path packet then this exact2-path amendment; original source/evidence is never rewritten'};
  pending=@('manager independent closed-byte review','Paul Linux tests/lint/typecheck/build and actual AccountBar manifest/complete bundle measurement','current STATUS/ADR owner integration without Source7 rollback','actual image/full/original fixture/privacy/CSP/budget/device gates; formal milestones remain pending');
  executed=@('literal source authoring/reads/hashes','read-only Git raw source/mode/blob/diff','scratch applicability check');not_run=@('product code','tests','compilers','parsers','validators','generators','formatters','builds','Docker','setup','environment probes','runtime qualification');product_repo_edits=$false;earlier_packet_edits=$false
}
WriteText 'source-bindings.json' (($record | ConvertTo-Json -Depth 9)+"`n")
WriteText 'scratch-apply-check.txt' "Read-only applicability check of this exact2-path patch against captured source preimages in scratch: success. Nothing applied; no tests, code, parser, compiler, build or validator executed.`n"
WriteText 'capture-summary.txt' ((@("Pin/observed HEAD: $headFinish",'Targets: exactly2 existing product paths; mode100644; ff7/59a9/current working bytes equal',"Patch SHA256: $($record.patch.sha256)",'4 original test bodies/assertions preserved +7 authored unrun additions','38-path packet disjoint; seals unchanged; source-binding metadata captured','Scratch git apply --check passed; shared porcelain empty; all runtime NOT RUN') -join "`n")+"`n")
$record.files | ForEach-Object { $_.path+': '+$_.before.sha256+' -> '+$_.after.sha256 }
'Patch SHA256: '+$record.patch.sha256
'Exactly2 targets; scratch applicability success; all runtime NOT RUN.'