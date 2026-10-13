# demo-vid-mcp — user guide and tutorials

This guide walks through actually using demo-vid-mcp from Claude Desktop (or any MCP
client), from the very first video through advanced customization. It's written for
someone who has never called any of this server's tools before.

## Before you start: what you need running

demo-vid-mcp needs three things to produce a fully-featured video, though it degrades
gracefully without any of them:

1. **FFmpeg** — hard requirement, no video composition happens without it. If you don't
   have it: `winget install ffmpeg` (Windows) or `scoop install ffmpeg`.
2. **Playwright with Chromium** — hard requirement for webapp recording. Usually
   auto-installed the first time you generate a video; if not, `npx playwright install
   chromium`.
3. **speech-mcp running** — optional but strongly recommended. Without it your video will
   still be produced, just silently, with subtitles instead of narration. Start it the
   same way you'd start any other fleet MCP server on your machine.

Two more services are entirely optional and only matter if you want music or sound
effects or real page transitions: **songgeneration-mcp** (background music),
**sfx-mcp** (sound effects — needs its own FreeSound API key configured separately), and
**vfx-mcp** (crossfade/wipe transitions between pages — without it, pages are just joined
with a plain cut, which still looks fine).

## Your first video: the simplest possible call

The absolute minimum is one parameter — the name of a fleet repo you want a demo of:

> "Generate a demo video of chitchat"

This calls `demo_vid_generate(repo="chitchat")`. Behind the scenes: demo-vid-mcp reads
chitchat's README to figure out what it does and what its pages are, starts chitchat's
own backend and frontend if they're not already running, records a walkthrough of its
pages (using keyword heuristics to decide which pages deserve more time — search and
dashboard-like pages get lingered on, settings and logs pages get skipped or shown
briefly), generates narration from the README's description of each page, aligns the
recording's pacing to match how long that narration actually takes to speak, and
composes everything into an MP4 with subtitles. This typically takes somewhere between
thirty seconds and two minutes depending on how many pages the target repo has and
whether speech-mcp needs to synthesize much narration.

When it finishes, you'll get back a result with `video_path`, `poster_path`, and subtitle
sidecar paths. The video itself is saved under `data/videos/chitchat/final.mp4` in
demo-vid-mcp's own data directory, and it's also visible in the Depot page of the
operator webapp if you have that running.

## Choosing what gets emphasis: page_config

The auto-drafter's keyword heuristics get you a reasonable default, but you know your
own repo better than a keyword match does. If you want to be explicit about which pages
matter:

> "First show me the pages for arxiv-mcp, then generate a video where the search and
> depot pages get detailed narration but skip the logs and API docs pages"

This is two calls: `demo_vid_list_pages(repo="arxiv-mcp")` to see what pages exist and
what level they'd get by default, then
`demo_vid_generate(repo="arxiv-mcp", page_config={"search": "detail", "depot": "detail",
"logs": "skip", "apidocs": "skip"})`. The three levels are:

- **`"skip"`** — this page never appears in the video at all.
- **`"show"`** — a brief visit, a couple of seconds, minimal narration.
- **`"detail"`** — a longer dwell (six to eight seconds) with fuller narration describing
  what the page actually does, pulled from the repo's README if it documents that page,
  or a generic-but-substantive line if it doesn't.

Only override the pages where the default guess is wrong — anything you don't mention in
`page_config` keeps its heuristic default.

## Picking a narration voice

Three voices are available: `heart` (the default), `sky`, and `adam`. To use a specific
one:

> "Generate a video for blender-mcp using the adam voice"

This is `demo_vid_generate(repo="blender-mcp", voice="adam")`. If you're using the
operator webapp instead of talking to Claude directly, the dedicated Speech settings
page lets you pick a voice once and it's remembered for future Generate-page calls,
along with a preview button so you can hear what each voice actually sounds like before
committing to a full video generation.

## Adding background music

Background music is off by default — turning it on is one extra parameter, plus
optionally describing the mood you want:

> "Generate a demo of songgeneration-mcp itself, with upbeat background music"

`demo_vid_generate(repo="songgeneration-mcp", music_enabled=True,
music_prompt="upbeat electronic")`. The music is generated fresh each time (it's a real
generative call to whichever backend songgeneration-mcp has configured — Lyria, ACE-Step,
Stable Audio, or a local Studio instance, tried in that order until one succeeds) and
mixed under your narration with automatic ducking, meaning the music volume
automatically drops while anyone is talking and comes back up during quiet stretches, so
it never fights with the narration for attention. If you don't specify a `music_prompt`,
a calm ambient instrumental default is used, which works reasonably as a background bed
for almost any kind of walkthrough.

