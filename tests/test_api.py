"""Tests for the FastAPI REST endpoints."""

from fastapi.testclient import TestClient

from demo_vid_mcp.app import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_skills():
    r = client.get("/api/skills")
    assert r.status_code == 200
    data = r.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)


def test_repos():
    r = client.get("/api/repos")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_llm_discover():
    r = client.get("/api/llm/discover")
    assert r.status_code == 200
    data = r.json()
    assert "providers" in data
    assert isinstance(data["providers"], list)


def test_logs_defaults():
    r = client.get("/api/logs")
    assert r.status_code == 200


def test_videos_empty():
    r = client.get("/api/videos")
    assert r.status_code == 200
    data = r.json()
    assert "videos" in data


def test_depot_empty():
    r = client.get("/api/depot")
    assert r.status_code == 200


def test_script_draft_invalid():
    r = client.post("/api/script-draft", json={"repo": ""})
    assert r.status_code == 200
    data = r.json()
    assert "success" in data


def test_generate_invalid_repo():
    r = client.post("/api/generate", json={"repo": ""})
    assert r.status_code == 200
