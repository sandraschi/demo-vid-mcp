"""FastAPI application - REST API for demo video webapp."""

import logging
import platform
import time
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

# Ring-buffer log handler - stores last 500 log records in memory
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
_START_TIME = time.monotonic()

_TOOL_NAMES = [
    "demo_vid_generate",
    "demo_vid_script_draft",
    "demo_vid_script_validate",
    "demo_vid_list",
    "demo_vid_refine",
    "demo_vid_help",
    "demo_vid_shutdown",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    from demo_vid_mcp.pipeline.queue import job_queue

    logger = logging.getLogger("demo-vid-mcp")
    async with _mcp_http.router.lifespan_context(_mcp_http):
        await job_queue.start_worker()
        logger.info("demo-vid-mcp ready with background job queue active")
        yield


app = FastAPI(
    title="demo-vid-mcp", description="Demo video pipeline", version=__version__, lifespan=lifespan
)

_ALLOWED_ORIGINS = [
    "http://127.0.0.1:11135",
    "http://localhost:11135",
    "http://127.0.0.1:11134",
    "http://localhost:11134",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|100\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
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
        "videos_served": sum(1 for _ in videos_dir.rglob("*.mp4")),
    }


@app.get("/api/v1/diagnostics")
async def diagnostics():
    """Full diagnostics for CUA-NSIS smoke testing: tool list, system info, errors."""
    errors = [
        entry["message"]
        for entry in list(_log_buffer)[-50:]
        if entry["level"] in ("ERROR", "CRITICAL")
    ]
    return {
        "status": "ok",
        "server": "demo-vid-mcp",
        "version": __version__,
        "uptime_seconds": int(time.monotonic() - _START_TIME),
        "tool_count": len(_TOOL_NAMES),
        "tools": [{"name": name} for name in _TOOL_NAMES],
        "system": {
            "windows": platform.system() == "Windows",
            "platform": platform.platform(),
        },
        "errors": errors,
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

    repo = body.get("repo", "").strip()
    if not repo:
        return {"success": False, "error": "repo required"}

    result = await demo_vid_generate(repo=repo, script_yaml=body.get("script_yaml"))
    return result


@app.post("/api/script-draft")
async def api_script_draft(body: dict):
    """Draft a narration script for a repo (calls demo_vid_script_draft tool)."""

    from demo_vid_mcp.pipeline.script import default_script

    repo = body.get("repo", "")
    if not repo:
        return {"success": False, "error": "repo required"}
    script = default_script(repo)
    return {"success": True, "script": script, "message": f"Drafted script for {repo}"}


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
        poster_path = repo_dir / "poster.jpg"
        vtt_path = repo_dir / "subtitles.vtt"
        for vid in mp4:
            s = vid.stat()
            entries.append(
                {
                    "repo": repo_dir.name,
                    "name": vid.stem,
                    "video_path": f"/videos/{repo_dir.name}/{vid.name}",
                    "poster_path": f"/videos/{repo_dir.name}/poster.jpg"
                    if poster_path.exists()
                    else None,
                    "vtt_path": f"/videos/{repo_dir.name}/subtitles.vtt"
                    if vtt_path.exists()
                    else None,
                    "size_kb": s.st_size // 1024,
                    "created": str(int(s.st_mtime)),
                    "has_script": script_path.exists(),
                    "script": script_path.read_text(encoding="utf-8")
                    if script_path.exists()
                    else None,
                }
            )
    return {"repos": entries, "videos": entries}


@app.get("/api/queue")
async def queue_list():
    """Return persistent generation queue status."""
    from demo_vid_mcp.pipeline.queue import job_queue

    return {"jobs": job_queue.list_jobs()}


@app.post("/api/queue")
async def queue_enqueue(body: dict):
    """Enqueue a video generation job."""
    from demo_vid_mcp.pipeline.queue import job_queue

    repo = body.get("repo", "").strip()
    if not repo:
        return {"success": False, "error": "repo parameter is required"}
    job = job_queue.enqueue(
        repo=repo,
        script_yaml=body.get("script_yaml"),
        aspect_ratio=body.get("aspect_ratio", "16:9"),
        resolution=body.get("resolution", "720p"),
    )
    return {"success": True, "job": job}


@app.delete("/api/queue/{job_id}")
async def queue_cancel(job_id: str):
    """Cancel a pending generation job."""
    from demo_vid_mcp.pipeline.queue import job_queue

    canceled = job_queue.cancel_job(job_id)
    return {"success": canceled}


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

    timeout = httpx.Timeout(connect=2.0, read=60.0, write=10.0, pool=2.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
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
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError):
        port = cfg["base"].split(":")[-1]
        return {
            "success": True,
            "offline": True,
            "message": {
                "role": "assistant",
                "content": (
                    f"*(Notice: {provider.capitalize()} is not running on port {port})*\n\n"
                    "The **demo video pipeline is fully functional without Ollama** — Playwright capture, "
                    "speech-mcp voiceover, and FFmpeg video composition do not require an LLM.\n\n"
                    f"To enable interactive AI chat, start the service:\n"
                    f"```bash\n{provider.lower()} serve\n```"
                ),
            },
            "error": f"Provider {provider} not reachable on {cfg['base']}",
            "suggestions": [f"Start {provider}: {provider} serve", "Use Generate page directly"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/llm/discover")
async def llm_discover():
    """Probe common LLM providers concurrently and return detected ones with available models."""
    probe_configs = [
        {
            "name": "Ollama",
            "port": 11434,
            "path": "/api/tags",
            "model_path": "/api/tags",
            "model_key": "models",
            "model_name_key": "name",
            "start_hint": "ollama serve",
        },
        {
            "name": "LM Studio",
            "port": 1234,
            "path": "/v1/models",
            "model_path": "/v1/models",
            "model_key": "data",
            "model_name_key": "id",
            "start_hint": "Start LM Studio local server on port 1234",
        },
    ]

    async def probe_one(cfg: dict) -> dict:
        try:
            timeout = httpx.Timeout(connect=0.6, read=1.0, write=0.5, pool=0.5)
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(f"http://127.0.0.1:{cfg['port']}{cfg['path']}")
                if r.status_code == 200:
                    data = r.json()
                    models_data = data.get(cfg["model_key"], []) if cfg["model_key"] else []
                    models = (
                        [m.get(cfg["model_name_key"], str(m)) for m in models_data]
                        if isinstance(models_data, list)
                        else []
                    )
                    return {
                        "name": cfg["name"],
                        "port": cfg["port"],
                        "detected": True,
                        "status": "online",
                        "models": models,
                    }
                return {
                    "name": cfg["name"],
                    "port": cfg["port"],
                    "detected": False,
                    "status": f"HTTP {r.status_code}",
                    "hint": cfg["start_hint"],
                }
        except Exception:
            return {
                "name": cfg["name"],
                "port": cfg["port"],
                "detected": False,
                "status": "offline",
                "hint": cfg["start_hint"],
            }

    import asyncio

    providers = await asyncio.gather(*(probe_one(c) for c in probe_configs))
    return {"providers": list(providers)}


@app.post("/api/shutdown")
async def api_shutdown():
    """Graceful server shutdown."""
    import asyncio
    import os
    import signal

    async def _die():
        await asyncio.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(_die())
    return {"success": True, "message": "Server shutting down..."}
