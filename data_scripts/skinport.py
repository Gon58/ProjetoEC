import json

import requests

BASE_URL = "https://api.skinport.com/v1/items"
HEADERS = {"Accept-Encoding": "br", "User-Agent": "PythonSkinPortClient/1.0"}


def fetch_items(app_id=730, currency="USD", tradable=True):
    params = {"app_id": app_id, "currency": currency, "tradable": 1 if tradable else 0}

    res = requests.get(BASE_URL, params=params, headers=HEADERS)

    if res.status_code != 200:
        raise Exception(f"HTTP {res.status_code} | {res.text}")

    return res.json()


if __name__ == "__main__":
    items = fetch_items()
    print(f"Quantidade de items: {len(items)}")

    print("\nPrimeiros:")
    for item in items[:5]:
        print(json.dumps(item, indent=2))
