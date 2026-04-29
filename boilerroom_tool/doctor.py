from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from .settings import PEAKS_DIR, SCORES_DIR, SET_SUMMARY_PATH, TRACKS_DIR


def _exists_label(path: Path) -> str:
    return "ok" if path.exists() else "missing"


def _command_label(name: str) -> str:
    return "ok" if shutil.which(name) else "missing"


def build_doctor_report() -> str:
    lines = ["CrowdPulse doctor report:"]
    lines.append(f"- ffmpeg: {_command_label('ffmpeg')}")
    lines.append(f"- yt-dlp: {_command_label('yt-dlp')}")
    lines.append(f"- set_summary.csv: {_exists_label(SET_SUMMARY_PATH)}")

    if SET_SUMMARY_PATH.exists():
        summary = pd.read_csv(SET_SUMMARY_PATH)
        lines.append(f"- analyzed sets: {len(summary)}")
    else:
        summary = pd.DataFrame()
        lines.append("- analyzed sets: 0")

    score_count = len(list(SCORES_DIR.glob("set_*_scores.csv")))
    moment_count = len(list(PEAKS_DIR.glob("set_*_moments.csv")))
    track_files = list(TRACKS_DIR.glob("set_*_tracks.csv"))
    lines.append(f"- score files: {score_count}")
    lines.append(f"- moment files: {moment_count}")
    lines.append(f"- track files: {len(track_files)}")

    identified_sets = 0
    total_tracks = 0
    for path in track_files:
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        total_tracks += len(df)
        if len(df) > 0:
            identified_sets += 1
    lines.append(f"- sets with identified tracks: {identified_sets}")
    lines.append(f"- identified track rows: {total_tracks}")

    if not summary.empty and score_count >= len(summary) and moment_count >= len(summary):
        lines.append("- status: ready for demo")
    else:
        lines.append("- status: refresh recommended")

    return "\n".join(lines)
