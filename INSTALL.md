# Installing demo-vid-mcp

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop | Required host | [download](https://claude.ai/download) |
| Python + uv | Run server | `winget install astral-sh.uv` |
| FFmpeg | Video composition | `winget install FFmpeg` |

## Option A — Drag and Drop (Recommended)

1. Go to [Releases](https://github.com/sandraschi/demo-vid-mcp/releases/latest)
2. Download `.mcpb`
3. Open Claude Desktop → drag the file onto the window

## Option B — mcpb CLI

```bash
npx @anthropic-ai/mcpb install https://github.com/sandraschi/demo-vid-mcp
```

## Option C — Manual Configuration

```bash
git clone https://github.com/sandraschi/demo-vid-mcp
cd demo-vid-mcp
uv sync
uv run python -m demo_vid_mcp --serve
```

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "demo-vid-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\demo-vid-mcp", "run", "python", "-m", "demo_vid_mcp"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

## Verify

Ask Claude: "List all demo videos" — should return `demo_vid_list`.
