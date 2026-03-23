import pandas as pd
from data_pipeline.processing.merge_datasets import merge_datasets


def test_merge_datasets():
    kaggle_df = pd.DataFrame([
        {"market_hash_name": "AK-47", "min_price": 10}
    ])

    skinport_df = pd.DataFrame([
        {"market_hash_name": "AK-47", "min_price": 12}
    ])

    merged = merge_datasets(kaggle_df, skinport_df)

    assert len(merged) >= 1
    assert "market_hash_name" in merged.columns