## Sound effects on specific moments

Sound effects aren't a top-level parameter — they're something you add as steps inside a
hand-authored or edited script, because a sound effect only makes sense tied to a
specific moment (a click, a page transition, a success state), not the video as a whole.
The easiest way to add one is through the Choreography page in the operator webapp: add
a "Sound Effect" step at the point in your timeline where you want it, and give it a
short text description of the sound you want (like "click" or "whoosh" or "success
chime") — that description becomes the search query sent to sfx-mcp, which looks up a
matching CC0-licensed sound from FreeSound and downloads the first good match. If you're
building the script by hand instead, this is just:

```yaml
steps:
  - action: goto
    url: /dashboard
    wait: 2
    say: "Here's the dashboard."
  - action: sfx
    text: "notification chime"
    wait: 1
  - action: goto
    url: /settings
    wait: 2
```

The sound effect step doesn't do anything visible on the page — it's purely an audio
overlay mixed in at that exact point in the timeline during composition.

## Real transitions between pages

By default, pages are joined with a crossfade — the previous page fades into the next
one rather than cutting abruptly. If you'd rather have a different transition, or none
at all, set `transition_style` in your script (or, if you're using a hand-authored
script through `demo_vid_generate`'s `script_yaml` parameter, add it at the top level
alongside `title` and `voice`):

- `"crossfade"` — the default, a smooth cross-dissolve.
- `"fade_to_black"` — each page fades out to black before the next fades in.
- `"wipe_left"` / `"wipe_right"` — one page wipes off screen as the next slides in.
- `"slide"` — a sliding transition between pages.
- `"none"` — a plain hard cut, no transition at all.

If vfx-mcp isn't running or isn't configured, whatever `transition_style` you asked for
silently falls back to a plain cut — you'll still get a complete video, just without the
requested visual flourish, and this fallback is intentional so a missing optional
service never blocks you from getting a finished video.

## Working with an existing video

Once you've produced a video for a repo, you don't have to start over to fix something
small:

> "Increase the wait time on the chitchat video to 4 seconds per step and switch it to
> the sky voice"

This is `demo_vid_refine(video_name="chitchat", feedback="increase wait to 4 seconds and
voice to sky")`. It reads the previously-saved narration script for that video, applies
both changes to it, writes the update back to disk, and calls `demo_vid_generate` with
the result *in the same tool call* — you get the regenerated video back directly, no
follow-up call needed. `demo_vid_refine`'s feedback parsing is pattern-based rather than
a full language model, so it recognizes phrasings close to "wait/timing/pause to/of
&lt;number&gt;" and "voice to &lt;name&gt;" specifically; vaguer phrasing like "slow it down a
bit" with no number won't match anything and the script will be left unchanged. When in
doubt, phrase the number and the field explicitly, the way the example above does.

To see everything you've already produced:

> "What demo videos have been generated so far?"

`demo_vid_list()` with no `repo` filter lists everything; add `repo="chitchat"` to see
just one repo's videos and whether it has a saved script available for refinement.

## Batch-generating videos for many repos

If you want demo videos for a whole batch of repos rather than one at a time, use the
background queue instead of calling `demo_vid_generate` repeatedly and waiting for each
one to finish — the operator webapp's Queue page lets you enqueue a job (same parameters
as `demo_vid_generate`) and watch it process in the background, with jobs surviving even
if the server restarts partway through a batch. Through Claude directly, this looks like
calling the equivalent `POST /api/queue` REST endpoint the webapp itself uses, though the
straightforward MCP-tool path for a handful of repos is simply calling
`demo_vid_generate` once per repo and letting each one complete before starting the next.

## Desktop-capture mode: demoing native applications

Not everything is a webapp. If you want a demo video of, say, Blender actually modeling
something, or Resonite actually being driven by its own MCP server, you need
desktop-capture mode — there's no auto-draft path for this, you write the script by
hand:

```yaml
title: "Blender chair demo"
desktop_capture: true
capture_window: "Blender"
obs_scene: "blender-demo"
steps:
  - action: mcp_call
    server: blender_mcp
    tool: blender_mesh
    params: { operation: "create_cube" }
    say: "Let's start with a simple cube."
    wait: 3
  - action: end
    say: "And that's a chair, roughly."
    wait: 2
```

