# Re-record a repo's demo video and gate on voice/picture sync.
# One entry point: engines -> generate -> check_sync. Exit code 1 on poor sync.
param(
    [Parameter(Mandatory = $true)][string]$Repo,
    [int]$TimeoutSec = 1800,
    [switch]$SkipEngines
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$api = 'http://127.0.0.1:11134'

if (-not $SkipEngines) {
    & (Join-Path $PSScriptRoot 'ensure-engines.ps1')
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'engines incomplete - transitions and sfx will degrade, generation continues'
    }
}

try {
    Invoke-RestMethod "$api/api/health" -TimeoutSec 3 | Out-Null
} catch {
    throw "demo-vid backend not reachable on $api. Start it with: cd $root; just serve"
}

$payload = @{ repo = $Repo }
$scriptPath = Join-Path $root ("data\videos\{0}\narration.yaml" -f $Repo)
if (Test-Path $scriptPath) {
    # Reuse the curated script (voice, voice_speed, waits, sfx steps) instead
    # of drafting a fresh one. Delete the file to force a re-draft.
    $payload.script_yaml = Get-Content $scriptPath -Raw
    Write-Output ("reusing saved script: {0}" -f $scriptPath)
}
$body = $payload | ConvertTo-Json -Depth 4
Write-Output ("generating {0} (full tour; timeout {1}s)" -f $Repo, $TimeoutSec)
$started = Get-Date
$result = Invoke-RestMethod -Method Post -Uri "$api/api/generate" -ContentType 'application/json' -Body $body -TimeoutSec $TimeoutSec
$elapsed = [math]::Round(((Get-Date) - $started).TotalSeconds, 1)
$result | ConvertTo-Json -Depth 6
Write-Output ("generation took {0}s success={1}" -f $elapsed, $result.success)

if (-not $result.success) { exit 1 }

$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { throw "venv python missing at $py" }
& $py (Join-Path $PSScriptRoot 'check_sync.py') --repo $Repo
exit $LASTEXITCODE
