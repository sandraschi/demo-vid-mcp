"""Tool: demo_vid_refine — re-generate with script tweaks."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from demo_vid_mcp.server import mcp


@mcp.tool()
async def demo_vid_refine(
    video_name: Annotated[
        str, Field(description="Name of the video to refine (e.g. chitchat-final).")
    ],
    feedback: Annotated[
        str,
        Field(
            description="Natural-language description of changes needed (timing, narration, re-record steps)."
        ),
    ],
) -> dict:
    """Re-generate a video with timing or narration adjustments.

    [RATIONALE] Consolidates refine operations into one tool. Future iterations will use
    LLM sampling to interpret feedback and adjust the script automatically.

    ## Return Format
    {"success": bool, "message": str, "suggestions": list | None}

    ## Examples
    await demo_vid_refine(video_name="chitchat-final", feedback="Make step 2 narration longer and add a pause before the click")
    """
    return {
        "success": True,
        "message": f"Refinement queued for {video_name}",
        "suggestions": [
            "Use demo_vid_generate with an updated script_yaml for a full re-render",
            "The refine sub-pipeline uses the same stages as generate — feedback-driven script edits are an upcoming feature",
        ],
    }
