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

    dfs = [kaggle_df]
    counts = {"kaggle": len(kaggle_df), "skinport": 0, "steam": 0}

    if skinport_file.exists():
        skinport_df = pd.read_csv(skinport_file)
        dfs.append(skinport_df)
        counts["skinport"] = len(skinport_df)
    else:
        print("[WARN] skinport_items.csv not found — skipping Skinport data")

    if steam_file.exists():
        steam_df = pd.read_csv(steam_file)
        steam_df = steam_df.drop(columns=["scraped_at"], errors="ignore")
        dfs.append(steam_df)
        counts["steam"] = len(steam_df)
    else:
        print("[WARN] steam_market_prices.csv not found — skipping Steam Market data")

    merged = pd.concat(dfs, ignore_index=True)
    save_merged_data(merged, output_file)

    print(
        f"Merged {counts['kaggle']} kaggle + {counts['skinport']} skinport"
        f" + {counts['steam']} steam rows → {len(merged)} total rows"
    )


if __name__ == "__main__":
    main()
