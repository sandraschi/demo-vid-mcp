# Build Log

Running record of NSIS installer builds for demo-vid-mcp: what was built, what broke, and the fix.

## 2026-09-04 — v0.3.0 Tauri retrofit completion + first successful NSIS build

**Context:** The Tauri/NSIS scaffold retrofit (commit `0ce5f1f`) had shipped with a
half-finished `backend.rs` (single-layer `free_port`, no TCP health poll) and a webapp
with no `@tauri-apps/api` dependency, so the desktop shell had no way to know when its
own backend was ready. Full assess-and-fix pass (see `reports/assess-2026-09-03.md`)
scored the repo 0/100 against the fleet checklist, driven almost entirely by this
incomplete retrofit plus missing session-context files, a stub MCPB prompt pack, and a
missing CUA-NSIS test harness — not by broken application code (all Python/web gates
were already green).

**Pre-build audit against `TAURI_PRODUCTION_PITFALLS.md` Phase 1 checklist:**

| Check | Before | After |
|---|---|---|
| `free_port()` multi-layer kill | Single `taskkill`-by-port only (the exact pattern that killed Docker Desktop's wslrelay fleet-wide, TRAPS #608) | Fleet canonical: image-name kill + port-holder kill + 240s poll, re-kill at 5s, UAC escalation at 15s |
| TCP health poll | Absent — stdout text-match only | 30x2s `TcpStream::connect_timeout` loop as the authoritative ready signal |
| `@tauri-apps/api` in webapp | Missing entirely | `^2.2.0` added; global Zustand store consumes `listen("backend-status")` + HTTP poll fallback (exponential backoff) |
| "Restart Backend" button | Absent | Added to Dashboard, wired to the existing `start_backend` invoke command |
| `tauri.conf.json` resources | `backend.exe` only | `+ .env.example` |
| `targets` | `["nsis"]` ✓ | unchanged (already correct) |
| `Cargo.toml` plugin deps | ✓ compliant | unchanged |
| `hooks.nsh` PREINSTALL/PREUNINSTALL | ✓ compliant | unchanged |
| CUA-NSIS smoke harness | Absent (`scripts/cua-smoke.py`, config, justfile recipes all missing) | Added (fleet template v3, `CUA_SMOKE_VERSION=3`) |
| `GET /api/v1/diagnostics` | Missing | Added |

**Build toolchain on this machine:** Rust 1.96.0 / cargo 1.96.0, NSIS (makensis) present
under `C:\Program Files (x86)\NSIS`, Node 24.4.1, bun 1.3.14. `@tauri-apps/cli` resolves
via `npx` (not globally installed as a named command). FFmpeg was **not** on PATH at
session start — installed via `winget install ffmpeg` (Gyan.FFmpeg 9.0.1) to unblock
both the real pipeline and a truthful build/test pass. `pywinauto`, `Pillow`,
`pytesseract` were not dev dependencies — added (required by the CUA smoke test
standard); Tesseract OCR was already present at the standard path.

**Build result:** `powershell -File src-tauri/build.ps1` — frontend `tsc -b && vite
build` clean, PyInstaller backend exe 16.97 MB (>5 MB size gate, not a runt build per
`tauri_nsis_building.md` Gate 0), `cargo build --release` for `demo-vid-mcp-native`
finished in 6m46s, NSIS bundle produced successfully:

```
D:\Dev\repos\demo-vid-mcp\src-tauri\target\release\bundle\nsis\Demo Vid MCP_0.3.0_x64-setup.exe
```

**First build attempt failed** with a TypeScript error (`Settings.tsx(3,1): 'useBackendStore' is declared but its value is never read`) — a genuine transient race in this session (an edit landed mid-build), not a repo defect; fixed and rebuilt clean.

**CUA-NSIS smoke test — two real bugs found and fixed via this pass, not environmental
noise:**

1. **Window-detection false negative in the smoke harness itself.** `cua_find_window()`
   did a single immediate lookup right after backend health passed, with no retry — the
   WebView2 window can render a couple seconds after the backend binds. First run
   silently skipped the nav walk entirely while still reporting "11/11 phases passed"
   (the exact false-positive class `cua_nsis_smoke_testing.md` warns about). Fixed with
   a 10s retry loop inside `cua_find_window()`; propagated to the fleet template
   (`CUA_SMOKE_VERSION` 3 -> 4).
2. **The installed backend crashed on every launch** (`ImportError: attempted relative
   import with no known parent package` from `__main__.py`, then after fixing that,
   `ModuleNotFoundError: No module named 'fastapi'`) — this is why "backend not
   reachable after 30s" kept recurring once the window-detection fix surfaced it
   properly instead of masking it. Root causes, both in the PyInstaller entry point:
   - `demo-vid-mcp-backend.spec` froze `src/demo_vid_mcp/__main__.py` directly as the
     entry script, giving it no package context for its `from .config import config`
     relative import. **Fix**: added `run_server.py` at repo root (fleet-standard
     PyInstaller entry point pattern) that imports `demo_vid_mcp.__main__` as a real
     package; spec now points at `run_server.py`.
   - `__main__.py` called `uvicorn.run("demo_vid_mcp.app:app", ...)` — a **string** app
     reference. PyInstaller's static analyzer only traces imports it can see in the
     AST; a string passed to `uvicorn.run()` at runtime is invisible to it, so `app.py`
     (and everything it imports — fastapi, starlette, etc.) was never bundled. **Fix**:
     changed to `from .app import app; uvicorn.run(app, ...)` — a direct object
     reference, matching the fleet standard's own `run_server.py` example exactly.
   Verified directly (bypassing Tauri) after the fix: `dist/demo-vid-mcp-backend.exe`
   with `PORT=11134` now serves `/api/health` and `/api/v1/diagnostics` correctly.

**Final CUA-NSIS run against the fixed installer** — real, fresh install of `Demo Vid
MCP_0.3.0_x64-setup.exe`: backend reported healthy on attempt 9 (~27s, within the
free_port poll's normal range), `GET /api/health` returned 200, `GET
/api/v1/diagnostics` returned the full real tool list/uptime/system payload, no errors
in the app log. This is genuine functional proof the fixed backend works end-to-end
through a real install — not a mock. **The window-detection retry fix (above) did not
fully resolve the gap**: `cua_find_window()` still could not find a window matching
`"Demo Vid MCP"` even with the 10s retry, so the visual nav-walk (Phase 9) and
screenshot (Phase 5) still did not execute; the script reported "11/11 phases passed"
on the strength of the REST-level checks (6, 7, 10) alone, non-fatal skips elsewhere.
**Follow-up needed**: root-cause why pywinauto's `find_elements(title_re=...)` doesn't
match this window — check the actual rendered window title/class via a live
`pywinauto.findwindows.find_elements()` dump next time the app is installed, rather than
assuming the configured title is correct just because it matches `tauri.conf.json`.

## 2026-09-04 (continued) — two more real bugs, found by direct instrumentation

The "follow-up needed" above turned out not to be a pywinauto quirk — the window really
wasn't in a findable state, because the app was crashing/hanging on every real launch.
Root-caused by directly instrumenting the installed app (`Get-Process` lifetime +
`Responding` state, `pywinauto.findwindows.find_elements()` window class dump) instead
of re-running the CUA script blind:

1. **The app self-killed ~1.5s after every launch.** `free_port()`'s image-name kill ran
   `Stop-Process -Name 'demo-vid-mcp-native'` to clear stale zombies — but `free_port()`
   executes *from inside* the currently-running `demo-vid-mcp-native.exe` process itself
   (`spawn_backend` is called from `setup()`, i.e. on the process's own startup), so this
   command matched and killed the caller. Windows process-name matching has no "not me"
   concept. Observed directly: `Get-Process -Id $pid` showed `MainWindowTitle=[Demo Vid
   MCP]` for ~1.5s, then the process vanished — every single launch, deterministically.
   **This is the same bug the fleet canonical `backend.rs.template` and the documented
   example in `tauri_nsis_building.md` both shipped** — not repo-specific drift, a
   template-level defect. **Fix**: exclude the caller's own PID
   (`std::process::id()`) from every native-image kill in `free_port()`.
2. **Even past #1, the window froze on launch** — Windows substituted a `"Demo Vid MCP
   (Not Responding)"` **Ghost**-class placeholder window (confirmed via
   `pywinauto.findwindows.find_elements()`: `class: Ghost`). `main.rs` called the
   blocking `spawn_backend()` directly inside `.setup()`, which runs on the thread also
   responsible for pumping the window's message loop — freezing the UI for however long
   `free_port()` took (several sequential PowerShell subprocess spawns at minimum, up to
   240s worst case). **Also present in `main.rs.template`** (the doc's own example in
   `tauri_nsis_building.md` already used `tauri::async_runtime::spawn` correctly — the
   template had drifted from its own documentation). **Fix**: run `spawn_backend()` on
   its own `std::thread` so `setup()` returns immediately.

**Verified genuinely fixed**, not just "no error reported": relaunched after both fixes,
`Get-Process` showed `Responding=True` from the very first poll (t=0s) and stayed alive
indefinitely; `pywinauto` reported the window's real class as `Tauri Window` (not
`Ghost`), `visible=True`; `curl http://127.0.0.1:11134/api/health` and `/api/v1/diagnostics`
both returned 200 with live data while the app sat on screen, responsive.

