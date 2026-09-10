# Changelog

## 0.4.0 (2026-09-11)

- **Real background music**: `pipeline/music.py` generates ambient tracks via songgeneration-mcp
  (Lyria 3 Pro / ACE-Step / Stable Audio / Studio SG2, tried in order) and mixes them under the
  voiceover with genuine sidechain ducking in `composer.py` - the "Background Audio Bed... with
  voiceover ducking" bullet had described a stub field (`bg_music`) that nothing ever read since
  v0.3.0. New `demo_vid_generate(music_enabled, music_prompt)` params; dedicated **Music** webapp
  page (enable toggle, mood/style prompt, health check, generate-and-preview).
- **Real timed sound effects**: `pipeline/sfx.py` resolves each Choreography `action: sfx` step
  (a step type that existed in the UI with no backend behind it) via sfx-mcp (FreeSound CC0) and
  mixes the result in at its exact timestamp. Falls back to a skipped-with-warning, non-fatal, when
  sfx-mcp isn't configured or no match is found.
- **Real page-to-page video transitions**: `playwright-capture.js` now records one clip per page
  visit (opening a fresh Playwright page per `goto`) instead of one flat continuous capture;
  `pipeline/vfx.py` joins the clips via vfx-mcp's real crossfade/fade-to-black/wipe/slide, falling
  back to a plain hard-cut concat (no re-encode) when vfx-mcp is unavailable, disabled
  (`transition_style: "none"`), or a transition call fails partway through. Single-page scripts are
  unaffected - still exactly one clip, byte-for-byte the same as before.
  - Found and fixed 5 real bugs in vfx-mcp's own codebase while integrating it (pushed upstream):
    a completely unreachable `/mcp` endpoint (missing `http_app(path="/")` + no
    `lifespan=mcp_app.lifespan`), a `"crossfade"` transition using an FFmpeg filter name that
    doesn't exist (`xfade=transition=fade` is correct) plus a missing `offset` on every xfade-based
    transition so the blend started at frame 0 instead of the real clip boundary, an error dict key
    mismatch that silently swallowed the real FFmpeg error behind a generic fallback message, and
    that error being truncated to only FFmpeg's useless version banner.
  - Root cause underneath several of the above, on this repo's side: `config.data_dir` defaults to
    the bare relative string `"data"`, which resolves fine for every file operation this process
    does itself, but vfx-mcp/sfx-mcp are *separate processes* with their own cwd - a relative path
    handed to them over MCP resolved against the wrong directory entirely. All cross-process paths
    now resolved to absolute before leaving this process.
- **Narration no longer desyncs from video on long lines.** Voiceover now runs first, alone (not in
  parallel with recording); each segment's true TTS length is probed (`wave` stdlib module, no
  FFmpeg needed) and every narrated step's `wait` is stretched to
  `max(authored, narration + 0.8s pad, 1.0s floor)` before the browser ever opens - the capture
  advances on end-of-speech, not a fixed 2-8s guess. Subtitles now end at true speech-end instead of
  the full stretched wait block.
- **Fixed**: speech-mcp's actual TTS query parameter is `voice_id`, not `voice` - confirmed at the
  source (`api_tts_wav`'s signature takes no `voice` parameter at all). Every voice selection made
  anywhere in this app - the Speech page, `demo_vid_generate`'s `voice` param, Choreography's
  picker - was silently ignored by FastAPI's unmatched-param fallback since voice selection was
  first added; speech-mcp's own default voice played every time regardless of selection.
- **Fixed**: the packaged app's Content-Security-Policy declared `connect-src`/`img-src` but no
  `media-src`, which fell back to `default-src 'self'` - blocking both `blob:` URLs (Speech/Music
  preview audio) and `http://127.0.0.1:11134` (Depot/Detail's `<video>` player) with no visible
  error, the whole time.
- **New dedicated Speech and Music settings pages**: voice picker (heart/sky/adam, shared with
  Generate/Choreography via `localStorage`), health checks against speech-mcp/songgeneration-mcp,
  and real generate-and-preview flows backed by new `/api/speech/preview` and `/api/music/preview`
  proxy endpoints.
- **Per-page detail control**: `default_page_level()` classifies each auto-drafted page as
  Skip/Show/Detail by keyword heuristics (`search`/`depot`/`dashboard`/`chat`/`generate` → detail;
  `log`/`swagger`/`apidocs`/`settings` → skip), overridable via a new Generate-page checklist and
  `demo_vid_list_pages`/`page_config`. "Detail" pages get real dwell time and substantive narration
  even when the target repo's README has no `## Webapp` purpose table. `duration_target` now
  reflects actual narrated content (`sum(step waits) + 5s`, 30s floor) instead of a step-count guess.
- **Fixed**: `recorder.py`'s Playwright capture timeout was a flat 45s, too short once
  detail-level scripts routinely produced 50s+ of content - now scales with the script's own
  content length.
- **Fixed**: `.env` was never actually loaded anywhere in the codebase, despite every fleet-service
  URL being read via `os.getenv()` - `config.py` now loads it before its dataclass field defaults
  are evaluated, trying the dev repo root, then the packaged app's install dir, then its
  `resources/` folder.
- **Fixed**: `SFX_MCP_URL`/`VFX_MCP_URL`/`STEMS_MCP_URL` in `.env.example` pointed at the wrong
  ports (frontend instead of backend) with no `/mcp` suffix - pre-existing copy-paste errors never
  caught before anything tried to actually connect through them.
- **Fixed**: the background job queue's `enqueue()` stored `aspect_ratio`/`resolution` on the job
  but `_process_queue()` never passed them to the generator - the Generate page's selectors were
  silent no-ops for anything sent to the background queue.
- **Fixed**: Choreography's "Desktop" checkbox (desktop-capture mode) had no effect - tracked in
  component state and rendered as a checkbox, never written into the generated script.

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
