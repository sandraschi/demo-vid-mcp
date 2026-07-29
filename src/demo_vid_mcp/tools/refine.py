"""Tool: demo_vid_refine — re-generate with tweaks."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from demo_vid_mcp.server import mcp


@mcp.tool()
async def demo_vid_refine(
    video_name: Annotated[
        str, Field(description="Name of the video to refine (e.g. chitchat-final).")
    ],
    feedback: Annotated[str, Field(description="Natural-language description of changes needed.")],
) -> dict:
    """Re-generate a video with timing or narration adjustments.

    [RATIONALE] This tool is a stub — refinement requires LLM-driven script mutation
    which is not yet implemented. It returns a helpful message pointing to the
    working alternative (demo_vid_generate with an updated script).

    ## Return Format
    {"success": False, "error": str, "suggestions": list}

    ## Examples
    await demo_vid_refine(video_name="chitchat-final", feedback="Make step 2 narration longer")
    """
    return {
        "success": False,
        "error": "demo_vid_refine is not yet implemented",
        "suggestions": [
            "Edit the narration.yaml in data/videos/{repo}/ and re-run demo_vid_generate with script_yaml=...",
            "Use the Depot page — click the Code icon to view the script, edit it, paste into the Generate page",
        ],
    }