Both template-level fixes propagated to `mcp-central-docs/templates/tauri-native/src/{backend.rs,main.rs}.template`
and the documented `free_port()` example in `standards/rules/tauri_nsis_building.md`.
Every repo that scaffolded a Tauri shell from this template before 2026-09-04 likely
inherited both bugs and should be re-audited.

**Known gaps not addressed in this pass** (deferred, tracked in
`reports/assess-2026-09-03.md`): webapp font-size/contrast sweep (`text-xs`/
`text-slate-400` etc., ~150+ occurrences across the SPA), full loading/error-state
coverage on 4 pages, GPU-detection prompt in `/api/llm/discover`, real streaming on
`/api/llm/chat` (currently buffers the full response), Chat page skill-first wiring
(`GET /api/skills` exists but isn't called by the Chat page on mount).

## 2026-09-04 (continued) — two more real bugs from actually using the packaged app

**All /api/ fetches were relative paths, unreachable in the packaged app.** The whole
webapp (11 files) called `fetch("/api/...")`. In dev mode (`bun run dev`) Vite's proxy
makes relative paths reach the backend; in the **packaged Tauri app**, the frontend is
served from the `tauri://localhost` origin, and a relative fetch resolves against
*that* origin (Tauri's asset protocol, no `/api/*` route) instead of
`http://127.0.0.1:11134` - the request never left the WebView. This is why Settings/Chat
showed "No provider detected" even though `/api/llm/discover` correctly reported both
Ollama and LM Studio online when hit directly - the frontend never actually called it.
`tauri.conf.json`'s CSP already whitelisted `http://127.0.0.1:11134` in `connect-src`,
confirming this was the intended design, just never implemented. Fixed with
`webapp/src/lib/api.ts`'s `apiUrl()` helper (absolute origin inside Tauri, relative
otherwise) applied to every fetch call and every `<video>/<img>/<track>` `src` built
from a backend-returned path.

**Video recording failed in the packaged app**: `"Capture script not found at
C:\Users\...\Temp\scripts\playwright-capture.js"`. Two causes: (1)
`recorder.py` resolved the script path via `Path(__file__).resolve().parents[3]`, valid
only for a dev-repo checkout - inside the PyInstaller-frozen backend, `__file__`
resolves under a temp extraction dir with no `scripts/` sibling. (2)
`scripts/playwright-capture.js` was never added to the PyInstaller spec's `datas` or to
`tauri.conf.json`'s `bundle.resources` - the file didn't exist anywhere in the
installed app. Fixed: bundled `resources/playwright-capture.js` (build.ps1 now copies
it), and `recorder.py` tries three candidate locations matching the existing
`_find_ffmpeg()` pattern, including `Path.cwd() / "resources"` (Tauri sets the
backend's cwd to the install dir). Also added a best-effort `NODE_PATH` (via `npm root
-g`) so `require("playwright")` can still find a **global** Playwright install from the
installed `resources/` folder, which has no local `node_modules` ancestor to walk up to
the way a dev checkout does.

**Verified both fixes directly**, not by re-running the full pipeline blind (an earlier
attempt at this got confused by a self-referential test - pointing `demo_vid_generate`
at `repo="demo-vid-mcp"` triggers the tool's own auto-start logic against the
already-running instance, causing a port collision with a symptomatically identical but
unrelated "connection forcibly closed" error). Isolated `recorder.record()` calls
against a trivial static test server, once with `cwd` at the repo root (dev-mode
resolution branch) and once with `cwd` set to the real
`%LOCALAPPDATA%\Demo Vid MCP` install directory (packaged-mode resolution branch, exact
match for what `backend.rs::spawn_backend` sets), both produced real, playable
`.webm` files.

**Still an open architectural question, not resolved in this pass**: the packaged app's
video recording depends on Node.js + a reachable Playwright install as an external
prerequisite (same category as FFmpeg) - `NODE_PATH` finds a *global* npm install if one
exists, but nothing bundles Playwright/Chromium (~300MB+) into the installer for a
truly zero-setup experience on a machine with neither. That remains a deliberate
packaging-size decision for whoever owns the release, not something to decide silently.

## 2026-09-04 update 4 — auto-drafted videos too short, no way to steer per-page depth

User feedback after watching a generated `arxiv-mcp` video: 15s total was too short, and
the most important pages (search, depot) got the same throwaway one-liner as every other
page - no way to tell the auto-drafter "linger here, this page matters."

Root cause: `default_script()` gave every page a flat 2-4s visit regardless of
importance, and `duration_target` was `min(len(steps) * 15, 90)` - a step-count guess
disconnected from what was actually being narrated.

Fixed:
- `default_page_level()` classifies each page as skip/show/detail from keyword matching
  (log/swagger/apidocs/settings -> skip; search/depot/dashboard/chat/generate -> detail),
  overridable per-page via a new `page_config` param threaded through
  `default_script()`, `demo_vid_script_draft`, `demo_vid_generate`, and the background
  job queue (`enqueue()` / `_process_queue()`).
- "detail" pages get real dwell time (6-8s) and substantive narration even when the
  target repo's README has no `## Webapp` purpose table to pull from - previously fell
  back to the same bare 2-3s "The X page." as everything else. (arxiv-mcp's actual
  per-feature docs live in `docs/WEBAPP.md` with fleet-inconsistent structure, not the
  `## Webapp` table convention `_read_webapp_table` targets - building a parser for
  arbitrary doc formats was out of scope; the generic detail fallback covers this case
  without depending on a specific doc file existing.)
- `duration_target` is now `max(30, sum(step waits) + 5)` instead of a step-count guess,
  so it reflects actual narrated content with a 30s floor.
- New `demo_vid_list_pages` tool + `GET /api/repos/{repo}/pages` exposes each page's
  purpose and default level for a page-selection UI.
- Generate.tsx now shows a Skip/Show/Detail checklist per page, defaulted from the
  backend heuristic, sending only the overrides that differ from default as
  `page_config`.
- Found in passing while wiring `page_config` through the queue: `enqueue()` stored
  `aspect_ratio`/`resolution` on the job but `_process_queue()` never passed them to
  `demo_vid_generate` - the Generate page's aspect-ratio/resolution selectors were
  silently no-ops for anything sent to the background queue. Fixed alongside.

**Verified end-to-end in the rebuilt installer**, not just via unit tests: reinstalled,
confirmed a single healthy backend+native process pair, hit
`GET /api/repos/arxiv-mcp/pages` directly against the packaged backend (correct
skip/show/detail defaults for all 15 pages), then drove the actual Tauri window via
`pywinauto` (screenshot-verified, since the packaged webview is `tauri://localhost` and
not reachable from a normal browser) - selected arxiv-mcp on the Generate page, saw the
checklist render with the same defaults, clicked Draft script, and confirmed the output
JSON had `duration_target: 55` (up from the previous ~15s) with the intro `text_overlay`
step carrying the README's actual first line, em-dash included, rendering correctly in
the live webview.

## 2026-09-04 update 5 — capture timeout regression + .env never actually loaded

Two more bugs surfaced from real usage after update 4 shipped.

**Bug 1: `recorder.py`'s capture subprocess had a flat 45s timeout.** Fine when scripts
totaled ~15s of wait time; once detail-level pages started producing 50s+ of narrated
content, a genuinely-still-running capture got killed and reported as `"Playwright
capture timed out after 45s"` - the very first real generation attempt after update 4.
`_capture_timeout()` now scales with the script's own content
(`sum(wait times) + 60s` buffer for browser launch/navigation), extracted as a small
pure function (`recorder.py`) with direct unit tests instead of computed inline.

Verified with a real, non-mocked capture: 54.5s elapsed against arxiv-mcp (would have
hit the old 45s cap and failed exactly as reported), producing a genuine 3.7MB `.webm`.

**Bug 2: `.env` was never actually loaded, anywhere, ever.** Every fleet-service URL
(`SPEECH_MCP_URL` etc.) is read via `os.getenv()` in `config.py`, and the app's own
error message says `"Set SPEECH_MCP_URL in .env"` - but nothing in the codebase called
`load_dotenv()`. The dev repo's `.env` had `SPEECH_MCP_URL` correctly set the entire
time; it was simply never read, so voiceover always failed with `"speech-mcp not
configured"` even with speech-mcp healthy and running on port 10909. Compounding this,
the packaged app's `resources/` only ever got `.env.example` copied into it, never a
real `.env` - so even with the loading bug fixed, a fresh install would have found
nothing to load.

Fixed both: `_load_env_file()` in `config.py` calls `load_dotenv()` against the first
existing candidate (dev repo root, then `Path.cwd()` - Tauri's cwd is the install dir -
then `cwd/resources`), called before `class Config` so it runs ahead of the dataclass
field defaults being evaluated (those run once at import time). `build.ps1` now also
seeds `resources/.env` from `.env.example` on build, but only if one doesn't already
exist there, so a customized `.env` from a prior install is never clobbered on upgrade -
same non-clobber pattern as the `.mcpbignore` fix in `mcp-central-docs`. Added
`resources/.env` to `tauri.conf.json`'s bundle list so it actually ships.

**Verified end-to-end in the rebuilt, reinstalled packaged app**: ran a real generation
via the exact `POST /api/generate` call the Generate page's button makes.
`stages.voiceover` came back `{"success": true, "message": "Voiceover generated: 14
segments"}` (previously `"speech-mcp not configured"` on every attempt), and the final
`.mp4` in the app's own `data/videos/arxiv-mcp/` carries a real AAC audio stream
alongside the h264 video (`ffprobe` confirmed both), running 66.3s with full narration -
not a silent video with subtitles as a fallback, an actually-spoken one.
