"""Tools: demo_vid_script_draft and demo_vid_script_validate."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from demo_vid_mcp.pipeline.script import default_script, list_pages_with_defaults, validate_script
from demo_vid_mcp.server import mcp


@mcp.tool()
async def demo_vid_script_draft(
    repo: Annotated[str, Field(description="Repository name to draft a script for.")],
    page_config: Annotated[
        dict[str, str] | None,
        Field(
            description="Optional {page name: 'skip'|'show'|'detail'} overrides. "
            "See demo_vid_list_pages for a repo's pages and default levels."
        ),
    ] = None,
) -> dict:
    """Draft a default narration script for a repo.

    Generates a placeholder YAML script that can be edited and passed to demo_vid_generate.

    ## Return Format
    {"success": bool, "script": dict, "message": str}

    ## Examples
    await demo_vid_script_draft(repo="chitchat")
    await demo_vid_script_draft(repo="arxiv-mcp", page_config={"search": "detail", "logs": "skip"})
    """
    script = default_script(repo, page_config)
    return {
        "success": True,
        "script": script,
        "message": "Default script - edit steps and re-run with demo_vid_generate",
    }


@mcp.tool(name="demo_vid_list_pages")
async def demo_vid_list_pages(
    repo: Annotated[str, Field(description="Repository name to list webapp pages for.")],
) -> dict:
    """List a repo's webapp pages with their README-sourced purpose and default detail level.

    For building a page-selection checklist before drafting a script: each page comes
    back with a default level ("skip" | "show" | "detail") from keyword heuristics,
    which the caller can override via demo_vid_script_draft's/demo_vid_generate's
    page_config parameter.

    ## Return Format
    {"success": bool, "pages": [{"name": str, "path": str, "purpose": str | None, "level": str}], "message": str}

    ## Examples
    await demo_vid_list_pages(repo="arxiv-mcp")
    """
    pages = list_pages_with_defaults(repo)
    return {
        "success": True,
        "pages": pages,
        "message": f"{len(pages)} pages found for {repo}",
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
    return {"success": True, "message": f"Script valid - {len(result['script']['steps'])} steps"}
