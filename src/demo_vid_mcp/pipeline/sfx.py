"""Sound-effect resolution via sfx-mcp (FreeSound CC0 wrapper).

sfx-mcp exposes no REST route for search/download - only its `sfx_search`
MCP tool - so this goes through the real MCP protocol via fastmcp.Client,
same pattern as pipeline/desktop_capture.py's _call().
"""

from __future__ import annotations

import logging

from fastmcp import Client
from fastmcp.exceptions import ToolError

logger = logging.getLogger("demo-vid-mcp.sfx")


def _tool_data(result) -> dict:
    return result.data if hasattr(result, "data") else result


async def resolve_sfx_clip(query: str, output_dir: str, sfx_mcp_url: str | None) -> dict:
    """Search FreeSound for a short CC0 sound matching `query` and download
    the first result directly into output_dir (sfx-mcp's download operation
    accepts a destination directory, so no separate copy step is needed -
    fleet servers are all localhost, same filesystem).

    ## Return Format
    {"success": bool, "audio_path": str | None, "error": str | None}
    """
    if not sfx_mcp_url:
        return {
            "success": False,
            "audio_path": None,
            "error": "sfx-mcp not configured",
            "suggestions": ["Set SFX_MCP_URL in .env"],
        }

    try:
        async with Client(sfx_mcp_url) as client:
            search_result = _tool_data(
                await client.call_tool(
                    "sfx_search",
                    {"operation": "search", "query": query, "duration_max": 5},
                )
            )
            if not search_result.get("success"):
                return {
                    "success": False,
                    "audio_path": None,
                    "error": search_result.get("error", "sfx search failed"),
                }
            sounds = search_result.get("data", {}).get("sounds", [])
            if not sounds:
                return {
                    "success": False,
                    "audio_path": None,
                    "error": f"No CC0 sounds found for '{query}'",
                }

            sound_id = sounds[0]["id"]
            download_result = _tool_data(
                await client.call_tool(
                    "sfx_search",
                    {"operation": "download", "sound_id": sound_id, "destination": output_dir},
                )
            )
            if not download_result.get("success"):
                return {
                    "success": False,
                    "audio_path": None,
                    "error": download_result.get("error", "sfx download failed"),
                }
            path = download_result.get("data", {}).get("file_path")
            logger.info("Resolved sfx '%s' -> %s (sound %s)", query, path, sound_id)
            return {"success": True, "audio_path": path}
    except ToolError as e:
        return {"success": False, "audio_path": None, "error": f"sfx_search failed: {e}"}
    except Exception as e:  # connection errors, timeouts, etc.
        return {
            "success": False,
            "audio_path": None,
            "error": f"Could not reach sfx-mcp at {sfx_mcp_url}: {e}",
        }


def step_timestamps(steps: list[dict]) -> list[float]:
    """Cumulative start time (seconds) of each step, from wait durations.

    Same cumulative-time logic as composer.generate_subtitles() - kept as a
    small shared helper since sfx timing needs the same computation.
    """
    times = []
    current = 0.0
    for step in steps:
        times.append(current)
        current += float(step.get("wait", 2.0))
    return times


async def resolve_all_sfx(
    steps: list[dict], output_dir: str, sfx_mcp_url: str | None
) -> list[dict]:
    """Resolve every `action: sfx` step's sound effect and its timestamp.

    Steps that fail to resolve (no sfx-mcp, no search match, download error)
    are skipped with a warning rather than failing the whole generation -
    matching the non-fatal degrade pattern used for voiceover/music.

    ## Return Format
    [{"audio_path": str, "start": float}, ...]
    """
    timestamps = step_timestamps(steps)
    resolved = []
    for step, start in zip(steps, timestamps, strict=True):
        if step.get("action") != "sfx":
            continue
        query = step.get("text") or "click"
        result = await resolve_sfx_clip(query, output_dir, sfx_mcp_url)
        if result["success"]:
            resolved.append({"audio_path": result["audio_path"], "start": start})
        else:
            logger.warning("Skipping sfx step ('%s' at %.1fs): %s", query, start, result["error"])
    return resolved
