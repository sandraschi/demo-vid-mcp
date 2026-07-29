# demo-vid-mcp

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="https://glama.ai/mcp/servers"><img src="https://img.shields.io/badge/Glama-MCP_server-7c5cfc?style=flat-square" alt="Glama"></a>
  <a href="https://github.com/tailwindlabs/tailwindcss"><img src="https://img.shields.io/badge/Tailwind-4-06b6d4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind"></a>
</p>

Demo video pipeline for fleet repos. Records narrated walkthroughs of any webapp by orchestrating Playwright, speech-mcp TTS, and FFmpeg composition.

## Quick Install

```bash
uvx mcpb install sandraschi/demo-vid-mcp
```

## What You Can Do

- **Generate a video**: `demo_vid_generate(repo="chitchat")` — auto-starts the target webapp, records it, adds voiceover, composes MP4
- **Draft a script**: `demo_vid_script_draft(repo="chitchat")` — reads the README and generates a narration script
- **Browse the depot**: Categorized gallery of produced videos with inline player, rebuild, delete, and insert into repo README
- **Chat about it**: Built-in chat with personalities, example prompts, and local LLM integration (Ollama/LM Studio)

## Tools

| Tool | Description |
|------|-------------|
| `demo_vid_generate(repo)` | Full pipeline: auto-start target webapp → record (Playwright) → voiceover (speech-mcp) → compose (FFmpeg) → MP4 |
| `demo_vid_script_draft(repo)` | Generate a narration YAML from the target repo's README and webapp page structure |
| `demo_vid_script_validate(yaml)` | Validate a narration script's structure and timing |
| `demo_vid_list(repo?)` | List produced videos with metadata |
| `demo_vid_refine(name, feedback)` | NOT YET IMPLEMENTED — edit narration.yaml directly and re-run generate |
| `demo_vid_help` | List all tools and usage |

## Webapp

| Page | Purpose |
|------|---------|
| **Dashboard** | Backend status, KPI cards, pipeline overview |
| **Depot** | Categorized gallery with inline player, rebuild, delete, insert buttons |
| **Generate** | Select target repo by category → generate |
| **Choreography** | Visual script builder — 11 step types, global options, YAML preview |
| **Chat** | SOTA chat with personalities, localStorage, example prompts, LLM integration |
| **Settings** | LLM provider probe (Ollama/LM Studio), model selection, persistence |
| **Logs** | Ring-buffer log viewer with level filter and search |
| **Help** | 6-tab reference: overview, architecture, tools, config, fleet, troubleshooting |

## Autostart

`demo_vid_generate` automatically starts the target repo's backend and Vite frontend before recording. Zombie-kills stale processes first. No manual setup — the pipeline scans for `start.ps1` and `webapp/` directories.

## Fleet Services

Required: speech-mcp (voiceover), Playwright (recording), FFmpeg (composition).
Optional: blender-mcp (3D titles), OBS-mcp (human-in-video), stems-mcp (music), vfx-mcp (effects).

## Ports

Backend: **11134**, Frontend: **11135**, speech-mcp: **10909**.
See [WEBAPP_PORTS.md](https://github.com/sandraschi/mcp-central-docs/blob/main/operations/WEBAPP_PORTS.md).

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Configuration](docs/CONFIGURATION.md) | Env vars, config options |
| [Tool Reference](docs/TOOLS.md) | All available tools |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## Requirements

- Python 3.12+ with `uv`
- FFmpeg (for composition)
- speech-mcp (for voiceover)
- Playwright (for recording, auto-installed)

## License

MIT
