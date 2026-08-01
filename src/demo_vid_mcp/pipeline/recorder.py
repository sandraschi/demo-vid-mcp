"""Playwright recording stage."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("demo-vid-mcp.recorder")


async def record(script: dict, output_dir: str, theme: str = "dark") -> dict:
    """Run Playwright to capture a .webm from a narration script.

    Uses Playwright's native video recording. Checks process exit code
    BEFORE looking for output files — prevents stale files from a
    previous run being reported as success. Kills subprocess on timeout
    to prevent hanging the pipeline.

    theme: "dark" (fleet default) or "light" — passed to the capture
    script, which forces the theme class on the target page so demo
    videos match the requested mode.

    ## Return Format
    {"success": bool, "video_path": str | None, "message": str}
    """
    steps = script.get("steps", [])

    # Nothing to record — succeed without spawning the browser. This keeps
    # the empty-script path hermetic (no node, no playwright, no Chromium),
    # so the pipeline works even on machines without the browser installed.
    if not steps:
        return {"success": True, "video_path": None, "message": "No steps — nothing to record"}

    script_dir = Path(__file__).resolve().parents[3] / "scripts"
    capture_js = script_dir / "playwright-capture.js"
    if not capture_js.exists():
        return {"success": False, "error": f"Capture script not found at {capture_js}"}

    # Fresh output directory — delete stale files from prior runs
    for old in Path(output_dir).glob("*.webm"):
        old.unlink(missing_ok=True)

    steps_file = Path(output_dir) / ".capture-steps.json"
    steps_file.write_text(json.dumps(steps), encoding="utf-8")
    output_base = str(Path(output_dir) / "recording")

    logger.info("Starting Playwright capture (%d steps, theme=%s)...", len(steps), theme)
    proc = await asyncio.create_subprocess_exec(
        "node",
        str(capture_js),
        str(steps_file),
        output_base,
        theme,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
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
