"""Tool: demo_vid_generate — full pipeline orchestration."""

from __future__ import annotations

import asyncio
import logging
import subprocess
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

_REPOS_ROOT = Path("D:/Dev/repos")
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


async def _ensure_target_running(repo: str, base_url: str) -> bool:
    """Try to start the target repo's webapp if it's not already running."""
    import httpx

    try:
        r = await httpx.get(base_url, timeout=3)
        if r.status_code < 400:
            return True
    except (httpx.ConnectError, httpx.RequestError):
        pass

    # Backend: uv run python -m {package}.app or similar
    repo_dir = _REPOS_ROOT / repo
    if not repo_dir.exists():
        logger.warning("Repo dir not found: %s", repo_dir)
        return False

    # Try starting the backend via the repo's own start.ps1
    start_ps1 = repo_dir / "start.ps1"
    if start_ps1.exists():
        logger.info("Starting %s webapp via start.ps1...", repo)
        _proc = await asyncio.create_subprocess_exec(  # noqa: F841 — fire-and-forget, don't wait
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(start_ps1),
            "-Headless",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Give it time — don't await, just fire-and-forget
        # The pre-check loop below will validate
    else:
        # Minimal backend start for common servers
        logger.info("Trying direct backend start for %s...", repo)
        try:
            await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"cd {repo_dir}; uv run python -m {repo.replace('-', '_')} --serve",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    # Wait for it to come up (up to 30s)
    for _ in range(30):
        await asyncio.sleep(1)
        try:
            r = await httpx.get(base_url, timeout=2)
            if r.status_code < 400:
                logger.info("Target %s is now reachable on %s", repo, base_url)
                return True
        except (httpx.ConnectError, httpx.RequestError):
            continue

    logger.warning("Target %s did not come up on %s after 30s", repo, base_url)
    return False


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

    # Pre-check: is the target webapp reachable? Try to start it if not.
    first_url = script.get("steps", [{}])[0].get("url", "")
    if first_url:
        if not await _ensure_target_running(repo, first_url):
            return {
                "success": False,
                "error": f"Target webapp not reachable at {first_url}",
                "suggestions": [
                    f"Start the target webapp (frontend) on {first_url}",
                    "The auto-start was attempted but failed — the backend may need a manual start",
                ],
            }

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
