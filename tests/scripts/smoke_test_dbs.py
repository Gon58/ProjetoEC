import os
import time
from typing import Any

import psycopg
from pymongo import MongoClient
import chromadb


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def test_postgres() -> None:
    host = env("POSTGRES_HOST", "ec-project-postgres")
    port = int(env("POSTGRES_PORT", "5432"))
    db = env("POSTGRES_DB", "ec_project")
    user = env("POSTGRES_USER", "ec_project")
    password = env("POSTGRES_PASSWORD", "ec_project_pass")

    conn_str = f"host={host} port={port} dbname={db} user={user} password={password}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            val = cur.fetchone()
            assert val == (1,)
    print("Postgres OK (SELECT 1)")


def test_mongo() -> None:
    host = env("MONGO_HOST", "ec-project-mongo")
    port = int(env("MONGO_PORT", "27017"))
    db_name = env("MONGO_DB", "ec_project")

    client = MongoClient(host=host, port=port, serverSelectionTimeoutMS=5000)
    # ping
    client.admin.command("ping")

    db = client[db_name]
    col = db["smoke_test"]

    # write + read
    doc: dict[str, Any] = {"_id": "hello", "msg": "world", "ts": time.time()}
    col.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    out = col.find_one({"_id": "hello"})
    assert out is not None and out.get("msg") == "world"
    print("Mongo OK (ping + insert + read)")


def test_chroma() -> None:
    host = env("CHROMA_HOST", "ec-project-chroma")
    port = int(env("CHROMA_PORT", "8000"))

    # Chroma server client
    client = chromadb.HttpClient(host=host, port=port)

    # collection
    col = client.get_or_create_collection(name="smoke_test")

    # add 1 embedding "dummy"
    col.upsert(
        ids=["doc1"],
        documents=["hello world"],
        metadatas=[{"source": "smoke"}],
        embeddings=[[0.1, 0.2, 0.3, 0.4]],
    )

    # query
    res = col.query(
        query_embeddings=[[0.1, 0.2, 0.3, 0.4]],
        n_results=1,
    )
    assert res["ids"][0][0] == "doc1"
    print("Chroma OK (collection + upsert + query)")


def main() -> None:
    test_postgres()
    test_mongo()
    test_chroma()
    print("\nSmoke test OK: app liga a Postgres + Mongo + Chroma")


if __name__ == "__main__":
    main()
