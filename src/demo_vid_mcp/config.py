import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_env_file(candidates: list[Path] | None = None) -> None:
    """Load .env into the process environment before Config's field defaults
    are evaluated (dataclass default expressions run once, at class-body
    execution time - i.e. now, at import - so this must run before `class
    Config` below, not just before `config = Config()`).

    python-dotenv's own find_dotenv() walks up from the current working
    directory, which happens to work in dev (uv run's cwd is the repo root)
    but not in the packaged app: Tauri sets the backend's cwd to the install
    directory (see backend.rs spawn_backend), which has no .env unless one
    was placed there - same "packaged app has a different cwd than a dev
    checkout" problem as _find_ffmpeg()/_find_capture_script() elsewhere in
    this codebase. Previously nothing loaded .env at all in either mode, so
    SPEECH_MCP_URL and friends were silently never read even when a correctly
    filled-in .env existed right next to the code.
    """
    if candidates is None:
        candidates = [
            Path(__file__).resolve().parents[2] / ".env",  # dev repo root
            Path.cwd() / ".env",  # packaged install dir (Tauri's cwd)
            Path.cwd() / "resources" / ".env",  # packaged resources dir
        ]
    for c in candidates:
        if c.exists():
            load_dotenv(c)
            return


_load_env_file()


@dataclass
class Config:
    host: str = os.getenv("HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("PORT", "11134"))
    log_level: str = os.getenv("DEMO_VID_LOG_LEVEL", "info")
    data_dir: str = os.getenv("DEMO_VID_DATA_DIR", "data")
    repos_root: Path = Path(os.getenv("DEMO_VID_REPOS_ROOT", "D:/Dev/repos"))

    # All *_mcp_url fields below must be the target server's FULL MCP endpoint
    # URL (e.g. "http://127.0.0.1:10793/mcp"), not just host:port - they're
    # used with fastmcp.Client, which speaks the real MCP protocol, since
    # fleet servers do NOT share a uniform REST tool-call shortcut.
    # speech_mcp_url and songgeneration_mcp_url are exceptions to the "full
    # MCP endpoint" rule above - both are called over their plain REST APIs
    # (httpx directly), not fastmcp.Client, so these are just the REST base
    # (e.g. "http://127.0.0.1:10909", no /mcp suffix).
    speech_mcp_url: str | None = os.getenv("SPEECH_MCP_URL")
    songgeneration_mcp_url: str | None = os.getenv("SONGGENERATION_MCP_URL")
    blender_mcp_url: str | None = os.getenv("BLENDER_MCP_URL")
    gimp_mcp_url: str | None = os.getenv("GIMP_MCP_URL")
    resolve_mcp_url: str | None = os.getenv("DAVINCI_RESOLVE_MCP_URL")
    stems_mcp_url: str | None = os.getenv("STEMS_MCP_URL")
    sfx_mcp_url: str | None = os.getenv("SFX_MCP_URL")
    vfx_mcp_url: str | None = os.getenv("VFX_MCP_URL")
    resonite_mcp_url: str | None = os.getenv("RESONITE_MCP_URL")

    # Desktop-capture mode (native app driven live by its MCP server, e.g. Blender/Resonite)
    windows_computer_use_mcp_url: str | None = os.getenv("WINDOWS_COMPUTER_USE_MCP_URL")
    obs_mcp_url: str | None = os.getenv("OBS_MCP_URL")


config = Config()
