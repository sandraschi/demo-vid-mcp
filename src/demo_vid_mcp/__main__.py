"""Entry point - dual transport: stdio (MCP) or HTTP (FastAPI + webapp)."""

import asyncio
import os

from .config import config


def main() -> None:
    port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
    if port:
        import sys

        sys.argv = ["demo-vid-mcp", "--serve", "--port", str(port)]

    import argparse
    import logging

    parser = argparse.ArgumentParser(description="demo-vid-mcp")
    parser.add_argument("--serve", action="store_true", help="Start HTTP server")
    parser.add_argument("--port", type=int, default=config.backend_port, help="Port")
    parser.add_argument("--host", type=str, default=config.host, help="Host")
    parser.add_argument("--log-level", type=str, default=config.log_level, help="Log level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.serve:
        import uvicorn

        uvicorn.run(
            "demo_vid_mcp.app:app", host=args.host, port=args.port, log_level=args.log_level
        )
    else:
        from .server import mcp

        asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
