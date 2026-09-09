"""Tests for pipeline stages (composer, voiceover, recorder)."""

import asyncio
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from demo_vid_mcp.config import config
from demo_vid_mcp.pipeline import composer, music, recorder, sfx, vfx, voiceover


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


def test_build_audio_graph_sfx_only_delays_and_mixes():
    graph, out = composer._build_audio_graph(None, None, [(1, 5.0)])
    assert out == "[aout]"
    assert graph is not None
    assert "adelay=5000|5000" in graph
    assert "amix=inputs=1" in graph


def test_build_audio_graph_voice_and_sfx_no_music():
    graph, out = composer._build_audio_graph(1, None, [(2, 3.5)])
    assert out == "[aout]"
    assert graph is not None
    assert "adelay=3500|3500" in graph
    assert "amix=inputs=2" in graph


def test_build_audio_graph_all_three_sources():
    graph, out = composer._build_audio_graph(1, 2, [(3, 10.0), (4, 20.0)])
    assert out == "[aout]"
    assert graph is not None
    assert "sidechaincompress" in graph  # music still ducks under voice
    assert "adelay=10000|10000" in graph
    assert "adelay=20000|20000" in graph
    assert "amix=inputs=4" in graph  # voice + music_ducked + 2 sfx


def test_step_timestamps():
    steps = [{"wait": 3}, {"wait": 2}, {"wait": 5}]
    assert sfx.step_timestamps(steps) == [0.0, 3.0, 5.0]


@pytest.mark.anyio
async def test_resolve_sfx_clip_not_configured():
    result = await sfx.resolve_sfx_clip("whoosh", "/tmp", None)
    assert result["success"] is False
    assert "not configured" in result["error"]


@pytest.mark.anyio
async def test_resolve_all_sfx_skips_non_sfx_steps():
    steps = [
        {"action": "goto", "wait": 3},
        {"action": "sfx", "text": "click", "wait": 1},
    ]
    # No sfx-mcp configured - the sfx step should be skipped (non-fatal),
    # not raise, and the goto step should never even be considered.
    result = await sfx.resolve_all_sfx(steps, "/tmp", None)
    assert result == []


@pytest.mark.anyio
async def test_stitch_clips_no_clips():
    result = await vfx.stitch_clips([], "/tmp", None)
    assert result["success"] is False


@pytest.mark.anyio
async def test_stitch_clips_single_clip_passthrough():
    """A single clip needs no stitching at all - returned as-is, no ffmpeg
    or vfx-mcp call, no existence check (recorder.py already validated it)."""
    result = await vfx.stitch_clips(["only.webm"], "/tmp", None)
    assert result == {"success": True, "video_path": "only.webm", "used_transitions": False}


