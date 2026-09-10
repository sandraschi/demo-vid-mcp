# demo-vid-mcp — Product Requirements

## Purpose

Automate the production of short demo videos for fleet MCP server webapps. A single MCP tool call should be able to generate a narrated walkthrough of any fleet repo's UI.

## Architecture

Conductor service: orchestrates pipeline stages (script → voiceover → align → record page-by-page → stitch
transitions → mix music/sfx → compose) across fleet services (speech-mcp, songgeneration-mcp, sfx-mcp, vfx-mcp,
Playwright, FFmpeg). Target repo is auto-started and zombie-killed before each recording. Also ships as a native
Tauri/NSIS desktop app (no Claude Desktop required) alongside the MCP server.

```
README → script draft (YAML) → speech-mcp TTS (.wav, wait-aligned to true speech length)
  → Playwright record per page (.webm clips) → vfx-mcp transitions or plain cut (single .webm)
  → songgeneration-mcp music + sfx-mcp timed effects mixed in → FFmpeg compose (.mp4) → depot
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

## Shipped Features (v0.2.0 – v0.3.0)

- Desktop-capture mode: `pipeline/desktop_capture.py` drives a native app (Blender, Resonite) live via its own
  MCP server while OBS records the window - real tool calls during the recording, not a staged screencast
- Native Tauri/NSIS desktop installer (packaged backend.exe + WebView2 shell), independent of Claude Desktop
- Subtitles (.vtt/.srt) generated from narration step timing; poster-frame extraction; 16:9/9:16 aspect ratio
  and 720p/1080p resolution presets
- Persistent background job queue with disk recovery
- Per-page Skip/Show/Detail checklist (`demo_vid_list_pages`) driving auto-drafted script depth and pacing
- `page_config` threaded through `demo_vid_generate`/`demo_vid_script_draft` and the webapp's Generate page

## Shipped Features (v0.4.0)

- **Real background music** via songgeneration-mcp (Lyria 3 Pro / ACE-Step / Stable Audio / Studio SG2, tried in
  order), mixed under the voiceover with genuine sidechain ducking - the "audio bed" this project's release notes
  claimed since v0.3.0 but never actually implemented until now
- **Real timed sound effects** via sfx-mcp (FreeSound CC0) - Choreography's `sfx` step type existed with no
  backend behind it until now; each step resolves a sound and mixes it in at its exact timestamp
- **Real page-to-page video transitions** via vfx-mcp - recording now captures one clip per page visit and joins
  them with crossfade/fade-to-black/wipe/slide, falling back to a plain hard-cut concat when vfx-mcp is
  unavailable. Fixed 5 real bugs in vfx-mcp itself along the way (broken `/mcp` endpoint, non-existent filter
  name, wrong error-key reads, truncated error messages, relative paths resolving against the wrong process)
- **Narration/video sync**: each page's dwell time is stretched to its narration's true spoken length (probed via
  the TTS response, not guessed) before recording starts, so long lines never get cut off mid-sentence; subtitles
  end at true speech-end instead of the full stretched wait block
- **Fixed**: speech-mcp's actual TTS parameter is `voice_id`, not `voice` - every voice selection anywhere in the
  app (Speech page, Generate, Choreography) was silently ignored since voice selection was first added
  in favor of speech-mcp's own default voice
- **Fixed**: the packaged app's Content-Security-Policy had no `media-src`, silently blocking all audio/video
  playback (Speech/Music preview and Depot's video player) with no visible error
- Dedicated Speech and Music settings pages: voice picker (shared with Generate/Choreography), health checks,
  real generate-and-preview flows

## Future

- Dedicated SFX/VFX settings pages (mirroring Speech/Music) - currently reachable only via Choreography's raw
  script fields (`action: sfx`, `transition_style`)
- Bundle Playwright/Chromium into the installer for a fully zero-setup experience (currently an external
  prerequisite, same category as FFmpeg)
- `fade_to_black` transition in vfx-mcp likely has the same "multiple `-filter_complex` flags only the last
  takes effect" bug as the now-fixed `crossfade` - not yet root-caused
