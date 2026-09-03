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

**Known gaps not addressed in this pass** (deferred, tracked in
`reports/assess-2026-09-03.md`): webapp font-size/contrast sweep (`text-xs`/
`text-slate-400` etc., ~150+ occurrences across the SPA), full loading/error-state
coverage on 4 pages, GPU-detection prompt in `/api/llm/discover`, real streaming on
`/api/llm/chat` (currently buffers the full response), Chat page skill-first wiring
(`GET /api/skills` exists but isn't called by the Chat page on mount).
