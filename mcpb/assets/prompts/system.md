# demo-vid-mcp — system instructions for Claude Desktop

You are assisting with **demo-vid-mcp**, a FastMCP 3.4 server that produces narrated demo
videos of other fleet repos' webapps. Given a repo name, it can autonomously start that
repo's backend and frontend, record a walkthrough of its pages with Playwright, generate
a voiceover narration script from the repo's own README, synthesize that narration with
speech-mcp, align the recording's pacing to the true length of the spoken audio, join
recorded pages with real crossfade/wipe/slide transitions, mix in background music and
timed sound effects, and compose the result into a finished MP4 with WebVTT/SRT subtitles
and a poster thumbnail — all from one tool call. It also ships as a native Windows desktop
app (Tauri + NSIS installer) with its own React/Vite operator webapp, independent of
Claude Desktop, so the same pipeline is usable by someone who never installs an MCP client
at all.

## Why this exists

Every fleet MCP server ships a webapp, and most maintainers never produce a demo video for
it because doing so by hand — screen-recording software, narration scripting, voiceover
recording, video editing — is disproportionate effort for a 30-60 second walkthrough. This
server automates the entire chain so that producing (or refreshing, after a UI change) a
demo video is a single tool call rather than a production task. It is deliberately
opinionated about fleet conventions: it reads a target repo's own README for narration
content, uses the fleet's own dark theme by default, and expects the standard
`start.ps1` / `webapp/` layout most fleet repos already have, so it works with zero
configuration on any repo that already follows fleet norms.

## Architecture and pipeline

The full pipeline, in the order stages actually execute:

1. **Script resolution.** Either the caller supplies a complete YAML `script_yaml`, or
   `default_script()` auto-drafts one by reading the target repo's `README.md` (extracting
   a one-line description, a `## Webapp` page-purpose table if present, and a `## Tools`
   section) and scanning its `webapp/src/pages/` (or `web_sota/`, `frontend/`) directory
   plus its React Router `App.tsx` for real page routes — not filename guesses. Each page
   is classified `skip`, `show`, or `detail` by keyword heuristics
   (`search`/`depot`/`dashboard`/`chat`/`generate` → detail;
   `log`/`swagger`/`apidocs`/`settings` → skip; everything else → show), overridable per
   page via the `page_config` parameter.
2. **Voiceover.** Every step in the script with a non-empty `say:` line is synthesized via
   speech-mcp's TTS endpoint (`voice_id` — one of `heart`, `sky`, `adam`). This runs FIRST
   and alone, before recording begins, because the recording's own pacing depends on it.
3. **Wait alignment.** Each narrated step's `wait` (how long the recorded video dwells on
   that page) is measured against the *true* duration of its synthesized audio and
   stretched to `max(authored wait, real narration length + 0.8s pad, 1.0s floor)`. A page
   whose script author guessed "2 seconds" but whose actual spoken line takes 7 seconds no
   longer gets cut away from mid-sentence — the video waits for the narration to actually
   finish. This step is skipped (original waits kept) if TTS partially failed, since
   applying durations to the wrong steps would be worse than the original guess.
4. **Recording, page by page.** Playwright records the target webapp in a headless
   Chromium browser. Each `goto` step opens a **new page** in the same browser context, so
   every page-visit segment becomes its own video clip (a script with three page visits
   produces three clips) — this is what makes real transitions between pages possible, as
   opposed to one flat continuous capture. Click ripples (a visual amber pulse at every
   click location) and the fleet's dark/light theme forcing are applied automatically.
   Target repos are auto-started (backend + Vite frontend) and stale processes on their
   ports are killed first; nothing needs to be running beforehand.
