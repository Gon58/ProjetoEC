import os
import time

import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_required_int_env(name: str) -> int:
    value = _get_required_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got: {value}") from exc


def _get_required_list_env(name: str) -> list[str]:
    value = _get_required_env(name)
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise ValueError(f"Environment variable {name} must contain at least one value")
    return items


def _build_mongo_client(mongo_port: int) -> MongoClient:
    primary_host = _get_required_env("MONGO_HOST")
    fallback_host = os.getenv("MONGO_HOST_FALLBACK")

    client = MongoClient(host=primary_host, port=mongo_port, serverSelectionTimeoutMS=5000)

    try:
        client.admin.command("ping")
        return client
    except ServerSelectionTimeoutError:
        client.close()
        if not fallback_host:
            raise

        print(
            f"Could not connect to Mongo host '{primary_host}'. "
            f"Trying fallback host '{fallback_host}'."
        )
        fallback_client = MongoClient(
            host=fallback_host,
            port=mongo_port,
            serverSelectionTimeoutMS=5000,
        )
        fallback_client.admin.command("ping")
        return fallback_client


def scrape_reddit_json(
    subreddit: str,
    target_documents: int = 1000,
    collection_name: str = "reddit_posts",
) -> None:
    """
    Scrapes subreddit posts from Reddit public JSON endpoint with pagination.
    Requires a custom User-Agent to avoid HTTP 429 Too Many Requests errors.
    """
    mongo_port = int(_get_required_env("MONGO_PORT"))
    mongo_db = _get_required_env("MONGO_DB")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    client = _build_mongo_client(mongo_port=mongo_port)
    db = client[mongo_db]
    collection = db[collection_name]

    after = None
    valid_processed = 0
    inserted_count = 0
    updated_count = 0

    while valid_processed < target_documents:
        remaining = target_documents - valid_processed
        page_limit = min(100, remaining)
        params = {"limit": page_limit}
        if after:
            params["after"] = after

        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 429:
            print(f"Rate limited on r/{subreddit}. Waiting 2 seconds and retrying...")
            time.sleep(2)
            continue

        if response.status_code != 200:
            print(f"Failed to fetch data from r/{subreddit}: {response.status_code}")
            break

        data = response.json().get("data", {})
        posts = data.get("children", [])
        after = data.get("after")

        if not posts:
            break

        page_valid = 0
        page_inserted = 0
        page_updated = 0

        for post in posts:
            post_data = post["data"]

            if not post_data.get("selftext"):
                continue

            document = {
                "post_id": post_data.get("id"),
                "title": post_data.get("title"),
                "selftext": post_data.get("selftext"),
                "subreddit": post_data.get("subreddit"),
                "created_utc": post_data.get("created_utc"),
                "url": post_data.get("url"),
                "source": "reddit_json_scraper",
            }

            result = collection.update_one(
                {"post_id": document["post_id"]},
                {"$set": document},
                upsert=True,
            )

            valid_processed += 1
            page_valid += 1

            if result.upserted_id:
                inserted_count += 1
                page_inserted += 1
            elif result.modified_count > 0:
                updated_count += 1
                page_updated += 1

            if valid_processed >= target_documents:
                break

        print(
            f"r/{subreddit}: processed_valid={valid_processed}/{target_documents} "
            f"(page_valid={page_valid}, page_inserted={page_inserted}, page_updated={page_updated})"
        )

        if after is None:
            break

        time.sleep(0.8)

    print(
        f"Completed r/{subreddit} in '{collection_name}': processed_valid={valid_processed}, "
        f"inserted={inserted_count}, updated={updated_count}."
    )
    client.close()


def run_reddit_ingestion_from_env() -> None:
    target_subreddits = _get_required_list_env("REDDIT_SUBREDDITS")
    reddit_target_documents = _get_required_int_env("REDDIT_TARGET_DOCUMENTS")
    reddit_collection = _get_required_env("REDDIT_COLLECTION")

    for sub in target_subreddits:
        print(f"Starting ingestion for r/{sub}...")
        scrape_reddit_json(
            subreddit=sub,
            target_documents=reddit_target_documents,
            collection_name=reddit_collection,
        )

if __name__ == "__main__":
    run_reddit_ingestion_from_env()