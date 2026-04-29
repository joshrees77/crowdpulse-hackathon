from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import pandas as pd

from .io_utils import seconds_to_hms
from .settings import DATA_DIR, RAW_VIDEO_DIR

try:
    from shazamio import Shazam
except Exception:
    Shazam = None


@dataclass
class FingerprintSample:
    start_sec: int
    clip_path: Path


def _video_duration_seconds(video_path: Path) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()
    if fps <= 0:
        return 0
    return int(frames / fps)


def _build_sample_times(duration_sec: int, sample_interval_sec: int, max_samples: int) -> list[int]:
    if duration_sec <= 0:
        return []

    start = min(60, max(duration_sec // 10, 0))
    end = max(duration_sec - 30, start)

    times = list(range(start, end, sample_interval_sec))
    if not times:
        times = [max(duration_sec // 2, 0)]

    if len(times) > max_samples:
        step = len(times) / float(max_samples)
        times = [times[int(i * step)] for i in range(max_samples)]

    # Deduplicate in case of rounding collisions.
    uniq = []
    seen = set()
    for t in times:
        if t not in seen:
            uniq.append(t)
            seen.add(t)
    return uniq


def _extract_audio_clip(video_path: Path, out_path: Path, start_sec: int, clip_duration_sec: int) -> bool:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start_sec),
        "-i",
        str(video_path),
        "-t",
        str(clip_duration_sec),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "44100",
        str(out_path),
        "-y",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode == 0 and out_path.exists()


def _find_video_path(set_id: str) -> Path | None:
    matches = sorted(RAW_VIDEO_DIR.glob(f"{set_id}.*"))
    for candidate in matches:
        if candidate.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
            return candidate
    return None


async def _recognize_samples(samples: list[FingerprintSample]) -> list[dict]:
    if Shazam is None:
        return []

    shazam = Shazam()
    rows: list[dict] = []

    for sample in samples:
        try:
            out = await asyncio.wait_for(shazam.recognize(str(sample.clip_path)), timeout=25.0)
        except Exception:
            continue

        track = out.get("track") or {}
        title = str(track.get("title") or "").strip()
        artist = str(track.get("subtitle") or "").strip()
        if not title and not artist:
            continue

        if artist and title:
            label = f"{artist} - {title}"
        else:
            label = title or artist

        match_count = len(out.get("matches") or [])
        confidence = 0.78 + min(match_count, 6) * 0.03
        confidence = min(confidence, 0.95)

        rows.append(
            {
                "start_sec": int(sample.start_sec),
                "timestamp": seconds_to_hms(int(sample.start_sec)),
                "track": label,
                "source": "audio_fingerprint",
                "confidence": round(float(confidence), 3),
            }
        )

    return rows


def fingerprint_tracks_for_set(
    set_id: str,
    sample_interval_sec: int = 240,
    clip_duration_sec: int = 20,
    max_samples: int = 12,
) -> pd.DataFrame:
    """
    Build a best-effort track timeline using audio fingerprinting.

    Returns columns: start_sec,timestamp,track,source,confidence
    """
    if Shazam is None:
        return pd.DataFrame(columns=["set_id", "start_sec", "timestamp", "track", "source", "confidence"])

    video_path = _find_video_path(set_id)
    if not video_path:
        return pd.DataFrame(columns=["set_id", "start_sec", "timestamp", "track", "source", "confidence"])

    duration = _video_duration_seconds(video_path)
    sample_times = _build_sample_times(duration, sample_interval_sec, max_samples)
    if not sample_times:
        return pd.DataFrame(columns=["set_id", "start_sec", "timestamp", "track", "source", "confidence"])

    clip_dir = DATA_DIR / "tmp_clips" / set_id
    clip_dir.mkdir(parents=True, exist_ok=True)

    samples: list[FingerprintSample] = []
    for t in sample_times:
        clip_path = clip_dir / f"{set_id}_{t}.mp3"
        ok = _extract_audio_clip(video_path, clip_path, t, clip_duration_sec)
        if ok:
            samples.append(FingerprintSample(start_sec=t, clip_path=clip_path))

    if not samples:
        return pd.DataFrame(columns=["set_id", "start_sec", "timestamp", "track", "source", "confidence"])

    rows = asyncio.run(_recognize_samples(samples))

    # Best-effort cleanup of generated clips.
    for sample in samples:
        try:
            sample.clip_path.unlink(missing_ok=True)
        except Exception:
            pass

    if not rows:
        return pd.DataFrame(columns=["set_id", "start_sec", "timestamp", "track", "source", "confidence"])

    df = pd.DataFrame(rows)
    df["set_id"] = set_id

    df = df.sort_values("start_sec").reset_index(drop=True)

    # Remove immediate repeated recognitions to stabilize the timeline.
    keep = []
    prev_track = None
    for _, row in df.iterrows():
        track = str(row["track"])
        if track == prev_track:
            continue
        keep.append(row)
        prev_track = track

    out = pd.DataFrame(keep)
    return out[["set_id", "start_sec", "timestamp", "track", "source", "confidence"]]
