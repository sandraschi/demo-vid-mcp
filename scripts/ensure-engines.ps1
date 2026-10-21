# Start the optional audio/video engines demo-vid-mcp calls, if they are down.
# Idempotent: ports already listening are left alone. ASCII only (PS 5.1 safe).
$ErrorActionPreference = 'Continue'

function Test-Port([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return [bool]$conn
}

function Wait-Port([int]$Port, [int]$Seconds = 45) {
    for ($i = 0; $i -lt ($Seconds * 2); $i++) {
        if (Test-Port $Port) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

$uv = 'C:\Users\sandr\.local\bin\uv.exe'
$engines = @(
    # sfx-mcp's `-m sfx_mcp` entry point is stdio-only; the HTTP /mcp endpoint
    # that SFX_MCP_URL points at comes from run_server.py.
    @{ Name = 'sfx-mcp'; Port = 11120; WorkDir = 'D:\Dev\repos\sfx-mcp'; Args = @('run', 'python', 'run_server.py') },
    @{ Name = 'vfx-mcp'; Port = 11122; WorkDir = 'D:\Dev\repos\vfx-mcp'; Args = @('run', 'python', '-m', 'vfx_mcp', '--serve') }
)

$failed = 0
foreach ($engine in $engines) {
    if (Test-Port $engine.Port) {
        Write-Output ("{0}: already listening on {1}" -f $engine.Name, $engine.Port)
        continue
    }
    if (-not (Test-Path $engine.WorkDir)) {
        Write-Output ("{0}: MISSING repo {1}" -f $engine.Name, $engine.WorkDir)
        $failed++
        continue
    }
    Write-Output ("{0}: starting on port {1}" -f $engine.Name, $engine.Port)
    # sfx-mcp's run_server.py picks HTTP mode only when MCP_PORT is set.
    $env:MCP_PORT = [string]$engine.Port
    Start-Process -FilePath $uv -ArgumentList $engine.Args -WorkingDirectory $engine.WorkDir -WindowStyle Hidden
    Remove-Item Env:MCP_PORT -ErrorAction SilentlyContinue
    if (Wait-Port $engine.Port 45) {
        Write-Output ("{0}: up" -f $engine.Name)
    } else {
        Write-Output ("{0}: did NOT come up on {1} (check its log, then re-run)" -f $engine.Name, $engine.Port)
        $failed++
    }
}

if (Test-Port 10909) { Write-Output 'speech-mcp: listening on 10909' }
else { Write-Output 'speech-mcp: DOWN on 10909 - voiceover will fail'; $failed++ }

# sfx-mcp needs FREESOUND_API_KEY for anything to resolve; report it here so a
# silent "0 effects" is never a mystery.
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:11120/api/health' -TimeoutSec 3
    $keyState = if ($health.has_api_key) { 'configured' } else { 'MISSING - sfx steps will be skipped' }
    Write-Output ("sfx-mcp FREESOUND_API_KEY: {0}" -f $keyState)
} catch {
    Write-Output 'sfx-mcp: HTTP API not reachable on 11120 (MCP endpoint is /mcp/ with a trailing slash)'
}

if ($failed -gt 0) { exit 1 }
exit 0
