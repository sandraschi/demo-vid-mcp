# Fleet: mcp-central-docs/templates/pre-commit-biome.ps1 (demo-vid-mcp copy)
# Used by .pre-commit-config.yaml local hook.
# Detects webapp/, ensures node_modules via bun (this repo's package manager), runs bun run biome:ci.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

$webRoot = $null
foreach ($candidate in @("webapp", "web_sota", "web-sota", "webapp/frontend", "web")) {
    $path = Join-Path $repoRoot $candidate
    if (Test-Path (Join-Path $path "package.json")) {
        $webRoot = $path
        break
    }
}

if (-not $webRoot) {
    exit 0
}

Push-Location $webRoot
try {
    if (-not (Test-Path "node_modules")) {
        bun install --silent
        if ($LASTEXITCODE -ne 0) {
            throw "bun install failed with exit code $LASTEXITCODE"
        }
    }
    bun run biome:ci
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
