"""Voiceover stage - calls speech-mcp TTS, then lays it on the video timeline.

The one rule this module exists to enforce: **the audio timeline and the video
timeline are the same timeline.** Video page boundaries sit at cumulative
`wait` values (a page advances after its wait, holds included). Narration for
a page starts when that page appears and lasts as long as its TTS segment.
So the silence between two segments is not a constant: it is

    gap[i] = start[i+1] - (start[i] + duration[i])

where start[] are cumulative waits. A fixed gap desynchronises every page
whose authored wait is longer than its line: measured on the japanophile tour
(2026-10-20), SRT cue 2 started at 10.1 s while the audio reached it at
~7.1 s, and the error accumulated page by page. That is why the previous
"keep both constants equal" comment was not enough - the constants never
matched authored waits in the first place.

`PAGE_GAP_S` is now only the MINIMUM tail after a line, and it is also the
pad `align_script_waits` adds, so a page always holds at least that long past
end-of-speech.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import subprocess
import wave
from pathlib import Path

import httpx
from pydub import AudioSegment

logger = logging.getLogger("demo-vid-mcp.voiceover")

# Minimum silence after a narrated line before the next page's line starts.
# Also the pad align_script_waits adds to a page that would otherwise cut away
# before its narration finished. 2.0 s is the fleet's preferred breathing room.
PAGE_GAP_S = 2.0
END_OF_LINE_PAD_S = PAGE_GAP_S
MIN_STEP_WAIT_S = 1.0


def wav_duration_s(path: Path) -> float | None:
    """True duration of a WAV file in seconds, stdlib-only (no FFmpeg).

    Returns None when the file can't be probed (corrupt download, non-WAV
    bytes) so callers can fall back to the script's own wait estimate.
    """
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as w:
            frames = w.getnframes()
            rate = w.getframerate()
            if rate <= 0:
                return None
            return frames / float(rate)
    except Exception:
        pass
    try:
        seg = AudioSegment.from_file(path)
        return len(seg) / 1000.0
    except Exception:
        return None


def align_script_waits(
    script: dict,
    segment_durations: list[float],
    pad: float = END_OF_LINE_PAD_S,
    min_wait: float = MIN_STEP_WAIT_S,
) -> dict:
    """Stretch each narrated step's wait so the page holds past end-of-speech.

    Consumes segment_durations in order against steps that carry a non-empty
    `say:` line (the same order generate_voiceover synthesizes them in).
    A step's wait becomes max(original wait, narration + pad) - pages with
    short lines keep their authored dwell, pages with long narration hold
    long enough for the line to finish instead of cutting to the next page
    mid-sentence on a fixed tick.

    Mutates script in place (steps + duration_target) and returns a summary:
    {"adjusted": int, "old_total": float, "new_total": float}.
    No-op when segment_durations is empty (silent video / TTS failed).
    """
    steps = script.get("steps", [])
    seg_idx = 0
    adjusted = 0
    old_total = sum(float(s.get("wait", 0) or 0) for s in steps)
    for step in steps:
        say_text = (step.get("say") or "").strip()
        if not say_text:
            continue
        if seg_idx >= len(segment_durations):
            break
        needed = segment_durations[seg_idx] + pad
        seg_idx += 1
        current = float(step.get("wait", 0) or 0)
        target = max(current, needed, min_wait)
        if target > current + 1e-9:
            step["wait"] = round(target, 1)
            adjusted += 1
    new_total = sum(float(s.get("wait", 0) or 0) for s in steps)
    script["duration_target"] = max(30, round(new_total) + 5)
    return {"adjusted": adjusted, "old_total": old_total, "new_total": new_total}


def narration_timeline(
    steps: list[dict], durations: list[float], min_gap: float = PAGE_GAP_S
) -> dict:
    """Where each narrated line sits on the video timeline.

    start[i] is the cumulative `wait` of every step before that line's step,
    which is exactly when the browser shows that page. gap[i] is the silence
    available after segment i before the next page's line; the last one runs
    to the end of the video. `tight` counts gaps below min_gap - alignment
    normally prevents them, and a non-zero count is worth logging.
    """
    starts: list[float] = []
    cursor = 0.0
    for step in steps:
        if (step.get("say") or "").strip() and len(starts) < len(durations):
            starts.append(round(cursor, 3))
        cursor += float(step.get("wait", 0) or 0)
    total = round(cursor, 3)
    gaps: list[float] = []
    tight = 0
    for i, start in enumerate(starts):
        end = start + durations[i]
        next_start = starts[i + 1] if i + 1 < len(starts) else total
        gap = round(max(0.0, next_start - end), 3)
        gaps.append(gap)
        if i + 1 < len(starts) and gap + 1e-6 < min_gap:
            tight += 1
    return {"starts": starts, "gaps": gaps, "total": total, "tight": tight}


def _atempo(path: Path, speed: float, out_path: Path) -> bool:
    """Resample time without shifting pitch (atempo). False when unavailable."""
    if abs(speed - 1.0) < 1e-6:
        return True
    try:
        from demo_vid_mcp.pipeline.composer import _FFMPEG_PATH
    except Exception:  # pragma: no cover - import cycle safety
        return False
    if not _FFMPEG_PATH:
        return False
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, absolute binary, no shell
            [
                str(_FFMPEG_PATH),
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(path),
                "-filter:a",
                f"atempo={speed:.4f}",
                str(out_path),
            ],
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("atempo failed for %s: %s", path.name, exc)
        return False
    if proc.returncode != 0:
        logger.warning("atempo exited %d: %s", proc.returncode, proc.stderr[-300:])
        return False
    return True


async def generate_voiceover(
    script: dict,
    output_dir: str,
    speech_mcp_url: str | None,
    speed: float = 1.0,
) -> dict:
    """Synthesize one WAV per `say:` segment, optionally slowed to `speed`.

    Does NOT concatenate: page waits are aligned from the true segment
    durations first, so the caller can then lay the segments on the video
    timeline with assemble_voiceover().

    ## Return Format
    {"success": bool, "segment_paths": [...] | None, "segment_durations": [...],
     "audio_path": None, "speed": float, "message": str}
    """
    if not speech_mcp_url:
        return {
            "success": False,
            "error": "speech-mcp not configured",
            "suggestions": ["Set SPEECH_MCP_URL in .env"],
        }

    steps = script.get("steps", [])
    say_segments = [s["say"] for s in steps if s.get("say")]
    if not say_segments:
        return {"success": True, "audio_path": None, "message": "No speech segments - silent video"}

    speed = max(0.5, min(2.0, float(speed or 1.0)))
    audio_paths: list[Path] = []
    segment_durations: list[float] = []
    slowed = 0
    async with httpx.AsyncClient(timeout=60) as client:
        for i, text in enumerate(say_segments):
            try:
                params = {"text": text, "voice_id": script.get("voice", "heart")}
                r = await client.get(f"{speech_mcp_url}/api/v1/tts/wav", params=params)
                if r.status_code == 200 and len(r.content) > 100:
                    seg_path = Path(output_dir) / f"segment_{i}.wav"
                    seg_path.write_bytes(r.content)
                    if abs(speed - 1.0) > 1e-6:
                        slower = seg_path.with_name(f"segment_{i}_{speed:g}x.wav")
                        if await asyncio.to_thread(_atempo, seg_path, speed, slower):
                            seg_path.unlink(missing_ok=True)
                            seg_path = slower
                            slowed += 1
                    audio_paths.append(seg_path)
                    dur = wav_duration_s(seg_path)
                    if dur is not None:
                        segment_durations.append(dur)
                    else:
                        logger.warning("Could not probe TTS duration for seg %d", i)
                else:
                    logger.warning(
                        "TTS fail seg %d: HTTP %d, %d bytes", i, r.status_code, len(r.content)
                    )
            except httpx.RequestError as e:
                logger.warning("TTS request failed for segment %d: %s", i, e)

    if not audio_paths:
        return {
            "success": False,
            "error": "No voiceover segments generated",
            "suggestions": [
                "Check that speech-mcp is running on SPEECH_MCP_URL",
                "Check speech-mcp logs for TTS errors",
            ],
        }

    return {
        "success": True,
        "audio_path": None,
        "segment_paths": [str(p) for p in audio_paths],
        "segment_durations": segment_durations,
        "say_count": len(say_segments),
        "speed": speed,
        "slowed_segments": slowed,
        "message": f"{len(audio_paths)}/{len(say_segments)} segments at {speed:g}x",
    }


def assemble_voiceover(
    voice: dict,
    script: dict,
    output_dir: str,
    min_gap: float = PAGE_GAP_S,
) -> dict:
    """Concatenate segments on the page timeline and write voiceover.wav.

    Adds audio_path, total_duration and timeline to `voice`. When the segment
    count does not match the narrated step count the timeline is unknowable,
    so it falls back to a flat min_gap between segments and says so.
    """
    paths = [Path(p) for p in (voice.get("segment_paths") or [])]
    durations = list(voice.get("segment_durations") or [])
    if not paths:
        return voice

    started = len(durations) == len(paths)
    if started:
        timeline = narration_timeline(script.get("steps", []), durations, min_gap=min_gap)
    else:
        starts: list[float] = []
        cursor = 0.0
        for dur in durations:
            starts.append(round(cursor, 3))
            cursor += dur + min_gap
        timeline = {
            "starts": starts,
            "gaps": [min_gap] * len(paths),
            "total": round(max(0.0, cursor - min_gap), 3),
            "tight": 0,
            "degraded": True,
        }

    # Absolute placement, not concatenation: each segment starts where its
    # page appears. If a line overruns its page (only possible without
    # alignment), the bed grows to hold it and `overrun` says by how much,
    # instead of silently shifting every later line.
    last_end = (timeline["starts"][-1] if timeline["starts"] else 0.0) + durations[-1]
    bed_s = max(timeline["total"], round(last_end, 3))
    bed = AudioSegment.silent(duration=int(bed_s * 1000))
    for i, path in enumerate(paths):
        position = int(timeline["starts"][i] * 1000) if i < len(timeline["starts"]) else 0
        bed = bed.overlay(AudioSegment.from_file(path), position=position)

    combined_path = Path(output_dir) / "voiceover.wav"
    bed.export(str(combined_path), format="wav")
    for path in paths:
        path.unlink(missing_ok=True)

    total = wav_duration_s(combined_path)
    timeline["overrun"] = round(max(0.0, last_end - timeline["total"]), 3)
    voice.update(
        {
            "audio_path": str(combined_path),
            "total_duration": total,
            "timeline": timeline,
            "segment_paths": [],
            "message": (
                f"Voiceover {len(paths)} segments, {total:.1f}s "
                f"({timeline.get('total', 0):.1f}s of picture)"
            ),
        }
    )
    logger.info(
        "Voiceover timeline: %s",
        json.dumps(
            {
                "starts": timeline["starts"][:3],
                "gaps": timeline["gaps"][:3],
                "tight": timeline.get("tight"),
                "overrun": timeline.get("overrun"),
            }
        ),
    )
    return voice
