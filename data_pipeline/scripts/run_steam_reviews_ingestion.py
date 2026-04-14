from __future__ import annotations

import argparse
import os

from data_pipeline.ingestion.steam_reviews import run_ingestion


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Steam app reviews into MongoDB for market-context RAG."
    )
    parser.add_argument(
        "--appid",
        type=int,
        default=int(os.getenv("STEAM_APP_ID", "730")),
        help="Steam app id (default: STEAM_APP_ID env or 730).",
    )
    parser.add_argument(
        "--target-total",
        type=int,
        default=55000,
        help="Target number of reviews to fetch.",
    )
    parser.add_argument(
        "--sleep-sec",
        type=float,
        default=1.0,
        help="Sleep between Steam API requests in seconds.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.target_total <= 0:
        raise SystemExit("--target-total must be > 0")

    if args.sleep_sec < 0:
        raise SystemExit("--sleep-sec must be >= 0")

    total, relevant = run_ingestion(
        appid=args.appid,
        target_total=args.target_total,
        sleep_sec=args.sleep_sec,
    )

    print(
        "Steam reviews ingestion finished: "
        f"appid={args.appid} total={total} relevant={relevant}"
    )


if __name__ == "__main__":
    main()
