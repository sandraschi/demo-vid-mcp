"""Composition stage — FFmpeg-based video composition."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("demo-vid-mcp.composer")

_FFMPEG_PATH: str | None = None


def _find_ffmpeg() -> str | None:
    candidates = [
        shutil.which("ffmpeg"),
        "C:\\Users\\sandr\\scoop\\shims\\ffmpeg.exe",
        "C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe",
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


_FFMPEG_PATH = _find_ffmpeg()


async def compose(
    script: dict, video_path: str | None, audio_path: str | None, output_dir: str
) -> dict:
    """Compose final .mp4 from recording + optional voiceover + title card.

    ## Return Format
    {"success": bool, "mp4_path": str | None, "message": str}
    """
    output = Path(output_dir) / "final.mp4"
    title = script.get("title", "Demo Video")

    if not video_path or not Path(video_path).exists():
        return {
            "success": False,
            "error": "No recording to compose",
            "suggestions": ["Run recording stage first"],
        }

    if not _FFMPEG_PATH:
        return {
            "success": False,
            "error": "FFmpeg not found — cannot compose video",
            "suggestions": [
                "Install FFmpeg: scoop install ffmpeg",
                "Install FFmpeg: winget install ffmpeg",
            ],
        }

    audio_file = Path(audio_path) if audio_path and Path(audio_path).exists() else None

    try:
        cmd = [_FFMPEG_PATH, "-y", "-i", str(video_path)]
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
                "suggestions": ["Check source video file exists and is valid"],
            }
        return {"success": True, "mp4_path": str(output), "message": "Composition complete"}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "FFmpeg binary not found at resolved path",
            "suggestions": ["Reinstall FFmpeg: scoop install ffmpeg"],
        }
    except TimeoutError:
        return {"success": False, "error": "Composition timed out after 5 minutes"}
    except Exception as e:
        return {"success": False, "error": str(e)}
