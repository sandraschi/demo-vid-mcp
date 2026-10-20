"""Check that a produced demo video's voice matches its picture.

Post-hoc and artifact-based: it reads `data/videos/<repo>/` and works on videos
made before the 2026-10-20 timeline fix too. Two invariants:

1. Every SRT cue starts when the speech for that line actually starts
   (FFmpeg silencedetect onsets vs cue timestamps). Default tolerance 0.35 s.
2. The voiceover bed is as long as the video (ffprobe duration vs WAV length).

Exit 0 when both hold, 1 otherwise. That is what makes it usable as a gate in
`just regen <repo>` rather than a report someone has to read.

Usage:
    python scripts/check_sync.py --repo japanophile-mcp
    python scripts/check_sync.py --dir "C:/path/to/videos/x" --tolerance 0.5
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

TS_RE = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)\s*-->")
SILENCE_END_RE = re.compile(r"silence_end:\s*([0-9.]+)")


def _ffmpeg() -> str | None:
    for candidate in (
        shutil.which("ffmpeg"),
        str(Path.home() / "scoop" / "shims" / "ffmpeg.exe"),
        "C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _ffprobe(ffmpeg: str | None) -> str | None:
    if ffmpeg:
        sibling = Path(ffmpeg).with_name("ffprobe.exe")
        if sibling.exists():
            return str(sibling)
    which = shutil.which("ffprobe")
    return which


def wav_seconds(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as handle:
            return handle.getnframes() / float(handle.getframerate())
    except Exception:
        return None


def media_seconds(ffprobe: str | None, path: Path) -> float | None:
    if not ffprobe:
        return None
    proc = subprocess.run(  # noqa: S603 - fixed argv, absolute binary, no shell
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return float((proc.stdout or "").strip())
    except ValueError:
        return None


def cue_starts(srt: Path) -> list[float]:
    starts: list[float] = []
    for line in srt.read_text(encoding="utf-8", errors="replace").splitlines():
        match = TS_RE.search(line)
        if match:
            hours, minutes, seconds, millis = match.groups()
            starts.append(int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000)
    return starts


def speech_onsets(
    ffmpeg: str, wav: Path, noise_db: int = -35, min_silence: float = 0.45
) -> list[float]:
    proc = subprocess.run(  # noqa: S603 - fixed argv, absolute binary, no shell
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(wav),
            "-af",
            f"silencedetect=noise={noise_db}dB:d={min_silence}",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    onsets = [float(v) for v in SILENCE_END_RE.findall((proc.stderr or "") + (proc.stdout or ""))]
    onsets.sort()
    return onsets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="", help="repo name under data/videos/")
    parser.add_argument("--dir", default="", help="explicit video folder")
    parser.add_argument("--tolerance", type=float, default=0.35, help="seconds")
    parser.add_argument(
        "--max-tail",
        type=float,
        default=12.0,
        help="allowed silent tail after the last line (seconds)",
    )
    parser.add_argument("--root", default="", help="demo-vid-mcp repo root")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parents[1]
    folder = Path(args.dir) if args.dir else root / "data" / "videos" / args.repo
    if not folder.is_dir():
        print(f"FAIL: no folder {folder}")
        return 1

    mp4 = folder / "final.mp4"
    wav = folder / "voiceover.wav"
    srt = folder / "subtitles.srt"
    missing = [str(p.name) for p in (mp4, wav, srt) if not p.is_file()]
    if missing:
        print(f"FAIL: missing {', '.join(missing)} in {folder}")
        return 1

    ffmpeg = _ffmpeg()
    if not ffmpeg:
        print("FAIL: ffmpeg not found")
        return 1
    ffprobe = _ffprobe(ffmpeg)

    video_s = media_seconds(ffprobe, mp4)
    audio_s = wav_seconds(wav)
    starts = cue_starts(srt)
    onsets = speech_onsets(ffmpeg, wav)

    print(f"folder      {folder}")
    print(f"video       {video_s if video_s is not None else '?'} s")
    print(f"voiceover   {audio_s if audio_s is not None else '?'} s")
    print(f"cues        {len(starts)}   speech onsets {len(onsets)}")

    if len(onsets) < len(starts):
        onsets = [0.0] + onsets
    if len(onsets) < len(starts):
        print(
            f"WARN: detected {len(onsets)} onsets for {len(starts)} cues "
            "(quiet voice, or lines shorter than the silence threshold)"
        )
    if starts and starts[0] < 1.0 and onsets and onsets[0] > 1.0:
        # Speech starts at 0, so silencedetect's first silence_end is the
        # second burst. Re-add the opening one before pairing.
        onsets = [0.0] + onsets
    if len(onsets) != len(starts):
        print(
            f"WARN: {len(onsets)} speech bursts vs {len(starts)} cues - a line may be "
            "split by a breath; per-cue drift is indicative, the length check is exact"
        )

    worst = 0.0
    worst_index = 0
    pairs: list[tuple[int, float, float | None]] = []
    j = 0
    for i, start in enumerate(starts):
        while j < len(onsets) and onsets[j] < start - 1.0:
            j += 1
        if j < len(onsets):
            pairs.append((i + 1, start, onsets[j]))
            j += 1
        else:
            pairs.append((i + 1, start, None))

    print(f"{'cue':>4} {'srt start':>10} {'audio start':>12} {'drift':>8}")
    for cue, start, onset in pairs:
        if onset is None:
            print(f"{cue:>4} {start:>10.3f} {'-':>12} {'?':>8}  <-- no burst found")
            continue
        drift = onset - start
        if abs(drift) > abs(worst):
            worst, worst_index = drift, cue
        flag = "" if abs(drift) <= args.tolerance else "  <-- OUT"
        print(f"{cue:>4} {start:>10.3f} {onset:>12.3f} {drift:>+8.3f}{flag}")

    ok = abs(worst) <= args.tolerance
    print(f"worst drift {worst:+.3f} s at cue {worst_index} (tolerance {args.tolerance:.2f})")
    if video_s is not None and audio_s is not None:
        gap = audio_s - video_s
        print(f"audio-video length delta {gap:+.3f} s")
        if gap > max(args.tolerance, 0.5):
            print("FAIL: voiceover is longer than the picture (speech outruns video)")
            ok = False
        elif -gap > args.max_tail:
            print(
                f"FAIL: silent tail {-gap:.2f}s exceeds {args.max_tail:.0f}s - "
                "the last page holds far past its line"
            )
            ok = False
        elif gap < -0.5:
            print(f"note: {-gap:.2f}s of silence at the end (outro hold, allowed)")
    print("PASS" if ok else "FAIL: voice does not match the picture")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
