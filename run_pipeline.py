from __future__ import annotations

import argparse
from pathlib import Path

from boilerroom_tool.ask import answer_question
from boilerroom_tool.doctor import build_doctor_report
from boilerroom_tool.ingest import download_sets
from boilerroom_tool.io_utils import load_sets_csv
from boilerroom_tool.pipeline import (
    build_top_sets_from_trends,
    enrich_set_labels_from_metadata,
    run_discovery_only,
    run_full_pipeline,
)
from boilerroom_tool.settings import INPUT_DIR
from boilerroom_tool.tracks import parse_and_map_tracks_for_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boiler Room crowd analytics pipeline")

    sub = parser.add_subparsers(dest="cmd", required=True)

    ask = sub.add_parser("ask", help="Answer a natural-language question from processed analysis outputs")
    ask.add_argument("question", nargs="+", help="Question to answer")
    ask.add_argument("--top-n", type=int, default=10, help="Number of rows to include where relevant")

    sub.add_parser("doctor", help="Check dependencies and processed output coverage")

    sub.add_parser("discover", help="Discover trending DJs from YouTube+Reddit")
    top = sub.add_parser("prepare-top10", help="Build sets CSV from top trending DJ set URLs")
    top.add_argument("--top-n", type=int, default=10, help="Number of sets to include")
    top.add_argument(
        "--output",
        default=str(INPUT_DIR / "sets.csv"),
        help="Output CSV path",
    )
    top.add_argument(
        "--include-generic-boiler-room",
        action="store_true",
        help="Include generic 'Boiler Room' entity if present in trends",
    )

    dl = sub.add_parser("download", help="Download sets listed in CSV without running analysis")
    dl.add_argument(
        "--sets-csv",
        default=str(INPUT_DIR / "sets.csv"),
        help="Path to sets CSV with set_id,dj_name,set_title,youtube_url",
    )
    dl.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if local files exist",
    )

    trk = sub.add_parser(
        "refresh-tracks",
        help="Rebuild track timelines and remap peak/low moments (includes audio fingerprint fallback)",
    )
    trk.add_argument(
        "--sets-csv",
        default=str(INPUT_DIR / "sets.csv"),
        help="Path to sets CSV with set_id,dj_name,set_title,youtube_url",
    )

    refresh = sub.add_parser(
        "refresh-top10",
        help="Discover trends, rebuild top sets list, download, and analyze in one run",
    )
    refresh.add_argument("--top-n", type=int, default=10, help="Number of sets to include")
    refresh.add_argument(
        "--sets-csv",
        default=str(INPUT_DIR / "sets.csv"),
        help="Path to write/read sets CSV",
    )
    refresh.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Crowd scoring interval in seconds",
    )
    refresh.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if local files exist",
    )
    refresh.add_argument(
        "--include-generic-boiler-room",
        action="store_true",
        help="Include generic 'Boiler Room' entity if present in trends",
    )

    full = sub.add_parser("run", help="Run full pipeline")
    full.add_argument(
        "--sets-csv",
        default=str(INPUT_DIR / "sets.csv"),
        help="Path to sets CSV with set_id,dj_name,set_title,youtube_url",
    )
    full.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Crowd scoring interval in seconds",
    )
    full.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if local files exist",
    )
    full.add_argument(
        "--skip-discovery",
        action="store_true",
        help="Skip trend discovery step",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.cmd == "discover":
        df = run_discovery_only()
        print(df.head(15).to_string(index=False))
        return

    if args.cmd == "ask":
        print(answer_question(" ".join(args.question), top_n=args.top_n))
        return

    if args.cmd == "doctor":
        print(build_doctor_report())
        return

    if args.cmd == "prepare-top10":
        df = build_top_sets_from_trends(
            top_n=args.top_n,
            output_path=Path(args.output),
            exclude_generic_boiler_room=not args.include_generic_boiler_room,
        )
        print(df.to_string(index=False))
        print(f"\nWrote {len(df)} rows to {Path(args.output).resolve()}")
        return

    if args.cmd == "download":
        sets_path = Path(args.sets_csv)
        sets_df = load_sets_csv(sets_path)
        dl_df = download_sets(sets_df, force=args.force_download)
        sets_df = enrich_set_labels_from_metadata(sets_df)
        sets_df.to_csv(sets_path, index=False)
        print(dl_df.to_string(index=False))
        return

    if args.cmd == "refresh-top10":
        sets_path = Path(args.sets_csv)
        run_discovery_only()
        build_top_sets_from_trends(
            top_n=args.top_n,
            output_path=sets_path,
            exclude_generic_boiler_room=not args.include_generic_boiler_room,
        )
        result = run_full_pipeline(
            sets_csv_path=sets_path,
            interval_seconds=args.interval,
            force_download=args.force_download,
            run_discovery=False,
        )
        print("\nRefresh complete.")
        print(f"Sets loaded: {len(result['sets'])}")
        print(f"Downloads attempted: {len(result['downloads'])}")
        if not result["summary"].empty:
            print("\nSet summary:")
            print(result["summary"].to_string(index=False))
        return

    if args.cmd == "refresh-tracks":
        sets_df = load_sets_csv(Path(args.sets_csv))
        parse_and_map_tracks_for_all(sets_df["set_id"].tolist())
        print(f"Track timelines refreshed for {len(sets_df)} sets")
        return

    result = run_full_pipeline(
        sets_csv_path=Path(args.sets_csv),
        interval_seconds=args.interval,
        force_download=args.force_download,
        run_discovery=not args.skip_discovery,
    )

    print("\nPipeline complete.")
    print(f"Sets loaded: {len(result['sets'])}")
    print(f"Downloads attempted: {len(result['downloads'])}")
    if not result["summary"].empty:
        print("\nSet summary:")
        print(result["summary"].to_string(index=False))


if __name__ == "__main__":
    main()
