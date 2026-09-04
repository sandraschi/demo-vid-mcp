"""Composition stage - FFmpeg-based video composition."""

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


def _find_font() -> str | None:
    """Locate a usable TTF for FFmpeg's drawtext filter.

    drawtext with no explicit fontfile= falls back to fontconfig's default
    font lookup - Windows has no fonts.conf, so any fontconfig-enabled
    FFmpeg build (e.g. the Gyan full_build from winget) crashes with
    "Fontconfig error: Cannot load default config file" (surfaces as a
    raw access-violation exit code, not a clean error return). Passing
    fontfile= explicitly bypasses fontconfig lookup entirely.
    """
    candidates = [
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


_FONT_PATH = _find_font()


def generate_subtitles(steps: list[dict], output_dir: Path) -> tuple[Path | None, Path | None]:
    """Generate WebVTT and SRT subtitle sidecars based on narration step timings."""
    vtt_lines = ["WEBVTT", ""]
    srt_lines = []

    current_s = 0.0
    index = 1

    for step in steps:
        wait_s = float(step.get("wait", 2.0))
        say_text = (step.get("say") or "").strip()
        if say_text:
            start_s = current_s
            end_s = current_s + wait_s

            def fmt_time(sec: float, decimal_sep: str) -> str:
                hours = int(sec // 3600)
                mins = int((sec % 3600) // 60)
                secs = int(sec % 60)
                ms = int(round((sec - int(sec)) * 1000))
                return f"{hours:02d}:{mins:02d}:{secs:02d}{decimal_sep}{ms:03d}"

            vtt_start, vtt_end = fmt_time(start_s, "."), fmt_time(end_s, ".")
            srt_start, srt_end = fmt_time(start_s, ","), fmt_time(end_s, ",")

            vtt_lines.append(f"{index}")
            vtt_lines.append(f"{vtt_start} --> {vtt_end}")
            vtt_lines.append(say_text)
            vtt_lines.append("")

            srt_lines.append(f"{index}")
            srt_lines.append(f"{srt_start} --> {srt_end}")
            srt_lines.append(say_text)
            srt_lines.append("")
            index += 1

        current_s += wait_s

    vtt_path = output_dir / "subtitles.vtt"
    srt_path = output_dir / "subtitles.srt"

    try:
        vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
        return vtt_path, srt_path
    except Exception as e:
        logger.warning("Failed to write subtitle sidecars: %s", e)
        return None, None


async def extract_poster(video_path: Path, output_dir: Path) -> Path | None:
    """Extract a high-quality poster frame from the composed video."""
    if not _FFMPEG_PATH or not video_path.exists():
        return None
    poster_path = output_dir / "poster.jpg"
    try:
        cmd = [
            _FFMPEG_PATH,
            "-y",
            "-ss",
            "00:00:01.500",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(poster_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode == 0 and poster_path.exists():
            return poster_path
    except Exception as e:
        logger.warning("Failed to extract poster frame: %s", e)
    return None


async def compose(
    script: dict, video_path: str | None, audio_path: str | None, output_dir: str
) -> dict:
    """Compose final .mp4 from recording + optional voiceover + title card.

    ## Return Format
    {"success": bool, "mp4_path": str | None, "poster_path": str | None, "vtt_path": str | None, "srt_path": str | None, "message": str}
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "final.mp4"
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
            "error": "FFmpeg not found - cannot compose video",
            "suggestions": [
                "Install FFmpeg: scoop install ffmpeg",
                "Install FFmpeg: winget install ffmpeg",
            ],
        }

    audio_file = Path(audio_path) if audio_path and Path(audio_path).exists() else None

    try:
        safe_title = title.replace("\\", r"\\").replace("'", r"\'").replace(":", r"\:")
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
        ]
        if _FONT_PATH:
            # fontfile= bypasses fontconfig's default-font lookup entirely -
            # required on Windows (see _find_font()). Escape backslashes and
            # the drive-letter colon per FFmpeg filtergraph syntax.
            safe_font = _FONT_PATH.replace("\\", "/").replace(":", r"\:")
            drawtext = (
                f"drawtext=fontfile='{safe_font}':text='{safe_title}':"
                "fontsize=24:fontcolor=white:x=10:y=10"
            )
            cmd += ["-vf", drawtext]
        else:
            logger.warning("No usable font found for drawtext - composing without a title overlay")
        if audio_file:
            cmd += ["-c:a", "aac", "-b:a", "128k"]
        else:
            cmd += ["-an"]
        cmd += [
            "-pix_fmt",
            "yuv420p",
            # Without faststart, FFmpeg writes the moov atom (container
            # metadata, including duration) at the END of the file. Browsers'
            # <video> elements typically can't report duration or seek until
            # that's been read, showing "0:00" for what's actually a full-
            # length video - this is exactly what surfaced as "success, but
            # the video is 0 seconds" in the Depot player.
            "-movflags",
            "+faststart",
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

        # Generate subtitles & poster thumbnail
        vtt_path, srt_path = generate_subtitles(script.get("steps", []), out_dir)
        poster_path = await extract_poster(output, out_dir)

        return {
            "success": True,
            "mp4_path": str(output),
            "poster_path": str(poster_path) if poster_path else None,
            "vtt_path": str(vtt_path) if vtt_path else None,
            "srt_path": str(srt_path) if srt_path else None,
            "message": "Composition complete",
        }
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
