$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Pkg = "demo_vid_mcp"
$Stage = Join-Path $Root "mcpb"

Write-Host "=== demo-vid-mcp MCPB Pack ===" -ForegroundColor Cyan

if (Test-Path "$Stage\src") { Remove-Item -Recurse -Force "$Stage\src" }
New-Item -ItemType Directory -Force -Path "$Stage\src\$Pkg" | Out-Null
Copy-Item -Recurse -Force "$Root\src\$Pkg\*" "$Stage\src\$Pkg\"
Copy-Item -Force "$Root\README.md" "$Stage\"
Copy-Item -Force "$Root\CHANGELOG.md" "$Stage\"

if (-not (Test-Path "$Stage\assets\prompts\system.md")) {
    New-Item -ItemType Directory -Force -Path "$Stage\assets\prompts" | Out-Null
    "# demo-vid-mcp — core capabilities`n`n" | Set-Content "$Stage\assets\prompts\system.md"
    "# demo-vid-mcp — user guide`n`n" | Set-Content "$Stage\assets\prompts\user.md"
    "[]" | Set-Content "$Stage\assets\prompts\examples.json"
}

Write-Host "Packing..." -ForegroundColor Yellow
$cli = "bunx", "@anthropic-ai/mcpb", "pack", $Stage, "$Root\dist\demo-vid-mcp-v0.1.0.mcpb"
& $cli
if ($LASTEXITCODE -eq 0) {
    Write-Host "Pack complete: dist/demo-vid-mcp-v0.1.0.mcpb" -ForegroundColor Green
}
