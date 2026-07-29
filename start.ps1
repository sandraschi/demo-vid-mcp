param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 11134
$FrontendPort = 11135

# Port zombie clearing
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Start backend
$BackendJob = Start-Job -Name "demo-vid-backend" -ScriptBlock { param($Root, $Port) Set-Location $Root; uv run python -m demo_vid_mcp --serve --port $Port } -ArgumentList $ScriptRoot, $BackendPort

# Wait for backend
for ($i = 0; $i -lt 60; $i++) {
    try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue; if ($r.StatusCode -eq 200) { break } } catch {}
    Start-Sleep 1
}

# Start frontend
$WebRoot = Join-Path $ScriptRoot "webapp"
Start-Process -NoNewWindow -FilePath "bun" -ArgumentList "run dev" -WorkingDirectory $WebRoot

# Open browser
if (-not $NoBrowser -and -not $Headless) { Start-Process "http://127.0.0.1:$FrontendPort" }

Write-Host "demo-vid-mcp: backend $BackendPort, frontend $FrontendPort"

while ($true) {
    if ($BackendJob.State -in @("Completed", "Failed")) { Receive-Job $BackendJob; break }
    Start-Sleep 2
}
