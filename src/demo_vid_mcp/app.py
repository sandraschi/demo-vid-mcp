"""FastAPI application — REST API for demo video webapp."""

import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import httpx
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
        _log_buffer.append(
            {
                "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                "level": record.levelname,
                "source": record.name,
                "message": record.getMessage(),
            }
        )


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


@app.get("/api/health/speech")
async def speech_health():
    """Probe speech-mcp health via backend (avoids browser CORS issues)."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get("http://127.0.0.1:10909/api/health")
            return {"detected": r.status_code == 200, "status": r.status_code}
    except httpx.ConnectError:
        return {"detected": False}
    except Exception as e:
        return {"detected": False, "error": str(e)}


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
        e
        for e in _log_buffer
        if levels.get(e["level"], 1) >= min_level
        and (not search or search.lower() in e["message"].lower())
    ]
    return {"logs": filtered[-limit:], "total": len(filtered)}


@app.delete("/api/videos/{repo}")
async def delete_repo_videos(repo: str):
    """Delete all videos and scripts for a repo from the depot."""
    repo_dir = Path(config.data_dir) / "videos" / repo
    if not repo_dir.exists():
        return {"success": False, "error": f"No videos found for {repo}"}
    import shutil

    shutil.rmtree(repo_dir, ignore_errors=True)
    return {"success": True, "message": f"Deleted all videos for {repo}"}


@app.delete("/api/videos/{repo}/{name}")
async def delete_video(repo: str, name: str):
    """Delete a single video and its script from the depot."""
    repo_dir = Path(config.data_dir) / "videos" / repo
    (repo_dir / f"{name}.mp4").unlink(missing_ok=True)
    (repo_dir / "narration.yaml").unlink(missing_ok=True)
    remaining = list(repo_dir.glob("*.mp4"))
    if not remaining:
        import shutil

        shutil.rmtree(repo_dir, ignore_errors=True)
    return {"success": True, "message": f"Deleted {name} for {repo}"}


@app.post("/api/videos/{repo}/insert")
async def insert_into_repo(repo: str):
    """Copy video into target repo's docs/screenshots/ and add README link."""
    import re as _re
    import shutil

    repo_vid_dir = Path(config.data_dir) / "videos" / repo
    mp4_files = list(repo_vid_dir.glob("*.mp4"))
    if not mp4_files:
        return {"success": False, "error": f"No video found for {repo}"}

    target_dir = config.repos_root / repo / "docs" / "screenshots"
    target_dir.mkdir(parents=True, exist_ok=True)
    for v in mp4_files:
        shutil.copy2(v, target_dir / v.name)

    readme_path = config.repos_root / repo / "README.md"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        preview_lines = ["## Preview\n"]
        for v in mp4_files:
            preview_lines.append(f"![Demo video](docs/screenshots/{v.name})\n")
        preview_block = "\n" + "".join(preview_lines) + "\n"
        if "## Preview" in text:
            text = _re.sub(
                r"## Preview.*?(?=\n## |\Z)", preview_block.strip(), text, flags=_re.DOTALL
            )
        else:
            text = text.replace("# ", "# \n" + preview_block, 1)
        readme_path.write_text(text, encoding="utf-8")
        return {
            "success": True,
            "message": f"Inserted {len(mp4_files)} video(s) into {repo} README",
        }
    return {"success": True, "message": f"Copied {len(mp4_files)} video(s) to {repo} (no README)"}


@app.get("/api/skills")
async def list_skills():
    """Return available skills (preprompts) for the chat page."""
    return {
        "skills": [
            {
                "name": "demo-vid-mcp",
                "description": "Expert in generating fleet demo videos with Playwright, speech-mcp, and FFmpeg.",
            },
        ]
    }


@app.get("/api/skills/demo-vid-mcp")
async def get_skill():
    return {
        "content": "# demo-vid-mcp skill\n\nYou are a demo video generation expert.\n\n## Tools\n- demo_vid_generate: Full pipeline\n- demo_vid_script_draft: Generate narration scripts\n- demo_vid_script_validate: Validate scripts\n\n## Workflow\n1. Draft a script with demo_vid_script_draft\n2. Validate with demo_vid_script_validate\n3. Generate the video with demo_vid_generate\n4. Review in the Depot page\n5. Insert into the repo README"
    }


@app.post("/api/llm/chat")
async def llm_chat(body: dict):
    """Proxy chat requests to the configured LLM provider."""
    provider = body.get("provider", "ollama")
    model = body.get("model", "gemma4:2b")
    messages = body.get("messages", [])

    provider_configs = {
        "ollama": {"base": "http://127.0.0.1:11434", "path": "/api/chat"},
        "lmstudio": {"base": "http://127.0.0.1:1234", "path": "/v1/chat/completions"},
    }
    cfg = provider_configs.get(provider.lower(), provider_configs["ollama"])

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            if provider.lower() == "ollama":
                payload = {"model": model, "messages": messages, "stream": True}
                r = await client.post(f"{cfg['base']}{cfg['path']}", json=payload)
                r.raise_for_status()
                lines = r.text.strip().splitlines()
                full_content = ""
                for line in lines:
                    if line.startswith("data: "):
                        import json

                        chunk = json.loads(line[6:])
                        if "message" in chunk and "content" in chunk["message"]:
                            full_content += chunk["message"]["content"]
                    elif line.startswith("{"):
                        import json

                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            full_content += chunk["message"]["content"]
                return {"success": True, "message": {"role": "assistant", "content": full_content}}
            else:
                payload = {"model": model, "messages": messages}
                r = await client.post(f"{cfg['base']}{cfg['path']}", json=payload)
                r.raise_for_status()
                data = r.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "message": {"role": "assistant", "content": content}}
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Provider {provider} not reachable on {cfg['base']}",
            "suggestions": [f"Start {provider}: ollama serve", "Check the provider port"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/llm/discover")
async def llm_discover():
    """Probe common LLM providers and return detected ones with available models."""
    providers = []
    probe_configs = [
        {
            "name": "Ollama",
            "port": 11434,
            "path": "/api/tags",
            "model_path": "/api/tags",
            "model_key": "models",
            "model_name_key": "name",
        },
        {
            "name": "LM Studio",
            "port": 1234,
            "path": "/v1/models",
            "model_path": "/v1/models",
            "model_key": "data",
            "model_name_key": "id",
        },
    ]
    for cfg in probe_configs:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                r = await client.get(f"http://127.0.0.1:{cfg['port']}{cfg['path']}")
                if r.status_code == 200:
                    data = r.json()
                    models_data = data.get(cfg["model_key"], []) if cfg["model_key"] else []
                    models = (
                        [m.get(cfg["model_name_key"], str(m)) for m in models_data]
                        if isinstance(models_data, list)
                        else []
                    )
                    providers.append(
                        {
                            "name": cfg["name"],
                            "port": cfg["port"],
                            "detected": True,
                            "models": models,
                        }
                    )
                else:
                    providers.append({"name": cfg["name"], "port": cfg["port"], "detected": False})
        except (httpx.ConnectError, httpx.TimeoutException):
            providers.append({"name": cfg["name"], "port": cfg["port"], "detected": False})
    return {"providers": providers}
