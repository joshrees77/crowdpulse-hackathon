from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd

from .settings import RAW_META_DIR, RAW_VIDEO_DIR, ensure_dirs


def _find_video_path(set_id: str) -> Path | None:
    matches = sorted(RAW_VIDEO_DIR.glob(f"{set_id}.*"))
    for candidate in matches:
        if candidate.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
            return candidate
    return None


def _find_info_json_path(set_id: str) -> Path | None:
    direct = RAW_META_DIR / f"{set_id}.info.json"
    if direct.exists():
        return direct

    for candidate in RAW_VIDEO_DIR.glob(f"{set_id}.info.json"):
        return candidate
    return None


def _download_one_set(set_id: str, youtube_url: str, force: bool = False) -> dict:
    ensure_dirs()

    existing_video = _find_video_path(set_id)
    existing_meta = _find_info_json_path(set_id)

    if existing_video and existing_meta and not force:
        return {
            "set_id": set_id,
            "status": "skipped_existing",
            "video_path": str(existing_video),
            "meta_path": str(existing_meta),
        }

    output_template = str((RAW_VIDEO_DIR / f"{set_id}.%(ext)s").resolve())
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--merge-output-format",
        "mp4",
        "--format",
        "bv*[height<=1080]+ba/b[height<=1080]/best",
        "--write-info-json",
        "--output",
        output_template,
        youtube_url,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {
            "set_id": set_id,
            "status": "error",
            "error": proc.stderr.strip() or proc.stdout.strip(),
            "video_path": "",
            "meta_path": "",
        }

    video_path = _find_video_path(set_id)
    info_path = _find_info_json_path(set_id)

    if info_path and info_path.parent != RAW_META_DIR:
        target = RAW_META_DIR / info_path.name
        info_path.replace(target)
        info_path = target

    return {
        "set_id": set_id,
        "status": "downloaded",
        "video_path": str(video_path) if video_path else "",
        "meta_path": str(info_path) if info_path else "",
    }


def download_sets(sets_df: pd.DataFrame, force: bool = False) -> pd.DataFrame:
    rows = []
    for _, row in sets_df.iterrows():
        rows.append(_download_one_set(row["set_id"], row["youtube_url"], force=force))
    return pd.DataFrame(rows)
