# Onboarding — demo-vid-mcp

## What this is for

demo-vid-mcp turns a YAML narration script into a finished MP4 demo video: it drives
Playwright (or a native desktop capture via obs-mcp) to record a target webapp or app
window, adds TTS voiceover through speech-mcp, and composes the result with FFmpeg —
subtitles, poster frame, and all. It does **not** host or stream video, and it does not
record arbitrary desktops unattended; every recording is driven by an explicit script.

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | No |
| Free tier? | N/A — everything runs locally |
| Credit card required? | No |
| Ongoing cost? | Free |
| Who bills? | Nobody — no third-party vendor is involved |

## Prerequisites outside this repo

- **FFmpeg** on `PATH` — composes the final MP4/subtitles. Install with
  `scoop install ffmpeg` or `winget install ffmpeg`. Without it, `demo_vid_generate`
  fails at the compose step with an actionable error naming the install command.
- **Node.js + Playwright Chromium** — the recorder shells out to
  `scripts/playwright-capture.js` (uses the root `@playwright/test` dependency). Run
  `npx playwright install chromium` once after `npm install`/`bun install`.
- **speech-mcp** (optional) — provides TTS narration on `http://127.0.0.1:10909` by
  default (`SPEECH_MCP_URL` in `.env`). If it's not running, generation still succeeds
  but videos have no voiceover — this is a graceful degrade, not a hard failure.
- **Ollama or LM Studio** (optional) — only needed for the webapp's Chat page. Detected
  automatically on `:11434` / `:1234`; the rest of the app works fully without either.
- **Sibling fleet MCPs** (optional, desktop-capture mode only) — `blender-mcp`,
  `gimp-mcp`, `davinci-resolve-mcp`, obs-mcp, etc. Only relevant if you're recording a
  native app window instead of a webapp; see `data/scripts/*.yaml` for examples.

## First-timer setup steps

1. Install the Python side: `uv sync --group dev`
2. Install FFmpeg: `scoop install ffmpeg` (or `winget install ffmpeg`)
3. Install the frontend + Playwright browser:
   ```powershell
   bun install
   npx playwright install chromium
   ```
4. Start the backend: `just serve` (or `.\start.ps1` for the full Tauri desktop shell)
5. Open the webapp Dashboard — the backend status dot should turn green
6. Generate your first video: `demo_vid_generate(repo="chitchat")` (or any repo under
   `DEMO_VID_REPOS_ROOT`), or use the **Generate** page in the webapp

## Pitfalls

- **FFmpeg not on PATH but "installed"** — Windows PATH changes need a new shell/process;
  restart the backend after installing FFmpeg.
- **`npx playwright install chromium` skipped** — recording fails with a Chromium-launch
  error; the message tells you the exact command to run.
- **Desktop-capture scripts assume a specific sibling MCP is already running** — those
  scripts call the target app's own MCP server (e.g. Blender) during recording; if it's
  not running, the `mcp_call` steps fail mid-recording, not at validation time.
- **Recording a repo whose `start.ps1` binds a port already in use** — the autostart
  step zombie-kills stale processes on that repo's port first, but a genuinely different
  service squatting the port will still block the recording.

## Sanity check

- `GET /api/health` reports `"status": "ok"` and the Dashboard backend dot is green
- `GET /api/health/speech` reports `"detected": true` if speech-mcp is running (narration
  will be silent, not broken, if it reports `false`)
- A `demo_vid_generate(repo="chitchat")` dry run against a small repo produces an MP4
  under `data/videos/` with a non-zero size and a `.vtt` subtitle sidecar

## Declared doubles

None. There is no mock/sample-data mode — the Dashboard, Depot, and Queue pages show
real backend state only. When the backend is offline, pages show an honest "Offline"
state (see `backend-dot` / offline banner on the Dashboard) rather than fake content.
