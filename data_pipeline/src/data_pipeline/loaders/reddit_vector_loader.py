import os

import chromadb
import requests
from pymongo import MongoClient


def _build_mongo_client() -> MongoClient:
    return MongoClient(
        host=os.getenv("MONGO_HOST", "localhost"),
        port=int(os.getenv("MONGO_PORT", 27017)),
    )


def _build_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", 8000)),
    )


def _embed_text(ollama_url: str, text: str) -> list[float] | None:
    response = requests.post(
        f"{ollama_url}/api/embed",
        json={"model": "embeddinggemma:latest", "input": text},
        timeout=60,
    )
    if response.status_code != 200:
        print(f"Embedding request failed: {response.status_code} {response.text[:250]}")
        return None

    payload = response.json()
    embeddings = payload.get("embeddings") or []
    if not embeddings:
        return None

    return embeddings[0]


def _index_collection(
    mongo_collection,
    chroma_collection,
    source_label: str,
    document_builder,
    id_field: str,
) -> int:
    documents = list(mongo_collection.find({}))
    print(f"Indexing {len(documents)} documents from {source_label} to Chroma...")

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    indexed_count = 0

    for index, document in enumerate(documents, start=1):
        doc_text = document_builder(document).strip()
        if not doc_text:
            continue

        embedding = _embed_text(ollama_url, doc_text)
        if not embedding:
            continue

        chroma_collection.upsert(
            ids=[document[id_field]],
            metadatas=[{
                "subreddit": document.get("subreddit"),
                "url": document.get("url"),
                "source": document.get("source"),
                "collection": source_label,
                "post_id": document.get("post_id"),
                "comment_id": document.get("comment_id"),
                "parent_id": document.get("parent_id"),
                "depth": document.get("depth"),
            }],
            embeddings=[embedding],
            documents=[doc_text],
        )
        indexed_count += 1

        if index % 50 == 0:
            print(f"  {index}/{len(documents)} processed from {source_label}")

    print(f"Done! {indexed_count} documents indexed in Chroma collection '{source_label}'")
    return indexed_count


def index_reddit_posts_to_chroma() -> None:
    mongo_client = _build_mongo_client()
    db = mongo_client[os.getenv("MONGO_DB", "ec_project")]
    chroma_client = _build_chroma_client()

    reddit_collection_name = os.getenv("REDDIT_COLLECTION", "reddit_posts")
    reddit_comments_collection_name = os.getenv("REDDIT_COMMENT_COLLECTION", "reddit_comments")

    posts_collection = db[reddit_collection_name]
    posts_chroma_collection = chroma_client.get_or_create_collection(name=reddit_collection_name)

    _index_collection(
        mongo_collection=posts_collection,
        chroma_collection=posts_chroma_collection,
        source_label=reddit_collection_name,
        document_builder=lambda item: f"{item.get('title', '')} {item.get('selftext', '')}",
        id_field="post_id",
    )

    if reddit_comments_collection_name in db.list_collection_names():
        comments_collection = db[reddit_comments_collection_name]
        comments_chroma_collection = chroma_client.get_or_create_collection(name=reddit_comments_collection_name)

        _index_collection(
            mongo_collection=comments_collection,
            chroma_collection=comments_chroma_collection,
            source_label=reddit_comments_collection_name,
            document_builder=lambda item: item.get("body", ""),
            id_field="comment_id",
        )
    else:
        print(f"Skipping '{reddit_comments_collection_name}' because the Mongo collection does not exist yet.")

    mongo_client.close()


if __name__ == "__main__":
    index_reddit_posts_to_chroma()