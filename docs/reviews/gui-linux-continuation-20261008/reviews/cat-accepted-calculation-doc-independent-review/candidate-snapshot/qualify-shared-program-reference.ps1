$ErrorActionPreference = 'Stop'
$packetRoot = 'C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$blockPath = Join-Path $packetRoot 'PROGRAM_CLARIFICATION.md'
$oldBlock = [System.IO.File]::ReadAllText($blockPath,$utf8).TrimEnd([char]10)
$newBlock = $oldBlock + ' Decision: cat_de_roman_esti/docs/adr/0185-accepted-eager-startup-bundle-accounting.md.'
$programPath = Join-Path $packetRoot 'after/docs/PROGRAM.md'
$program = [System.IO.File]::ReadAllText($programPath,$utf8)
if (!$program.Contains($oldBlock)) { throw 'PROGRAM exact shared block changed' }
[System.IO.File]::WriteAllText($programPath,$program.Replace($oldBlock,$newBlock),$utf8)
[System.IO.File]::WriteAllText($blockPath,$newBlock+[char]10,$utf8)
Write-Output 'Reusable block now names the Cat ADR with identical repository-qualified text; local links remain outside it.'