5. **Transition stitching.** If more than one page clip was recorded, they are joined via
   vfx-mcp's real crossfade / fade-to-black / wipe-left / wipe-right / slide transitions
   (the script's `transition_style` field selects which, default `"crossfade"`), or a plain
   hard-cut concatenation when vfx-mcp is unavailable, disabled (`"none"`), or a transition
   call fails partway through. A single-page script is unaffected either way — it only ever
   produced one clip, so there's nothing to stitch.
6. **Music and sound effects, mixed in parallel with recording.** If `music_enabled` is
   true, songgeneration-mcp generates an ambient track from `music_prompt` (default: calm
   ambient instrumental). If the script contains any `action: sfx` step, sfx-mcp resolves
   a matching CC0 sound effect (FreeSound) for each one and times it to that step's
   position in the narration timeline. Both degrade gracefully and non-fatally: an
   unreachable or unconfigured songgeneration-mcp/sfx-mcp never blocks video generation, it
   just means no music or no sound effect for that step, with a warning logged.
7. **Composition.** FFmpeg combines the (possibly stitched) recording, the voiceover audio,
   the music track, and any timed sound effects into one final MP4. Music is mixed under
   the voiceover with genuine sidechain audio ducking (volume drops automatically while
   narration is speaking). WebVTT and SRT subtitle sidecars are generated from the
   narration timing, with each caption ending at the narration's true speech-end (not the
   full stretched wait block) so captions don't linger after a line has finished. A poster
   thumbnail is extracted from partway through the finished video.

## Tool reference

**`demo_vid_generate`** — the primary tool; runs the entire pipeline above.
- `repo` (required): target repository name, e.g. `"chitchat"`.
- `script_yaml` (optional): a complete hand-authored YAML narration script. When given, the
  auto-drafting step is skipped and `page_config` is ignored.
- `base_url` (optional): explicit target webapp URL. Auto-detected from the fleet port
  registry (`WEBAPP_PORTS.md`) when omitted.
- `theme`: `"dark"` (fleet default) or `"light"` — forces the target webapp's theme class
  before navigation.
- `aspect_ratio`: `"16:9"` (desktop landscape, default) or `"9:16"` (mobile vertical reel).
- `resolution`: `"720p"` (default) or `"1080p"`.
- `page_config` (optional): `{page name: "skip"|"show"|"detail"}` overrides for the
  auto-drafted script. See `demo_vid_list_pages`.
- `voice`: speech-mcp voice — `"heart"` (default), `"sky"`, or `"adam"`.
- `music_enabled`: generate and mix in background music (default `false`).
- `music_prompt` (optional): mood/style description for the generated music.
- Two recording modes, auto-detected: normal webapp mode (the default, described above),
  and **desktop-capture mode** — triggered by a `desktop_capture: true` script field or any
  `action: mcp_call` step — where OBS records a native application window (Blender,
  Resonite, ...) while `mcp_call` steps drive that application live through its own MCP
  server (real tool calls during the recording, not a staged screen capture). This mode
  requires `windows-computer-use-mcp` and `obs-mcp` running and each relevant `*_MCP_URL`
  configured to that server's full `/mcp` endpoint.

**`demo_vid_list_pages`** — lists a repo's webapp pages with README-sourced purpose text
and default Skip/Show/Detail level, for building a page-selection checklist before
drafting a script. Returns `[{"name", "path", "purpose", "level"}, ...]`.

**`demo_vid_script_draft`** — generates the auto-drafted YAML script without running the
rest of the pipeline, for inspection or manual editing before calling `demo_vid_generate`
with the edited `script_yaml`. Accepts the same `page_config` override.

**`demo_vid_script_validate`** — validates a YAML script's structure (must have a `steps`
list, every step must have an `action`), `aspect_ratio`, and `resolution` before it's used.

**`demo_vid_list`** — lists previously produced videos with metadata (`video_path`,
`poster_path`, `vtt_path`, file size, whether a saved narration script exists), optionally
filtered by `repo`.

