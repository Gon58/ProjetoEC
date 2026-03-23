import os

import pandas as pd


def merge_datasets(skinport_df: pd.DataFrame, kaggle_df: pd.DataFrame) -> pd.DataFrame:
    """Concatena e normaliza datasets Skinport + Kaggle."""
    return pd.concat([skinport_df, kaggle_df], ignore_index=True)


def save_merged_data(df: pd.DataFrame, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)


def load_kaggle_processed_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Kaggle processed data file not found: {path}")
    return pd.read_csv(path)


def load_skinport_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Skinport data file not found: {path}")
    return pd.read_csv(path)
