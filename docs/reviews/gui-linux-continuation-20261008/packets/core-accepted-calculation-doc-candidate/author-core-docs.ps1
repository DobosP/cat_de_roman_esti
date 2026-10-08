$ErrorActionPreference = 'Stop'
$coreRepo = 'C:\Users\Paul Work\personal_repos\roedu-ui'
$packetRoot = $PSScriptRoot
$catPacket = 'C:\Users\Paul Work\personal_repos\_temp\roedu-gui-manager-20261008\cat-accepted-calculation-doc-candidate'
$corePin = '9add2483ea95b4ee4a742b3332002e83b9766e5d'
$coreTree = 'a420dc8cf21b90053a047c2f25b883008a96e2e7'
$utf8 = [Text.UTF8Encoding]::new($false, $true)
function Write-Literal([string]$path, [string]$text) {
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
    [IO.File]::WriteAllText($path, $text, $utf8)
}
function Capture-Blob([string]$blob, [string]$path) {
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
    $start = [Diagnostics.ProcessStartInfo]::new('git')
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($arg in @('-C', $coreRepo, 'cat-file', 'blob', $blob)) { $start.ArgumentList.Add($arg) }
    $process = [Diagnostics.Process]::Start($start)
    $stream = [IO.File]::Create($path)
    try { $process.StandardOutput.BaseStream.CopyTo($stream) } finally { $stream.Dispose() }
    $diagnostic = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "Read-only Git blob capture failed: $diagnostic" }
}
if ((& git -C $coreRepo rev-parse HEAD).Trim() -ne $corePin) { throw 'Core HEAD drift' }
if ((& git -C $coreRepo rev-parse 'HEAD^{tree}').Trim() -ne $coreTree) { throw 'Core tree drift' }
if ((& git -C $coreRepo status --porcelain).Count -ne 0) { throw 'Core checkout is not clean' }
if ((Get-FileHash -LiteralPath (Join-Path $catPacket 'SEAL.json')).Hash.ToLowerInvariant() -ne 'a5e90bd370c1659a3164a011467a7bef396d129a9cf1b75293f535bd4ea9d57b') { throw 'Closed Cat producer seal drift' }
$clarification = $utf8.GetString([IO.File]::ReadAllBytes((Join-Path $catPacket 'PROGRAM_CLARIFICATION.md'))).Trim()
Write-Literal (Join-Path $packetRoot 'PROGRAM_CLARIFICATION.md') ($clarification + "`n")
$bindings = @()
foreach ($target in @('README.md', 'docs/PROGRAM.md')) {
    $treeRow = (& git -C $coreRepo ls-tree $corePin -- $target).Trim()
    if ($treeRow -notmatch '^100644 blob ([0-9a-f]{40})\t') { throw "Unexpected mode/blob for $target" }
    $blob = $Matches[1]
    $beforePath = Join-Path $packetRoot ('before/' + $target)
    $afterPath = Join-Path $packetRoot ('after/' + $target)
    Capture-Blob $blob $beforePath
    $text = $utf8.GetString([IO.File]::ReadAllBytes($beforePath))
    if ($target -eq 'docs/PROGRAM.md') {
        $anchor = '### 4.7 Device checkpoint (hard stop)'
        if ($text.IndexOf($anchor) -lt 0 -or $text.IndexOf($anchor) -ne $text.LastIndexOf($anchor)) { throw 'PROGRAM anchor not unique' }
        $after = $text.Replace($anchor, $clarification + "`n`n" + $anchor)
    } else {
        $anchor = 'The Cat-only sealed staged-UI contract and confined same-repo Go audits from'
        if ($text.IndexOf($anchor) -lt 0 -or $text.IndexOf($anchor) -ne $text.LastIndexOf($anchor)) { throw 'README anchor not unique' }
        $checkpoint = @'
Paul accepted Cat's startup calculation on 2026-10-08: entry/static JS/CSS plus
immediately mounted AccountBar and its recursive static closure, counted once.
[Cat ADR-0185](../cat_de_roman_esti/docs/adr/0185-accepted-eager-startup-bundle-accounting.md)
records the source decision. At the Windows checkpoint, code/docs are unapplied
and unqualified; current Vite/startup gzip is unacquired and all 11 amended tests NOT RUN.
Frontend 120 KiB JS/CSS and canonical 40,960/30,720-byte JS remain distinct and unchanged.
'@
        $after = $text.Replace($anchor, $checkpoint.Trim() + "`n`n" + $anchor)
        $oldVerification = 'This post-tag update runs documentation checks only. Full native captures remain'
        $newVerification = 'Earlier post-tag documentation checks retain their recorded scope. This source-only'
        if (-not $after.Contains($oldVerification)) { throw 'README verification anchor absent' }
        $after = $after.Replace($oldVerification, $newVerification + "`n" + 'amendment has no executed checks. Full native captures remain')
        if (($after.Split("`n").Count - 1) -gt 120) { throw 'README line budget exceeded' }
    }
    Write-Literal $afterPath $after
    $bindings += [ordered]@{path=$target;condition='Exact raw Git beforeimage/blob/mode100644 required';before=[ordered]@{mode='100644';blob=$blob;bytes=(Get-Item -LiteralPath $beforePath).Length;sha256=(Get-FileHash -LiteralPath $beforePath).Hash.ToLowerInvariant()};after=[ordered]@{mode='100644';bytes=(Get-Item -LiteralPath $afterPath).Length;sha256=(Get-FileHash -LiteralPath $afterPath).Hash.ToLowerInvariant()}}
}
Write-Literal (Join-Path $packetRoot 'source-bindings.json') (([ordered]@{schema=1;state='OWNER ACCEPTED CAT CALCULATION; CORE DOCUMENTATION SOURCE ONLY; UNAPPLIED; UNQUALIFIED';pin=$corePin;tree=$coreTree;files=$bindings;catProducerSeal='a5e90bd370c1659a3164a011467a7bef396d129a9cf1b75293f535bd4ea9d57b';catClarificationSha256=(Get-FileHash -LiteralPath (Join-Path $catPacket 'PROGRAM_CLARIFICATION.md')).Hash.ToLowerInvariant();reusableClarificationSha256=(Get-FileHash -LiteralPath (Join-Path $packetRoot 'PROGRAM_CLARIFICATION.md')).Hash.ToLowerInvariant();coreRelease='9e0a88e33d44ba7ce9e84ead890c897b36d41dd4';tagObject='b5e1c817608e79411595da7f46618475e92acc13';runtime='NOT RUN';applied=$false;qualified=$false;integrationOrder=@('original38 Cat source','separate2 Cat eager code','separate9 Cat docs','separate2 core docs');scope='Same narrow PROGRAM clarification; README checkpoint only. No shared SDK contract/core ADR/repacked release.'} | ConvertTo-Json -Depth 12) + "`n")
$bindings | ConvertTo-Json -Depth 6
