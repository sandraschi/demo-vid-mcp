# Tool Reference

## demo_vid_generate

Full pipeline: validate script → voiceover (speech-mcp) → record (Playwright with click ripple) → compose (FFmpeg).

- `repo` (required, str): Target repository name (e.g. `"chitchat"`).
- `script_yaml` (optional, str): Custom YAML narration script. Defaults to auto-generated from README and webapp routes.
- `base_url` (optional, str): Target webapp URL (auto-detected from fleet port registry if omitted).
- `theme` (optional, str): `"dark"` (fleet default) or `"light"` (bright demo).
- `aspect_ratio` (optional, str): `"16:9"` (desktop landscape) or `"9:16"` (mobile vertical reel).
- `resolution` (optional, str): `"720p"` or `"1080p"`.

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

## demo_vid_script_validate

Validate a narration YAML script for proper structure, timing, action types, aspect ratio, and resolution.

- `script_yaml` (required, str): YAML content to validate.

## demo_vid_help

Return overview, tool reference, and usage examples for `demo-vid-mcp`.

## demo_vid_shutdown

Gracefully terminate the `demo-vid-mcp` server, background queue worker, and active subprocesses.
