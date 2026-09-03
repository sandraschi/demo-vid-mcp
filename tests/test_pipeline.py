"""Tests for pipeline stages (composer, voiceover, recorder)."""

from unittest.mock import patch

import pytest

from demo_vid_mcp.config import config
from demo_vid_mcp.pipeline import composer, recorder, voiceover


@pytest.mark.anyio
async def test_composer_no_video():
    r = composer._find_ffmpeg()
    assert r is None or isinstance(r, str)

    result = await composer.compose({"title": "test"}, None, None, "/tmp")
    assert result["success"] is False


@pytest.mark.anyio
async def test_composer_no_ffmpeg(tmp_path):
    video = tmp_path / "recording.webm"
    video.write_text("fake")
    with patch.object(composer, "_FFMPEG_PATH", None):
        result = await composer.compose({"title": "test"}, str(video), None, str(tmp_path))
        assert result["success"] is False
        assert "FFmpeg not found" in result.get("error", "")


@pytest.mark.anyio
async def test_voiceover_no_url():
    result = await voiceover.generate_voiceover({"steps": []}, "/tmp", None)
    assert result["success"] is False
    assert "not configured" in result.get("error", "")


@pytest.mark.anyio
async def test_voiceover_no_say_segments():
    result = await voiceover.generate_voiceover(
        {"steps": [{"action": "goto"}]}, "/tmp", "http://fake:10909"
    )
    assert result["success"] is True
    assert result["audio_path"] is None


@pytest.mark.anyio
async def test_recorder_empty_steps(tmp_path):
    result = await recorder.record({"steps": []}, str(tmp_path))
    assert result["success"] is True


def test_config_defaults():
    assert config.host == "127.0.0.1"
    assert isinstance(config.backend_port, int)
    assert config.backend_port == 11134


def test_generate_subtitles(tmp_path):
    steps = [
        {"action": "goto", "wait": 3, "say": "Welcome to demo."},
        {"action": "click", "wait": 2, "say": "Clicking settings."},
    ]
    vtt, srt = composer.generate_subtitles(steps, tmp_path)
    assert vtt is not None and vtt.exists()
    assert srt is not None and srt.exists()
    vtt_text = vtt.read_text(encoding="utf-8")
    assert "WEBVTT" in vtt_text
    assert "Welcome to demo." in vtt_text
    assert "00:00:00.000 --> 00:00:03.000" in vtt_text
    srt_text = srt.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:03,000" in srt_text


def test_job_queue_persistence(tmp_path):
    from demo_vid_mcp.pipeline.queue import JobQueue

    q_file = tmp_path / "test_queue.json"
    q = JobQueue(queue_file=q_file)
    job = q.enqueue(repo="chitchat", aspect_ratio="9:16")
    assert job["id"].startswith("job-")
    assert job["status"] == "pending"
    assert job["aspect_ratio"] == "9:16"
    assert len(q.list_jobs()) == 1

    # Reload from disk to verify persistence
    q2 = JobQueue(queue_file=q_file)
    assert len(q2.list_jobs()) == 1
    assert q2.get_job(job["id"]) is not None
    assert q2.get_job(job["id"])["repo"] == "chitchat"
    assert q2.cancel_job(job["id"]) is True
    assert q2.get_job(job["id"])["status"] == "canceled"
