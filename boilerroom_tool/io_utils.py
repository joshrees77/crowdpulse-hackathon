from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REQUIRED_SET_COLUMNS = ["set_id", "dj_name", "set_title", "youtube_url"]


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "set"


def parse_timestamp_to_seconds(text: str) -> int | None:
    """Parse MM:SS or HH:MM:SS into integer seconds."""
    raw = text.strip()
    if not raw:
        return None

    parts = raw.split(":")
    if len(parts) not in (2, 3):
        return None
    if not all(p.isdigit() for p in parts):
        return None

    nums = [int(p) for p in parts]
    if len(nums) == 2:
        mm, ss = nums
        return mm * 60 + ss

    hh, mm, ss = nums
    return hh * 3600 + mm * 60 + ss


def seconds_to_hms(total_seconds: float | int) -> str:
    sec = int(total_seconds)
    hh = sec // 3600
    mm = (sec % 3600) // 60
    ss = sec % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def load_sets_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing sets file: {path}")

    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_SET_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "sets.csv missing required columns: " + ", ".join(missing)
        )

    out = df[REQUIRED_SET_COLUMNS].copy()
    for col in REQUIRED_SET_COLUMNS:
        out[col] = out[col].fillna("").astype(str).str.strip()

    for idx, row in out.iterrows():
        if not row["set_id"]:
            out.at[idx, "set_id"] = slugify(f"{row['dj_name']}-{row['set_title']}")

    invalid = out[(out["youtube_url"] == "") | (out["set_id"] == "")]
    if not invalid.empty:
        raise ValueError("Some rows are missing set_id or youtube_url")

    return out
