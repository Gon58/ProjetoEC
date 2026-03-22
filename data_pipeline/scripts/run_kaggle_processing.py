from pathlib import Path
from data_pipeline.processing.kaggle_processor import (
    process_kaggle_dataset,
    save_processed_kaggle,
)
from data_pipeline.loaders.ingestion_logger import log_ingestion_event

base_dir = Path(__file__).resolve().parents[1]


def main():
    base_dir = Path(__file__).resolve().parents[1]
    kaggle_dir = base_dir / "data" / "raw" / "kaggle_dataset"
    output_file = base_dir / "data" / "processed" / "concatenated_kaggle_items.csv"

    try:
        df = process_kaggle_dataset(str(kaggle_dir))
        save_processed_kaggle(df, str(output_file))

        log_ingestion_event(
            source="kaggle",
            event_type="ingestion_run",
            description=f"Processed Kaggle dataset and wrote {len(df)} rows to CSV.",
            status="success",
            records_count=len(df),
            details={"input_dir": str(kaggle_dir), "output_file": str(output_file)},
        )

        print(f"Saved processed Kaggle dataset with {len(df)} rows to {output_file}")
    except Exception as exc:
        log_ingestion_event(
            source="kaggle",
            event_type="ingestion_run",
            description="Kaggle processing failed while generating processed CSV.",
            status="error",
            records_count=0,
            error_message=str(exc),
            details={"input_dir": str(kaggle_dir), "output_file": str(output_file)},
        )
        raise


if __name__ == "__main__":
    main()
