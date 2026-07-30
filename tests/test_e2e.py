"""End-to-end API tests using httpx against a running backend."""

import httpx
import pytest

BACKEND = "http://127.0.0.1:11134"


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
