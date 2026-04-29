from __future__ import annotations

import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests

from .settings import TRENDING_DJ_PATH, ensure_dirs

DEFAULT_REDDIT_SUBS = [
    "electronicmusic",
    "DJs",
    "Techno",
    "house",
    "EDM",
    "BoilerRoom",
]


def _guess_dj_name(title: str, uploader: str | None = None) -> str:
    text = re.sub(r"\s+", " ", title).strip()

    patterns = [
        r"^(.+?)\s*[\|\-]\s*Boiler Room",
        r"^Boiler Room.*?:\s*(.+)$",
        r"^(.+?)\s*\(.*Boiler Room.*\)$",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" -|:")
            if candidate:
                return candidate

    if "|" in text:
        left = text.split("|", 1)[0].strip()
        if left and len(left) <= 50:
            return left

    if uploader:
        return uploader.strip()

    return text[:50]


def _youtube_search_candidates(query: str, max_results: int) -> pd.DataFrame:
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json",
        "--skip-download",
        "--quiet",
        "--ignore-errors",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp search failed: {proc.stderr.strip()}")

    rows: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        title = payload.get("title") or ""
        uploader = payload.get("uploader") or ""
        dj_guess = _guess_dj_name(title, uploader)

        rows.append(
            {
                "title": title,
                "uploader": uploader,
                "url": payload.get("webpage_url") or payload.get("url") or "",
                "view_count": int(payload.get("view_count") or 0),
                "upload_date": payload.get("upload_date") or "",
                "dj_name": dj_guess,
            }
        )

    return pd.DataFrame(rows)


def _reddit_mentions_for_djs(dj_names: list[str], window: str = "month") -> pd.DataFrame:
    """Fetch rough Reddit mention stats for each DJ via public Reddit search JSON."""
    headers = {"User-Agent": "boilerroom-hackathon-mvp/0.1"}
    session = requests.Session()

    rows: list[dict] = []
    for dj in dj_names:
        total_posts = 0
        engagement = 0

        for sub in DEFAULT_REDDIT_SUBS:
            query = f'"{dj}" "boiler room" subreddit:{sub}'
            params = {
                "q": query,
                "restrict_sr": "false",
                "sort": "new",
                "t": window,
                "limit": 50,
            }
            try:
                resp = session.get(
                    "https://www.reddit.com/search.json",
                    params=params,
                    headers=headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue

            posts = data.get("data", {}).get("children", [])
            total_posts += len(posts)
            for item in posts:
                post = item.get("data", {})
                engagement += int(post.get("score", 0)) + int(post.get("num_comments", 0))

        rows.append(
            {
                "dj_name": dj,
                "reddit_posts": total_posts,
                "reddit_engagement": engagement,
            }
        )

    return pd.DataFrame(rows)


def discover_trending_djs(
    query: str = "boiler room set",
    max_results: int = 60,
    reddit_window: str = "month",
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Discover trending DJs from YouTube search + Reddit mentions.

    This is a lightweight heuristic suitable for a hackathon MVP.
    """
    ensure_dirs()

    try:
        yt_df = _youtube_search_candidates(query=query, max_results=max_results)
    except Exception:
        yt_df = pd.DataFrame()

    if yt_df.empty:
        if output_path and output_path.exists():
            return pd.read_csv(output_path)
        if TRENDING_DJ_PATH.exists():
            return pd.read_csv(TRENDING_DJ_PATH)
        return pd.DataFrame(
            columns=[
                "rank",
                "dj_name",
                "trending_score",
                "youtube_hits",
                "youtube_total_views",
                "reddit_posts",
                "reddit_engagement",
                "sample_url",
            ]
        )

    grouped = (
        yt_df.groupby("dj_name", dropna=False)
        .agg(
            youtube_hits=("dj_name", "count"),
            youtube_total_views=("view_count", "sum"),
            sample_url=("url", "first"),
        )
        .reset_index()
    )

    top_djs = grouped.sort_values("youtube_hits", ascending=False).head(25)["dj_name"].tolist()
    reddit_df = _reddit_mentions_for_djs(top_djs, window=reddit_window)

    merged = grouped.merge(reddit_df, on="dj_name", how="left").fillna(0)
    merged["reddit_posts"] = merged["reddit_posts"].astype(int)
    merged["reddit_engagement"] = merged["reddit_engagement"].astype(int)

    max_hits = max(int(merged["youtube_hits"].max()), 1)
    max_views = max(int(merged["youtube_total_views"].max()), 1)
    max_reddit = max(int(merged["reddit_engagement"].max()), 1)

    merged["youtube_hits_norm"] = merged["youtube_hits"] / max_hits
    merged["youtube_views_norm"] = merged["youtube_total_views"] / max_views
    merged["reddit_norm"] = merged["reddit_engagement"] / max_reddit

    merged["trending_score"] = (
        0.45 * merged["youtube_hits_norm"]
        + 0.35 * merged["youtube_views_norm"]
        + 0.20 * merged["reddit_norm"]
    )

    merged = merged.sort_values("trending_score", ascending=False).reset_index(drop=True)
    merged["rank"] = merged.index + 1

    path = output_path or TRENDING_DJ_PATH
    merged.to_csv(path, index=False)
    return merged
