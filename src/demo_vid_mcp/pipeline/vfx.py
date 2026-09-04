"""Video-transition stitching via vfx-mcp (FFmpeg effects wrapper).

vfx-mcp exposes no REST route for its actual effects - only the `vfx_apply`
MCP tool - so this goes through the real MCP protocol via fastmcp.Client,
same pattern as pipeline/desktop_capture.py's _call() and pipeline/sfx.py.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError

from demo_vid_mcp.pipeline.composer import _FFMPEG_PATH

logger = logging.getLogger("demo-vid-mcp.vfx")

DEFAULT_TRANSITION = "crossfade"
DEFAULT_TRANSITION_DURATION = 1


def _tool_data(result) -> dict:
    return result.data if hasattr(result, "data") else result


async def _vfx_transition(
    input_a: str, input_b: str, output_path: str, transition: str, duration: int, vfx_mcp_url: str
) -> dict:
    try:
        async with Client(vfx_mcp_url) as client:
            result = _tool_data(
                await client.call_tool(
                    "vfx_apply",
                    {
                        "operation": "transition",
                        "input_a": input_a,
                        "input_b": input_b,
                        "output_path": output_path,
                        "transition": transition,
                        "duration": duration,
                    },
                )
            )
        if result.get("success") is False:
            return {"success": False, "error": result.get("error", "transition failed")}
        if not Path(output_path).exists():
            return {
                "success": False,
                "error": f"vfx_apply reported success but {output_path} wasn't created",
            }
        return {"success": True, "output_path": output_path}
    except ToolError as e:
        return {"success": False, "error": f"vfx_apply failed: {e}"}
    except Exception as e:  # connection errors, timeouts, etc.
        return {"success": False, "error": f"Could not reach vfx-mcp at {vfx_mcp_url}: {e}"}


async def _plain_concat(clips: list[str], output_path: str) -> dict:
    """Hard-cut join via FFmpeg's concat demuxer (stream copy, no re-encode).

    The always-available fallback: used when vfx-mcp isn't configured,
    when transitions are explicitly disabled, or when a transition call
    fails partway through a multi-clip stitch. Requires FFmpeg (already a
    hard dependency of the compose stage).
    """
    if not _FFMPEG_PATH:
        return {"success": False, "error": "FFmpeg not found - cannot concatenate clips"}
    list_file = Path(output_path).with_suffix(".concat.txt")
    escaped = [str(Path(c).resolve()).replace("'", r"'\''") for c in clips]
    list_file.write_text("\n".join(f"file '{c}'" for c in escaped), encoding="utf-8")
    cmd = [
        _FFMPEG_PATH,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        output_path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
    finally:
        list_file.unlink(missing_ok=True)
    if proc.returncode != 0:
        return {"success": False, "error": f"concat failed: {stderr.decode()[:300]}"}
    return {"success": True, "output_path": output_path}


async def stitch_clips(
    clips: list[str],
    output_dir: str,
    vfx_mcp_url: str | None,
    transition: str = DEFAULT_TRANSITION,
    duration: int = DEFAULT_TRANSITION_DURATION,
) -> dict:
    """Join multiple recorded page-visit clips into one video.

    Uses vfx-mcp for real crossfade/fade_to_black/wipe/slide transitions
    between clips when configured and reachable; falls back to a plain
    hard-cut concatenation (no re-encode) when vfx-mcp is unavailable, when
    transition is "none", or when a transition call fails partway through -
    a missing or broken vfx-mcp never blocks video generation, it just
    means plain cuts between pages instead of crossfades.

    ## Return Format
    {"success": bool, "video_path": str | None, "used_transitions": bool, "error": str | None}
    """
    if not clips:
        return {
            "success": False,
            "video_path": None,
            "used_transitions": False,
            "error": "No clips to stitch",
        }
    if len(clips) == 1:
        return {"success": True, "video_path": clips[0], "used_transitions": False}

    out_dir = Path(output_dir)
    fallback_path = str(out_dir / "recording.webm")
    merge_files: list[Path] = []

    if vfx_mcp_url and transition != "none":
        merged = clips[0]
        used_transitions = True
        for i in range(1, len(clips)):
            tmp_out = out_dir / f"_vfx_merge_{i}.webm"
            merge_files.append(tmp_out)
            result = await _vfx_transition(
                merged, clips[i], str(tmp_out), transition, duration, vfx_mcp_url
            )
            if not result["success"]:
                logger.warning(
                    "vfx-mcp transition failed at clip %d/%d (%s) - falling back to plain concat",
                    i,
                    len(clips) - 1,
                    result["error"],
                )
                used_transitions = False
                break
            merged = result["output_path"]
        if used_transitions:
            final = Path(merged)
            merge_files.remove(final)  # the last merge IS the output - don't delete it
            for f in merge_files:
                f.unlink(missing_ok=True)
            if str(final) != fallback_path:
                final.replace(fallback_path)
            return {"success": True, "video_path": fallback_path, "used_transitions": True}
        for f in merge_files:
            f.unlink(missing_ok=True)

    concat_result = await _plain_concat(clips, fallback_path)
    if not concat_result["success"]:
        return {
            "success": False,
            "video_path": None,
            "used_transitions": False,
            "error": concat_result["error"],
        }
    return {"success": True, "video_path": fallback_path, "used_transitions": False}
