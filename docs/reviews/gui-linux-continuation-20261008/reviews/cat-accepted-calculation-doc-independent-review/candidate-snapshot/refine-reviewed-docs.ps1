$ErrorActionPreference = 'Stop'
$packetRoot = 'C:/Users/Paul Work/personal_repos/_temp/roedu-gui-manager-20261008/cat-accepted-calculation-doc-candidate'
$utf8 = [System.Text.UTF8Encoding]::new($false)
function Fix([string]$relative,[string]$before,[string]$after) {
 $absolute=Join-Path $packetRoot ('after/'+$relative)
 $content=[System.IO.File]::ReadAllText($absolute,$utf8)
 if(!$content.Contains($before)){throw ('Exact refinement anchor missing: '+$relative)}
 [System.IO.File]::WriteAllText($absolute,$content.Replace($before,$after),$utf8)
}
Fix 'docs/adr/0185-accepted-eager-startup-bundle-accounting.md' 'accounting. Games remain loaded on play.' 'accounting. Game chunks remain route-lazy and outside this bounded startup set.'
Fix 'README.md' 'Caddy. Change the local published port with `PORT=9000 docker compose up`.' 'Caddy. Change the local published port with `PORT=9000 docker compose up`.
The retained root recipe still uses Node 24/historical output and needs managed
pre-image alignment; selected consumer image binding/qualification remains pending.'
Fix 'README.md' 'The complete native-only gate is `scripts/qualify_go_toolchain.sh`, with explicit task
scratch/PG and Python/Rust absent from PATH. Retained Python validators/Ruff/pytest are
optional independent references, with complete commands in
[`docs/agent-testing.md`](docs/agent-testing.md). The active Python reference CI job remains
automatic until the exact manual-routing proposal receives human approval (ADR-0168).' 'The standalone native-only recipe `scripts/qualify_go_toolchain.sh` currently awaits
selected-toolchain source alignment; explicit task scratch/PG and independent native
obligations remain. Retained Python validators/Ruff/pytest are optional independent
references; commands and the owning GUI context are in
[`docs/agent-testing.md`](docs/agent-testing.md). GitHub Actions use manual dispatch;
retained Python/Rust reference jobs are opt-in ([ADR-0164](docs/adr/0164-manual-github-actions.md)).'
Write-Output 'Corrected remaining review wording only in same nine doc afterimages; all runtime NOT RUN.'
