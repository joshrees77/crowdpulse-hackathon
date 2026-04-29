from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from .crowd import analyze_all_sets
from .ingest import download_sets
from .io_utils import load_sets_csv
from .settings import INPUT_DIR, RAW_META_DIR, TRENDING_DJ_PATH, ensure_dirs
from .tracks import parse_and_map_tracks_for_all
from .trends import discover_trending_djs


def run_discovery_only() -> pd.DataFrame:
    return discover_trending_djs()


def _extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.strip("/").split("/")[0] or "unknown"
    q = parse_qs(parsed.query)
    if "v" in q and q["v"]:
        return q["v"][0]
    parts = [p for p in parsed.path.split("/") if p]
    return parts[-1] if parts else "unknown"


def _load_info_json_for_set(set_id: str) -> dict:
    direct = RAW_META_DIR / f"{set_id}.info.json"
    if direct.exists():
        try:
            return json.loads(direct.read_text(encoding="utf-8"))
        except Exception:
            return {}

    for candidate in RAW_META_DIR.glob(f"*{set_id}*.info.json"):
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def _is_generic_title(value: str) -> bool:
    v = value.strip().lower()
    if not v:
        return True
    if v.startswith("set "):
        return True
    return False


def _dj_from_yt_title(title: str) -> str:
    if "|" in title:
        return title.split("|", 1)[0].strip()
    return title.strip()


def enrich_set_labels_from_metadata(sets_df: pd.DataFrame) -> pd.DataFrame:
    """
    Improve dj_name/set_title using downloaded yt-dlp metadata.
    """
    out = sets_df.copy()
    for idx, row in out.iterrows():
        info = _load_info_json_for_set(str(row["set_id"]))
        if not info:
            continue

        yt_title = str(info.get("title") or "").strip()
        dj_guess = _dj_from_yt_title(yt_title) if yt_title else ""

        current_dj = str(row["dj_name"]).strip()
        current_title = str(row["set_title"]).strip()

        if (not current_dj or current_dj.lower() == "unknown dj") and dj_guess:
            out.at[idx, "dj_name"] = dj_guess

        # Prefer true YouTube title if current title is generic placeholder.
        if _is_generic_title(current_title) and yt_title:
            out.at[idx, "set_title"] = yt_title

    return out


def build_top_sets_from_trends(
    top_n: int = 10,
    output_path: Path | None = None,
    exclude_generic_boiler_room: bool = True,
) -> pd.DataFrame:
    """
    Build a sets CSV from trending DJ rows and save it for downloading/analysis.
    """
    ensure_dirs()

    trends_path = TRENDING_DJ_PATH
    if not trends_path.exists():
        discover_trending_djs()

    trends_df = pd.read_csv(trends_path)
    trends_df = trends_df[trends_df["sample_url"].astype(str).str.len() > 0].copy()

    if exclude_generic_boiler_room:
        trends_df = trends_df[trends_df["dj_name"].astype(str).str.lower() != "boiler room"]

    trends_df = trends_df.sort_values("trending_score", ascending=False)

    out_rows = []
    seen_urls: set[str] = set()
    for _, row in trends_df.iterrows():
        url = str(row["sample_url"]).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        video_id = _extract_video_id(url)
        dj = str(row["dj_name"]).strip() or "Unknown DJ"
        out_rows.append(
            {
                "set_id": f"set_{video_id}",
                "dj_name": dj,
                "set_title": f"{dj} Boiler Room Set",
                "youtube_url": url,
            }
        )
        if len(out_rows) >= top_n:
            break

    sets_df = pd.DataFrame(out_rows, columns=["set_id", "dj_name", "set_title", "youtube_url"])
    path = output_path or (INPUT_DIR / "sets.csv")
    sets_df.to_csv(path, index=False)
    return sets_df


def run_full_pipeline(
    sets_csv_path: Path | None = None,
    interval_seconds: int = 10,
    force_download: bool = False,
    run_discovery: bool = True,
) -> dict:
    ensure_dirs()

    if run_discovery:
        try:
            discover_trending_djs()
        except Exception as exc:
            print(f"[warn] Trend discovery failed, continuing without it: {exc}")

    sets_path = sets_csv_path or (INPUT_DIR / "sets.csv")
    sets_df = load_sets_csv(sets_path)

    downloads_df = download_sets(sets_df, force=force_download)
    sets_df = enrich_set_labels_from_metadata(sets_df)
    sets_df.to_csv(sets_path, index=False)

    scores_df, peaks_df, summary_df = analyze_all_sets(
        downloads_df=downloads_df,
        set_metadata_df=sets_df,
        interval_seconds=interval_seconds,
    )

    set_ids = [row["set_id"] for _, row in downloads_df.iterrows() if row.get("status") != "error"]
    parse_and_map_tracks_for_all(set_ids)

    return {
        "sets": sets_df,
        "downloads": downloads_df,
        "scores": scores_df,
        "peaks": peaks_df,
        "summary": summary_df,
    }
