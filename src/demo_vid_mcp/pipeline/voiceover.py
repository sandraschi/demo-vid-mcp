"""Voiceover stage - calls speech-mcp TTS."""

from __future__ import annotations

import contextlib
import logging
import wave
from pathlib import Path

import httpx
from pydub import AudioSegment

logger = logging.getLogger("demo-vid-mcp.voiceover")

# Silence inserted between concatenated narration segments so adjacent lines
# don't run together, and breathing room held on each page after its line
# finishes before the capture advances (see align_script_waits). The two are
# deliberately EQUAL: the mux lays one continuous audio track over video
# whose page boundaries sit at cumulative wait sums, so wait[i] must equal
# duration[i] + gap for narration N+1 to start exactly when page N+1 appears.
# A smaller audio gap would let narration drift ever-earlier vs. the picture
# (0.4s per page); the leftover 0.8s after the final line becomes the tail
# hold on the closing frame.
INTER_SEGMENT_SILENCE_S = 0.8
END_OF_LINE_PAD_S = 0.8
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
    mid-sentence on a fixed 2-3s tick.

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


async def generate_voiceover(script: dict, output_dir: str, speech_mcp_url: str | None) -> dict:
    """Generate TTS voiceover from script say: segments.

    ## Return Format
    {"success": bool, "audio_path": str | None, "message": str}
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

    audio_paths = []
    segment_durations: list[float] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for i, text in enumerate(say_segments):
            try:
                # Use GET /wav endpoint which returns actual audio bytes
                params = {"text": text, "voice_id": script.get("voice", "heart")}
                r = await client.get(f"{speech_mcp_url}/api/v1/tts/wav", params=params)
                if r.status_code == 200 and len(r.content) > 100:
                    seg_path = Path(output_dir) / f"segment_{i}.wav"
                    seg_path.write_bytes(r.content)
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

    if len(audio_paths) > 1:
        combined = AudioSegment.empty()
        for n, p in enumerate(audio_paths):
            if n > 0:
                combined += AudioSegment.silent(duration=int(INTER_SEGMENT_SILENCE_S * 1000))
            combined += AudioSegment.from_file(p)
        combined_path = Path(output_dir) / "voiceover.wav"
        combined.export(str(combined_path), format="wav")
        for p in audio_paths:
            p.unlink(missing_ok=True)
        total = wav_duration_s(combined_path)
        if total is None:
            total = sum(segment_durations) + INTER_SEGMENT_SILENCE_S * (len(segment_durations) - 1)
        return {
            "success": True,
            "audio_path": str(combined_path),
            "message": f"Voiceover generated: {len(audio_paths)}/{len(say_segments)} segments",
            "segment_durations": segment_durations,
            "total_duration": total,
            "say_count": len(say_segments),
        }
    elif audio_paths:
        import shutil

        final = Path(output_dir) / "voiceover.wav"
        if len(audio_paths) == 1:
            shutil.copy2(audio_paths[0], final)
            audio_paths[0].unlink()
        total = wav_duration_s(final)
        if total is None and segment_durations:
            total = segment_durations[0]
        return {
            "success": True,
            "audio_path": str(final),
            "message": "Voiceover generated (single segment)",
            "segment_durations": segment_durations,
            "total_duration": total,
            "say_count": len(say_segments),
        }

    return {
        "success": False,
        "error": "Speech generation failed",
        "suggestions": ["Install pydub for multi-segment concatenation: pip install pydub"],
    }
