from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from .audio_fingerprint import fingerprint_tracks_for_set
from .io_utils import parse_timestamp_to_seconds, seconds_to_hms
from .settings import INPUT_DIR, PEAKS_DIR, RAW_META_DIR, TRACKS_DIR, ensure_dirs

TIMESTAMP_LINE_RE = re.compile(
    r"\b(?P<ts>(?:\d{1,2}:)?\d{1,2}:\d{2})\b\s*[-–—|:]?\s*(?P<track>.+)"
)

SOURCE_PRIORITY = {
    "description_timestamp": 1,
    "audio_fingerprint": 2,
    "youtube_chapter": 3,
    "manual_override": 4,
}

TRACK_COLS = [
    "set_id",
    "start_sec",
    "timestamp",
    "track",
    "source",
    "confidence",
]

MANUAL_OVERRIDE_PATH = INPUT_DIR / "manual_track_overrides.csv"
DUPLICATE_TRACK_WINDOW_SEC = 20 * 60


def _empty_tracks_df() -> pd.DataFrame:
    return pd.DataFrame(columns=TRACK_COLS)


def _canonical_track_key(track_name: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9]+", " ", str(track_name).lower()).strip()
    return re.sub(r"\s+", " ", key)


def _dedupe_nearby_tracks(df: pd.DataFrame, window_sec: int = DUPLICATE_TRACK_WINDOW_SEC) -> pd.DataFrame:
    """
    Remove duplicate song labels detected too close together.

    This prevents repeated detections of the same track from sampled audio windows.
    """
    if df.empty:
        return df

    work = df.copy()
    work["track_key"] = work["track"].apply(_canonical_track_key)

    keep_idx = []
    last_seen_sec: dict[str, int] = {}
    for idx, row in work.sort_values("start_sec").iterrows():
        key = str(row["track_key"])
        t_sec = int(row["start_sec"])
        prev = last_seen_sec.get(key)
        if prev is not None and (t_sec - prev) < window_sec:
            continue
        keep_idx.append(idx)
        last_seen_sec[key] = t_sec

    out = work.loc[keep_idx].sort_values("start_sec").reset_index(drop=True)
    return out.drop(columns=["track_key"], errors="ignore")


