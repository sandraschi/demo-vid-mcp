$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Pkg = "demo_vid_mcp"
$Stage = Join-Path $Root "mcpb"

Write-Host "=== demo-vid-mcp MCPB Pack ===" -ForegroundColor Cyan

# Fresh stage: wipe + recopy
if (Test-Path "$Stage\src") { Remove-Item -Recurse -Force "$Stage\src" }
New-Item -ItemType Directory -Force -Path "$Stage\src\$Pkg" | Out-Null
Copy-Item -Recurse -Force "$Root\src\$Pkg\*" "$Stage\src\$Pkg\"
Copy-Item -Force "$Root\README.md" "$Stage\"
Copy-Item -Force "$Root\CHANGELOG.md" "$Stage\"
Copy-Item -Force "$Root\manifest.json" "$Stage\"

# Prompts (stub — expand before shipping)
if (-not (Test-Path "$Stage\assets\prompts\system.md")) {
    New-Item -ItemType Directory -Force -Path "$Stage\assets\prompts" | Out-Null
    $sys = @"
# demo-vid-mcp — core capabilities

demo-vid-mcp generates narrated walkthrough videos for any webapp.
It orchestrates Playwright (screen recording), speech-mcp (TTS voiceover),
and FFmpeg (composition) into a single MP4.

## Tools

- demo_vid_generate: full pipeline (auto-start, record, voiceover, compose)
- demo_vid_list: list produced videos
- demo_vid_script_draft: generate narration script from repo README
- demo_vid_script_validate: validate narration YAML
- demo_vid_help: list tools

## Pipeline

1. Script (YAML narration steps)
2. Auto-start target webapp backend + frontend
3. Playwright headless Chromium recording (.webm)
4. speech-mcp TTS voiceover (.wav)
5. FFmpeg composition (.mp4 + title card)
"@
    [System.IO.File]::WriteAllText("$Stage\assets\prompts\system.md", $sys, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText("$Stage\assets\prompts\user.md", "# demo-vid-mcp — user guide`n`nGenerate demo videos for any fleet webapp.", [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText("$Stage\assets\prompts\examples.json", '[]', [System.Text.UTF8Encoding]::new($false))
}

Write-Host "Packing..." -ForegroundColor Yellow
& "bunx" "@anthropic-ai/mcpb" "pack" $Stage "$Root\dist\demo-vid-mcp-v0.1.0.mcpb"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Pack complete: dist/demo-vid-mcp-v0.1.0.mcpb" -ForegroundColor Green
}
