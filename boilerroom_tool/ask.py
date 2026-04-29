from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .settings import PEAKS_DIR, SET_SUMMARY_PATH, TRACKS_DIR


def _canonical(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", str(value).lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _load_summary() -> pd.DataFrame:
    if not SET_SUMMARY_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(SET_SUMMARY_PATH)


def _format_set_row(row: pd.Series) -> str:
    return (
        f"{row.get('dj_name', row.get('set_id'))} "
        f"({row.get('set_title', row.get('set_id'))}) - "
        f"avg_energy={float(row.get('avg_energy', 0)):.3f}, "
        f"max_energy={float(row.get('max_energy', 0)):.3f}"
    )


def _top_songs(top_n: int = 10) -> str:
    rows = []
    for path in sorted(PEAKS_DIR.glob("set_*_moments.csv")):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if df.empty or "track" not in df.columns:
            continue
        df = df[df["track"].fillna("Unknown") != "Unknown"].copy()
        if "moment_type" in df.columns:
            df = df[df["moment_type"] == "high"]
        if df.empty:
            continue
        rows.append(df)

    if not rows:
        return "No identified high-moment songs found yet."

    songs = pd.concat(rows, ignore_index=True)
    songs["track_key"] = songs["track"].apply(_canonical)
    agg = (
        songs.groupby("track_key", dropna=False)
        .agg(
            track=("track", lambda x: x.value_counts().index[0]),
            high_moment_hits=("track", "count"),
            set_coverage=("set_id", "nunique"),
            avg_energy=("crowd_energy_smooth", "mean"),
        )
        .sort_values(["high_moment_hits", "avg_energy"], ascending=[False, False])
        .head(top_n)
        .reset_index(drop=True)
    )

    lines = ["Top songs across high-energy moments:"]
    for idx, row in agg.iterrows():
        lines.append(
            f"{idx + 1}. {row['track']} - "
            f"{int(row['high_moment_hits'])} high moments, "
            f"{int(row['set_coverage'])} set(s), avg_energy={float(row['avg_energy']):.3f}"
        )
    return "\n".join(lines)


def _track_coverage() -> str:
    rows = []
    for path in sorted(TRACKS_DIR.glob("set_*_tracks.csv")):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        sources = "none"
        if not df.empty and "source" in df.columns:
            sources = ", ".join(sorted(df["source"].dropna().astype(str).unique()))
        rows.append((path.name.replace("_tracks.csv", ""), len(df), sources))

    if not rows:
        return "No track timeline files found."

    lines = ["Track identification coverage:"]
    for set_id, count, sources in rows:
        lines.append(f"- {set_id}: {count} track(s), source(s): {sources}")
    return "\n".join(lines)


def _compare_sets(question: str, summary: pd.DataFrame) -> str:
    q = _canonical(question)
    matches = []
    for _, row in summary.iterrows():
        haystack = " ".join(
            [
                str(row.get("set_id", "")),
                str(row.get("dj_name", "")),
                str(row.get("set_title", "")),
            ]
        )
        if _canonical(row.get("dj_name", "")) in q or _canonical(row.get("set_id", "")) in q:
            matches.append(row)
        elif any(token and token in _canonical(haystack) for token in q.split() if len(token) > 4):
            matches.append(row)

    if not matches:
        return "I could not confidently identify the sets to compare. Try naming the DJ or set_id."

    unique = pd.DataFrame(matches).drop_duplicates("set_id")
    unique = unique.sort_values("avg_energy", ascending=False)
    lines = ["Comparison:"]
    for _, row in unique.head(6).iterrows():
        lines.append(f"- {_format_set_row(row)}")
    return "\n".join(lines)


def _peak_moments(question: str, summary: pd.DataFrame, top_n: int = 5) -> str:
    q = _canonical(question)
    best = None
    for _, row in summary.iterrows():
        identifiers = [
            _canonical(row.get("set_id", "")),
            _canonical(row.get("dj_name", "")),
            _canonical(row.get("set_title", "")),
        ]
        if any(identifier and identifier in q for identifier in identifiers):
            best = row
            break

    if best is None and not summary.empty:
        best = summary.sort_values("avg_energy", ascending=False).iloc[0]

    if best is None:
        return "No set summary is available."

    path = PEAKS_DIR / f"{best['set_id']}_moments.csv"
    if not path.exists():
        return f"No peak moments file found for {best['set_id']}."

    df = pd.read_csv(path)
    if df.empty:
        return f"No peak moments found for {best['set_id']}."

    if "moment_type" in df.columns:
        df = df[df["moment_type"] == "high"]
    df = df.sort_values("crowd_energy_smooth", ascending=False).head(top_n)

    lines = [f"Top moments for {best.get('dj_name', best['set_id'])}:"]
    for _, row in df.iterrows():
        track = row.get("track", "Unknown")
        lines.append(
            f"- t={int(row['t_sec'])}s, energy={float(row['crowd_energy_smooth']):.3f}, track={track}"
        )
    return "\n".join(lines)


def answer_question(question: str, top_n: int = 10) -> str:
    summary = _load_summary()
    q = _canonical(question)

    if summary.empty:
        return "No set summary exists yet. Run the analysis pipeline first."

    if any(term in q for term in ["top song", "top songs", "best song", "songs across"]):
        return _top_songs(top_n=top_n)

    if "track coverage" in q or "identified" in q or "tracklist" in q:
        return _track_coverage()

    if "compare" in q or " vs " in f" {q} " or "versus" in q:
        return _compare_sets(question, summary)

    if "peak" in q or "moment" in q or "highest moment" in q:
        return _peak_moments(question, summary, top_n=min(top_n, 8))

    if "lowest" in q or "worst" in q or "least" in q:
        row = summary.sort_values("avg_energy", ascending=True).iloc[0]
        return f"Lowest average crowd energy: {_format_set_row(row)}"

    if "highest" in q or "best" in q or "top dj" in q or "top set" in q:
        row = summary.sort_values("avg_energy", ascending=False).iloc[0]
        return f"Highest average crowd energy: {_format_set_row(row)}"

    lines = ["CrowdPulse summary:"]
    ranked = summary.sort_values("avg_energy", ascending=False).head(top_n)
    for idx, row in ranked.iterrows():
        lines.append(f"- {_format_set_row(row)}")
    lines.append("\nTry: 'top songs across sets', 'compare Kaytranada and Fred again', or 'peak moments for Solomun'.")
    return "\n".join(lines)
