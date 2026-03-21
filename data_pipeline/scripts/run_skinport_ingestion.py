from pathlib import Path
from data_pipeline.ingestion.skinport import fetch_items, normalize_items
import pandas as pd

base_dir = Path(__file__).resolve().parents[1]


def main():
    output_dir = base_dir / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "skinport_items.csv"

    raw_items = fetch_items()
    normalized_items = normalize_items(raw_items)

    df = pd.DataFrame(normalized_items)
    df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"Saved {len(df)} skinport items to {output_file}")


if __name__ == "__main__":
    main()  