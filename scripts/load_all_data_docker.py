from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


MAX_FULL_REVIEWS = 55000


def _run(cmd: list[str], label: str) -> None:
    print(f"\n=== {label} ===")
    print("$", " ".join(shlex.quote(part) for part in cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {label}")


def _compute_caps(max_runtime_minutes: int, full_mode: bool) -> tuple[int, int]:
    if full_mode:
        return MAX_FULL_REVIEWS, MAX_FULL_REVIEWS

    # Conservative budget to keep execution under ~30 minutes on typical local setups.
    # We reserve time for startup/build + SQL pipeline and split the remainder across
    # Steam fetch + Chroma indexing.
    budget = max(10, max_runtime_minutes)
    reserved_minutes = 10
    remaining = max(5, budget - reserved_minutes)

    # Throughput assumptions are intentionally conservative to avoid overruns.
    reviews_per_minute_fetch = 140
    reviews_per_minute_index = 30

    target_reviews = min(MAX_FULL_REVIEWS, remaining * reviews_per_minute_fetch)
    index_limit = min(target_reviews, remaining * reviews_per_minute_index)

    # Keep a useful minimum amount of data in capped mode.
    target_reviews = max(1000, int(target_reviews))
    index_limit = max(600, int(index_limit))
    index_limit = min(index_limit, target_reviews)

    return target_reviews, index_limit


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Boot docker services and load project data into Postgres, Mongo, and Chroma. "
            "Default mode caps Steam ingestion/indexing for ~30 minute runs."
        )
    )
    parser.add_argument(
        "--max-runtime-minutes",
        type=int,
        default=30,
        help="Runtime budget used to auto-cap Steam ingestion/indexing (default: 30).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Attempt full Steam ingestion/indexing (can take much longer).",
    )
    parser.add_argument(
        "--steam-appid",
        type=int,
        default=int(os.getenv("STEAM_APP_ID", "730")),
        help="Steam app id (default: STEAM_APP_ID env or 730).",
    )
    parser.add_argument(
        "--steam-target-total",
        type=int,
        default=None,
        help="Override target number of Steam reviews to ingest.",
    )
    parser.add_argument(
        "--index-limit",
        type=int,
        default=None,
        help="Override number of reviews to index into Chroma.",
    )
    parser.add_argument(
        "--steam-sleep-sec",
        type=float,
        default=1.0,
        help="Sleep between Steam API requests in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip docker compose build for test containers.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    if args.max_runtime_minutes <= 0:
        raise SystemExit("--max-runtime-minutes must be > 0")

    if args.steam_sleep_sec < 0:
        raise SystemExit("--steam-sleep-sec must be >= 0")

    auto_target, auto_index = _compute_caps(args.max_runtime_minutes, args.full)
    steam_target_total = args.steam_target_total or auto_target
    index_limit = args.index_limit or auto_index

    if steam_target_total <= 0:
        raise SystemExit("steam target total must be > 0")

    if index_limit <= 0:
        raise SystemExit("index limit must be > 0")

    print("\nPlan:")
    print(f"- steam_target_total={steam_target_total}")
    print(f"- index_limit={index_limit}")
    print(f"- steam_appid={args.steam_appid}")
    print(f"- full_mode={args.full}")

    _run(
        [
            "docker",
            "compose",
            "up",
            "-d",
            "ec-project-postgres",
            "ec-project-mongo",
            "ec-project-chroma",
            "ec-project-ollama",
        ],
        "Starting Docker services",
    )

    if not args.skip_build:
        _run(
            [
                "docker",
                "compose",
                "build",
                "ec-project-tests",
                "ec-project-backend-tests",
            ],
            "Building data-loader containers",
        )

    _run(
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "ec-project-tests",
            "python",
            "data_pipeline/scripts/run_full_pipeline.py",
        ],
        "Loading structured data into PostgreSQL",
    )

    _run(
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "ec-project-tests",
            "python",
            "data_pipeline/scripts/run_steam_reviews_ingestion.py",
            "--appid",
            str(args.steam_appid),
            "--target-total",
            str(steam_target_total),
            "--sleep-sec",
            str(args.steam_sleep_sec),
        ],
        "Loading Steam reviews into MongoDB",
    )

    _run(
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "ec-project-backend-tests",
            "python",
            "backend/scripts/index_steam_reviews_to_chroma.py",
            "--limit",
            str(index_limit),
            "--collection",
            "steam_reviews",
        ],
        "Indexing reviews into ChromaDB",
    )

    print("\nDone. Docker services are up and data load steps completed.")


if __name__ == "__main__":
    main()
