set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

# Bootstrap: install dev deps + pre-commit hook
bootstrap:
    uv sync --group dev
    uv run pre-commit install
    if (Test-Path "webapp\package.json") { Set-Location webapp; bun install }
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green

# Serve the backend
serve:
    uv run python -m demo_vid_mcp --serve

# Run tests
test:
    uv run pytest -q --tb=short tests/

# Lint
lint:
    uv run ruff check src/

# Format
fmt:
    uv run ruff format src/

# CI
ci: lint test

# MCPB pack
mcpb-pack:
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File scripts/mcpb-pack.ps1
