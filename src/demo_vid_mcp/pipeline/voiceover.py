"""Voiceover stage — calls speech-mcp TTS."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

logger = logging.getLogger("demo-vid-mcp.voiceover")


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
        return {"success": True, "audio_path": None, "message": "No speech segments — silent video"}

    try:
        from pydub import AudioSegment

        has_pydub = True
    except ImportError:
        has_pydub = False

    audio_paths = []
    async with httpx.AsyncClient(timeout=30) as client:
        for i, text in enumerate(say_segments):
            try:
                r = await client.post(f"{speech_mcp_url}/api/v1/tts", json={"text": text})
                if r.status_code == 200:
                    seg_path = Path(output_dir) / f"segment_{i}.wav"
                    seg_path.write_bytes(r.content)
                    audio_paths.append(seg_path)
                else:
                    logger.warning("TTS failed for segment %d: HTTP %d", i, r.status_code)
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

    if has_pydub and len(audio_paths) > 1:
        combined = AudioSegment.empty()
        for p in audio_paths:
            combined += AudioSegment.from_file(p)
        combined_path = Path(output_dir) / "voiceover.wav"
        combined.export(str(combined_path), format="wav")
        for p in audio_paths:
            p.unlink(missing_ok=True)
        return {
            "success": True,
            "audio_path": str(combined_path),
            "message": f"Voiceover generated: {len(say_segments)} segments",
        }
    elif audio_paths:
        import shutil

        final = Path(output_dir) / "voiceover.wav"
        if len(audio_paths) == 1:
            shutil.copy2(audio_paths[0], final)
            audio_paths[0].unlink()
        return {
            "success": True,
            "audio_path": str(final),
            "message": "Voiceover generated (single segment)",
        }

    return {
        "success": False,
        "error": "Speech generation failed",
        "suggestions": ["Install pydub for multi-segment concatenation: pip install pydub"],
    }
