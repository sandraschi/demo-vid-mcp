# Changelog

## 0.1.1 (2026-08-01)

- `demo_vid_generate(theme=...)`: `"dark"` (default, fleet identity) or `"light"` (bright demo). Capture script forces the target webapp's theme class before navigation — handles both `.dark` toggling and persisted localStorage light-mode keys.
- `pydub` added as a runtime dependency (audio merging) + `audioop-lts` (pydub needs `audioop`, removed in Python 3.13).
- `requires-python` raised to `>=3.13` (audioop-lts constraint).
- `pyright` added to dev deps; `ctx: Context | None` typing; pydub import moved to module top (was guarded try/except).

## 0.1.0-beta (2026-07-29)

- Initial scaffold: pipeline tools, FastAPI + FastMCP backend, Vite React webapp
- 6 MCP tools: demo_vid_generate, demo_vid_list, demo_vid_refine, demo_vid_script_draft, demo_vid_script_validate, demo_vid_help
- Speech-mcp TTS voiceover via `GET /api/v1/tts/wav` (WAV bytes, not JSON)
- Playwright headless Chromium recording with native .webm output
- FFmpeg composition (drawtext title card, audio mix from voiceover .wav)
- README-aware script generation (reads target repo README, scans webapp pages)
- Auto-start target webapp backend + frontend before recording
- Zombie-kill stale processes on target ports before starting
- Content-aware recording: blank/error page detection in Playwright capture
- Dynamic port registry (136 repos auto-detected from WEBAPP_PORTS.md)
- Categorized repo selector (8 categories, 80+ repos) in Generate page
- Draft Script button: one-click YAML generation from repo README
- Depot page: categorized video gallery with inline player, repo filter via URL params, script viewer, rebuild, delete, insert into README
- Choreography page: visual script builder with 11 step types, global toggles, YAML preview
- SOTA Chat page: personalities, localStorage history, LLM provider integration, example prompts, export/clear
- SOTA Settings page: LLM provider probe (Ollama/LM Studio), model selection, backend health, speech-mcp status
- Help page: 6 horizontal tabs (overview, architecture, tools, config, fleet, troubleshooting)
- Logs page: ring-buffer log viewer with level filter and search
- Dashboard: dynamic KPIs (video count, depot repos, speech-mcp status, pipeline phase)
- 14 REST API endpoints covering all features
- Parallel voiceover + recording (asyncio.create_task)
- Stale-file-safe recorder (deletes old .webm, checks exit code first)
- Honest demo_vid_refine stub (returns actionable error, not fake success)
- manifest.json, mcpb-pack.ps1 with fresh-stage copy
- Hardcoded paths deduplicated into config.repos_root
- pre-commit hooks (ruff, format, trailing-whitespace, eof-fixer)
- GitHub CI workflow (Windows, uv, ruff, pytest)
- Justfile with bootstrap, serve, test, lint, ci, cifull recipes
- Pre-commit hook installed and active
- README badges (Just, Ruff, Python, FastMCP, Glama, Tailwind)
- GitHub topics: mcp, video, playwright, ffmpeg, demo, fleet
- Desktop capture (PyWinAuto via cua_* tools) — planned for v0.2
- See DEMO_VID_MCP_PLAN.md for full roadmap
