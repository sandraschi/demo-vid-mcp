# Configuration

`.env` is loaded automatically from the dev repo root, or (in the packaged app) the
install directory / its `resources/` folder - whichever exists first. A template
lives at `.env.example`; the packaged app seeds a real `.env` from it on first
install (never overwritten on upgrade if you've customized it).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Backend bind address |
| `PORT` | `11134` | Backend port |
| `DEMO_VID_DATA_DIR` | `data` | Data directory for videos |
| `DEMO_VID_LOG_LEVEL` | `info` | Logging level |
| `DEMO_VID_REPOS_ROOT` | `D:/Dev/repos` | Fleet repos root, for README-aware script drafting |
| `SPEECH_MCP_URL` | (optional) | speech-mcp endpoint (REST base, e.g. `http://127.0.0.1:10909`) - voiceover narration |
| `SONGGENERATION_MCP_URL` | (optional) | songgeneration-mcp endpoint (REST base, e.g. `http://127.0.0.1:10885`) - background music generation. Aggregates Lyria 3 Pro/ACE-Step/Stable Audio/Studio SG2, tried in order |
| `SFX_MCP_URL` | (optional) | sfx-mcp `/mcp` endpoint (e.g. `http://127.0.0.1:11120/mcp`) - timed sound effects via FreeSound CC0. Requires sfx-mcp's own `FREESOUND_API_KEY` |
| `VFX_MCP_URL` | (optional) | vfx-mcp `/mcp` endpoint (e.g. `http://127.0.0.1:11122/mcp`) - real crossfade/wipe/slide transitions between recorded pages |
| `BLENDER_MCP_URL` | (optional) | blender-mcp `/mcp` endpoint - desktop-capture mode |
| `GIMP_MCP_URL` | (optional) | gimp-mcp `/mcp` endpoint |
| `DAVINCI_RESOLVE_MCP_URL` | (optional) | davinci-resolve-mcp `/mcp` endpoint |
| `STEMS_MCP_URL` | (optional) | stems-mcp `/mcp` endpoint - audio stem *separation*, not generation (not currently wired into any pipeline stage) |
| `RESONITE_MCP_URL` | (optional) | resonite-mcp `/mcp` endpoint - desktop-capture mode |
| `WINDOWS_COMPUTER_USE_MCP_URL` | (optional) | windows-computer-use-mcp `/mcp` endpoint - window focus for desktop-capture mode |
| `OBS_MCP_URL` | (optional) | obs-mcp `/mcp` endpoint - desktop-capture mode recording |

`SPEECH_MCP_URL`/`SONGGENERATION_MCP_URL` are called over plain REST (no `/mcp` suffix); every other
`*_MCP_URL` is called via the real MCP protocol (`fastmcp.Client`) and needs the full `/mcp` endpoint URL.
