"""Playwright recording stage."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("demo-vid-mcp.recorder")


async def record(script: dict, output_dir: str) -> dict:
    """Run Playwright to capture a .webm from a narration script.

    Uses Playwright's native video recording (recordVideo context option).
    Checks process exit code BEFORE looking for output files — prevents
    stale files from a previous run being reported as success.

    ## Return Format
    {"success": bool, "video_path": str | None, "message": str}
    """
    steps = script.get("steps", [])

    script_dir = Path(__file__).resolve().parents[3] / "scripts"
    capture_js = script_dir / "playwright-capture.js"
    if not capture_js.exists():
        return {"success": False, "error": f"Capture script not found at {capture_js}"}

    # Delete any stale recording from previous run
    stale = Path(output_dir) / "recording.webm"
    stale.unlink(missing_ok=True)
    for old in Path(output_dir).glob("*.webm"):
        old.unlink(missing_ok=True)

    steps_file = Path(output_dir) / ".capture-steps.json"
    steps_file.write_text(json.dumps(steps), encoding="utf-8")
    output_base = str(Path(output_dir) / "recording")

    try:
        proc = await asyncio.create_subprocess_exec(
            "node",
            str(capture_js),
            str(steps_file),
            output_base,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        steps_file.unlink(missing_ok=True)

        # Check exit code BEFORE looking for files — JS may have exited 1 on blank page
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

        return {"success": True, "video_path": str(output), "message": "Recording complete"}
    except TimeoutError:
        return {"success": False, "error": "Recording timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}
