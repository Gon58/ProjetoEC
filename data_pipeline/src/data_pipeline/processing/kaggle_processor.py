import os
import csv

import pandas as pd

from ..core.utils import decode_base64


def process_kaggle_dataset(input_dir: str) -> pd.DataFrame:
    """Processa o dataset Kaggle de skins e retorna um DataFrame com agregações."""
    index_file = os.path.join(input_dir, "item_index.csv")
    items_dir = os.path.join(input_dir, "items")

    if not os.path.exists(index_file):
        raise FileNotFoundError(f"Index file not found: {index_file}")

    df_index = pd.read_csv(index_file)
    results = []

    for i, row in df_index.iterrows():
        market_hash_name = decode_base64(row.get("item_hash_name_base64", ""))
        file_name = row.get("file_name")
        item_path = os.path.join(items_dir, file_name)

        if not os.path.exists(item_path):
            continue

        try:
            df_item = pd.read_csv(item_path)
            if df_item.empty:
                continue

            prices = df_item["price_dollar"]
            sells = df_item["sells"]

            results.append(
                {
                    "market_hash_name": market_hash_name,
                    "currency": "USD",
                    "min_price": prices.min(),
                    "max_price": prices.max(),
                    "mean_price": prices.mean(),
                    "median_price": prices.median(),
                    "quantity_sold": sells.sum(),
                }
            )
        except Exception:
            continue

    return pd.DataFrame(results)


def save_processed_kaggle(df: pd.DataFrame, output_file: str) -> None:
    """Guarda o DataFrame processado em CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
