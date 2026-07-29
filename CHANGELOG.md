# Changelog

## 0.1.0 (2026-07-29)

- Initial scaffold: pipeline tools, FastAPI + FastMCP backend, Vite React webapp
- 6 MCP tools: demo_vid_generate, demo_vid_list, demo_vid_refine, demo_vid_script_draft, demo_vid_script_validate, demo_vid_help
- Speech-mcp TTS voiceover via `GET /api/v1/tts/wav` (WAV bytes, not JSON)
- Playwright headless Chromium recording with native .webm output
- FFmpeg composition (drawtext title card, audio mix from voiceover .wav)
- README-aware script generation (reads target repo README, scans webapp pages)
- Auto-start target webapp backend + frontend before recording
- Content-aware recording: blank/error page detection in Playwright capture
- Known port registry for 12+ fleet repos
- Categorized repo selector (8 categories) in Generate page
- Depot page: categorized video gallery with inline player, script viewer, rebuild, delete
- Logs page: ring-buffer log viewer with level filter and search
- Parallel voiceover + recording (asyncio.create_task)
- Stale-file-safe recorder (deletes old .webm, checks exit code first)
- Honest demo_vid_refine stub (returns actionable error, not fake success)
- manifest.json, mcpb-pack.ps1 with fresh-stage copy
- Hardcoded paths deduplicated into config.repos_root
- Desktop capture (PyWinAuto via cua_* tools) — planned for v0.2
- See DEMO_VID_MCP_PLAN.md for full roadmap
