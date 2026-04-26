from pathlib import Path
from data_pipeline.processing.merge_datasets import save_merged_data
import pandas as pd

base_dir = Path(__file__).resolve().parents[1]


def main():
    base_dir = Path(__file__).resolve().parents[1]
    kaggle_file = base_dir / "data" / "processed" / "concatenated_kaggle_items.csv"
    skinport_file = base_dir / "data" / "processed" / "skinport_items.csv"
    steam_file   = base_dir / "data" / "processed" / "steam_market_prices.csv"
    output_file = base_dir / "data" / "processed" / "combined_data.csv"

    kaggle_df = pd.read_csv(kaggle_file)
    skinport_df = pd.read_csv(skinport_file)
    steam_df    = pd.read_csv(steam_file)

    steam_df = steam_df.drop(columns=["scraped_at"], errors="ignore")

    merged = pd.concat([skinport_df, kaggle_df, steam_df], ignore_index=True)
    save_merged_data(merged, output_file)

    print(f"Merged {len(kaggle_df)} kaggle + {len(skinport_df)} skinport rows into {len(merged)} rows")


if __name__ == "__main__":
    main()
