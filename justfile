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

# Typecheck
typecheck:
    uv run pyright src/

# Format
fmt:
    uv run ruff format src/

# --- CI  local equivalent  must pass before push ---
ci: lint typecheck test

# Run E2E tests against local backend
test-e2e:
    uv run pytest -q --tb=short tests/test_e2e.py

# Full CI including webapp build
cifull: ci
    if (Test-Path "webapp\package.json") { Set-Location webapp; bun run check; bun run build }

# MCPB pack
mcpb-pack:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Dev\repos\mcp-central-docs\scripts\make-mcpb.ps1" -RepoPath (Get-Location).Path
