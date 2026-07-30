# demo-vid-mcp — Product Requirements

## Purpose

Automate the production of short demo videos for fleet MCP server webapps. A single MCP tool call should be able to generate a narrated walkthrough of any fleet repo's UI.

## Architecture

Conductor service: orchestrates 4 pipeline stages (script → voiceover → record → compose) across 3 fleet services (speech-mcp, Playwright, FFmpeg). Target repo is auto-started and zombie-killed before each recording.

```
README → script draft (YAML) → speech-mcp TTS (.wav) → Playwright record (.webm) → FFmpeg compose (.mp4) → depot
```

## Shipped Features (v0.1.0-beta)

- 6 MCP tools: generate, list, refine, script_draft, script_validate, help
- Speech-mcp TTS voiceover (WAV bytes API)
- Playwright headless Chromium recording with blank-page detection
- FFmpeg composition with title card and audio mix
- Auto-start target backend + frontend with zombie kill
- Dynamic port registry (136 repos from WEBAPP_PORTS.md)
- 8-category repo selector (80+ repos)
- Categorized video depot with inline player, rebuild, delete, insert into README
- Choreography page (11 step types, YAML preview)
- SOTA Chat page with personalities, LLM provider integration
- SOTA Settings page with LLM probe
- 7 webapp pages: Dashboard, Depot, Generate, Choreography, Chat, Settings, Logs, Help
- 14 REST API endpoints
- Justfile with bootstrap, serve, test, lint, ci recipes
- GitHub CI (Windows, uv, ruff, pytest)
- pre-commit hooks (ruff + format)

## Future

- **v0.2**: Desktop window capture (PyWinAuto/gdigrab), mixed webapp+desktop timeline
- **v0.3**: OBS-mcp human-in-video, subtitle burn-in, music/stems integration
