from pathlib import Path
from data_pipeline.processing.kaggle_processor import (
    process_kaggle_dataset,
    save_processed_kaggle,
)

base_dir = Path(__file__).resolve().parents[1]


def main():
    base_dir = Path(__file__).resolve().parents[1]
    kaggle_dir = base_dir / "data" / "raw" / "kaggle_dataset"
    output_file = base_dir / "data" / "processed" / "concatenated_kaggle_items.csv"

    df = process_kaggle_dataset(str(kaggle_dir))
    save_processed_kaggle(df, str(output_file))
    print(f"Saved processed Kaggle dataset with {len(df)} rows to {output_file}")


if __name__ == "__main__":
    main()
