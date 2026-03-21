"""
Smoke test for integration.

Objective:
- Validate that the application container can connect and perform minimal operations
  on the 3 types of persistence in the project:
  1) SQL: PostgreSQL
  2) NoSQL: MongoDB
  3) Vectorial: ChromaDB

How to execute (inside the app container):
    python scripts/smoke_test_dbs.py

This script performs real operations (read/write/query) to ensure that the services
are operational and that communication between containers is correct.
"""

import os
import time
from typing import Any

import chromadb
import psycopg
from pymongo import MongoClient


def env(name: str, default: str) -> str:
    """
    Reads an environment variable with fallback.

    Args:
        name: Name of the environment variable.
        default: Default value if the variable does not exist.

    Returns:
        The value of the environment variable if it exists; otherwise, `default`.
    """
    return os.getenv(name, default)


def test_postgres() -> None:
    """
    Tests connectivity and basic execution in PostgreSQL.

    Operations:
    - Connects to PostgreSQL using parameters from docker-compose (.env vars).
    - Executes `SELECT 1` to validate connection and query execution capability.

    Raises:
        AssertionError: If the query result is not as expected.
        psycopg.Error: If there is a connection/authentication/network error.
    """
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
    """
    Tests connectivity and basic read/write in MongoDB.

    Operations:
    - Creates MongoDB client and pings the server.
    - Upserts 1 document in the `smoke_test` collection.
    - Reads the document and validates content.

    Raises:
        AssertionError: If the document is not read or has unexpected values.
        pymongo.errors.PyMongoError: If there is a connection/network/server error.
    """
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
    """
    Tests connectivity and basic operation in Chroma (Vector DB) via HTTP.

    Operations:
    - Connects to the Chroma server.
    - Creates/gets the `smoke_test` collection.
    - Upserts 1 document with a "dummy" embedding.
    - Queries with the same embedding and validates that it returns the expected id.

    Note:
        The embedding used is small and artificial, only to validate the pipeline.

    Raises:
        AssertionError: If the query result does not return the expected id.
        Exception: If there is a connection error to the Chroma server.
    """
    host = env("CHROMA_HOST", "ec-project-chroma")
    port = int(env("CHROMA_PORT", "8000"))

    # Chroma server client
    client = chromadb.HttpClient(host=host, port=port)

    # collection
    col = client.get_or_create_collection(name="smoke_test")

    # add 1 "dummy" embedding
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
    print("\nSmoke test OK: app connects to Postgres + Mongo + Chroma")


if __name__ == "__main__":
    main()