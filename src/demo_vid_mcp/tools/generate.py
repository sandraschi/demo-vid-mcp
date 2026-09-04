"""Tool: demo_vid_generate - full pipeline orchestration."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import httpx
from fastmcp import Context
from pydantic import Field

from demo_vid_mcp.config import config
from demo_vid_mcp.pipeline.composer import compose
from demo_vid_mcp.pipeline.desktop_capture import record_desktop
from demo_vid_mcp.pipeline.music import DEFAULT_MUSIC_PROMPT, generate_background_music
from demo_vid_mcp.pipeline.recorder import record
from demo_vid_mcp.pipeline.script import default_script, validate_script
from demo_vid_mcp.pipeline.voiceover import generate_voiceover
from demo_vid_mcp.server import mcp

logger = logging.getLogger("demo-vid-mcp.tools.generate")


def _load_frontend_ports() -> dict[str, int]:
    """Read frontend ports from WEBAPP_PORTS.md."""
    ports_path = config.repos_root / "mcp-central-docs" / "operations" / "WEBAPP_PORTS.md"
    if not ports_path.exists():
        logger.warning("WEBAPP_PORTS.md not found at %s", ports_path)
        return {"chitchat": 10975}
    result = {}
    import re

    for line in ports_path.read_text(encoding="utf-8").splitlines():
        m = re.match(
            r"\|\s*(\d+)\s*\|\s*([\w-]+(?:-mcp|_mcp)?)\s*\|\s*(.*\b(Frontend|frontend|dashboard frontend)\b.*)",
            line,
        )
        if m:
            repo, port = m.group(2), int(m.group(1))
            if repo not in result:
                result[repo] = port
    return result or {"chitchat": 10975}


_FRONTEND_PORTS = _load_frontend_ports()


async def _ensure_target_running(repo: str, base_url: str) -> bool:
    """Start the target repo's backend AND frontend, wait for both to respond."""
    parsed = urlparse(base_url)
    frontend_port = parsed.port or 10975

    repo_dir = config.repos_root / repo
    if not repo_dir.exists():
        logger.warning("Repo dir not found: %s", repo_dir)
        return False

    # Kill zombies on the target frontend port (stale processes from previous runs)
    import subprocess as _sp

    try:
        _sp.run(
            [
                "powershell.exe",
                "-NoProfile",
                f"Get-NetTCPConnection -LocalPort {frontend_port} -ErrorAction SilentlyContinue | "
                f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}",
            ],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass

    # Check if already running (zombie kill may have freed the port)
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(base_url)
        if r.status_code < 400:
            return True
    except (httpx.ConnectError, httpx.RequestError):
        pass

    # 1. Start backend
    start_ps1 = repo_dir / "start.ps1"
    if start_ps1.exists():
        logger.info("Starting %s backend via start.ps1...", repo)
        _proc = await asyncio.create_subprocess_exec(  # noqa: F841
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(start_ps1),
            "-Headless",
            "-BackendOnly",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        logger.info("Starting %s backend directly...", repo)
        _proc = await asyncio.create_subprocess_exec(  # noqa: F841
            "powershell.exe",
            "-NoProfile",
            "-Command",
            f"cd {repo_dir}; uv run python -m {repo.replace('-', '_')} --serve",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # 2. Start frontend (Vite dev server)
    webapp_dirs = ["webapp", "web_sota", "frontend"]
    for wd in webapp_dirs:
        webapp_dir = repo_dir / wd
        if webapp_dir.exists() and (webapp_dir / "package.json").exists():
            logger.info("Starting %s frontend (Vite) from %s...", repo, wd)
            _proc = await asyncio.create_subprocess_exec(  # noqa: F841
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"cd {webapp_dir}; bun run dev --port {frontend_port}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            break

    # 3. Wait for both to come up (up to 30s)
    for i in range(30):
        await asyncio.sleep(1)
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                r = await client.get(base_url)
            if r.status_code < 400:
                logger.info(
                    "Target %s is now reachable on %s (attempt %d/%d)", repo, base_url, i + 1, 30
                )
                return True
        except httpx.RequestError:
            continue

    logger.warning("Target %s did not come up on %s after 30s", repo, base_url)
    return False


def _resolve_base_url(repo: str, base_url: str | None) -> str:
    if base_url:
        return base_url.rstrip("/")
    port = _FRONTEND_PORTS.get(repo, 10975)
    return f"http://127.0.0.1:{port}"


def _resolve_urls(script: dict, base_url: str) -> dict:
    """Prefix relative URLs in script steps with the base URL."""
    for step in script.get("steps", []):
        url = step.get("url", "")
        if url and not url.startswith("http"):
            step["url"] = f"{base_url}{url}"
    return script


def _is_desktop_capture(script: dict) -> bool:
    """True if this script drives a native app window (Blender/Resonite/...)
    instead of recording a fleet webapp. Set explicitly via the top-level
    `desktop_capture` flag, or inferred from an `mcp_call` step being present."""
    if script.get("desktop_capture"):
        return True
    return any(step.get("action") == "mcp_call" for step in script.get("steps", []))


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
    theme: Annotated[
        str, Field(description="Video theme: 'dark' (fleet default) or 'light' (bright demo).")
    ] = "dark",
    aspect_ratio: Annotated[
        str, Field(description="Aspect ratio: '16:9' (desktop) or '9:16' (mobile vertical).")
    ] = "16:9",
    resolution: Annotated[str, Field(description="Resolution preset: '720p' or '1080p'.")] = "720p",
    page_config: Annotated[
        dict[str, str] | None,
        Field(
            description="Optional {page name: 'skip'|'show'|'detail'} overrides for the "
            "auto-drafted script (ignored if script_yaml is given). See demo_vid_list_pages."
        ),
    ] = None,
    voice: Annotated[
        str, Field(description="speech-mcp voice: 'heart', 'sky', or 'adam'.")
    ] = "heart",
    music_enabled: Annotated[
        bool,
        Field(
            description="Generate and mix in ambient background music via songgeneration-mcp, "
            "ducked under the voiceover. Requires SONGGENERATION_MCP_URL configured."
        ),
    ] = False,
    music_prompt: Annotated[
        str,
        Field(description="Text prompt describing the background music's mood/style."),
    ] = DEFAULT_MUSIC_PROMPT,
    ctx: Context | None = None,
) -> dict:
    """Generate a demo video for a fleet repo.

    Runs the full pipeline: validate script → voiceover (speech-mcp) → record → compose (FFmpeg).
    Stages run in parallel where possible. Output saved to data/videos/.
    theme="light" records the target webapp with its light-mode toggle forced
    on (bright demo); default "dark" matches fleet identity.
    aspect_ratio="9:16" generates mobile vertical video; default "16:9" is landscape desktop.

    Two recording modes, auto-detected from the script:
    - Webapp mode (default): Playwright records the repo's own webapp on its
      registered port. base_url/theme apply here.
    - Desktop-capture mode: triggered by a top-level `desktop_capture: true`
      flag or any step with `action: mcp_call` in script_yaml. OBS records a
      window-capture scene (`obs_scene`, auto-created if missing) of a native
      app (`capture_window`, e.g. "Blender" or "Resonite") while `mcp_call`
      steps actually drive that app's own MCP server live via the real MCP
      protocol - real tool calls, not a staged screen recording. Requires
      windows-computer-use-mcp + obs-mcp running, and each *_MCP_URL env var
      set to the target server's full /mcp endpoint (see DEMO_VID_MCP_PLAN.md).

    ## Return Format
    {"success": bool, "message": str, "video_path": str | None, "poster_path": str | None, "vtt_path": str | None, "stages": {...}}

    ## Examples
    await demo_vid_generate(repo="chitchat")
    await demo_vid_generate(repo="chitchat", theme="light", aspect_ratio="9:16")
    await demo_vid_generate(repo="chitchat", base_url="http://127.0.0.1:10975")
    await demo_vid_generate(repo="arxiv-mcp", page_config={"search": "detail", "logs": "skip"})
    await demo_vid_generate(repo="chitchat", music_enabled=True, music_prompt="upbeat lofi hip hop")
    await demo_vid_generate(repo="blender-mcp", script_yaml=open("data/scripts/blender-chair-demo.yaml").read())
    """
    if not repo or not repo.strip():
        return {
            "success": False,
            "error": "repo parameter is required",
            "suggestions": ["Provide a valid fleet repository name, e.g. 'chitchat'"],
        }

    if script_yaml:
        validated = validate_script(script_yaml)
        if not validated["success"]:
            return {"success": False, "error": validated["error"]}
        script = validated["script"]
    else:
        script = default_script(repo, page_config)

    if aspect_ratio:
        script["aspect_ratio"] = aspect_ratio
    if resolution:
        script["resolution"] = resolution
    if voice:
        script["voice"] = voice
    script["bg_music"] = music_enabled
    if music_prompt:
        script["music_prompt"] = music_prompt

    desktop_mode = _is_desktop_capture(script)

    if not desktop_mode:
        base = _resolve_base_url(repo, base_url)
        script = _resolve_urls(script, base)

    video_dir = Path(config.data_dir) / "videos" / repo
    video_dir.mkdir(parents=True, exist_ok=True)

    # Save the narration script alongside the video for rebuild
    import yaml

    script_path = video_dir / "narration.yaml"
    script_path.write_text(yaml.dump(script, default_flow_style=False), encoding="utf-8")

    if not desktop_mode:
        # Pre-check: is the target webapp reachable? Try to start it if not.
        first_url = script.get("steps", [{}])[0].get("url", "")
        if first_url:
            if not await _ensure_target_running(repo, first_url):
                return {
                    "success": False,
                    "error": f"Target webapp not reachable at {first_url}",
                    "suggestions": [
                        f"Start the target webapp (frontend) on {first_url}",
                        "The auto-start was attempted but failed - the backend may need a manual start",
                    ],
                }

    stages = {}

    # Voiceover, music and recording all run in parallel - music generation
    # in particular can take up to two minutes (it's a real generative model
    # call, not TTS), so it needs to overlap with recording rather than run
    # after it. In desktop_mode, the "recording" is OBS capturing a native
    # app window while mcp_call steps drive it live (see
    # pipeline/desktop_capture.py) instead of Playwright recording a webapp.
    voice_task = asyncio.create_task(
        generate_voiceover(script, str(video_dir), config.speech_mcp_url)
    )
    music_task = (
        asyncio.create_task(
            generate_background_music(
                script.get("music_prompt") or DEFAULT_MUSIC_PROMPT,
                float(script.get("duration_target", 30)),
                str(video_dir),
                config.songgeneration_mcp_url,
            )
        )
        if script.get("bg_music")
        else None
    )
    if desktop_mode:
        record_task = asyncio.create_task(
            record_desktop(
                script,
                str(video_dir),
                script.get("capture_window", ""),
                script.get("obs_scene", ""),
            )
        )
    else:
        record_task = asyncio.create_task(record(script, str(video_dir), theme=theme))

    voice_result = await voice_task
    stages["voiceover"] = voice_result

    record_result = await record_task
    stages["recording"] = record_result

    music_result = await music_task if music_task else None
    if music_result is not None:
        stages["music"] = music_result

    if not record_result["success"]:
        return {
            "success": False,
            "error": record_result["error"],
            "stages": stages,
            "suggestions": record_result.get("suggestions")
            or [
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
        music_path=(music_result or {}).get("audio_path"),
    )
    stages["compose"] = compose_result

    if compose_result["success"]:
        return {
            "success": True,
            "message": f"Video generated for {repo}",
            "video_path": compose_result.get("mp4_path"),
            "poster_path": compose_result.get("poster_path"),
            "vtt_path": compose_result.get("vtt_path"),
            "srt_path": compose_result.get("srt_path"),
            "stages": stages,
        }
    return {"success": False, "error": compose_result["error"], "stages": stages}
