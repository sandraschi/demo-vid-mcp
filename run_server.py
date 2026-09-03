"""PyInstaller entry point.

PyInstaller freezing `src/demo_vid_mcp/__main__.py` directly as the entry
script fails with "attempted relative import with no known parent package" -
`__main__.py` uses `from .config import config`, which requires real package
context. Importing `demo_vid_mcp.__main__` from here (with `src` on the
analysis pathex) gives it that context; `__main__.main()` already handles
the dual-transport switch (stdio vs HTTP via MCP_PORT/PORT env vars).
"""

import sys

sys.path.insert(0, "src")

from demo_vid_mcp.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
