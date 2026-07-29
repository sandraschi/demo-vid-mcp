# Tool Reference

## demo_vid_generate

Full pipeline: validate script → voiceover (speech-mcp) → record (Playwright) → compose (FFmpeg).

- `repo` (required): Repository name
- `script_yaml` (optional): Custom YAML narration script

## demo_vid_list

List produced videos with metadata. Optional `repo` filter.

## demo_vid_refine

Re-generate a video with timing/narration adjustments.

## demo_vid_script_draft

Generate a placeholder narration YAML for a repo.

## demo_vid_script_validate

Validate a narration YAML for structure and timing.
