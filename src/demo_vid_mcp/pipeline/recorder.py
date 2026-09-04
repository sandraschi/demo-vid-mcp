"""Playwright recording stage."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("demo-vid-mcp.recorder")


def _find_capture_script() -> Path | None:
    """Locate playwright-capture.js in dev (repo checkout) or packaged mode.

    `Path(__file__).resolve().parents[3]` only makes sense for a real
    source-tree layout; inside a PyInstaller-frozen backend.exe, __file__
    resolves somewhere under a temp extraction dir with no "scripts/"
    sibling, so that alone always fails once installed. When Tauri spawns
    the backend it sets cwd to the install directory (see backend.rs
    spawn_backend), so a bundled resources/playwright-capture.js is
    reachable via Path.cwd() there - same pattern as _find_ffmpeg().
    """
    candidates = [
        Path(__file__).resolve().parents[3] / "scripts" / "playwright-capture.js",
        Path.cwd() / "resources" / "playwright-capture.js",
        Path(sys.executable).resolve().parent / "resources" / "playwright-capture.js",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _node_path_env() -> dict[str, str]:
    """Extra NODE_PATH entries so `require("playwright")` resolves even when
    playwright-capture.js runs from resources/ (no local node_modules
    ancestor to walk up to - the packaged app's install dir isn't nested
    under the dev repo). Covers a global `npm install -g playwright` if one
    exists; does not bundle Playwright/Chromium into the installer itself
    (~300MB+) - that remains a separate, deliberate packaging decision.
    """
    env = os.environ.copy()
    extra = []
    try:
        result = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True,
        )
        if result.returncode == 0:
            global_root = result.stdout.strip()
            if global_root and Path(global_root).exists():
                extra.append(global_root)
    except Exception:
        pass
    if extra:
        existing = env.get("NODE_PATH", "")
        env["NODE_PATH"] = (
            os.pathsep.join([*extra, existing]) if existing else os.pathsep.join(extra)
        )
    return env


async def record(script: dict, output_dir: str, theme: str = "dark") -> dict:
    """Run Playwright to capture a .webm from a narration script.

    Uses Playwright's native video recording. Checks process exit code
    BEFORE looking for output files - prevents stale files from a
    previous run being reported as success. Kills subprocess on timeout
    to prevent hanging the pipeline.

    theme: "dark" (fleet default) or "light" - passed to the capture
    script, which forces the theme class on the target page so demo
    videos match the requested mode.

    ## Return Format
    {"success": bool, "video_path": str | None, "message": str}
    """
    steps = script.get("steps", [])

    # Nothing to record - succeed without spawning the browser. This keeps
    # the empty-script path hermetic (no node, no playwright, no Chromium),
    # so the pipeline works even on machines without the browser installed.
    if not steps:
        return {"success": True, "video_path": None, "message": "No steps - nothing to record"}

    capture_js = _find_capture_script()
    if capture_js is None:
        return {
            "success": False,
            "error": "Capture script (playwright-capture.js) not found",
            "suggestions": [
                "Dev checkout: confirm scripts/playwright-capture.js exists at the repo root",
                "Packaged app: confirm the installed resources/ directory contains "
                "playwright-capture.js (reinstall if missing)",
            ],
        }

    # Fresh output directory - delete stale files from prior runs
    for old in Path(output_dir).glob("*.webm"):
        old.unlink(missing_ok=True)

    steps_file = Path(output_dir) / ".capture-steps.json"
    steps_file.write_text(json.dumps(steps), encoding="utf-8")
    output_base = str(Path(output_dir) / "recording")

    aspect = str(script.get("aspect_ratio", "16:9"))
    resolution = str(script.get("resolution", "720p"))

    logger.info(
        "Starting Playwright capture (%d steps, theme=%s, aspect=%s, res=%s)...",
        len(steps),
        theme,
        aspect,
        resolution,
    )
    proc = await asyncio.create_subprocess_exec(
        "node",
        str(capture_js),
        str(steps_file),
        output_base,
        theme,
        aspect,
        resolution,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=_node_path_env(),
    )

    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=45)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        steps_file.unlink(missing_ok=True)
        return {
            "success": False,
            "error": "Playwright capture timed out after 45s",
            "suggestions": [
                "Check the target webapp loads without errors",
                "Check Chromium can launch: npx playwright install chromium",
            ],
        }

    steps_file.unlink(missing_ok=True)
    logger.info("Playwright exited with code %d", proc.returncode)

    if proc.returncode != 0:
        err_text = stderr.decode()[:500] if stderr else f"Exit code {proc.returncode}"
        return {
            "success": False,
            "error": err_text,
            "suggestions": ["Check the target webapp is running and has actual content"],
        }

    # Find the output webm
    output = Path(output_dir) / "recording.webm"
    if not output.exists():
        base = Path(output_dir) / "recording"
        if base.exists():
            base.rename(output)
        else:
            webms = list(Path(output_dir).glob("*.webm"))
            if webms:
                output = webms[0]
            else:
                return {
                    "success": False,
                    "error": "Recording produced no video file",
                    "suggestions": [
                        "Check Playwright is installed: npx playwright install chromium",
                        "Check the target URLs resolve in a browser",
                    ],
                }

    size_kb = output.stat().st_size // 1024
    logger.info("Recording complete: %s (%d KB)", output.name, size_kb)
    return {"success": True, "video_path": str(output), "message": "Recording complete"}
