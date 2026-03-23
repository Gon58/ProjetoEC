import os
import time
from typing import Dict, List, Tuple

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DEFAULT_KEYWORDS = [
    "skin", "market", "case", "knife", "trade", "price", "sticker", "float", "key",
    "wear", "pattern", "buff", "investment", "stattrak", "fn", "mw", "ft", "ww", "bs",
    "fade", "doppler", "souvenir",
]


def get_mongo_client() -> MongoClient:
    mongo_host = os.getenv("MONGO_HOST", "ec-project-mongo")
    return MongoClient(host=mongo_host, port=27017)


def fetch_reviews(
    appid: int,
    cursor: str = "*",
    day_range: int = 30,
    num_per_page: int = 100,
    timeout: int = 10,
) -> Dict:
    url = f"https://store.steampowered.com/appreviews/{appid}"
    params = {
        "json": 1,
        "filter": "all",
        "language": "english",
        "cursor": cursor,
        "num_per_page": num_per_page,
        "purchase_type": "all",
        "day_range": day_range,
    }

    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def is_market_related(review_text: str, keywords: List[str] = DEFAULT_KEYWORDS) -> bool:
    text = (review_text or "").lower()
    return any(keyword in text for keyword in keywords)


def classify_reviews(reviews: List[Dict]) -> Tuple[List[Dict], int]:
    processed_reviews = []
    relevant_count = 0

    for review in reviews:
        review_copy = dict(review)
        review_copy["is_market_related"] = is_market_related(review_copy.get("review", ""))
        review_copy["source"] = "steam_reviews_api"

        if review_copy["is_market_related"]:
            relevant_count += 1

        processed_reviews.append(review_copy)

    return processed_reviews, relevant_count


def save_reviews_to_mongo(reviews: List[Dict], mongo_db: str = None) -> None:
    if not reviews:
        return

    mongo_db = mongo_db or os.getenv("MONGO_DB", "ec_project")

    client = get_mongo_client()
    db = client[mongo_db]
    collection = db["steam_reviews"]

    for doc in reviews:
        collection.update_one(
            {"recommendationid": doc["recommendationid"]},
            {"$set": doc},
            upsert=True,
        )


def log_ingestion_run(appid: int, total: int, relevant: int, status: str = "success") -> None:
    mongo_db = os.getenv("MONGO_DB", "ec_project")

    client = get_mongo_client()
    db = client[mongo_db]
    logs_collection = db["system_logs"]

    logs_collection.insert_one(
        {
            "event": "ingestion_run",
            "appid": appid,
            "records_reached": total,
            "relevant": relevant,
            "status": status,
            "timestamp": time.time(),
        }
    )


def run_ingestion(appid: int, target_total: int = 55000, sleep_sec: float = 1.5) -> Tuple[int, int]:
    cursor = "*"
    total = 0
    relevant = 0

    while total < target_total:
        data = fetch_reviews(appid, cursor)

        if data.get("success") != 1 or not data.get("reviews"):
            break

        cursor = data.get("cursor", cursor)
        fetched_reviews = data["reviews"]

        processed_reviews, relevant_in_batch = classify_reviews(fetched_reviews)
        save_reviews_to_mongo(processed_reviews)

        total += len(processed_reviews)
        relevant += relevant_in_batch

        time.sleep(sleep_sec)

    log_ingestion_run(appid=appid, total=total, relevant=relevant)
    return total, relevant