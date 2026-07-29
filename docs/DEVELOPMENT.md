# Development

## Tools Required

```bash
winget install astral-sh.uv
winget install Git.Git
winget install Casey.Just
winget install FFmpeg  # for composition
```

## Setup

```bash
git clone https://github.com/sandraschi/demo-vid-mcp
cd demo-vid-mcp
just bootstrap
```

## Common Tasks

```bash
just serve      # Start backend
just test       # Run tests
just lint       # Ruff check
just fmt        # Ruff format
```

## Code Standards

- FastMCP 3.4.4+ per [fleet standards](https://github.com/sandraschi/mcp-central-docs)
- Ruff linting, Biome for webapp
- Dialogic returns: `{"success": bool, "message": str, "suggestions": list}`
