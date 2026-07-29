# CLAUDE.md — demo-vid-mcp

Per-repo agent instructions for the demo video pipeline server.

## Entry points

- `src/demo_vid_mcp/__main__.py` — dual-transport IO core
- `src/demo_vid_mcp/server.py` — FastMCP tool registrations
- `src/demo_vid_mcp/app.py` — FastAPI REST + webapp backend

## Standards

- FastMCP 3.4.4+, `prefab-ui` core dep
- Bun for webapp, Vite stays
- No stubs — every tool must return real results
- Dialogic returns on failure (`suggestions`/`recovery_options`)
