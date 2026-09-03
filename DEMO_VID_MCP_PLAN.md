# demo-vid-mcp — Roadmap & Architecture

This is the file `CHANGELOG.md` has referenced since v0.1.0-beta ("See DEMO_VID_MCP_PLAN.md for
full roadmap") without it actually existing. It exists now.

## v0.1 (shipped) — webapp narration pipeline

`demo_vid_generate(repo)` auto-starts a fleet repo's webapp, records it with Playwright, narrates
with speech-mcp TTS, composes with FFmpeg. Real, tested, in production use. See `README.md` for
the full tool/webapp reference.

## v0.2 (shipped) — desktop-capture: native apps driven live

**What it does:** records a native app window (not a webapp) via OBS, while the narration script's
`action: mcp_call` steps actually invoke real tools on the app's own MCP server during the
recording — Blender building a chair via `blender-mcp`'s `blender_mesh` tool, or a Resonite session
having fixtures spawned via `resonite-mcp`'s `resonite_link_*` tools. Not a staged screen recording
— the software is genuinely being driven while the camera rolls.

### Architecture

```
script.yaml (desktop_capture: true, capture_window, obs_scene, steps[mcp_call])
        │
        ▼
generate.py: _is_desktop_capture() → skip webapp preflight → record_desktop()
        │
        ├─→ windows-computer-use-mcp: automation_windows(find, focus) — bring app to front
        ├─→ obs-mcp: obs_create_capture_scene(obs_scene, window_match) — auto-creates the
        │     scene + Window Capture source if it doesn't exist yet (see below)
        ├─→ obs-mcp: obs_scene_switch(obs_scene) → obs_recording_start()
        ├─→ for each mcp_call step: fastmcp.Client(server_url).call_tool(tool, params)
        │     (real MCP protocol call to blender-mcp / resonite-mcp / etc. — the actual demo content)
        ├─→ obs-mcp: obs_recording_stop() → obs_recording_status() for the output file path
        ▼
composer.py (unchanged — format-agnostic, feeds any video file to FFmpeg)
```

**Correction from the first draft of this doc:** cross-server calls go through `fastmcp.Client`
(the real MCP protocol), not a REST shortcut. Checked and confirmed: fleet servers do **not**
share a uniform REST tool-invocation path — freecad-mcp uses `/api/v1/control/tool`,
resonite-mcp uses `/api/v1/tool`, blender-mcp and windows-computer-use-mcp expose no REST
tool-call route at all (pure FastMCP ASGI apps), and obs-mcp's REST layer is bespoke per-action
paths (`/scenes/switch`, `/recording/start`, ...) with no generic passthrough and no route for
`obs_create_capture_scene` specifically. MCP's own `call_tool` is the one interface every server
actually guarantees, so that's what `desktop_capture.py` uses uniformly. `*_MCP_URL` env vars must
point at each server's full `/mcp` endpoint (e.g. `http://127.0.0.1:10793/mcp`), not just host:port.

### New step type: `mcp_call`

```yaml
- action: mcp_call
  server: blender_mcp        # resolves via config.py's *_mcp_url fields
  tool: blender_mesh
  params: {operation: "create_cube", name: "Seat", location: [0,0,0.5]}
  say: "First the seat."     # still narrated, same as any other step
  wait: 2                    # pacing between calls
```

This one primitive covers every "native app driven live" demo — it's server-agnostic. See
`data/scripts/blender-chair-demo.yaml` and `data/scripts/resonite-nekomimi-demo.yaml` for complete
working examples.

### Real constraints

- ~~OBS scene setup is manual~~ **Automated as of the same pass**: `obs-mcp` gained
  `obs_create_capture_scene(scene_name, window_match)`, which creates the scene and a
  Window Capture source matched to a live open window — no OBS UI clicking required, and no CUA/GUI
  automation either. It's a native obs-websocket call (`CreateInput` + `GetInputPropertiesListPropertyItems`,
  the same protocol OBS's own properties dialog uses internally). `record_desktop()` calls it
  automatically before every recording, idempotently.
- **Resonite still has no scriptable camera** — this one's a genuine, unresolved limitation.
  `resonite-mcp`'s tool surface has nothing for in-world viewpoint/spectator control (checked — not
  in `docs/TOOLS.md`). The shot is whatever the desktop client's view happens to be. A human
  positions it before recording starts; the demo script says so explicitly rather than pretending
  otherwise.
- **No narration/video timing sync.** Pre-existing limitation, not new to v0.2: `voiceover.py`
  concatenates narration segments sequentially and mixes the result in wholesale; `wait:` only
  paces the capture itself. Applies identically to webapp and desktop-capture modes.

### New config (`config.py`)

`windows_computer_use_mcp_url` (`WINDOWS_COMPUTER_USE_MCP_URL`), `obs_mcp_url` (`OBS_MCP_URL`),
`resonite_mcp_url` (`RESONITE_MCP_URL`) — plus this finally puts the previously-unused
`blender_mcp_url` field to work.

## v0.3 (future)

- Subtitle burn-in for accessibility.
- Music/stems integration (`stems-mcp`) as background bed under narration.
- Narration/video timing reconciliation (the gap noted above).
- A scriptable Resonite camera/spectator path, if `resonite-mcp` ever grows one — the last real
  manual step in the desktop-capture pipeline.
