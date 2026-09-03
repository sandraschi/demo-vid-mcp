"""Tool: demo_vid_help - documentation."""

from demo_vid_mcp.server import mcp


@mcp.tool(name="demo_vid_help")
async def demo_vid_help() -> dict:
    """List all available demo-vid-mcp tools and their purpose.

    ## Return Format
    {"success": bool, "tools": [{"name": str, "description": str}], "message": str}
    """
    return {
        "success": True,
        "tools": [
            {
                "name": "demo_vid_generate",
                "description": "Full pipeline: validate script, record, voiceover, compose → .mp4",
            },
            {"name": "demo_vid_list", "description": "List produced videos with metadata"},
            {
                "name": "demo_vid_refine",
                "description": "Re-generate a video with timing/narration adjustments",
            },
            {
                "name": "demo_vid_script_draft",
                "description": "Draft a default narration YAML script for a repo",
            },
            {
                "name": "demo_vid_script_validate",
                "description": "Validate a narration script's structure and timing",
            },
            {"name": "demo_vid_help", "description": "List all tools and usage"},
        ],
        "message": "6 tools available. Use demo_vid_generate to produce a video.",
    }
