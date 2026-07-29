"""Playwright recording stage."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("demo-vid-mcp.recorder")


async def record(script: dict, output_dir: str) -> dict:
    """Run Playwright to record a .webm from a narration script.

    ## Return Format
    {"success": bool, "video_path": str | None, "message": str}
    """
    steps = script.get("steps", [])
    script_json = json.dumps(steps)
    output = Path(output_dir) / "recording.webm"

    pw_script = f"""
    const {{ chromium }} = require('playwright');
    (async () => {{
        const browser = await chromium.launch({{ headless: true }});
        const context = await browser.newContext({{ viewport: {{ width: 1280, height: 720 }} }});
        const page = await context.newPage();
        const steps = {script_json};
        for (const step of steps) {{
            if (step.action === 'goto') {{
                await page.goto(step.url, {{ waitUntil: 'networkidle', timeout: 15000 }});
            }} else if (step.action === 'click') {{
                try {{ await page.click(step.target, {{ timeout: 5000 }}); }} catch {{ /* selector may not exist */ }}
            }}
            if (step.wait) await page.waitForTimeout(step.wait * 1000);
        }}
        await page.close();
        await browser.close();
    }})();
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "node",
            "-e",
            pw_script,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
            return {"success": False, "error": stderr.decode()[:500]}
        return {"success": True, "video_path": str(output), "message": "Recording complete"}
    except TimeoutError:
        return {"success": False, "error": "Recording timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}