`demo_vid_generate(repo="blender-mcp", script_yaml=<the above>)`. This requires
`windows-computer-use-mcp` and `obs-mcp` running, plus `BLENDER_MCP_URL` (or whichever
server your `mcp_call` steps target) configured to that server's real `/mcp` endpoint.
The result is a genuine screen recording of Blender actually executing those tool calls
live — not a narrated screenshot, an actual demonstration of the tool working.

## Common problems and what they mean

**"speech-mcp not configured" but you expected narration** — either `SPEECH_MCP_URL`
isn't set in your `.env`, or speech-mcp isn't actually running on the port that variable
points at. Your video was still produced; it's just silent with subtitles. Fix the URL
or start speech-mcp, then regenerate.

**A video came out with no music despite `music_enabled=True`** — songgeneration-mcp
either isn't running, isn't configured (`SONGGENERATION_MCP_URL`), or none of its
backends (Lyria, ACE-Step, Stable Audio, Studio) are actually installed/available. Check
the Music settings page's health indicator in the operator webapp, or just try the
"Generate & Preview" button there to see the actual error.

**Pages are joined with a hard cut instead of the crossfade you expected** — vfx-mcp
either isn't running or isn't reachable at its configured `/mcp` URL, or the transition
call itself failed for some reason. The video is still complete and correct, just with a
plainer visual join between pages than requested.

**"Target webapp not reachable" and generation fails outright** — this is not a graceful
degradation case; it's a real failure. It means the target repo's own frontend didn't
come up within the auto-start timeout. Try starting that repo's own `start.ps1` manually
first and see what it reports — the problem is almost always in the target repo, not in
demo-vid-mcp itself.

**A long narration line got cut off mid-sentence in an older video** — this was a real
bug that existed before narration/video alignment was added: recording used to run on a
fixed guess for how long each page should be shown, and any line whose actual spoken
length exceeded that guess got interrupted by the next page appearing. This is fixed now
— every narrated page's dwell time is measured against the real synthesized audio and
stretched to cover it — so regenerating an old video that suffered from this will produce
a corrected one automatically.

## Choosing aspect ratio and resolution

Most demo videos are landscape, meant for a README embed or a desktop-focused audience,
which is the `"16:9"` default. If you're producing something for a vertical format —
a social media reel, a mobile-first showcase — switch to `"9:16"`:

> "Generate a vertical demo of chitchat for social media"

`demo_vid_generate(repo="chitchat", aspect_ratio="9:16")`. Resolution defaults to
`"720p"`, which is fine for most purposes and renders faster; bump to `"1080p"` if you
need a higher-fidelity output and don't mind the longer composition time. Both
parameters combine independently — a `9:16` video at `1080p` is a full-resolution
vertical mobile format, `16:9` at `720p` is a fast, small landscape file well suited for
embedding directly in a repo's README.

## Validating a hand-written script before running it

If you've written or heavily edited a YAML script by hand and want to check it's
structurally sound before spending the time to actually record and compose it:

> "Check whether this narration script is valid before I generate the video"

This calls `demo_vid_script_validate(script_yaml=<your yaml>)`, which confirms the
document parses as YAML, has a `steps` list, that every step has an `action`, and that
any `aspect_ratio`/`resolution` values given are ones this pipeline actually supports.
It won't catch every possible problem (a `click` step targeting a selector that doesn't
exist on the real page, for instance, can only be discovered by actually running the
capture), but it catches the class of error that would otherwise only surface after
several minutes of recording and composing.

## Drafting without generating

Sometimes you want to see what the auto-drafter would produce without committing to a
full generation run — maybe to hand-tune the narration wording before recording, or just
out of curiosity about how a particular repo's README gets turned into a script:

> "Show me what script would get auto-drafted for gimp-mcp, but don't generate the video
> yet"

`demo_vid_script_draft(repo="gimp-mcp")` returns the YAML without touching Playwright,
speech-mcp, or any other pipeline stage — nothing is recorded or composed. This is also
the natural first step if you're planning to hand-edit the result: draft it, review the
narration lines and page selection, adjust anything that reads awkwardly or picks the
wrong pages, then pass your edited version back in as `script_yaml` to
`demo_vid_generate`.

## Frequently confused things

