# Changelog

## 0.3.0 (2026-09-03)

- **Subtitles & Closed Captions (.vtt & .srt)**: `composer.py` now automatically parses narration script step timings and generates WebVTT (`subtitles.vtt`) and SubRip (`subtitles.srt`) sidecars. The webapp video player in `Depot.tsx` and `Detail.tsx` renders native `<track kind="subtitles">` elements.
- **Visual Cursor Highlights (Playwright Click Ripples)**: `scripts/playwright-capture.js` injects a non-intrusive CSS/JS pulse listener on `page.addInitScript`. Every click action displays an expanding amber ripple effect at `(e.clientX, e.clientY)` that fades smoothly over 400ms.
- **Aspect Ratio & Resolution Presets**: Support for `aspect_ratio: "16:9" | "9:16"` (landscape walkthrough vs. mobile vertical reel) and `resolution: "720p" | "1080p"` across script validation, Playwright viewport, and the Generate webapp page.
- **Automated Poster Image Extraction**: `composer.py` captures a frame at `00:00:01.500` via FFmpeg to generate `poster.jpg`. Exposed through `/api/videos` and rendered in Depot and Detail video cards.
- **Background Audio Bed & Ducking**: Script schema supports `bg_music: true/false`, with multi-stream composition in `composer.py` ducking ambient audio under voiceover narration.
- **Persistent Background Job Queue**: New `pipeline/queue.py` (`JobQueue`) with disk persistence in `data/queue.json`, FIFO background execution, cancellation, and recovery across server restarts. Fully wired to `GET /api/queue`, `POST /api/queue`, `DELETE /api/queue/{id}`, and an interactive `Queue.tsx` webapp dashboard.
- **Dead Port Resilience (11134 & 11434)**:
  - `tests/test_e2e.py` probes socket connectivity before running; cleanly skips in 1.3s if port 11134 is closed.
  - Webapp Dashboard displays an explicit offline banner with one-click retry and exact CLI startup instructions.
  - LLM discovery probes Ollama (11434) and LM Studio (1234) with 0.6s non-blocking timeouts and helpful fallback guidance.
- **Tool Surface & Quality Gates**:
  - Implemented real `demo_vid_refine` mutation logic (replacing stub).
  - Added and registered `demo_vid_shutdown` tool and `/api/shutdown` endpoint.
  - Adopted fleet standard `biome.json` with 100% clean formatting and linting.
  - Fast empty-string validation on `repo` parameter (15ms vs 170s hang).
  - Escaped colons and quotes in FFmpeg `drawtext` title filter.

## 0.2.0 (2026-09-03)


- **Desktop-capture mode**: new `pipeline/desktop_capture.py` records a native app window via
  obs-mcp while `action: mcp_call` narration steps drive the app live through its own MCP server
  (e.g. `blender-mcp`'s `blender_mesh`, `resonite-mcp`'s `resonite_link_*`) — real tool calls
  during the recording, not a staged screen capture.
- New `mcp_call` step type: `{action: mcp_call, server, tool, params, say, wait}` — server-agnostic,
  works for any fleet MCP server with a `POST /api/v1/control/tool` endpoint.
- `generate.py`: auto-detects desktop-capture mode (`desktop_capture: true` flag or any `mcp_call`
  step) and skips the webapp-specific preflight/URL-resolution entirely for that path.
- `config.py`: new `windows_computer_use_mcp_url`, `obs_mcp_url`, `resonite_mcp_url` fields;
  `blender_mcp_url` (previously declared, unused) now actually wired up.
- Two working example scripts: `data/scripts/blender-chair-demo.yaml`,
  `data/scripts/resonite-nekomimi-demo.yaml`.
- `composer.py`, `voiceover.py`, `script.py`: **zero changes needed** — confirmed format-agnostic
  (composer) and already action-agnostic (voiceover, validator) before writing any new code.
- Fixed: `DEMO_VID_MCP_PLAN.md`, referenced by this changelog since v0.1.0-beta, didn't exist. It
  does now — full v0.2 architecture + the one remaining real, documented constraint (no scriptable
  Resonite camera).
- **Corrected mid-implementation**: cross-server calls use `fastmcp.Client` (real MCP protocol),
  not a REST shortcut — fleet servers don't share a uniform REST tool-call path (checked: freecad-mcp,
  resonite-mcp, blender-mcp, and obs-mcp all differ or have none). `*_MCP_URL` env vars must be each
  server's full `/mcp` endpoint.
- **OBS scene setup is now automated too**, via `obs-mcp`'s new `obs_create_capture_scene` tool
  (see that repo's own changelog) — `record_desktop()` calls it before every recording. The only
  still-manual step is Resonite's in-world camera position (no protocol support for that).

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
