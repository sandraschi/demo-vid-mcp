"""Tool: demo_vid_generate — full pipeline orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from demo_vid_mcp.config import config
from demo_vid_mcp.pipeline.composer import compose
from demo_vid_mcp.pipeline.recorder import record
from demo_vid_mcp.pipeline.script import default_script, validate_script
from demo_vid_mcp.pipeline.voiceover import generate_voiceover
from demo_vid_mcp.server import mcp

logger = logging.getLogger("demo-vid-mcp.tools.generate")

# Fleet webapp port registry: {repo: frontend_port}
_KNOWN_PORTS = {
    "chitchat": 10975,
    "arxiv-mcp": 10771,
    "calibre-mcp": 10721,
    "pywinauto-mcp": 10789,
    "blender-mcp": 10849,
    "email-mcp": 10812,
    "games-app": 10986,
    "godot-mcp": 10992,
    "gimp-mcp": 10772,
    "resonite-mcp": 10978,
    "vroidstudio-mcp": 10880,
    "codecad-mcp": 11083,
    "comfyops-mcp": 11088,
    "learnbot-mcp": 11101,
}


def _resolve_base_url(repo: str, base_url: str | None) -> str:
    if base_url:
        return base_url.rstrip("/")
    port = _KNOWN_PORTS.get(repo, 10975)
    return f"http://127.0.0.1:{port}"


def _resolve_urls(script: dict, base_url: str) -> dict:
    """Prefix relative URLs in script steps with the base URL."""
    for step in script.get("steps", []):
        url = step.get("url", "")
        if url and not url.startswith("http"):
            step["url"] = f"{base_url}{url}"
    return script


@mcp.tool()
async def demo_vid_generate(
    repo: Annotated[str, Field(description="Repository name (e.g. 'chitchat').")],
    script_yaml: Annotated[
        str | None, Field(description="Optional YAML narration script. Defaults to auto-generated.")
    ] = None,
    base_url: Annotated[
        str | None,
        Field(
            description="Target webapp URL (e.g. 'http://127.0.0.1:10975'). Auto-detected from port registry if omitted."
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Generate a demo video for a fleet repo.

    Runs the full pipeline: validate script → voiceover (speech-mcp) → record (Playwright) → compose (FFmpeg).
    Stages run in parallel where possible. Output saved to data/videos/.

    ## Return Format
    {"success": bool, "message": str, "video_path": str | None, "stages": {...}}

    ## Examples
    await demo_vid_generate(repo="chitchat")
    await demo_vid_generate(repo="chitchat", base_url="http://127.0.0.1:10975")
    """
    if script_yaml:
        validated = validate_script(script_yaml)
        if not validated["success"]:
            return {"success": False, "error": validated["error"]}
        script = validated["script"]
    else:
        script = default_script(repo)

    base = _resolve_base_url(repo, base_url)
    script = _resolve_urls(script, base)

    video_dir = Path(config.data_dir) / "videos" / repo
    video_dir.mkdir(parents=True, exist_ok=True)

    # Save the narration script alongside the video for rebuild
    import yaml

    script_path = video_dir / "narration.yaml"
    script_path.write_text(yaml.dump(script, default_flow_style=False), encoding="utf-8")

    # Pre-check: is the target webapp reachable?
    first_url = script.get("steps", [{}])[0].get("url", "")
    if first_url:
        import httpx
        try:
            head_r = await httpx.head(first_url, timeout=5)
            if head_r.status_code >= 400:
                return {"success": False, "error": f"Target webapp returned HTTP {head_r.status_code} at {first_url}",
                        "suggestions": [f"Start the target webapp (frontend) on {first_url}",
                                        "Check the repo's port in WEBAPP_PORTS.md"]}
        except httpx.ConnectError:
            return {"success": False, "error": f"Target webapp not reachable at {first_url}",
                    "suggestions": [f"Start the target webapp (frontend) on {first_url}",
                                    f"Run: cd D:\\Dev\\repos\\{repo}\\webapp && start.ps1"]}
        except httpx.RequestError as e:
            logger.warning("Pre-check failed: %s — continuing anyway", e)

    stages = {}

    voice_task = generate_voiceover(script, str(video_dir), config.speech_mcp_url)
    record_task = record(script, str(video_dir))

    voice_result = await voice_task
    stages["voiceover"] = voice_result

    record_result = await record_task
    stages["recording"] = record_result

    if not record_result["success"]:
        return {
            "success": False,
            "error": record_result["error"],
            "stages": stages,
            "suggestions": [
                "Check Playwright is installed: npx playwright install chromium",
                "Check the script selectors resolve in the live app",
                "Is the target webapp running on the expected port?",
            ],
        }

    compose_result = await compose(
        script,
        record_result.get("video_path"),
        voice_result.get("audio_path"),
        str(video_dir),
    )
    stages["compose"] = compose_result

    if compose_result["success"]:
        return {
            "success": True,
            "message": f"Video generated for {repo}",
            "video_path": compose_result.get("mp4_path"),
            "stages": stages,
        }
    return {"success": False, "error": compose_result["error"], "stages": stages}
