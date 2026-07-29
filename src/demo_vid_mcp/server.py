"""FastMCP server — registers demo video tools."""

from fastmcp import FastMCP

from . import __version__

mcp = FastMCP(name="demo-vid-mcp", version=__version__)
