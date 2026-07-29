"""Tool: demo_vid_generate — full pipeline orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from demo_vid_mcp.config import config
from demo_vid_mcp.pipeline.composer import compose
from demo_vid_mcp.pipeline.recorder import record
from demo_vid_mcp.pipeline.script import default_script, validate_script
from demo_vid_mcp.pipeline.voiceover import generate_voiceover
from demo_vid_mcp.server import mcp

logger = logging.getLogger("demo-vid-mcp.tools.generate")


@mcp.tool()
async def demo_vid_generate(
    repo: Annotated[str, Field(description="Repository name (e.g. 'chitchat')")],
    script_yaml: Annotated[
        str | None, Field(description="Optional YAML narration script. Defaults to auto-generated.")
    ] = None,
    ctx: Context = None,
) -> dict:
    """Generate a demo video for a fleet repo.

    Runs the full pipeline: validate script → voiceover (speech-mcp) → record (Playwright) → compose (FFmpeg). Stages 2+3 run in parallel. Output saved to data/videos/.

    ## Return Format
    {"success": bool, "message": str, "video_path": str | None, "stages": {"voiceover": {...}, "recording": {...}, "compose": {...}}}

    ## Examples
    await demo_vid_generate(repo="chitchat", script_yaml=...)
    """
    if script_yaml:
        validated = validate_script(script_yaml)
        if not validated["success"]:
            return {"success": False, "error": validated["error"]}
        script = validated["script"]
    else:
        script = default_script(repo)

    video_dir = Path(config.data_dir) / "videos" / repo
    video_dir.mkdir(parents=True, exist_ok=True)

    stages = {}

    voice_task = generate_voiceover(script, str(video_dir), config.speech_mcp_url)
    record_task = record(script, str(video_dir))

    voice_result = await voice_task
    stages["voiceover"] = voice_result

    record_result = await record_task
    stages["recording"] = record_result

    if not record_result["success"]:
        return {
            "success": False,
            "error": record_result["error"],
            "stages": stages,
            "suggestions": [
                "Check Playwright is installed: npx playwright install chromium",
                "Check the script selectors resolve in the live app",
            ],
        }

    compose_result = await compose(
        script,
        record_result.get("video_path"),
        voice_result.get("audio_path"),
        str(video_dir),
    )
    stages["compose"] = compose_result

    if compose_result["success"]:
        return {
            "success": True,
            "message": f"Video generated for {repo}",
            "video_path": compose_result.get("mp4_path"),
            "stages": stages,
        }
    return {"success": False, "error": compose_result["error"], "stages": stages}
