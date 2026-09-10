# Tool Reference

## demo_vid_generate

Full pipeline: voiceover (speech-mcp, wait-aligned to true speech length) → record page-by-page (Playwright with
click ripple) → join pages with real transitions (vfx-mcp) or a plain cut → mix in background music
(songgeneration-mcp) and timed sound effects (sfx-mcp) → compose (FFmpeg).

- `repo` (required, str): Target repository name (e.g. `"chitchat"`).
- `script_yaml` (optional, str): Custom YAML narration script. Defaults to auto-generated from README and webapp routes.
- `base_url` (optional, str): Target webapp URL (auto-detected from fleet port registry if omitted).
- `theme` (optional, str): `"dark"` (fleet default) or `"light"` (bright demo).
- `aspect_ratio` (optional, str): `"16:9"` (desktop landscape) or `"9:16"` (mobile vertical reel).
- `resolution` (optional, str): `"720p"` or `"1080p"`.
- `page_config` (optional, dict): `{page name: "skip"|"show"|"detail"}` overrides for the auto-drafted script (ignored if `script_yaml` is given). See `demo_vid_list_pages`.
- `voice` (optional, str, default `"heart"`): speech-mcp voice - `"heart"`, `"sky"`, or `"adam"`.
- `music_enabled` (optional, bool, default `False`): generate and mix in ambient background music via songgeneration-mcp, ducked under the voiceover. Requires `SONGGENERATION_MCP_URL` configured.
- `music_prompt` (optional, str): text prompt describing the background music's mood/style.

Sound effects and page transitions aren't separate params - they're driven by the script's own content:
an `action: sfx` step (with a `text` search query) resolves and times a sound effect via sfx-mcp; the script's
`transition_style` field (`"crossfade"` default, or `"fade_to_black"`/`"wipe_left"`/`"wipe_right"`/`"slide"`/`"none"`)
picks the transition vfx-mcp uses between recorded pages. Both degrade gracefully (plain cut, or a skipped sfx step
with a logged warning) when their MCP server isn't configured or unreachable - a missing vfx-mcp/sfx-mcp never
blocks generation.

## demo_vid_list_pages

List a repo's webapp pages with their README-sourced purpose and default detail level, for building a
page-selection checklist before drafting a script.

- `repo` (required, str): Target repository name.

Returns `pages`: `[{"name": str, "path": str, "purpose": str | None, "level": "skip"|"show"|"detail"}, ...]`.
Default level comes from keyword heuristics (`search`/`depot`/`dashboard`/`chat`/`generate` → detail;
`log`/`swagger`/`apidocs`/`settings` → skip; everything else → show) and can be overridden per page via
`demo_vid_generate`'s/`demo_vid_script_draft`'s `page_config` param.

## demo_vid_list

List produced videos with metadata.

- `repo` (optional, str): Filter by repository name.

Returns `videos` and `repos` lists with `name`, `video_path`, `poster_path`, `vtt_path`, `size_kb`, and `has_script`.

## demo_vid_refine

Automatically parse natural-language feedback and mutate YAML narration parameters (timing, voice, script steps).

- `name` (required, str): Video name or repository identifier.
- `feedback` (required, str): Plain text critique or refinement instructions (e.g., "slow down step 2 and switch to nova voice").

## demo_vid_script_draft

Generate a production narration YAML script by analyzing the target repository's README and scanning its frontend route hierarchy.

- `repo` (required, str): Target repository name.
- `page_config` (optional, dict): `{page name: "skip"|"show"|"detail"}` overrides, same as `demo_vid_generate`. See `demo_vid_list_pages`.

## demo_vid_script_validate

Validate a narration YAML script for proper structure, timing, action types, aspect ratio, and resolution.

- `script_yaml` (required, str): YAML content to validate.

## demo_vid_help

Return overview, tool reference, and usage examples for `demo-vid-mcp`.

## demo_vid_shutdown

Gracefully terminate the `demo-vid-mcp` server, background queue worker, and active subprocesses.
