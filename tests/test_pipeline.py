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
