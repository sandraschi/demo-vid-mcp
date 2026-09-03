"""Desktop-capture recording stage: OBS records a native app window while
`mcp_call` steps drive the target software live (Blender, Resonite, ...).

Same return contract as pipeline.recorder.record() so composer.py needs no changes:
{"success": bool, "video_path": str | None, "message": str}

All cross-server calls (windows-computer-use-mcp, obs-mcp, and whatever the
`mcp_call` step's "server" targets) go through the real MCP protocol via
fastmcp.Client, not a guessed REST shortcut - fleet servers do NOT share a
uniform REST tool-invocation path (freecad-mcp uses /api/v1/control/tool,
resonite-mcp uses /api/v1/tool, blender-mcp and windows-computer-use-mcp
expose no REST tool-call route at all, obs-mcp's REST layer is bespoke
per-action paths). MCP's own call_tool is the one interface every server
actually guarantees.
"""

from __future__ import annotations

import asyncio
import logging

from fastmcp import Client
from fastmcp.exceptions import ToolError

from demo_vid_mcp.config import config

logger = logging.getLogger("demo-vid-mcp.desktop_capture")

# server name (as used in a step's "server" field) -> config attribute holding
# its MCP endpoint URL (e.g. "http://127.0.0.1:10793/mcp" - the FULL /mcp URL,
# not just the host:port). Mirrors config.py's existing *_mcp_url fields.
_MCP_SERVERS: dict[str, str] = {
    "blender_mcp": "blender_mcp_url",
    "resonite_mcp": "resonite_mcp_url",
    "gimp_mcp": "gimp_mcp_url",
    "resolve_mcp": "resolve_mcp_url",
}


async def _call(server_url: str, tool: str, arguments: dict | None = None) -> dict:
    """Call a tool on any fleet MCP server via the real MCP protocol."""
    try:
        async with Client(server_url) as client:
            result = await client.call_tool(tool, arguments or {})
        return {"success": True, "data": result.data if hasattr(result, "data") else result}
    except ToolError as e:
        return {"success": False, "error": f"{tool} failed: {e}"}
    except Exception as e:  # connection errors, timeouts, etc.
        return {"success": False, "error": f"Could not reach {server_url} for {tool}: {e}"}


async def _focus_window(target: str) -> dict:
    """Bring the target app window to front via windows-computer-use-mcp."""
    if not config.windows_computer_use_mcp_url:
        return {"success": False, "error": "WINDOWS_COMPUTER_USE_MCP_URL not configured"}
    url = config.windows_computer_use_mcp_url
    found = await _call(url, "automation_windows", {"operation": "find", "title": target})
    if not found["success"]:
        return found
    return await _call(url, "automation_windows", {"operation": "focus", "title": target})


async def _obs(tool: str, arguments: dict | None = None) -> dict:
    if not config.obs_mcp_url:
        return {"success": False, "error": "OBS_MCP_URL not configured"}
    return await _call(config.obs_mcp_url, tool, arguments)


async def _mcp_call(server: str, tool: str, params: dict) -> dict:
    """Invoke a real tool on a real fleet MCP server (the actual demo action)."""
    attr = _MCP_SERVERS.get(server)
    server_url = getattr(config, attr, None) if attr else None
    if not server_url:
        return {
            "success": False,
            "error": f"No URL configured for server '{server}' (set its *_MCP_URL env var, e.g. BLENDER_MCP_URL=http://127.0.0.1:10793/mcp)",
        }
    return await _call(server_url, tool, params)


async def record_desktop(
    script: dict, output_dir: str, capture_window: str, obs_scene: str
) -> dict:
    """Record a native app window via OBS while mcp_call steps drive it live.

    Auto-creates the OBS capture scene via obs-mcp's obs_create_capture_scene
    tool (window_capture source matched to `capture_window` by substring) if
    it doesn't already exist - no manual OBS setup required, via obs-mcp's
    obs_create_capture_scene tool.
    """
    steps = script.get("steps", [])
    if not steps:
        return {"success": True, "video_path": None, "message": "No steps - nothing to record"}

    focus = await _focus_window(capture_window)
    if not focus["success"]:
        return {
            "success": False,
            "error": focus["error"],
            "suggestions": [
                "Is windows-computer-use-mcp running and WINDOWS_COMPUTER_USE_MCP_URL set to its /mcp URL?",
                f"Is a window titled/matching '{capture_window}' actually open?",
            ],
        }

    create_scene = await _obs(
        "obs_create_capture_scene",
        {"scene_name": obs_scene, "window_match": capture_window},
    )
    if not create_scene["success"]:
        return {
            "success": False,
            "error": create_scene["error"],
            "suggestions": [
                "Is obs-mcp running and OBS_MCP_URL set to its /mcp URL?",
                f"Is a window matching '{capture_window}' open for OBS to capture?",
            ],
        }

    scene = await _obs("obs_scene_switch", {"scene_name": obs_scene})
    if not scene["success"]:
        return {"success": False, "error": scene["error"]}

    start = await _obs("obs_recording_start")
    if not start["success"]:
        return {"success": False, "error": start["error"]}

    logger.info(
        "Recording started (scene=%s, window=%s), running %d steps...",
        obs_scene,
        capture_window,
        len(steps),
    )

    for i, step in enumerate(steps):
        action = step.get("action")
        wait_s = step.get("wait", 2)
        if action == "mcp_call":
            server, tool, params = step.get("server"), step.get("tool"), step.get("params", {})
            result = await _mcp_call(server, tool, params)
            if not result["success"]:
                logger.warning(
                    "Step %d mcp_call failed (continuing capture): %s", i, result["error"]
                )
        await asyncio.sleep(wait_s)

    stop = await _obs("obs_recording_stop")
    if not stop["success"]:
        return {"success": False, "error": stop["error"]}

    status = await _obs("obs_recording_status")
    video_path = None
    if status["success"]:
        data = status.get("data") or {}
        result_block = data.get("result", data) if isinstance(data, dict) else {}
        video_path = (
            result_block.get("output_path")
            or result_block.get("outputPath")
            or result_block.get("file_path")
            or result_block.get("path")
        )

    if not video_path:
        return {
            "success": False,
            "error": "Recording stopped but no output file path returned by obs_recording_status",
            "suggestions": [
                "Check obs-mcp's recording status response shape (output_path/outputPath/file_path/path)",
                "Check OBS's configured recording output directory",
            ],
        }

    return {"success": True, "video_path": video_path, "message": "Desktop capture complete"}
