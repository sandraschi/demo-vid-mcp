import os
from dataclasses import dataclass
from pathlib import Path


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
    speech_mcp_url: str | None = os.getenv("SPEECH_MCP_URL")
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
