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

    speech_mcp_url: str | None = os.getenv("SPEECH_MCP_URL")
    blender_mcp_url: str | None = os.getenv("BLENDER_MCP_URL")
    gimp_mcp_url: str | None = os.getenv("GIMP_MCP_URL")
    resolve_mcp_url: str | None = os.getenv("DAVINCI_RESOLVE_MCP_URL")
    stems_mcp_url: str | None = os.getenv("STEMS_MCP_URL")
    sfx_mcp_url: str | None = os.getenv("SFX_MCP_URL")
    vfx_mcp_url: str | None = os.getenv("VFX_MCP_URL")


config = Config()
