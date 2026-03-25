from data_pipeline.ingestion.reddit import run_reddit_ingestion_from_env


def main() -> None:
    run_reddit_ingestion_from_env()


if __name__ == "__main__":
    main()
