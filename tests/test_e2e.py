"""End-to-end API tests using httpx against a running backend."""

import socket

import httpx
import pytest

BACKEND = "http://127.0.0.1:11134"


def _backend_is_live() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 11134), timeout=0.5):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _backend_is_live(),
    reason="demo-vid-mcp backend not running on port 11134 (start with 'just serve' or 'start.ps1' to run E2E)",
)


@pytest.mark.anyio
async def test_backend_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND}/api/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"


@pytest.mark.anyio
async def test_backend_skills():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND}/api/skills", timeout=5)
        assert r.status_code == 200


@pytest.mark.anyio
async def test_backend_repos():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND}/api/repos", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "categories" in data


@pytest.mark.anyio
async def test_backend_videos():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND}/api/videos", timeout=5)
        assert r.status_code == 200


@pytest.mark.anyio
async def test_backend_depot():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND}/api/depot", timeout=5)
        assert r.status_code == 200
