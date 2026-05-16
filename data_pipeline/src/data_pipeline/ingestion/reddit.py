import os
import time
from typing import Any

import requests
from dotenv import load_dotenv
from pymongo import ASCENDING
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

load_dotenv()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 ProjetoEC/1.0"
)
DEFAULT_REDDIT_BASE_URLS = [
    "https://www.reddit.com",
    "https://old.reddit.com",
]


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_optional_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _get_required_int_env(name: str) -> int:
    value = _get_required_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got: {value}") from exc


def _get_optional_int_env(name: str, default: int) -> int:
    value = _get_optional_env(name)
    if value is None:
        return default
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


def _get_optional_list_env(name: str, default: list[str]) -> list[str]:
    value = _get_optional_env(name)
    if value is None:
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


def _get_optional_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"Environment variable {name} must be a boolean value, got: {value}")


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


def _ensure_post_indexes(collection) -> None:
    collection.create_index([("post_id", ASCENDING)], unique=True, name="ux_reddit_post_id")


def _ensure_comment_indexes(collection) -> None:
    collection.create_index([("comment_id", ASCENDING)], unique=True, name="ux_reddit_comment_id")
    collection.create_index([("post_id", ASCENDING)], name="ix_reddit_comment_post_id")


def _build_user_agent() -> str:
    configured_user_agent = _get_optional_env("REDDIT_USER_AGENT")
    if configured_user_agent:
        return configured_user_agent
    return DEFAULT_USER_AGENT


def _build_reddit_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": _build_user_agent(),
            "Accept": "application/json,text/html,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )
    return session


def _get_reddit_base_urls() -> list[str]:
    return _get_optional_list_env("REDDIT_BASE_URLS", DEFAULT_REDDIT_BASE_URLS)


def _reddit_public_get(
    session: requests.Session,
    path: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
) -> requests.Response | None:
    last_response = None

    for base_url in _get_reddit_base_urls():
        url = f"{base_url}{path}"
        for attempt in range(max_retries):
            response = session.get(url, params=params, timeout=20)
            last_response = response

            if response.status_code == 429 and attempt < max_retries - 1:
                wait_seconds = 2 * (attempt + 1)
                print(f"Rate limited on {url}. Waiting {wait_seconds} seconds...")
                time.sleep(wait_seconds)
                continue

            if response.status_code == 200:
                return response

            # 403/404 should try the next base URL early.
            if response.status_code in {403, 404}:
                break

    return last_response


def _normalize_comment_node(
    node: dict[str, Any],
    post_id: str,
    subreddit: str,
    depth: int,
) -> dict[str, Any] | None:
    if node.get("kind") != "t1":
        return None

    data = node.get("data", {})
    comment_id = data.get("id")
    body = data.get("body")

    if not comment_id or not body:
        return None

    return {
        "comment_id": comment_id,
        "post_id": post_id,
        "subreddit": subreddit,
        "body": body,
        "author": data.get("author"),
        "created_utc": data.get("created_utc"),
        "score": data.get("score"),
        "parent_id": data.get("parent_id"),
        "link_id": data.get("link_id"),
        "permalink": data.get("permalink"),
        "depth": depth,
        "source": "reddit_public_scraper",
    }