**"Why does music sound different every time I generate the same video?"** — background
music is generated fresh by songgeneration-mcp on every call, not cached or reused. If
you want the *exact* same music track across multiple generations of the same repo (say,
while iterating on narration wording), generate once, note which file was produced
(`music.wav` in that video's data directory), and reference it directly in a
hand-authored script rather than relying on `music_enabled` to regenerate it identically
— it won't, by design, since each generation call is an independent request to a
generative model.

**"I asked for a sound effect and nothing happened"** — the most common cause is sfx-mcp
not having a FreeSound API key configured (this is a separate setup step from just
running sfx-mcp; check that repo's own configuration). The second most common cause is
the search query in the `sfx` step's `text` field being too specific or unusual for
FreeSound's library to have a good CC0 match — try a more generic description ("click"
rather than "vintage typewriter carriage return").

**"Can I use a script from one repo on a different repo?"** — yes, mechanically: nothing
stops you passing `script_yaml` written for one target at a different `repo` value, since
`goto` URLs get resolved relative to whichever `base_url` is in effect for that call. But
the narration text won't make sense for a different repo's actual pages unless you also
edit it, so this is really only useful as a starting template, not a direct reuse.

**"The video is silent even though speech-mcp is running"** — confirm `SPEECH_MCP_URL`
in your `.env` actually matches the port speech-mcp is listening on, and that it's a bare
REST base URL (like `http://127.0.0.1:10909`) rather than an MCP endpoint URL with a
`/mcp` suffix — speech-mcp is one of the two services (the other being
songgeneration-mcp) called over plain REST rather than the MCP protocol, so it's the one
case where adding `/mcp` to the URL would actually break the connection rather than fix
it.

**"How long does a typical generation actually take?"** — for a webapp with four or five
pages and a couple dozen seconds of total narration, expect somewhere around one to two
minutes: a few seconds for the target's own startup if it wasn't already running, TTS
synthesis is usually fast (a few seconds per line), the Playwright recording itself takes
roughly as long as the video's own runtime since it's a real-time capture, and FFmpeg
composition adds a modest amount more. Enabling background music adds the most
variability, since generative music models can take anywhere from several seconds to a
couple of minutes depending on which backend songgeneration-mcp actually uses.

## Using the operator webapp directly

Everything described above is also reachable from demo-vid-mcp's own webapp, whether
you're running it as a plain dev server or as the packaged Tauri desktop app (which needs
no Claude Desktop at all — it's a standalone Windows application with its own installer).
The pages, briefly:

- **Dashboard** — a quick health overview: is the backend reachable, how many videos exist,
  whether speech-mcp is detected, with a one-click reconnect if the backend port looks
  dead.
- **Generate** — the fast path described above: pick a repo, adjust the page checklist,
  pick aspect ratio/resolution, optionally turn on music, then either generate immediately
  or send the job to the background queue.
- **Choreography** — the manual timeline editor. Every step type (goto, click, type,
  wait, narrate, sound effect, transition, text overlay, capture window, OBS scene, end)
  is available as a button you click to append it to the timeline; each step's fields
  (URL, target selector, wait duration, narration text) are edited inline; a live preview
  panel on the right shows the exact YAML/JSON that will be sent, updating as you build.
- **Speech** — a dedicated settings page for narration: pick a voice, see whether
  speech-mcp is currently reachable, and type a line of text to hear an actual preview in
  that voice before committing to a full generation.
- **Music** — the equivalent for background music: an enable toggle, a text field for
  the mood/style prompt, a health check against songgeneration-mcp, and a "generate and
  preview" button that produces a genuine ~15-second sample (which can take up to a couple
  of minutes on first use, since it's a real generative call) so you can hear what a given
  prompt actually produces before using it on a full video.
- **Depot** — the gallery of everything already produced: thumbnails, an inline video
  player with subtitle toggle, filtering by repo, and one-click actions to rebuild a video
  from its saved script, delete it, or insert a link to it into the target repo's own
  README.
- **Queue** — the background job manager: everything currently pending, running, or
  finished, with live status updates and a cancel button for anything not yet started.
- **Chat** — a general-purpose chat interface with a local LLM (Ollama or LM Studio,
  auto-detected), useful for asking questions about the pipeline or drafting narration
  wording before committing it to a script, independent of the video generation pipeline
  itself.
- **Settings** — LLM provider selection for the Chat page, plus an About section showing
  the current version and every fleet service's expected port.
- **Logs** and **Help** — a ring-buffer log viewer for diagnosing a failed generation, and
  a reference page covering the same tool surface and architecture this guide describes.

## A note on iteration speed

Because a full generation involves real subprocess work (a real browser recording in real
time, a real TTS synthesis call, potentially a real generative music call), the fastest
iteration loop when you're dialing in narration wording or page selection is usually:
draft the script without generating (`demo_vid_script_draft`), review and edit the
narration text directly in the returned YAML, *then* generate once with your edited
`script_yaml` rather than repeatedly calling `demo_vid_generate` with different
`page_config` values and waiting for a full recording each time just to see how the
wording reads. Once the page selection and wording both look right on paper, one full
generation confirms whether the timing and pacing also feel right in the actual video —
and if the pacing needs a tweak (a page you want lingered on longer, a line that reads a
bit rushed), the alignment feature already stretches narrated pages to match their true
spoken length automatically, so timing issues are far less common than they were before
that feature existed; most remaining pacing adjustments are really page-selection or
wording adjustments in disguise.

## More example dialogues

> **You:** "I want a demo video of blender-mcp actually modeling a simple chair, with
> commentary, and I want it recorded from the real Blender window, not a fake
> screenshot."
>
> **Claude:** "That needs desktop-capture mode, which means hand-writing the script since
> there's no auto-draft for driving a native app. I'll need windows-computer-use-mcp and
> obs-mcp running, and BLENDER_MCP_URL configured. Here's a script that creates a cube,
> narrates each step, and captures the real Blender window throughout — want me to run
> it?" *(after confirmation, calls `demo_vid_generate` with a hand-authored
> `desktop_capture: true` script containing `mcp_call` steps against `blender_mcp`)*
> "Done — this is a genuine screen recording of Blender executing those exact tool calls,
> not a staged narration over a static image."
>
> **You:** "Generate demos for arxiv-mcp, calibre-mcp, and blender-mcp, and don't make me
> wait around for each one."
>
> **Claude:** "I'll add all three to the background queue so they process one after
> another without you waiting on each call." *(enqueues three jobs via the queue path
> rather than three sequential blocking `demo_vid_generate` calls)* "All three are
> queued. You can check progress on the Queue page any time, or ask me and I'll check
> `demo_vid_list()` for you."
>
> **You:** "The last video for chitchat looks fine but I realize I never actually
> enabled music on it — can you just add music without redoing everything else?"
>
> **Claude:** "There's no way to add music to an already-composed video without
> re-running the pipeline, since the mixing happens during composition. Calling
> `demo_vid_generate` again without a `script_yaml` would re-draft a fresh script from
> the README rather than reuse the one already saved, so I'll read the existing saved
> `narration.yaml` first and pass its exact contents back in, just adding
> `music_enabled=True` on top — that way the pages and narration stay identical and only
> the music changes." *(reads the saved script, then calls
> `demo_vid_generate(repo="chitchat", script_yaml=<the saved script's contents>,
> music_enabled=True)`)* "Regenerated with background music added, everything else the
> same as before."
>
> **You:** "What's actually in the arxiv-mcp video I generated last week — does it have a
> script saved I could tweak?"
>
> **Claude:** *(calls `demo_vid_list(repo="arxiv-mcp")`)* "Yes — there's a saved
> `narration.yaml` alongside that video. Want me to show you its contents, or describe a
> change and I'll refine it directly?"

