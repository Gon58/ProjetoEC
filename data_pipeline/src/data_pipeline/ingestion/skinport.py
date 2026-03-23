import requests

BASE_URL = "https://api.skinport.com/v1/items"
HEADERS = {"Accept-Encoding": "br", "User-Agent": "PythonSkinPortClient/1.0"}


def fetch_items(app_id=730, currency="USD", tradable=True, timeout=10):
    """Buscador de items Skinport (API)."""
    params = {"app_id": app_id, "currency": currency, "tradable": 1 if tradable else 0}

    res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=timeout)

    if res.status_code != 200:
        raise RuntimeError(f"Skinport API error: HTTP {res.status_code} | {res.text}")

    return res.json()


def normalize_items(items):
    """Converte items raw Skinport para registos lista/dict padrão."""
    normalized = []
    for item in items:
        normalized.append(
            {
                "market_hash_name": item.get("market_hash_name"),
                "currency": item.get("currency"),
                "min_price": item.get("min_price"),
                "max_price": item.get("max_price"),
                "mean_price": item.get("mean_price"),
                "median_price": item.get("median_price"),
                "quantity_sold": item.get("quantity"),
                "source": "skinport",
            }
        )
    return normalized
