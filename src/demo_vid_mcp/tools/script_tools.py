"""Tools: demo_vid_script_draft and demo_vid_script_validate."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from demo_vid_mcp.pipeline.script import default_script, validate_script
from demo_vid_mcp.server import mcp


@mcp.tool()
async def demo_vid_script_draft(
    repo: Annotated[str, Field(description="Repository name to draft a script for.")],
) -> dict:
    """Draft a default narration script for a repo.

    Generates a placeholder YAML script that can be edited and passed to demo_vid_generate.

    ## Return Format
    {"success": bool, "script": dict, "message": str}

    ## Examples
    await demo_vid_script_draft(repo="chitchat")
    """
    script = default_script(repo)
    return {
        "success": True,
        "script": script,
        "message": "Default script — edit steps and re-run with demo_vid_generate",
    }


@mcp.tool(name="demo_vid_script_validate")
async def demo_vid_script_validate(
    script_yaml: Annotated[str, Field(description="YAML narration script content.")],
) -> dict:
    """Validate a narration script for structure and timing.

    Checks that the script has required fields ('steps'), each step has an 'action',
    and timing values are reasonable.

    ## Return Format
    {"success": bool, "message": str, "errors": list | None}

    ## Examples
    await demo_vid_script_validate(script_yaml="title: Test\nduration_target: 30\nsteps:\n  - action: goto\n    url: /\n    wait: 2\n")
    """
    result = validate_script(script_yaml)
    if not result["success"]:
        return {"success": False, "error": result["error"]}
    return {"success": True, "message": f"Script valid — {len(result['script']['steps'])} steps"}
