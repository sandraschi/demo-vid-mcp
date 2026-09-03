"""Tool: demo_vid_refine - re-generate with tweaks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import Field

from demo_vid_mcp.config import config
from demo_vid_mcp.server import mcp


@mcp.tool()
async def demo_vid_refine(
    video_name: Annotated[
        str,
        Field(
            description="Name of the video or repo to refine (e.g. 'chitchat' or 'chitchat-final')."
        ),
    ],
    feedback: Annotated[
        str, Field(description="Natural-language description or instruction for adjustments.")
    ],
) -> dict:
    """Re-generate a video with narration or timing adjustments.

    Locates the existing narration.yaml for the target video, applies adjustments
    or updates based on user feedback, and invokes the generation pipeline.

    ## Return Format
    {"success": bool, "message": str, "video_path": str | None, "error": str | None}

    ## Examples
    await demo_vid_refine(video_name="chitchat", feedback="Increase wait to 4 seconds")
    """
    from demo_vid_mcp.tools.generate import demo_vid_generate

    # Identify the target repo directory
    base_dir = Path(config.data_dir) / "videos"
    repo = video_name.split("-")[0].strip()
    script_path = base_dir / repo / "narration.yaml"

    if not script_path.exists():
        # Search all subdirectories if exact repo name match fails
        matching = list(base_dir.glob(f"*{repo}*/narration.yaml"))
        if matching:
            script_path = matching[0]
            repo = script_path.parent.name
        else:
            return {
                "success": False,
                "error": f"No existing narration script found for '{video_name}'",
                "suggestions": [
                    "Run demo_vid_generate first to establish an initial recording and script",
                    f"Check that data/videos/{repo}/narration.yaml exists",
                ],
            }

    try:
        script = yaml.safe_load(script_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        return {"success": False, "error": f"Failed to parse existing narration script: {e}"}

    steps = script.get("steps", [])
    lower_feedback = feedback.lower()

    # Parse common refinement adjustments
    # 1. Wait/timing adjustment
    wait_match = re.search(r"(?:wait|timing|pause)\s*(?:to|of|=)?\s*(\d+)", lower_feedback)
    if wait_match:
        new_wait = int(wait_match.group(1))
        for step in steps:
            if "wait" in step:
                step["wait"] = new_wait

    # 2. Voice adjustment
    voice_match = re.search(r"voice\s*(?:to|=)?\s*['\"]?(\w+)['\"]?", lower_feedback)
    if voice_match:
        script["voice"] = voice_match.group(1)

    # 3. Add narration note or step if requested
    if "say:" in feedback or "narrate:" in feedback:
        say_text = feedback.split(":", 1)[1].strip().strip("'\"")
        if steps:
            steps[-1]["say"] = say_text
    elif "append step" in lower_feedback or "add step" in lower_feedback:
        steps.append({"action": "wait", "wait": 2, "say": "Refined step added."})

    script["steps"] = steps
    updated_yaml = yaml.dump(script, default_flow_style=False)
    script_path.write_text(updated_yaml, encoding="utf-8")

    result = await demo_vid_generate(repo=repo, script_yaml=updated_yaml)
    if result.get("success"):
        result["message"] = (
            f"Refined and re-generated video for {repo} based on feedback: '{feedback}'"
        )
    return result
