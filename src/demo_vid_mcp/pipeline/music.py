"""Background-music generation via songgeneration-mcp.

songgeneration-mcp is a multi-backend aggregator (Lyria 3 Pro via Vertex AI,
ACE-Step 1.5, Stable Audio 3, SongGeneration-Studio) - one prompt, first
backend that succeeds wins. This module calls its plain REST API, not the
MCP protocol (see config.py's note on speech_mcp_url/songgeneration_mcp_url).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import httpx

logger = logging.getLogger("demo-vid-mcp.music")

DEFAULT_MUSIC_PROMPT = "calm ambient instrumental background music, no vocals"


async def generate_background_music(
    prompt: str, duration: float, output_dir: str, songgeneration_mcp_url: str | None
) -> dict:
    """Generate an ambient background track via songgeneration-mcp.

    songgeneration-mcp's /api/generate returns a local filesystem path (it
    writes the file rather than streaming bytes back) - fleet servers are
    all localhost-only, so that path is expected to be readable from this
    process too. Copied into output_dir since the backend's own tmp file
    may not outlive the request.

    ## Return Format
    {"success": bool, "audio_path": str | None, "backend": str | None, "error": str | None}
    """
    if not songgeneration_mcp_url:
        return {
            "success": False,
            "audio_path": None,
            "error": "songgeneration-mcp not configured",
            "suggestions": ["Set SONGGENERATION_MCP_URL in .env"],
        }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{songgeneration_mcp_url}/api/generate",
                json={"prompt": prompt, "duration": max(1, round(duration))},
            )
    except httpx.RequestError as e:
        return {
            "success": False,
            "audio_path": None,
            "error": f"songgeneration-mcp request failed: {e}",
            "suggestions": ["Check songgeneration-mcp is running on SONGGENERATION_MCP_URL"],
        }

    if r.status_code != 200:
        return {"success": False, "audio_path": None, "error": f"HTTP {r.status_code}"}

    data = r.json()
    if not data.get("success") or not data.get("file"):
        return {
            "success": False,
            "audio_path": None,
            "error": data.get("error", "Music generation failed - no backend produced audio"),
            "suggestions": [
                "Install at least one songgeneration-mcp backend "
                "(see songgeneration-mcp/docs/BACKENDS.md)"
            ],
        }

    src = Path(data["file"])
    if not src.exists():
        return {
            "success": False,
            "audio_path": None,
            "error": f"songgeneration-mcp reported {src} but it doesn't exist here",
        }

    dest = Path(output_dir) / "music.wav"
    shutil.copy2(src, dest)
    logger.info("Background music generated via %s backend: %s", data.get("backend"), dest.name)
    return {"success": True, "audio_path": str(dest), "backend": data.get("backend")}
