"""Composition stage — Remotion or FFmpeg fallback."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("demo-vid-mcp.composer")


async def compose(
    script: dict, video_path: str | None, audio_path: str | None, output_dir: str
) -> dict:
    """Compose final .mp4 from recording + voiceover + title card.

    Falls back from Remotion to FFmpeg if Remotion not available.

    ## Return Format
    {"success": bool, "mp4_path": str | None, "message": str}
    """
    output = Path(output_dir) / "final.mp4"
    title = script.get("title", "Demo Video")

    if video_path and Path(video_path).exists():
        vid_file = Path(video_path)
    else:
        return {
            "success": False,
            "error": "No recording to compose",
            "suggestions": ["Run recording stage first"],
        }

    audio_file = Path(audio_path) if audio_path and Path(audio_path).exists() else None

    try:
        cmd = ["ffmpeg", "-y", "-i", str(vid_file)]
        if audio_file:
            cmd += ["-i", str(audio_file)]
        cmd += [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-vf",
            f"drawtext=text='{title}':fontsize=24:fontcolor=white:x=10:y=10",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode != 0:
            logger.error("FFmpeg failed: %s", stderr.decode()[:500])
            return {
                "success": False,
                "error": f"Composition failed (FFmpeg exit {proc.returncode})",
                "suggestions": [
                    "Check FFmpeg is installed: winget install FFmpeg",
                    "Check source files exist",
                ],
            }
        return {"success": True, "mp4_path": str(output), "message": "Composition complete"}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "FFmpeg not found — cannot compose video",
            "suggestions": [
                "Install FFmpeg: winget install FFmpeg",
                "Or compile with Remotion (see docs/DEVELOPMENT.md)",
            ],
        }
    except TimeoutError:
        return {"success": False, "error": "Composition timed out after 5 minutes"}
    except Exception as e:
        return {"success": False, "error": str(e)}
