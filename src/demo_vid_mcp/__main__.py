"""Entry point — dual transport: stdio (MCP) or HTTP (FastAPI + webapp)."""

import os
import sys

from .config import config


def main() -> None:
    port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
    if port:
        sys.argv = ["run_server.py", "--mode", "http", "--host", config.host, "--port", str(port)]
    import argparse

    parser = argparse.ArgumentParser(description="demo-vid-mcp")
    parser.add_argument("--serve", action="store_true", help="Start HTTP server")
    parser.add_argument("--port", type=int, default=config.backend_port, help="Port")
    args = parser.parse_args()

    if args.serve:
        import uvicorn

        uvicorn.run(
            "demo_vid_mcp.app:app", host=config.host, port=args.port, log_level=config.log_level
        )
    else:
        from .server import mcp

        mcp.run_stdio_async()


if __name__ == "__main__":
    main()
