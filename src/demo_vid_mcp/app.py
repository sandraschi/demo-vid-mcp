"""FastAPI application — REST API for demo video webapp."""

import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import config
from .server import mcp

# Ring-buffer log handler — stores last 500 log records in memory
_log_buffer: deque[dict] = deque(maxlen=500)


class RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        _log_buffer.append({
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "source": record.name,
            "message": record.getMessage(),
        })


_log_handler = RingBufferHandler()
_log_handler.setLevel(logging.INFO)
logging.getLogger("demo-vid-mcp").addHandler(_log_handler)

_mcp_http = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger("demo-vid-mcp")
    async with _mcp_http.router.lifespan_context(_mcp_http):
        logger.info("demo-vid-mcp ready")
        yield


app = FastAPI(
    title="demo-vid-mcp", description="Demo video pipeline", version=__version__, lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/mcp", _mcp_http)

videos_dir = Path(config.data_dir) / "videos"
videos_dir.mkdir(parents=True, exist_ok=True)
if videos_dir.exists():
    app.mount("/videos", StaticFiles(directory=str(videos_dir)), name="videos")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": __version__,
        "videos_served": sum(1 for _ in videos_dir.iterdir() if _.suffix == ".mp4"),
    }


@app.post("/api/generate")
async def api_generate(body: dict):
    from demo_vid_mcp.tools.generate import demo_vid_generate

    result = await demo_vid_generate(repo=body.get("repo", ""), script_yaml=body.get("script_yaml"))
    return result


@app.get("/api/repos")
async def list_repos():
    """Return categorized repos available for demo video generation."""
    return {
        "categories": [
            {
                "name": "Research & Knowledge",
                "repos": [
                    "arxiv-mcp",
                    "calibre-mcp",
                    "llm-txt-mcp",
                    "notebooklm-fleet-mcp",
                    "readly-mcp",
                    "tvtropes-mcp",
                ],
            },
            {
                "name": "Media & Creativity",
                "repos": [
                    "blender-mcp",
                    "gimp-mcp",
                    "inkscape-mcp",
                    "davinci-resolve-mcp",
                    "vroidstudio-mcp",
                    "resonite-mcp",
                    "godot-mcp",
                    "unity3d-mcp",
                    "comfyops-mcp",
                    "suno-mcp",
                    "songgeneration-mcp",
                    "audiotool-nexus-mcp",
                    "virtualdj-mcp",
                    "reaper-mcp",
                    "obs-mcp",
                    "butterchurn-mcp",
                ],
            },
            {
                "name": "Communication",
                "repos": [
                    "email-mcp",
                    "discord-mcp",
                    "mastodon-mcp",
                    "bluesky-mcp",
                    "alexa-mcp",
                    "telephony-mcp",
                    "chitchat",
                ],
            },
            {
                "name": "Development & DevOps",
                "repos": [
                    "git-github-mcp",
                    "docker-mcp",
                    "filesystem-mcp",
                    "web-development-mcp",
                    "database-operations-mcp",
                    "browser-mcp",
                    "windows-operations-mcp",
                    "meta_mcp",
                    "fleetwatcher-mcp",
                    "monitoring-mcp",
                ],
            },
            {
                "name": "CAD & Design",
                "repos": [
                    "freecad-mcp",
                    "qcad-mcp",
                    "kicad-mcp",
                    "chip-design-mcp",
                    "codecad-mcp",
                    "sketchboard-excalidraw-mcp",
                ],
            },
            {
                "name": "Automation & Control",
                "repos": [
                    "multi-backup-mcp",
                    "devices-mcp",
                    "home-assistant-mcp",
                    "tapo-mcp",
                    "netatmo-weather-mcp",
                    "pdf-mcp",
                    "system-admin-mcp",
                    "disk-usage-mcp",
                ],
            },
            {
                "name": "Robotics & Simulation",
                "repos": [
                    "yahboom-mcp",
                    "robotics-mcp",
                    "gazebo-mcp",
                    "mujoco-mcp",
                    "ros-mcp",
                    "unitree-mcp",
                    "isaac-mcp",
                    "limx-robotics-mcp",
                ],
            },
            {
                "name": "Productivity & MCP",
                "repos": [
                    "advanced-memory-mcp",
                    "bookmarks-mcp",
                    "notion-mcp",
                    "obsidian-mcp",
                    "onenote-mcp",
                    "mcp-studio",
                    "depot-mcp",
                    "speech-mcp",
                    "glama-status-mcp",
                    "toolbench-mcp",
                ],
            },
        ]
    }


@app.get("/api/videos")
async def list_videos():
    files = sorted(videos_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "videos": [
            {"name": f.stem, "path": f"/videos/{f.name}", "size_kb": f.stat().st_size // 1024}
            for f in files
        ]
    }


@app.get("/api/depot")
async def list_depot():
    """Return all produced videos grouped by repo with their narration scripts."""
    repos_dir = Path(config.data_dir) / "videos"
    if not repos_dir.exists():
        return {"repos": []}

    entries = []
    for repo_dir in sorted(repos_dir.iterdir()):
        if not repo_dir.is_dir():
            continue
        mp4 = list(repo_dir.glob("*.mp4"))
        if not mp4:
            continue
        script_path = repo_dir / "narration.yaml"
        for vid in mp4:
            s = vid.stat()
            entries.append(
                {
                    "repo": repo_dir.name,
                    "name": vid.stem,
                    "video_path": f"/videos/{repo_dir.name}/{vid.name}",
                    "size_kb": s.st_size // 1024,
                    "created": str(int(s.st_mtime)),
                    "has_script": script_path.exists(),
                    "script": script_path.read_text(encoding="utf-8")
                    if script_path.exists()
                    else None,
                }
            )
    return {"repos": entries}


@app.get("/api/logs")
async def logs_get(limit: int = 50, level: str = "INFO", search: str = ""):
    """Return recent log entries from the ring buffer."""
    levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
    min_level = levels.get(level.upper(), 1)
    filtered = [
        e for e in _log_buffer
        if levels.get(e["level"], 1) >= min_level
        and (not search or search.lower() in e["message"].lower())
    ]
    return {"logs": filtered[-limit:], "total": len(filtered)}
