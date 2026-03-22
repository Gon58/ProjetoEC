from pathlib import Path
from data_pipeline.ingestion.skinport import fetch_items, normalize_items
from data_pipeline.loaders.ingestion_logger import log_ingestion_event
import pandas as pd

base_dir = Path(__file__).resolve().parents[1]


def main():
    output_dir = base_dir / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "skinport_items.csv"

    try:
        raw_items = fetch_items()
        normalized_items = normalize_items(raw_items)

        df = pd.DataFrame(normalized_items)
        df.to_csv(output_file, index=False, encoding="utf-8")

        log_ingestion_event(
            source="skinport",
            event_type="ingestion_run",
            description=f"Fetched and normalized {len(df)} Skinport items into CSV.",
            status="success",
            records_count=len(df),
            details={"output_file": str(output_file)},
        )

        print(f"Saved {len(df)} skinport items to {output_file}")
    except Exception as exc:
        log_ingestion_event(
            source="skinport",
            event_type="ingestion_run",
            description="Skinport ingestion failed during fetch/normalize/write.",
            status="error",
            records_count=0,
            error_message=str(exc),
            details={"output_file": str(output_file)},
        )
        raise


if __name__ == "__main__":
    main()  