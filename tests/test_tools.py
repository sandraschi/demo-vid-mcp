"""Test that all MCP tools are properly registered."""

import asyncio

import demo_vid_mcp.server as s


def test_all_tools_registered():
    """Verify the side-effect imports in server.py registered all tools.

    Without this test, ruff --fix silently removes the noqa: F401 imports
    in server.py, causing tools to disappear. This test catches that.
    """
    tools = asyncio.run(s.mcp.list_tools())
    names = {t.name for t in tools}
    expected = {
        "demo_vid_generate",
        "demo_vid_list",
        "demo_vid_refine",
        "demo_vid_script_draft",
        "demo_vid_script_validate",
        "demo_vid_help",
        "demo_vid_shutdown",
    }
    missing = expected - names
    assert not missing, f"Tool imports stripped by ruff --fix: missing {missing}"