## Example dialogue

> **You:** "Make me a video showing off the search and depot pages of arxiv-mcp in
> detail, skip the logs and settings pages, use the sky voice, and add some calm
> background music."
>
> **Claude:** *(calls `demo_vid_list_pages(repo="arxiv-mcp")` to confirm the real page
> names, then `demo_vid_generate(repo="arxiv-mcp", page_config={"search": "detail",
> "depot": "detail", "logs": "skip", "settings": "skip"}, voice="sky", music_enabled=True,
> music_prompt="calm ambient instrumental")`)* "Generated — the video is about 45 seconds,
> with detailed narration on the search and depot pages, the sky voice throughout, and a
> calm ambient music bed underneath. It's saved at
> `data/videos/arxiv-mcp/final.mp4`, and you can watch it in the Depot page."
>
> **You:** "The depot section talks too fast, can you slow down just that one page?"
>
> **Claude:** "`demo_vid_refine`'s timing adjustment applies to every step uniformly, not
> one page at a time, so for a single-page change I'll read the saved script and edit
> just the depot step's wait directly." *(reads `data/videos/arxiv-mcp/narration.yaml`,
> increases only the depot step's `wait`, then calls `demo_vid_generate(repo="arxiv-mcp",
> script_yaml=<the edited script>)`)* "Done — the depot page now holds for a few seconds
> longer before moving on, everything else unchanged. Regenerated video is ready at the
> same path."
