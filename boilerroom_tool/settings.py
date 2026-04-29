from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

INPUT_DIR = DATA_DIR / "input"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_VIDEO_DIR = RAW_DIR / "videos"
RAW_META_DIR = RAW_DIR / "meta"

SCORES_DIR = PROCESSED_DIR / "scores"
TRACKS_DIR = PROCESSED_DIR / "tracks"
PEAKS_DIR = PROCESSED_DIR / "peaks"
TRENDS_DIR = PROCESSED_DIR / "trends"

SET_SUMMARY_PATH = PROCESSED_DIR / "set_summary.csv"
TRENDING_DJ_PATH = TRENDS_DIR / "trending_djs.csv"


def ensure_dirs() -> None:
    """Create all required local directories."""
    for path in [
        INPUT_DIR,
        RAW_VIDEO_DIR,
        RAW_META_DIR,
        SCORES_DIR,
        TRACKS_DIR,
        PEAKS_DIR,
        TRENDS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