@pytest.mark.anyio
async def test_stitch_clips_falls_back_to_concat_without_vfx_mcp(tmp_path):
    """Real end-to-end check of the always-available path: two genuine tiny
    clips (ffmpeg's own synthetic test source, not Playwright output) get
    concatenated into one valid, longer file with no vfx-mcp involved."""
    if not composer._FFMPEG_PATH:
        pytest.skip("FFmpeg not available")

    clip_a = tmp_path / "a.webm"
    clip_b = tmp_path / "b.webm"
    for clip in (clip_a, clip_b):
        proc = await asyncio.create_subprocess_exec(
            composer._FFMPEG_PATH,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=64x64:rate=5",
            "-c:v",
            "libvpx",
            str(clip),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await proc.wait()
        assert clip.exists()

    result = await vfx.stitch_clips([str(clip_a), str(clip_b)], str(tmp_path), None)
    assert result["success"] is True
    assert result["used_transitions"] is False
    assert Path(result["video_path"]).exists()

    proc = await asyncio.create_subprocess_exec(
        composer._FFMPEG_PATH,
        "-v",
        "error",
        "-i",
        result["video_path"],
        "-f",
        "null",
        "-",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    assert proc.returncode == 0, stderr.decode()


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


def _write_test_wav(path: Path, seconds: float, rate: int = 8000) -> None:
    """A real, valid WAV file of exactly `seconds` duration (silence) - no
    FFmpeg/pydub dependency, just the stdlib wave module, matching how
    wav_duration_s itself reads files."""
    import wave as wave_module

    n_frames = int(seconds * rate)
    with wave_module.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n_frames)


def test_wav_duration_s_reads_real_wav(tmp_path):
    wav_path = tmp_path / "test.wav"
    _write_test_wav(wav_path, 2.5)
    assert voiceover.wav_duration_s(wav_path) == pytest.approx(2.5, abs=0.01)


def test_wav_duration_s_missing_file_returns_none(tmp_path):
    assert voiceover.wav_duration_s(tmp_path / "does-not-exist.wav") is None


def test_wav_duration_s_corrupt_file_returns_none(tmp_path):
    bad = tmp_path / "corrupt.wav"
    bad.write_bytes(b"not a real wav file")
    assert voiceover.wav_duration_s(bad) is None


def test_align_script_waits_stretches_long_narration():
    """A line whose real TTS length exceeds its authored wait gets stretched
    to narration + pad, so the page doesn't cut away mid-sentence."""
    script = {"steps": [{"action": "goto", "wait": 2, "say": "a long narrated line"}]}
    result = voiceover.align_script_waits(script, [5.0])
    assert result["adjusted"] == 1
    assert script["steps"][0]["wait"] == pytest.approx(5.0 + voiceover.END_OF_LINE_PAD_S)


def test_align_script_waits_keeps_short_narration_untouched():
    """A line whose authored wait already covers the real TTS length + pad
    is left alone - alignment only ever stretches, never shortens."""
    script = {"steps": [{"action": "goto", "wait": 10, "say": "short line"}]}
    result = voiceover.align_script_waits(script, [1.0])
    assert result["adjusted"] == 0
    assert script["steps"][0]["wait"] == 10


def test_align_script_waits_respects_min_wait():
    script = {"steps": [{"action": "goto", "wait": 0.1, "say": "hi"}]}
    voiceover.align_script_waits(script, [0.05], min_wait=1.0)
    assert script["steps"][0]["wait"] >= 1.0


def test_align_script_waits_skips_non_say_steps():
    """Steps with no `say` line don't consume a segment_duration and are
    never touched - only narrated steps participate in alignment."""
    script = {
        "steps": [
            {"action": "goto", "wait": 2},
            {"action": "goto", "wait": 2, "say": "narrated"},
        ]
    }
    voiceover.align_script_waits(script, [6.0])
    assert script["steps"][0]["wait"] == 2  # untouched, no say line
    assert script["steps"][1]["wait"] == pytest.approx(6.0 + voiceover.END_OF_LINE_PAD_S)


def test_align_script_waits_stops_when_durations_exhausted():
    """Fewer segment_durations than say-steps (partial TTS failure at the
    caller level) - steps beyond the available durations are left alone
    rather than guessing, matching generate.py's own choice to skip
    alignment entirely in this case rather than misalign steps to durations."""
    script = {
        "steps": [
            {"action": "goto", "wait": 2, "say": "first"},
            {"action": "goto", "wait": 2, "say": "second"},
        ]
    }
    result = voiceover.align_script_waits(script, [8.0])
    assert result["adjusted"] == 1
    assert script["steps"][0]["wait"] == pytest.approx(8.0 + voiceover.END_OF_LINE_PAD_S)
    assert script["steps"][1]["wait"] == 2  # never reached, durations ran out


def test_align_script_waits_updates_duration_target():
    script = {
        "duration_target": 30,
        "steps": [{"action": "goto", "wait": 2, "say": "a line needing more time"}],
    }
    voiceover.align_script_waits(script, [10.0])
    expected_total = 10.0 + voiceover.END_OF_LINE_PAD_S
    assert script["duration_target"] == max(30, round(expected_total) + 5)


@pytest.mark.anyio
async def test_generate_voiceover_uses_voice_id_param(monkeypatch, tmp_path):
    """speech-mcp's actual query param is voice_id, not voice - a
    regression guard for the bug that silently ignored the requested voice
    on every single call until this was caught."""
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b"\x00" * 200

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, params=None):
            captured["params"] = params
            return FakeResponse()

    monkeypatch.setattr(voiceover.httpx, "AsyncClient", lambda *a, **k: FakeClient())
    monkeypatch.setattr(voiceover, "wav_duration_s", lambda path: 1.0)

    script = {"voice": "sky", "steps": [{"action": "goto", "wait": 2, "say": "hi"}]}
    result = await voiceover.generate_voiceover(script, str(tmp_path), "http://fake:10909")

    assert result["success"] is True
    assert captured["params"] == {"text": "hi", "voice_id": "sky"}


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
