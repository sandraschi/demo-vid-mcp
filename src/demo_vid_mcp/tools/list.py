"""Tool: demo_vid_list - list produced videos."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from demo_vid_mcp.config import config
from demo_vid_mcp.server import mcp


@mcp.tool()
async def demo_vid_list(
    repo: Annotated[str | None, Field(description="Filter by repo name (optional).")] = None,
) -> dict:
    """List produced demo videos with metadata.

    Scans the local data/videos/ directory for .mp4 files and returns
    file name, size, and creation date for each.

    ## Return Format
    {"success": bool, "videos": [{"name": str, "repo": str, "size_kb": int, "created": str}], "count": int}

    ## Examples
    await demo_vid_list()
    await demo_vid_list(repo="chitchat")
    """
    base = Path(config.data_dir) / "videos"
    if not base.exists():
        return {"success": True, "videos": [], "count": 0, "message": "No videos produced yet"}

    if repo:
        search_dir = base / repo
        if not search_dir.exists():
            return {"success": True, "videos": [], "count": 0, "message": f"No videos for {repo}"}
        mp4s = list(search_dir.glob("*.mp4"))
    else:
        mp4s = list(base.rglob("*.mp4"))

    videos = []
    for f in sorted(mp4s, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        videos.append(
            {
                "name": f.stem,
                "repo": f.parent.name,
                "size_kb": stat.st_size // 1024,
                "created": f"{stat.st_mtime:.0f}",
            }
        )

    return {
        "success": True,
        "videos": videos,
        "count": len(videos),
        "message": f"Found {len(videos)} produced video(s)" if videos else "No videos found",
    }
