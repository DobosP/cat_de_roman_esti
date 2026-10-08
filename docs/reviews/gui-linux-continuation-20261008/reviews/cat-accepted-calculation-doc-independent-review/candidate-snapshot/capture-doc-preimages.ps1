$ErrorActionPreference = 'Stop'
$repoRoot = 'C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$packetRoot = 'C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$pin = '59a9a568c445654f69215d735091c9b3e0405831'
$utf8 = [System.Text.UTF8Encoding]::new($false)
function Read-GitBytes([string[]]$gitArgs) {
  $start = [System.Diagnostics.ProcessStartInfo]::new('git')
  $start.WorkingDirectory = $repoRoot
  $start.UseShellExecute = $false
  $start.CreateNoWindow = $true
  $start.RedirectStandardOutput = $true
  $start.RedirectStandardError = $true
  $start.Environment['GIT_OPTIONAL_LOCKS'] = '0'
  foreach ($arg in $gitArgs) { $start.ArgumentList.Add($arg) }
  $process = [System.Diagnostics.Process]::Start($start)
  $memory = [System.IO.MemoryStream]::new()
  $process.StandardOutput.BaseStream.CopyTo($memory)
  $stderr = $process.StandardError.ReadToEnd()
  $process.WaitForExit()
  if ($process.ExitCode -ne 0) { throw "Read-only Git failed: $stderr" }
  return ,$memory.ToArray()
}
function Git-Text([string[]]$gitArgs) { return $utf8.GetString((Read-GitBytes $gitArgs)).TrimEnd("`r", "`n") }
function Sha256([byte[]]$bytes) { return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
function Save-Lf([string]$relative, [string]$content) {
  $absolute = Join-Path $packetRoot $relative
  [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($absolute)) | Out-Null
  [System.IO.File]::WriteAllText($absolute, $content.Replace("`r`n", "`n"), $utf8)
}
if ((Git-Text @('rev-parse','HEAD')) -ne $pin) { throw 'HEAD drift; stop for sequencing' }
if ((Git-Text @('status','--porcelain')) -ne '') { throw 'Shared main not clean; report without changing it' }
$existingPaths = @(
 'README.md', 'frontend/README.md', 'docs/STATUS.md', 'docs/PROGRAM.md',
 'docs/execplans/s1-cat.md', 'docs/agent-testing.md', 'docs/adr/README.md',
 'docs/adr/0020-bound-launch-runtime-and-first-load.md'
)
$newPath = 'docs/adr/0185-accepted-eager-startup-bundle-accounting.md'
$claims = @()
$refs = @( (Git-Text @('for-each-ref','--format=%(refname)')).Split("`n",[System.StringSplitOptions]::RemoveEmptyEntries) )
foreach ($ref in @($pin) + $refs) {
 $names = Git-Text @('ls-tree','-r','--name-only',$ref,'--','docs/adr')
 foreach ($name in $names.Split("`n",[System.StringSplitOptions]::RemoveEmptyEntries)) {
   if ($name.StartsWith('docs/adr/0185-',[System.StringComparison]::Ordinal)) { $claims += "$ref $name" }
 }
}
if ($claims.Count -ne 0) { throw '0185 already claimed; stop for sequencing' }
if (Test-Path -LiteralPath (Join-Path $repoRoot $newPath)) { throw 'New ADR path is present' }
if ([System.IO.File]::ReadAllText((Join-Path $repoRoot 'docs/adr/README.md')).Contains('0185')) { throw 'ADR index claim exists' }
$rows = @()
foreach ($path in $existingPaths) {
 $meta = Git-Text @('ls-tree',$pin,'--',$path)
 $match = [regex]::Match($meta,'^(\d{6}) blob ([0-9a-f]{40})\t')
 if (!$match.Success -or $match.Groups[1].Value -ne '100644') { throw "Unexpected target metadata: $path" }
 $raw = Read-GitBytes @('cat-file','blob',"${pin}:$path")
 $working = [System.IO.File]::ReadAllBytes((Join-Path $repoRoot $path))
 if ((Sha256 $raw) -ne (Sha256 $working)) { throw "Working/raw Git preimage differs: $path" }
 foreach ($tree in @('before','after','check-tree')) {
   $destination = Join-Path $packetRoot "$tree/$path"
   [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($destination)) | Out-Null
   [System.IO.File]::WriteAllBytes($destination,$raw)
 }
 $rows += [ordered]@{ path=$path; condition='exact raw preimage, blob and100644 mode'; before=[ordered]@{ mode='100644'; blob=$match.Groups[2].Value; bytes=$raw.Length; sha256=(Sha256 $raw) } }
}
$rows += [ordered]@{ path=$newPath; condition='new-path absence and no0185 claim at pinned HEAD/all observed refs/index/working ADR directory'; before=$null }
$inputPaths = @('docs/GUI_MIGRATION_HANDOFF.md','docs/adr/0184-native-spa-toolchain-and-managed-output.md','frontend/package.json','frontend/vite.config.ts','frontend/src/App.tsx','scripts/qualify_go_toolchain.sh','run.sh','AGENTS.md')
$inputs = @()
foreach ($path in $inputPaths) {
 $meta = Git-Text @('ls-tree',$pin,'--',$path)
 $raw = Read-GitBytes @('cat-file','blob',"${pin}:$path")
 $inputs += [ordered]@{ path=$path; metadata=$meta; bytes=$raw.Length; sha256=(Sha256 $raw); capture='hash only; relevant source literal read; never modified' }
}
$binding = [ordered]@{
 schema=1; state='OWNER ACCEPTED DECISION; DOCUMENTATION SOURCE CANDIDATE; UNAPPLIED; UNQUALIFIED; ALL RUNTIME NOT RUN';
 pin=$pin; pin_git_tree=(Git-Text @('rev-parse',"$pin^{tree}")); observed_head_start=$pin; observed_porcelain='';
 existing_targets=8; new_targets=1; files=$rows; input_bindings=$inputs;
 new_adr_guard=[ordered]@{ number='0185'; observed_refs=$refs.Count; extra_pin_checked=$pin; existing_claims=@(); exact_path_absent=$true; working_index_claim_absent=$true; no_other_owner_worktree_scan=$true }
}
Save-Lf 'capture-bindings.json' (($binding | ConvertTo-Json -Depth 12) + "`n")
Save-Lf 'capture-summary.txt' "SOURCE ONLY. Exact8 raw existing preimages captured plus one new ADR absence guard. Shared HEAD $pin/empty porcelain. All tests/product parsers/compilers/validators/formatters/generators/builds/Docker/setup/environment probes NOT RUN. No repository write/apply/stage/commit/merge/push/cleanup. Existing expired GUI handoff retained hash-only unchanged.`n"
Write-Output "Captured8 existing doc preimages and1 absent ADR; checked$($refs.Count) refs plus pinned HEAD; shared main clean."