def _collect_comment_nodes(
    nodes: list[dict[str, Any]],
    post_id: str,
    subreddit: str,
    include_nested_replies: bool,
    max_reply_depth: int,
    current_depth: int = 0,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    for node in nodes:
        comment = _normalize_comment_node(node, post_id=post_id, subreddit=subreddit, depth=current_depth)
        if comment:
            collected.append(comment)

            replies = node.get("data", {}).get("replies")
            if (
                include_nested_replies
                and isinstance(replies, dict)
                and current_depth < max_reply_depth
            ):
                reply_children = replies.get("data", {}).get("children", [])
                collected.extend(
                    _collect_comment_nodes(
                        reply_children,
                        post_id=post_id,
                        subreddit=subreddit,
                        include_nested_replies=include_nested_replies,
                        max_reply_depth=max_reply_depth,
                        current_depth=current_depth + 1,
                    )
                )

    return collected


def _fetch_reddit_post_comments(
    session: requests.Session,
    subreddit: str,
    post_id: str,
    max_comments_per_post: int,
    include_nested_replies: bool,
    max_reply_depth: int,
) -> list[dict[str, Any]]:
    response = _reddit_public_get(
        session,
        f"/r/{subreddit}/comments/{post_id}.json",
        params={
            "sort": "top",
            "limit": min(max_comments_per_post, 100),
            "depth": max_reply_depth if include_nested_replies else 0,
            "raw_json": 1,
        },
        max_retries=3,
    )

    if not response or response.status_code != 200:
        status = response.status_code if response else "no-response"
        body_preview = response.text[:250] if response else ""
        print(
            f"Failed to scrape comments for r/{subreddit} post {post_id}: "
            f"{status} {body_preview}"
        )
        return []

    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        return []

    comment_children = payload[1].get("data", {}).get("children", [])
    collected = _collect_comment_nodes(
        comment_children,
        post_id=post_id,
        subreddit=subreddit,
        include_nested_replies=include_nested_replies,
        max_reply_depth=max_reply_depth,
    )

    return collected[:max_comments_per_post]


def _upsert_documents(collection, documents: list[dict[str, Any]], id_field: str) -> tuple[int, int]:
    inserted_count = 0
    updated_count = 0

    for document in documents:
        result = collection.update_one(
            {id_field: document[id_field]},
            {"$set": document},
            upsert=True,
        )

        if result.upserted_id:
            inserted_count += 1
        elif result.modified_count > 0:
            updated_count += 1

    return inserted_count, updated_count


def scrape_reddit_json(
    subreddit: str,
    target_documents: int = 1000,
    collection_name: str = "reddit_posts",
) -> None:
    """
    Scrapes subreddit posts and (optionally) comments from public Reddit endpoints.
    No OAuth credentials are required.
    """
    mongo_port = int(_get_required_env("MONGO_PORT"))
    mongo_db = _get_required_env("MONGO_DB")
    include_comments = _get_optional_bool_env("REDDIT_INCLUDE_COMMENTS", False)
    comment_collection_name = _get_optional_env("REDDIT_COMMENT_COLLECTION", "reddit_comments")
    max_comments_per_post = _get_optional_int_env("REDDIT_MAX_COMMENTS_PER_POST", 3)
    include_nested_replies = _get_optional_bool_env("REDDIT_INCLUDE_NESTED_REPLIES", True)
    max_reply_depth = _get_optional_int_env("REDDIT_MAX_REPLY_DEPTH", 2)

    session = _build_reddit_session()

    client = _build_mongo_client(mongo_port=mongo_port)
    db = client[mongo_db]
    collection = db[collection_name]
    _ensure_post_indexes(collection)

    comments_collection = None
    if include_comments:
        comments_collection = db[comment_collection_name]
        _ensure_comment_indexes(comments_collection)

    after = None
    valid_processed = 0
    inserted_count = 0
    updated_count = 0
    inserted_comments_count = 0
    updated_comments_count = 0

    while valid_processed < target_documents:
        remaining = target_documents - valid_processed
        page_limit = min(100, remaining)
        params = {"limit": page_limit, "raw_json": 1}
        if after:
            params["after"] = after

        response = _reddit_public_get(
            session,
            f"/r/{subreddit}/new.json",
            params=params,
            max_retries=3,
        )

        if not response or response.status_code != 200:
            status = response.status_code if response else "no-response"
            print(f"Failed to fetch data from r/{subreddit}: {status}")
            break

        data = response.json().get("data", {})
        posts = data.get("children", [])
        after = data.get("after")

        if not posts:
            break

        page_valid = 0
        page_inserted = 0
        page_updated = 0
        page_inserted_comments = 0
        page_updated_comments = 0

        for post in posts:
            post_data = post.get("data", {})
            post_id = post_data.get("id")
            if not post_id:
                continue

            post_text = (post_data.get("selftext") or "").strip()
            should_store_post = bool(post_text) or include_comments
            if not should_store_post:
                continue

            document = {
                "post_id": post_id,
                "title": post_data.get("title"),
                "selftext": post_data.get("selftext"),
                "subreddit": post_data.get("subreddit"),
                "created_utc": post_data.get("created_utc"),
                "url": post_data.get("url"),
                "source": "reddit_public_scraper",
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

            if include_comments and comments_collection is not None:
                comments = _fetch_reddit_post_comments(
                    session=session,
                    subreddit=subreddit,
                    post_id=post_id,
                    max_comments_per_post=max_comments_per_post,
                    include_nested_replies=include_nested_replies,
                    max_reply_depth=max_reply_depth,
                )

                if comments:
                    comments_inserted, comments_updated = _upsert_documents(
                        comments_collection,
                        comments,
                        id_field="comment_id",
                    )
                    inserted_comments_count += comments_inserted
                    updated_comments_count += comments_updated
                    page_inserted_comments += comments_inserted
                    page_updated_comments += comments_updated

                    collection.update_one(
                        {"post_id": post_id},
                        {
                            "$set": {
                                "reddit_comment_count": len(comments),
                                "reddit_comments_source": comment_collection_name,
                            }
                        },
                        upsert=False,
                    )

            if valid_processed >= target_documents:
                break

        print(
            f"r/{subreddit}: processed_valid={valid_processed}/{target_documents} "
            f"(page_valid={page_valid}, page_inserted={page_inserted}, page_updated={page_updated}, "
            f"comments_inserted={page_inserted_comments}, comments_updated={page_updated_comments})"
        )

        if after is None:
            break

        time.sleep(0.8)

    print(
        f"Completed r/{subreddit} in '{collection_name}': processed_valid={valid_processed}, "
        f"inserted={inserted_count}, updated={updated_count}."
    )
    if include_comments:
        print(
            f"Comment scraping for r/{subreddit} stored {inserted_comments_count} new comments "
            f"and updated {updated_comments_count}."
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
