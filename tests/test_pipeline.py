"""Tests for pipeline stages (composer, voiceover, recorder)."""

import os
from unittest.mock import patch

import pytest

from demo_vid_mcp.config import config
from demo_vid_mcp.pipeline import composer, music, recorder, voiceover


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


def test_build_audio_graph_neither():
    assert composer._build_audio_graph(None, None) == (None, None)


def test_build_audio_graph_voice_only_maps_directly_no_filtering():
    """No music present - just map the voice stream, same as before music
    support existed (no filter_complex needed at all)."""
    assert composer._build_audio_graph(1, None) == (None, "1:a")


def test_build_audio_graph_music_only_fixed_volume_no_duck():
    """Nothing to duck against without a voice track - just turn it down."""
    graph, out = composer._build_audio_graph(None, 1)
    assert out == "[aout]"
    assert graph == "[1:a]volume=0.35[aout]"


def test_build_audio_graph_both_ducks_music_under_voice():
    graph, out = composer._build_audio_graph(1, 2)
    assert out == "[aout]"
    assert graph is not None
    assert "sidechaincompress" in graph
    assert "[2:a]" in graph  # music is the ducked/main input
    assert "[1:a]" in graph  # voice is the sidechain trigger, and in the final amix


@pytest.mark.anyio
async def test_generate_background_music_not_configured():
    result = await music.generate_background_music("ambient", 30, "/tmp", None)
    assert result["success"] is False
    assert "not configured" in result.get("error", "")


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


def test_capture_timeout_floor():
    """Short scripts still get at least a 60s buffer for browser launch."""
    assert recorder._capture_timeout([{"wait": 2}, {"wait": 3}]) == 65
    assert recorder._capture_timeout([]) >= 45


def test_capture_timeout_scales_with_content():
    """A long detail-heavy script (regression: this used to hit a flat 45s
    cap and fail with 'Playwright capture timed out after 45s' even though
    the capture was still legitimately running)."""
    steps = [{"wait": 8}] * 6 + [{"wait": 2}]  # 50s of content, like arxiv-mcp's draft
    timeout = recorder._capture_timeout(steps)
    assert timeout > 45
    assert timeout == 50 + 60


def test_config_defaults():
    assert config.host == "127.0.0.1"
    assert isinstance(config.backend_port, int)
    assert config.backend_port == 11134


def test_load_env_file_reads_first_existing_candidate(tmp_path, monkeypatch):
    """Regression test: python-dotenv was a stated part of the design (the
    voiceover error message says "Set SPEECH_MCP_URL in .env") but nothing
    ever called load_dotenv() anywhere, so a correctly filled-in .env was
    silently ignored in both dev and the packaged app."""
    from demo_vid_mcp.config import _load_env_file

    missing = tmp_path / "does-not-exist" / ".env"
    real = tmp_path / ".env"
    real.write_text("DEMO_VID_TEST_REGRESSION_VAR=loaded\n", encoding="utf-8")
    monkeypatch.delenv("DEMO_VID_TEST_REGRESSION_VAR", raising=False)

    _load_env_file([missing, real])

    assert os.environ.get("DEMO_VID_TEST_REGRESSION_VAR") == "loaded"


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
    reloaded = q2.get_job(job["id"])
    assert reloaded is not None
    assert reloaded["repo"] == "chitchat"
    assert q2.cancel_job(job["id"]) is True
    canceled = q2.get_job(job["id"])
    assert canceled is not None
    assert canceled["status"] == "canceled"
