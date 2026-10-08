$ErrorActionPreference='Stop'
$packetRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-eager-bundle-accounting-candidate'
$utf8=[Text.UTF8Encoding]::new($false)
function HashBytes([byte[]]$bytes) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
$records=@(); $totalBytes=0
foreach($file in (Get-ChildItem -LiteralPath $packetRoot -Recurse -File | Sort-Object FullName)) {
  $relative=$file.FullName.Substring($packetRoot.Length+1).Replace('\','/')
  if($relative -in @('SHA256SUMS','SEAL.json')) { continue }
  $bytes=[IO.File]::ReadAllBytes($file.FullName)
  $records+=((HashBytes $bytes)+'  '+$relative); $totalBytes+=$bytes.Length
}
$sumsPath=Join-Path $packetRoot 'SHA256SUMS'
[IO.File]::WriteAllText($sumsPath,($records -join "`n")+"`n",$utf8)
$seal=[ordered]@{schema=1;kind='closed two-path eager bundle accounting source candidate';target_paths=@('frontend/scripts/check-bundle-budget.mjs','frontend/tests/bundle-budget.test.mjs');pin='59a9a568c445654f69215d735091c9b3e0405831';payload_files=$records.Length;payload_bytes=$totalBytes;sha256sums_sha256=(HashBytes ([IO.File]::ReadAllBytes($sumsPath)));patch_sha256=(HashBytes ([IO.File]::ReadAllBytes((Join-Path $packetRoot 'conditional-eager-accounting.patch'))));source_bindings_sha256=(HashBytes ([IO.File]::ReadAllBytes((Join-Path $packetRoot 'source-bindings.json'))));original_tests_preserved=4;additional_tests_authored_not_run=7;applied=$false;qualified=$false;independent_manager_acceptance='PENDING';not_run=@('product code','tests','compilers','parsers','validators','generators','formatters','builds','Docker','setup','environment probes','runtime qualification')}
$sealPath=Join-Path $packetRoot 'SEAL.json'
[IO.File]::WriteAllText($sealPath,($seal | ConvertTo-Json -Depth 4)+"`n",$utf8)
# Native byte verification only, after every payload file is fixed.
foreach($line in $records) {
  $expected=$line.Substring(0,64); $relative=$line.Substring(66)
  if((HashBytes ([IO.File]::ReadAllBytes((Join-Path $packetRoot $relative)))) -ne $expected) { throw ('Sealed payload mismatch: '+$relative) }
}
$seal
'Outer SEAL.json SHA256: '+(HashBytes ([IO.File]::ReadAllBytes($sealPath)))