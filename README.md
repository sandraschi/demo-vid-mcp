# demo-vid-mcp

Demo video pipeline for fleet repos. Records, narrates, composes, and refines intro videos by orchestrating fleet services.

## Preview

| Dashboard | Gallery |
|-----------|---------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Gallery](docs/screenshots/gallery.png) |

## Quick Install

```bash
uvx mcpb install sandraschi/demo-vid-mcp
```

## Tools

- `demo_vid_generate` — full pipeline: record, voiceover, compose → MP4
- `demo_vid_list` — list produced videos with metadata
- `demo_vid_refine` — re-generate with timing/narration adjustments
- `demo_vid_script_draft` — draft a default narration YAML script
- `demo_vid_script_validate` — validate a narration script's structure
- `demo_vid_help` — list all tools

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Configuration](docs/CONFIGURATION.md) | Env vars, config options |
| [Tool Reference](docs/TOOLS.md) | All available tools |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## Fleet Services

demo-vid-mcp delegates to: speech-mcp (voiceover), blender-mcp (3D titles), gimp-mcp (title art), davinci-resolve-mcp (composition), vfx-mcp (effects), stems-mcp (music), sfx-mcp (sound). Only speech-mcp is required.

## Ports

Backend: 11134, Frontend: 11135. See [WEBAPP_PORTS.md](https://github.com/sandraschi/mcp-central-docs/blob/main/operations/WEBAPP_PORTS.md).

## License

MIT