def _load_info_json(set_id: str) -> dict:
    direct = RAW_META_DIR / f"{set_id}.info.json"
    if direct.exists():
        with direct.open("r", encoding="utf-8") as f:
            return json.load(f)

    for candidate in RAW_META_DIR.glob(f"*{set_id}*.info.json"):
        with candidate.open("r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def parse_tracks_from_chapters(set_id: str) -> pd.DataFrame:
    """Parse YouTube chapters (if available) from info.json."""
    info = _load_info_json(set_id)
    chapters = info.get("chapters") or []
    if not isinstance(chapters, list) or not chapters:
        return _empty_tracks_df()

    rows = []
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        start_time = ch.get("start_time")
        title = str(ch.get("title") or "").strip()
        if start_time is None or not title:
            continue

        sec = int(float(start_time))
        rows.append(
            {
                "set_id": set_id,
                "start_sec": sec,
                "timestamp": seconds_to_hms(sec),
                "track": title,
                "source": "youtube_chapter",
                "confidence": 0.95,
            }
        )

    if not rows:
        return _empty_tracks_df()

    out = pd.DataFrame(rows, columns=TRACK_COLS)
    return out.sort_values("start_sec").drop_duplicates("start_sec", keep="first")


def parse_tracks_from_description(set_id: str) -> pd.DataFrame:
    """
    Parse timestamps from YouTube description into a track timeline.

    Expected lines like:
      12:30 Artist - Track Name
      01:02:10 Track Name
    """
    info = _load_info_json(set_id)
    description = str(info.get("description") or "")
    lines = [ln.strip() for ln in description.splitlines() if ln.strip()]

    rows = []
    for ln in lines:
        match = TIMESTAMP_LINE_RE.search(ln)
        if not match:
            continue
        ts = match.group("ts")
        sec = parse_timestamp_to_seconds(ts)
        if sec is None:
            continue

        track = match.group("track").strip(" -|:")
        if not track:
            continue

        rows.append(
            {
                "set_id": set_id,
                "start_sec": int(sec),
                "timestamp": ts,
                "track": track,
                "source": "description_timestamp",
                "confidence": 0.65,
            }
        )

    if not rows:
        return _empty_tracks_df()

    out = pd.DataFrame(rows, columns=TRACK_COLS)
    return out.sort_values("start_sec").drop_duplicates("start_sec", keep="first")


def load_manual_track_overrides(set_id: str) -> pd.DataFrame:
    """
    Load manual override track rows from data/input/manual_track_overrides.csv.

    Expected columns:
    - set_id (optional if file only contains one set)
    - start_sec or timestamp
    - track
    """
    if not MANUAL_OVERRIDE_PATH.exists():
        return _empty_tracks_df()

    try:
        df = pd.read_csv(MANUAL_OVERRIDE_PATH)
    except Exception:
        return _empty_tracks_df()

    if df.empty or "track" not in df.columns:
        return _empty_tracks_df()

    out = df.copy()
    if "set_id" in out.columns:
        out = out[out["set_id"].fillna("").astype(str).str.strip() == set_id]
    else:
        out["set_id"] = set_id

    if out.empty:
        return _empty_tracks_df()

    if "start_sec" not in out.columns:
        out["start_sec"] = pd.NA

    if "timestamp" not in out.columns:
        out["timestamp"] = ""

    out["start_sec"] = pd.to_numeric(out["start_sec"], errors="coerce")

    missing_start = out["start_sec"].isna()
    if missing_start.any():
        out.loc[missing_start, "start_sec"] = (
            out.loc[missing_start, "timestamp"].fillna("").astype(str).apply(parse_timestamp_to_seconds)
        )

    out = out.dropna(subset=["start_sec"])
    if out.empty:
        return _empty_tracks_df()

    out["start_sec"] = out["start_sec"].astype(int)
    out["track"] = out["track"].fillna("").astype(str).str.strip()
    out = out[out["track"] != ""]

    if out.empty:
        return _empty_tracks_df()

    out["timestamp"] = out["start_sec"].apply(seconds_to_hms)
    out["source"] = "manual_override"
    out["confidence"] = 1.0

    out = out[TRACK_COLS]
    return out.sort_values("start_sec").drop_duplicates("start_sec", keep="last")


def build_track_timeline(set_id: str) -> pd.DataFrame:
    """Build best-effort track timeline from multiple sources."""
    ensure_dirs()

    desc_df = parse_tracks_from_description(set_id)
    chapter_df = parse_tracks_from_chapters(set_id)
    manual_df = load_manual_track_overrides(set_id)

    frames = [df for df in [desc_df, chapter_df, manual_df] if not df.empty]

    # Fallback to audio fingerprinting when metadata sources are missing.
    if len(desc_df) + len(chapter_df) == 0:
        fingerprint_df = fingerprint_tracks_for_set(set_id)
        if not fingerprint_df.empty:
            frames.append(fingerprint_df)

    if not frames:
        out = _empty_tracks_df()
        out.to_csv(TRACKS_DIR / f"{set_id}_tracks.csv", index=False)
        return out

    merged = pd.concat(frames, ignore_index=True)
    merged["source_priority"] = merged["source"].map(SOURCE_PRIORITY).fillna(0)
    merged = merged.sort_values(["start_sec", "source_priority", "confidence"]) 
    merged = merged.drop_duplicates("start_sec", keep="last")
    merged = merged.sort_values("start_sec").reset_index(drop=True)
    merged = _dedupe_nearby_tracks(merged)

    out = merged[TRACK_COLS]
    out.to_csv(TRACKS_DIR / f"{set_id}_tracks.csv", index=False)
    return out


def map_moments_to_tracks(set_id: str) -> pd.DataFrame:
    moments_path = PEAKS_DIR / f"{set_id}_moments.csv"
    tracks_path = TRACKS_DIR / f"{set_id}_tracks.csv"

    if not moments_path.exists():
        raise FileNotFoundError(f"Missing moments file: {moments_path}")

    moments = pd.read_csv(moments_path)
    if moments.empty:
        return moments

    if not tracks_path.exists():
        moments["track"] = "Unknown"
        moments["track_source"] = "none"
        moments["track_confidence"] = 0.0
        moments.to_csv(moments_path, index=False)
        return moments

    try:
        tracks = pd.read_csv(tracks_path)
    except EmptyDataError:
        tracks = _empty_tracks_df()

    if tracks.empty:
        moments["track"] = "Unknown"
        moments["track_source"] = "none"
        moments["track_confidence"] = 0.0
        moments.to_csv(moments_path, index=False)
        return moments

    tracks = tracks.sort_values("start_sec").reset_index(drop=True)

    def lookup_track(t_sec: float) -> tuple[str, str, float]:
        valid = tracks[tracks["start_sec"] <= t_sec]
        if valid.empty:
            return "Unknown", "none", 0.0
        row = valid.iloc[-1]
        return str(row["track"]), str(row["source"]), float(row["confidence"])

    mapped = moments["t_sec"].apply(lookup_track)
    moments["track"] = mapped.apply(lambda x: x[0])
    moments["track_source"] = mapped.apply(lambda x: x[1])
    moments["track_confidence"] = mapped.apply(lambda x: x[2])
    moments.to_csv(moments_path, index=False)
    return moments


def parse_and_map_tracks_for_all(set_ids: list[str]) -> None:
    for set_id in set_ids:
        build_track_timeline(set_id)
        map_moments_to_tracks(set_id)
