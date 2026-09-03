## Session Context (demo-vid-mcp)

Fleet intro-video pipeline: turns a YAML script into an MP4 by driving Playwright
(records the target webapp) or a desktop capture (native apps), speech-mcp
(TTS narration), and FFmpeg (compose). 7 MCP tools.

**Before starting work:**
1. List existing videos/repos: `demo_vid_list()`
2. Read the tool summary: `demo_vid_help()`

**At end of work:**
- Validate any script edits before generating: `demo_vid_script_validate(script_yaml=...)`
- Prefer `demo_vid_refine(...)` over a full `demo_vid_generate(...)` re-run when only
  feedback-driven tweaks are needed
