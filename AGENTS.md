# AGENTS.md — demo-vid-mcp

## What this does

Demo video pipeline for fleet repos. Orchestrates Playwright recording, speech-mcp TTS, and FFmpeg/Resolve composition.

## Key files

| File | Purpose |
|------|---------|
| `src/demo_vid_mcp/server.py` | FastMCP server, tool registrations |
| `src/demo_vid_mcp/app.py` | FastAPI REST app (webapp backend) |
| `src/demo_vid_mcp/pipeline/` | Pipeline stages (recorder, voiceover, composer, script) |
| `src/demo_vid_mcp/tools/` | MCP tool implementations |
| `webapp/src/App.tsx` | SPA with 7 pages |

## Ports

Backend: 11134, Frontend: 11135

## Quick start

```powershell
just bootstrap
just serve
```
