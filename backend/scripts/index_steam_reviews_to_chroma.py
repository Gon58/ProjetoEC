"""Indexes Steam reviews from MongoDB into ChromaDB.

Usage:
    python scripts/index_steam_reviews_to_chroma.py
    python scripts/index_steam_reviews_to_chroma.py --limit 500
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Index Steam reviews into Chroma")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum reviews to index")
    parser.add_argument(
        "--collection",
        default="steam_reviews",
        help="Target Chroma collection name",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from pymongo import MongoClient

    from src.core.config import MONGO_DB, MONGO_HOST, MONGO_PORT
    from src.db.vectorial import index_document

    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    try:
        collection = client[MONGO_DB]["steam_reviews"]
        cursor = collection.find({}, {"_id": 0}).limit(args.limit)

        indexed = 0
        skipped = 0

        for review in cursor:
            review_id = str(
                review.get("review_id")
                or review.get("recommendationid")
                or review.get("id")
                or ""
            ).strip()
            text = str(review.get("review_text") or review.get("review") or review.get("text") or "").strip()
            if not review_id or not text:
                skipped += 1
                continue

            author = review.get("author") if isinstance(review.get("author"), dict) else {}

            metadata = {
                "source": "steam_reviews",
                "timestamp_created": review.get("timestamp_created"),
                "voted_up": review.get("voted_up"),
                "author_playtime_forever": author.get("playtime_forever"),
                "author_num_games_owned": author.get("num_games_owned"),
                "is_market_related": review.get("is_market_related"),
            }

            result = index_document(
                doc_id=f"steam_review_{review_id}",
                text=text,
                collection_name=args.collection,
                metadata=metadata,
            )

            if result.get("status") == "success":
                indexed += 1
            else:
                skipped += 1

        print(f"indexed={indexed} skipped={skipped} collection={args.collection}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
