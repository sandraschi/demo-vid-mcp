"""FastAPI application — REST API for demo video webapp."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import config
from .server import mcp

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


@app.get("/api/videos")
async def list_videos():
    files = sorted(videos_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "videos": [
            {"name": f.stem, "path": f"/videos/{f.name}", "size_kb": f.stat().st_size // 1024}
            for f in files
        ]
    }
