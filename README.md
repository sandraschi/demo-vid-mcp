# demo-vid-mcp

Demo video pipeline for fleet repos. Records narrated walkthroughs of any webapp by orchestrating Playwright, speech-mcp TTS, and FFmpeg composition.

## Quick Install

```bash
uvx mcpb install sandraschi/demo-vid-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `demo_vid_generate(repo)` | Full pipeline: auto-start target webapp → record (Playwright) → voiceover (speech-mcp) → compose (FFmpeg) → MP4 |
| `demo_vid_script_draft(repo)` | Generate a narration YAML from the target repo's README and webapp page structure |
| `demo_vid_script_validate(yaml)` | Validate a narration script's structure and timing |
| `demo_vid_list(repo?)` | List produced videos with metadata |
| `demo_vid_refine(name, feedback)` | Re-generate a video with timing/narration adjustments |
| `demo_vid_help` | List all tools and usage |

## Webapp

| Page | Purpose |
|------|---------|
| **Dashboard** | Backend status, KPI cards, pipeline overview |
| **Depot** | Categorized gallery with inline player, script viewer, rebuild and delete buttons |
| **Generate** | Select target repo by category (8 categories) → optional script edit → generate |
| **Logs** | Ring-buffer log viewer with level filter and search |
| **Scripts** | Narration script status across the fleet |
| **Help** | Architecture, ports, tool reference |

## Autostart

`demo_vid_generate` automatically starts the target repo's backend and Vite frontend before recording. No manual setup needed — the pipeline scans for `start.ps1` and `webapp/` directories.

## Content gate

The recorder checks for blank pages and HTTP errors. If the target webapp returns a 4xx/5xx, empty body, or only `<div id="root">`, the pipeline aborts with a clear error message. No silent white-screen videos.

## Fleet Services

Required: speech-mcp (voiceover), Playwright (recording), FFmpeg (composition).  
Optional: blender-mcp (3D titles), gimp-mcp (title art), davinci-resolve-mcp (composition), vfx-mcp (effects).

## Ports

Backend: 11134, Frontend: 11135. See [WEBAPP_PORTS.md](https://github.com/sandraschi/mcp-central-docs/blob/main/operations/WEBAPP_PORTS.md).

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Configuration](docs/CONFIGURATION.md) | Env vars, config options |
| [Tool Reference](docs/TOOLS.md) | All available tools |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## License

MIT
