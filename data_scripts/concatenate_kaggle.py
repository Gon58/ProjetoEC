import base64
import csv
import os

import pandas as pd


def decode_base64(encoded_str):
    try:
        return base64.b64decode(encoded_str).decode("utf-8")
    except Exception:
        return encoded_str

def process_kaggle_dataset(input_dir, output_file):
    index_file = os.path.join(input_dir, "item_index.csv")
    items_dir = os.path.join(input_dir, "items")

    if not os.path.exists(index_file):
        print(f"Index file not found: {index_file}")
        return

    df_index = pd.read_csv(index_file)

    results = []
    total_items = len(df_index)

    print(f"Processing {total_items} items...")

    for i, row in df_index.iterrows():
        base64_name = row["item_hash_name_base64"]
        file_name = row["file_name"]

        market_hash_name = decode_base64(base64_name)
        item_path = os.path.join(items_dir, file_name)

        if os.path.exists(item_path):
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
            except Exception as e:
                print(f"Error processing {file_name}: {e}")

        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1}/{total_items} items...")

    df_result = pd.DataFrame(results)
    df_result.to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"Successfully created {output_file} with {len(df_result)} rows.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    KAGGLE_DIR = os.path.join(script_dir, "kaggle_dataset")
    OUTPUT_CSV = os.path.join(KAGGLE_DIR, "concatenated_kaggle_items.csv")

    process_kaggle_dataset(KAGGLE_DIR, OUTPUT_CSV)
