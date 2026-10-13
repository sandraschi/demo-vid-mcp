# demo-vid-mcp (MCPB Bundle)

Fleet intro video pipeline â€” record, narrate, compose, refine.

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "demo-vid-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos\demo-vid-mcp", "python", "-m", "demo_vid_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos\demo-vid-mcp/src" }
    }
  }
}
\\\

## Tools

- **health**: health
- **diagnostics**: Full diagnostics for CUA-NSIS smoke testing: tool list, system info, errors.
- **speech_health**: Probe speech-mcp health via backend (avoids browser CORS issues).
- **music_health**: Probe songgeneration-mcp health via backend (avoids browser CORS issues).
- **speech_preview**: Proxy a short TTS sample from speech-mcp for the Speech settings page.      Accepts both `voice` ...
- **music_preview**: Generate a short music sample via songgeneration-mcp for the Music settings page.
- **api_generate**: api_generate
- **api_script_draft**: Draft a narration script for a repo (calls demo_vid_script_draft tool).
- **api_repo_pages**: List a repo's webapp pages with purpose + default detail level (page-selection checklist).
- **list_repos**: Return categorized repos available for demo video generation.
- **list_videos**: list_videos
- **list_depot**: Return all produced videos grouped by repo with their narration scripts.
- **queue_list**: Return persistent generation queue status.
- **queue_enqueue**: Enqueue a video generation job.
- **queue_cancel**: Cancel a pending generation job.
- **logs_get**: Return recent log entries from the ring buffer.
- **delete_repo_videos**: Delete all videos and scripts for a repo from the depot.
- **delete_video**: Delete a single video and its script from the depot.
- **insert_into_repo**: Copy video into target repo's docs/screenshots/ and add README link.
- **list_skills**: Return available skills (preprompts) for the chat page.
- **get_skill**: get_skill
- **llm_chat**: Proxy chat requests to the configured LLM provider.
- **llm_discover**: Probe common LLM providers concurrently and return detected ones with available models.
- **api_shutdown**: Graceful server shutdown.
- **demo_vid_generate**: demo_vid_generate
- **demo_vid_help**: demo_vid_help
- **demo_vid_list**: demo_vid_list
- **demo_vid_refine**: demo_vid_refine
- **demo_vid_script_draft**: demo_vid_script_draft
- **demo_vid_list_pages**: demo_vid_list_pages
- **demo_vid_script_validate**: demo_vid_script_validate
- **demo_vid_shutdown**: demo_vid_shutdown

## Requirements

- Python 3.12+
- uv
