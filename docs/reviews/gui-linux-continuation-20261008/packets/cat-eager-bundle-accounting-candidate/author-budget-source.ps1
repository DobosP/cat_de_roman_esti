$ErrorActionPreference='Stop'
$repoRoot='C:/Users/Paul Work/personal_repos/cat_de_roman_esti'
$packetRoot='C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-eager-bundle-accounting-candidate'
$utf8=[Text.UTF8Encoding]::new($false)
function GitBytes([string[]]$arguments) {
  $start=[Diagnostics.ProcessStartInfo]::new()
  $start.FileName='git'; $start.WorkingDirectory=$repoRoot
  $start.UseShellExecute=$false; $start.CreateNoWindow=$true
  $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
  $start.Environment['GIT_OPTIONAL_LOCKS']='0'
  foreach($argument in @('-c','core.autocrlf=false','-c','core.safecrlf=false')+$arguments) { $start.ArgumentList.Add($argument) }
  $process=[Diagnostics.Process]::Start($start)
  $stream=[IO.MemoryStream]::new(); $process.StandardOutput.BaseStream.CopyTo($stream)
  $diagnostic=$process.StandardError.ReadToEnd(); $process.WaitForExit()
  if($process.ExitCode -ne 0 -or $diagnostic.Trim()) { throw ('Read-only Git did not complete quietly: '+$diagnostic) }
  ,$stream.ToArray()
}
function HashBytes([byte[]]$bytes) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
function WriteBytes($relative,[byte[]]$bytes) {
  $destination=Join-Path $packetRoot $relative
  [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
  [IO.File]::WriteAllBytes($destination,$bytes)
}
function ReplaceExact($value,$old,$new) {
  if(($value.Split([string[]]@($old),[StringSplitOptions]::None)).Length -ne 2) { throw 'Expected one literal source anchor' }
  $value.Replace($old,$new)
}
$pin='59a9a568c445654f69215d735091c9b3e0405831'
foreach($relative in @('frontend/scripts/check-bundle-budget.mjs','frontend/tests/bundle-budget.test.mjs')) {
  $bytes=GitBytes @('cat-file','blob',($pin+':'+$relative))
  if((HashBytes $bytes) -ne (HashBytes ([IO.File]::ReadAllBytes((Join-Path $repoRoot $relative))))) { throw ('Target working bytes differ from pin: '+$relative) }
  WriteBytes ('before/'+$relative) $bytes
  WriteBytes ('check-tree/'+$relative) $bytes
}
$relative='frontend/scripts/check-bundle-budget.mjs'
$before=$utf8.GetString([IO.File]::ReadAllBytes((Join-Path $packetRoot ('before/'+$relative))))
$old='export const DEFAULT_INITIAL_GZIP_LIMIT_KIB = 120;'
$new="export const DEFAULT_INITIAL_GZIP_LIMIT_KIB = 120;`n`n// App mounts this lazy component on every route before any play action.`n// The key is Vite's source-relative manifest identity, not a chunk filename.`nconst REQUIRED_INITIAL_EAGER_ROOTS = Object.freeze([`n  `"src/components/AccountBar.tsx`",`n]);"
$after=ReplaceExact $before $old $new
$oldComment=" * Return the JS/CSS files required by every entry before any dynamic import.`n * Vite's ``imports`` edges are static; ``dynamicImports`` are intentionally excluded."
$newComment=" * Return entry/static JS/CSS, optionally including explicit eagerly mounted roots.`n * Only each root's static ``imports`` are followed; other dynamic edges stay excluded."
$after=ReplaceExact $after $oldComment $newComment
$after=ReplaceExact $after 'export function collectInitialBundleFiles(manifest) {' 'export function collectInitialBundleFiles(manifest, { eagerRoots = [] } = {}) {'
$old="  const visited = new Set();`n  const files = new Set();"
$new=@"
  if (!Array.isArray(eagerRoots) || eagerRoots.length > Object.keys(manifest).length) {
    throw new Error("Vite required eager roots must be a bounded manifest-key array");
  }
  for (const key of eagerRoots) {
    if (typeof key !== "string" || !key || !Object.hasOwn(manifest, key)) {
      throw new Error("Vite manifest is missing a required eager root: " + String(key));
    }
  }

  const visited = new Set();
  const files = new Set();
"@
$after=ReplaceExact $after $old $new.TrimEnd("`n")
$after=ReplaceExact $after '  function visit(key) {' '  function visit(key, required = false) {'
$old="    visited.add(key);`n    if (typeof chunk.file"
$new=@"
    if (required) {
      if (typeof chunk.file !== "string" || !isCodeOrStyle(chunk.file)) {
        throw new Error(```Vite manifest is missing a required eager asset: `${key}```);
      }
      if (chunk.css !== undefined && (!Array.isArray(chunk.css)
        || chunk.css.some((css) => typeof css !== "string" || !isCodeOrStyle(css)))) {
        throw new Error(```Vite manifest has invalid required eager assets: `${key}```);
      }
      if (chunk.imports !== undefined && (!Array.isArray(chunk.imports)
        || chunk.imports.some((imported) => typeof imported !== "string" || !imported
          || !Object.hasOwn(manifest, imported)))) {
        throw new Error(```Vite manifest references a missing required eager import: `${key}```);
      }
    }
    visited.add(key);
    if (typeof chunk.file
"@
$after=ReplaceExact $after $old $new.TrimEnd("`n")
$after=ReplaceExact $after '    for (const imported of chunk.imports ?? []) visit(imported);' '    for (const imported of chunk.imports ?? []) visit(imported, required);'
$after=ReplaceExact $after '  for (const entry of entries) visit(entry);' ("  // Validate eager closures first so an ordinary shared visit cannot hide bad assets.`n  for (const key of eagerRoots) visit(key, true);`n  for (const entry of entries) visit(entry);")
$old='  const measurements = measureGzipFiles(outputDir, collectInitialBundleFiles(manifest));'
$new="  const measurements = measureGzipFiles(outputDir, collectInitialBundleFiles(manifest, {`n    eagerRoots: REQUIRED_INITIAL_EAGER_ROOTS,`n  }));"
$after=ReplaceExact $after $old $new
WriteBytes ('after/'+$relative) ($utf8.GetBytes($after))
'Budget source afterimage authored; product code NOT RUN.'