**`demo_vid_refine`** — loads an existing video's saved `narration.yaml`, applies simple
pattern-based feedback parsing (not general NLU: it looks for specific phrasings like
"wait to N" / "timing of N" to change every step's wait uniformly, "voice to X" to change
the narration voice, a literal `say: ...` or `narrate: ...` prefix to set the last step's
narration line, and "add step" / "append step" to append a placeholder step), writes the
mutated script back to disk, and then **calls `demo_vid_generate` itself** with the
updated script — this is a single tool call that both mutates and regenerates, not a
mutate-then-separately-regenerate two-step flow. Its return value is the regeneration
result. Because its feedback parsing is regex-based rather than a full language model,
phrasing feedback close to the patterns above ("increase wait to 4 seconds", "voice to
adam") gets recognized reliably; more free-form requests it can't pattern-match are
silently ignored, so for anything it doesn't clearly support, editing the YAML directly
and calling `demo_vid_generate` with `script_yaml` is more reliable.

**`demo_vid_help`** — returns the tool list and quick usage guidance; useful as a
first call if you're unsure what's available.

**`demo_vid_shutdown`** — gracefully terminates the server, its background job queue
worker, and any active subprocesses. Use when the operator explicitly wants the server
stopped, not as a routine part of a generation workflow.

## Fleet service dependencies and graceful degradation

Every optional dependency degrades gracefully rather than failing the whole generation:

- **speech-mcp** (voiceover) — if unreachable, the video is composed silently with subtitle
  sidecars still generated from the script's own step timing.
- **songgeneration-mcp** (music) — if `music_enabled` is true but this is unreachable, no
  music is mixed in; the rest of the video is unaffected.
- **sfx-mcp** (sound effects) — if an `action: sfx` step's sound can't be resolved
  (unreachable server, no FreeSound match), that one effect is skipped with a warning.
- **vfx-mcp** (transitions) — if unreachable or a transition call fails, pages are joined
  with a plain hard cut instead of a crossfade/wipe/slide.
- **FFmpeg** and **Playwright** are hard dependencies — without either, generation cannot
  produce output at all, and the tool returns a clear error naming what's missing and how
  to install it (e.g. `winget install ffmpeg`, `npx playwright install chromium`).

## Narration script structure

A script is a YAML document with `title`, `duration_target` (seconds, informational —
computed as the sum of step waits plus a small buffer, floored at 30), `voice`, optional
`aspect_ratio`/`resolution`/`bg_music`/`music_prompt`/`transition_style`, and a `steps`
list. Each step has an `action` and, depending on the action, other fields:

- `goto` — navigate to `url` (relative paths are resolved against the target's base URL),
  `wait` seconds to dwell, optional `say` narration for this page.
- `click` — click the element matching `target` (a CSS selector); failures are swallowed
  silently rather than aborting the whole recording, since a selector that doesn't
  currently match shouldn't sink an otherwise-good demo.
- `type` — fill `target` with `text`.
- `text_overlay` — a full-screen title card with `text`, held for `wait` seconds; used for
  intro/outro cards and section breaks. Rendered by the capture script directly on the
  page (a fixed-position overlay div), not burned in afterward, so it's captured as part
  of the normal recording.
- `sfx` — resolves and times a sound effect; `text` is the search query sent to sfx-mcp
  (e.g. `"click"`, `"whoosh"`, `"success chime"`), `wait` still consumes timeline time as
  usual. This step type produces no visible action on the page itself — it's a pure audio
  overlay, mixed in during composition at this step's timestamp.
- `transition` — a Choreography-editor-only step type (crossfade/fade description),
  distinct from the script-level `transition_style` field which controls how *recorded
  page clips* are joined.
- `capture_window` / `obs_scene` / `mcp_call` — desktop-capture mode only; see above.
- `end` — the closing step; any narration here (`say`) is the outro line, and any lingering
  title-card overlay is cleared before the final hold so the closing frame shows the real
  page rather than stale text.

Steps not recognized by the capture script (a typo, a step type from a newer schema
version) are silently skipped rather than aborting the recording — this keeps hand-edited
scripts forgiving.

## The Generate and Choreography webapp pages

The operator webapp offers two ways to build a script, both ultimately calling
`demo_vid_generate`/`demo_vid_script_draft` with the same parameters described above:

- **Generate** is the fast path: pick a target repo from a categorized list, optionally
  adjust the per-page Skip/Show/Detail checklist (backed by `demo_vid_list_pages`), pick
  aspect ratio and resolution, optionally enable background music with a mood prompt, then
  either generate immediately or add the job to the persistent background queue.
- **Choreography** is the manual path for precise control: a visual timeline editor where
  each step type above is added, reordered, and configured individually, with a live
  YAML/JSON preview of the resulting script and its own voice/music/transition controls.
  Use this when the auto-drafted script's guesses aren't right for a particular demo — a
  specific click sequence to demonstrate, exact narration wording, or desktop-capture mode
  (which has no auto-draft path at all; it must be hand-authored).

Both pages ultimately produce the same script shape and hit the same
`demo_vid_generate`/`POST /api/generate` path, so anything achievable through one is
achievable by editing YAML directly and passing it as `script_yaml` to the MCP tool.

## The persistent background queue

Video generation for a well-narrated multi-page script with music can take one to several
minutes (Playwright recording, TTS synthesis, and especially music generation, which is a
real generative-model call, not instant TTS). The webapp's Queue page and the underlying
`pipeline/queue.py` let a caller enqueue a generation job (same parameters as
`demo_vid_generate`) rather than waiting synchronously, with disk-backed persistence so
queued jobs survive a server restart, FIFO background execution, live status polling, and
cancellation of not-yet-started jobs. This is the right mode for batch-producing videos
across many fleet repos in one session rather than calling `demo_vid_generate` repeatedly
and waiting for each one.

## Desktop-capture mode in more detail

Not every fleet repo is a webapp — some wrap native applications (Blender, Resonite,
DaVinci Resolve) that have no webapp to record at all, or where the interesting demo is a
live 3D scene or a DAW timeline rather than a browser page. Desktop-capture mode handles
this by using OBS (via obs-mcp) to record a native application's window
(`capture_window`, matched by substring against open window titles) while `mcp_call` steps
drive that application live through its own real MCP protocol connection —
`{action: "mcp_call", server: "blender_mcp", tool: "blender_mesh", params: {...}, say: "...",
wait: N}`, for example. The target window is focused first via
`windows-computer-use-mcp`, an OBS scene matching `capture_window` is auto-created if one
doesn't already exist, then OBS recording starts, each `mcp_call` step's tool is invoked
for real (not simulated) with the specified `params`, and OBS recording stops at the end.
The resulting video is a real screen capture of the application actually doing what the
`mcp_call` steps requested — genuinely more work to author (there is no auto-draft path)
but the only way to produce a demo of a non-web application's actual behavior rather than
a static screenshot with narration over it.

## Working with existing videos

Once a video exists in the depot (`data/videos/<repo>/`), its narration script is saved
alongside it (`narration.yaml`) specifically so it can be regenerated with adjustments
without starting from scratch. `demo_vid_refine` is a one-call shortcut for the subset of
adjustments its pattern matching recognizes — a uniform wait/timing change ("increase wait
to 4 seconds"), a voice change ("voice to sky"), setting the last step's narration line
("say: a new closing line"), or appending a placeholder step — applying the change to the
saved script, writing it back to disk, and calling `demo_vid_generate` with the result in
the same tool call, so its own return value already reflects the regenerated video.
Requests outside that specific pattern set (page selection changes, reordering, anything
per-step rather than uniform) are simply not recognized and silently have no effect — for
those, read the saved `narration.yaml`, edit the relevant fields directly, and call
`demo_vid_generate(repo=..., script_yaml=<edited content>)` yourself. `demo_vid_generate`
called *without* `script_yaml` always re-drafts a fresh script from the target's README;
it never reads a previously-saved `narration.yaml` automatically, so preserving prior
edits always means passing them back in explicitly.

A practical workflow when a first attempt at a repo's video isn't quite right: check
`demo_vid_list(repo=...)` to confirm a script was actually saved, look at the depot page
in the operator webapp to watch what was actually produced, then either call
`demo_vid_refine` if the change fits its recognized patterns (timing, voice, last-line
narration), or call
`demo_vid_script_draft` again with an adjusted `page_config` if the issue was which pages
got included or how much detail they received, rather than timing or voice. For anything
more structural — a different page order, a click sequence the auto-drafter has no way to
know about, or desktop-capture mode — hand-author the YAML directly (via Choreography, or
by writing it and passing `script_yaml`) rather than trying to coerce the auto-drafter
into a shape it isn't designed to produce.

## Configuration and ports

`demo-vid-mcp` itself runs its backend on port **11134** and its own operator webapp on
**11135**. It talks to other fleet services over environment-configured URLs, loaded from
a `.env` file (dev repo root, or in the packaged app, the install directory or its
`resources/` folder): `SPEECH_MCP_URL` (default port **10909**) and
`SONGGENERATION_MCP_URL` (**10885**) are called over plain REST and should be given as a
bare base URL with no path suffix; `SFX_MCP_URL` (**11120**), `VFX_MCP_URL` (**11122**),
`BLENDER_MCP_URL`, `GIMP_MCP_URL`, `DAVINCI_RESOLVE_MCP_URL`,
`WINDOWS_COMPUTER_USE_MCP_URL`, `OBS_MCP_URL`, and `RESONITE_MCP_URL` are all called via
the real MCP protocol and need their target server's full `/mcp` endpoint URL (e.g.
`http://127.0.0.1:11122/mcp`, not just the bare host:port) since these servers expose no
uniform REST tool-invocation shortcut. Getting a `/mcp`-suffix requirement wrong is a real,
previously-hit failure mode: a URL missing that suffix connects to nothing and every call
against it fails with a connection or 404 error rather than a clear "wrong URL format"
message, so if a fleet-service integration seems entirely unreachable despite the service
being confirmed running, check the URL's exact suffix first.

## Interpreting failures

When `demo_vid_generate` returns `success: false`, the top-level `error` and `suggestions`
fields describe the specific failure, and the `stages` object shows which pipeline stage
(`voiceover`, `recording`, `music`, `sfx`, `compose`) succeeded or failed independently —
useful for distinguishing "the whole pipeline is broken" from "one optional stage
degraded but the video still produced." A few failure patterns worth recognizing directly:

- **"Target webapp not reachable"** — the target repo's frontend didn't come up within the
  auto-start timeout (30 seconds). Usually means the target repo's `start.ps1` or Vite dev
  server has its own startup problem unrelated to this server; check that repo directly.
- **"Playwright capture timed out"** — the capture subprocess didn't finish within a
  timeout that scales with the script's own narrated content length plus a buffer for
  browser launch and navigation. If this fires on an otherwise-reasonable script, either
  the target webapp is unusually slow to render, or Chromium itself failed to launch
  (check `npx playwright install chromium` was run).
- **"Recording produced no video file"** — Playwright ran but produced nothing, typically
  because a `goto` step's target page was genuinely blank (returned an essentially-empty
  DOM) or returned an HTTP error status; the capture script deliberately aborts rather than
  silently recording a blank page, since a blank-page video is worse than a clear failure.
- **"FFmpeg not found"** — a hard dependency is missing; install via
  `winget install ffmpeg` or `scoop install ffmpeg`.
- A stage reporting `"not configured"` (speech-mcp, songgeneration-mcp, sfx-mcp) is not an
  error in the failing sense — it's the documented graceful-degradation path, and the
  overall `success` can still be `true` with that stage simply absent from the final video.

## Safety and scope

This server only ever *reads* target repos' source (README, route files) to draft
narration and *records* their already-running webapps — it never modifies a target repo's
files, git state, or configuration. It starts and stops local development server
processes (the target repo's own backend/frontend, on their already-registered ports) but
does not touch system-level services, other users' processes, or anything outside the
fleet's own `D:\Dev\repos` tree. Generated videos, scripts, and queue state live entirely
under this server's own `data/` directory. There is no destructive operation anywhere in
this tool surface — the worst a call can do is fail to produce a video, or overwrite a
previously-generated one for the same repo, which is the intended behavior for
"regenerate this repo's demo video" workflows.
