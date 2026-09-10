# demo-vid-mcp

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="https://tauri.app"><img src="https://img.shields.io/badge/Tauri-2-24C8DB?style=flat-square&logo=tauri&logoColor=white" alt="Tauri"></a>
  <a href="https://github.com/sandraschi/demo-vid-mcp/releases/latest"><img src="https://img.shields.io/github/v/release/sandraschi/demo-vid-mcp?style=flat-square&color=7c5cfc" alt="Latest release"></a>
  <a href="https://glama.ai/mcp/servers"><img src="https://img.shields.io/badge/Glama-MCP_server-7c5cfc?style=flat-square" alt="Glama"></a>
  <a href="https://github.com/tailwindlabs/tailwindcss"><img src="https://img.shields.io/badge/Tailwind-4-06b6d4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind"></a>
</p>

Demo video pipeline for fleet repos. Records narrated walkthroughs of any webapp by orchestrating Playwright, speech-mcp TTS, and FFmpeg composition — with real background music (songgeneration-mcp), sound effects (sfx-mcp), and crossfade/wipe transitions between pages (vfx-mcp).

## Quick Install

```bash
uvx mcpb install sandraschi/demo-vid-mcp
```

Or grab the native Windows installer (Tauri desktop app, no Claude Desktop required) from
[Releases](https://github.com/sandraschi/demo-vid-mcp/releases/latest).

## What You Can Do

- **Generate a video**: `demo_vid_generate(repo="chitchat")` — auto-starts the target webapp, records it page-by-page, adds voiceover synced to true speech length, mixes in music/sfx, joins pages with real transitions, composes MP4
- **Or drive a native app live**: `demo_vid_generate(repo="blender-mcp", script_yaml=<desktop-capture script>)` — OBS records a real app window (Blender, Resonite) while `mcp_call` steps actually invoke that app's own MCP server during the recording, not a staged screencast. See `data/scripts/*.yaml` for working examples and [DEMO_VID_MCP_PLAN.md](DEMO_VID_MCP_PLAN.md) for the architecture.
- **Draft a script**: `demo_vid_script_draft(repo="chitchat")` — reads the README and generates a narration script, with a per-page Skip/Show/Detail checklist (`demo_vid_list_pages`)
- **Narration that fits the picture**: each page's dwell time is stretched to match its actual spoken length (not a fixed guess), so long lines never get cut off mid-sentence
- **Browse the depot**: Categorized gallery of produced videos with inline player, subtitle tracks (.vtt), poster previews, rebuild, delete, and insert into repo README
- **Persistent queue**: Background queue manager to schedule and track batch video generation across the fleet
- **Chat about it**: Built-in chat with personalities, example prompts, and local LLM integration (Ollama/LM Studio)

## Tools

| Tool | Description |
|------|-------------|
| `demo_vid_generate(repo, script_yaml?, base_url?, theme="dark", aspect_ratio="16:9", resolution="720p", page_config?, voice="heart", music_enabled=False, music_prompt?)` | Full pipeline: voiceover (speech-mcp, wait-aligned to true speech length) → record page-by-page (Playwright with click ripples) → join pages with real transitions (vfx-mcp) or plain cuts → mix in background music (songgeneration-mcp) and timed sound effects (sfx-mcp, via `action: sfx` script steps) → compose (FFmpeg) → MP4 + WebVTT/SRT subtitles + poster image. Also auto-detects native desktop-capture mode via obs-mcp. |
| `demo_vid_list_pages(repo)` | List a repo's webapp pages with README-sourced purpose and default Skip/Show/Detail level, for building a page-selection checklist |
| `demo_vid_script_draft(repo, page_config?)` | Generate a narration YAML from the target repo's README and webapp page structure |
| `demo_vid_script_validate(yaml)` | Validate a narration script's structure, timing, aspect ratio, and resolution |
| `demo_vid_list(repo?)` | List produced videos with metadata, poster, and subtitle sidecar paths |
| `demo_vid_refine(name, feedback)` | Automatically parse user feedback and mutate YAML narration timing, voice, and steps |
| `demo_vid_help` | List all tools and usage information |
| `demo_vid_shutdown` | Gracefully terminate the server and background queue worker |

## Webapp

| Page | Purpose |
|------|---------|
| **Dashboard** | Backend status, KPI cards, dead port detection with one-click reconnect |
| **Depot** | Categorized gallery with HTML5 player, subtitle toggle, poster previews, rebuild, delete |
| **Queue** | Persistent background job queue manager with live polling, status badges, and cancel controls |
| **Generate** | Select target repo by category, per-page Skip/Show/Detail checklist, aspect ratio/resolution, draft YAML, and generate or queue |
| **Choreography** | Visual script builder — 11 step types (including timed sound effects and native transitions), global options, YAML preview |
| **Speech** | Voice picker (shared with Generate/Choreography), speech-mcp health, text-to-preview |
| **Music** | Background-music enable + mood/style prompt, songgeneration-mcp health, generate-and-preview |
| **Chat** | SOTA chat with personalities, localStorage, example prompts, LLM integration |
| **Settings** | LLM provider probe (Ollama/LM Studio), model selection, persistence |
| **Logs** | Ring-buffer log viewer with level filter and search |
| **Help** | 6-tab reference: overview, architecture, tools, config, fleet, troubleshooting |


## Autostart

`demo_vid_generate` automatically starts the target repo's backend and Vite frontend before recording. Zombie-kills stale processes first. No manual setup — the pipeline scans for `start.ps1` and `webapp/` directories.

## Themes

Recording is dark-mode by default (fleet identity). Pass `theme="light"` to record a bright demo — the capture script forces the target webapp's theme class (handles both `.dark` toggling and persisted localStorage light-mode keys) before navigation, per `chat_skills_prefab_standard.md` §7.1.

## Fleet Services

Required: speech-mcp (voiceover), Playwright (recording), FFmpeg (composition).
Optional: songgeneration-mcp (background music — Lyria/ACE-Step/Stable Audio/Studio, tried in order), sfx-mcp (timed sound effects, FreeSound CC0), vfx-mcp (real crossfade/wipe/slide transitions between pages — falls back to a plain cut when unavailable), blender-mcp (3D titles).

**Desktop-capture mode** (native apps driven live — see [DEMO_VID_MCP_PLAN.md](DEMO_VID_MCP_PLAN.md)):
windows-computer-use-mcp (window focus), obs-mcp (recording — window-capture *and* human-in-video),
plus whichever MCP server the demo actually drives (blender-mcp, resonite-mcp, ...).

## Ports

Backend: **11134**, Frontend: **11135**, speech-mcp: **10909**, songgeneration-mcp: **10885**, sfx-mcp: **11120**, vfx-mcp: **11122**.
See [WEBAPP_PORTS.md](https://github.com/sandraschi/mcp-central-docs/blob/main/operations/WEBAPP_PORTS.md).

## Documentation

| Doc | Contents |
|-----|----------|
| [Roadmap & Architecture](DEMO_VID_MCP_PLAN.md) | Desktop-capture mode design, the `mcp_call` step type, the real remaining constraint (no Resonite camera control), v0.3 plans |
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Configuration](docs/CONFIGURATION.md) | Env vars, config options |
| [Tool Reference](docs/TOOLS.md) | All available tools |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## Requirements

- Python 3.13+ with `uv`
- FFmpeg (for composition)
- speech-mcp (for voiceover)
- Playwright (for recording, auto-installed)

## License

MIT
