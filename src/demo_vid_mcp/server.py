"""FastMCP server - registers demo video tools."""

from fastmcp import FastMCP

from . import __version__

mcp = FastMCP(name="demo-vid-mcp", version=__version__)

# Side-effect imports: @mcp.tool() decorators register tools at import time.
# These MUST NOT be removed - ruff --fix will try to delete them as "unused imports."
import demo_vid_mcp.tools.generate  # noqa: E402, F401
import demo_vid_mcp.tools.help  # noqa: E402, F401
import demo_vid_mcp.tools.list  # noqa: E402, F401
import demo_vid_mcp.tools.refine  # noqa: E402, F401
import demo_vid_mcp.tools.script_tools  # noqa: E402, F401
import demo_vid_mcp.tools.shutdown  # noqa: E402, F401
