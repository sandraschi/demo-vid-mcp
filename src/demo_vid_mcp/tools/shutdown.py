"""Tool: demo_vid_shutdown - self-termination capability."""

from __future__ import annotations

import asyncio
import os
import signal

from demo_vid_mcp.server import mcp


@mcp.tool(name="demo_vid_shutdown")
async def demo_vid_shutdown() -> dict:
    """Shut down the demo-vid-mcp server gracefully.

    ## Return Format
    {"success": bool, "message": str}

    ## Examples
    await demo_vid_shutdown()
    """

    async def _die():
        await asyncio.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(_die())
    return {
        "success": True,
        "message": "demo-vid-mcp server shutting down gracefully",
    }
