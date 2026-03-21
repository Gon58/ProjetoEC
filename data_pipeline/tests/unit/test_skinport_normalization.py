from data_pipeline.ingestion.skinport import normalize_items


def test_normalize_skinport_items():
    raw = [
        {
            "market_hash_name": "AK-47 | Redline",
            "currency": "USD",
            "min_price": 10,
            "max_price": 20,
            "mean_price": 15,
            "median_price": 14,
            "quantity": 100,
        }
    ]

    result = normalize_items(raw)

    assert len(result) == 1
    item = result[0]

    assert item["market_hash_name"] == "AK-47 | Redline"
    assert item["quantity_sold"] == 100